from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from config import GROQ_API_KEY, ROUTER_MODEL, RAG_MODEL, ENABLE_REFLECTION
from retrieval import retrieve_context

class GraphState(TypedDict):
    query: str
    sentiment: str
    department: str
    context: str
    response: str
    reflection_feedback: str

# Pydantic model for categorization output
class CategoryOutput(BaseModel):
    sentiment: str = Field(description="The sentiment of the user query: Positive, Neutral, or Negative.")
    department: str = Field(description="The target department for the query. Must be one of: HR, IT Support, Billing & Payments, Shipping & Delivery, or Unknown.")

def get_router_llm():
    return ChatGroq(api_key=GROQ_API_KEY, model=ROUTER_MODEL, temperature=0)

def get_rag_llm():
    return ChatGroq(api_key=GROQ_API_KEY, model=RAG_MODEL, temperature=0.1)

def categorize_query(state: GraphState) -> GraphState:
    """Categorizes the query for sentiment and department."""
    llm = get_router_llm()
    structured_llm = llm.with_structured_output(CategoryOutput)
    
    prompt = f"""Analyze the following user query for a retail company (ShopUNow).
    
Query: "{state['query']}"

Determine the sentiment and which department should handle this query.
Valid departments: HR, IT Support, Billing & Payments, Shipping & Delivery.
If it doesn't clearly match one of these, output 'Unknown'.
"""
    result = structured_llm.invoke(prompt)
    
    return {
        "sentiment": result.sentiment,
        "department": result.department
    }

def human_escalation(state: GraphState) -> GraphState:
    """Provides a human escalation response."""
    return {
        "response": "Your query has been escalated to a human support agent. They will reach out to you shortly."
    }

def rag_generation(state: GraphState) -> GraphState:
    """Retrieves context and generates a grounded response."""
    # 1. Retrieve Context
    context = retrieve_context(state["query"], state["department"])
    
    # Check for controlled abstention
    if context == "I don't have enough information in the ShopUNow knowledge base to answer this accurately.":
        return {"context": context, "response": context}
        
    # 2. Generate Grounded Answer
    llm = get_rag_llm()
    
    system_prompt = f"""You are an AI assistant for ShopUNow, answering questions for the {state['department']} department.
    
CRITICAL INSTRUCTIONS:
- Use ONLY the following provided context to answer the question.
- Do NOT invent policies, dates, prices, procedures, or facts.
- If the provided context does not fully answer the question, state exactly: "I don't have enough information in the ShopUNow knowledge base to answer this accurately."
- Do NOT use general world knowledge to fill gaps.

CONTEXT:
{context}
"""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state['query'])
    ]
    
    response = llm.invoke(messages)
    
    return {
        "context": context,
        "response": response.content
    }

def reflection_node(state: GraphState) -> GraphState:
    """Reflects on the generated response and improves it if necessary."""
    # Skip reflection if we already abstained
    if state["response"] == "I don't have enough information in the ShopUNow knowledge base to answer this accurately.":
        return {"reflection_feedback": "Skipped (Abstention)"}

    llm = get_rag_llm()
    system_prompt = f"""You are a quality assurance reviewer for ShopUNow. 
Review the following answer based strictly on the provided context.
Ensure the answer is completely grounded in the context and doesn't contain hallucinations.
If the answer is good, just output the exact same answer.
If the answer hallucinated information, correct it to rely ONLY on the context.

CONTEXT:
{state['context']}

ORIGINAL ANSWER:
{state['response']}
"""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Review and output the final verified answer.")
    ]
    
    refined_response = llm.invoke(messages)
    
    return {
        "response": refined_response.content,
        "reflection_feedback": "Reflection Applied"
    }

def route_query(state: GraphState) -> str:
    """Routes the query based on categorization."""
    if state["sentiment"].lower() == "negative":
        return "escalate"
    
    if state["department"] == "Unknown":
        return "escalate"
        
    return "rag"

def should_reflect(state: GraphState) -> str:
    """Determines whether to route to reflection or end."""
    if ENABLE_REFLECTION:
        return "reflect"
    return "end"

# Build the LangGraph
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node("categorizer", categorize_query)
workflow.add_node("escalation", human_escalation)
workflow.add_node("rag", rag_generation)
workflow.add_node("reflection", reflection_node)

# Add Edges
workflow.add_edge(START, "categorizer")

workflow.add_conditional_edges(
    "categorizer",
    route_query,
    {
        "escalate": "escalation",
        "rag": "rag"
    }
)

workflow.add_edge("escalation", END)

workflow.add_conditional_edges(
    "rag",
    should_reflect,
    {
        "reflect": "reflection",
        "end": END
    }
)

workflow.add_edge("reflection", END)

# Compile Graph
graph_app = workflow.compile()
