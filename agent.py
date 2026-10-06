from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from config import (
    GROQ_API_KEY,
    ROUTER_MODEL,
    RAG_MODEL,
    ENABLE_REFLECTION
)

from retrieval import (
    retrieve_context,
    ABSTENTION_MESSAGE
)

# STATE

class GraphState(TypedDict, total=False):
    query: str
    sentiment: str
    department: str
    scope: str
    context: str
    response: str
    reflection_feedback: str
    needs_escalation: bool

# ROUTER OUTPUT

class CategoryOutput(BaseModel):

    sentiment: str = Field(
        description=(
            "User sentiment: Positive, Neutral, or Negative."
        )
    )

    department: str = Field(
        description=(
            "ShopUNow department: HR, IT Support, "
            "Billing & Payments, Shipping & Delivery, "
            "or Unknown."
        )
    )

    scope: str = Field(
        description=(
            "Whether the query is within ShopUNow scope. "
            "Return In-Scope or Out-of-Scope."
        )
    )


# GROQ MODELS

def get_router_llm():

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=ROUTER_MODEL,
        temperature=0
    )


def get_rag_llm():

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=RAG_MODEL,
        temperature=0.1
    )


# QUERY UNDERSTANDING / ROUTING

def categorize_query(state: GraphState) -> GraphState:

    llm = get_router_llm()

    structured_llm = llm.with_structured_output(
        CategoryOutput
    )

    prompt = f"""
You are the intelligent routing assistant for ShopUNow.

Analyze the user's query based on its meaning.

USER QUERY:
"{state['query']}"

Determine:

1. SENTIMENT

1. SENTIMENT

Choose exactly one:

- Positive
- Neutral
- Negative

IMPORTANT:
Sentiment describes the user's emotional attitude,
NOT the subject of the question.

A normal factual question is Neutral.

Examples:

"What is the weather today?"
→ Neutral

"What is the weather in Surrey?"
→ Neutral

"How do I reset my password?"
→ Neutral

"Can I get a refund?"
→ Neutral

"I am very frustrated with my refund."
→ Negative

"This is terrible. I have contacted you three times."
→ Negative

"I want to speak to a manager because nobody is helping me."
→ Negative

Do NOT classify a question as Negative simply because
the topic involves a problem, absence, refund, delivery,
or support request.

2. DEPARTMENT

Choose exactly one:

- HR
- IT Support
- Billing & Payments
- Shipping & Delivery
- Unknown

Use semantic meaning, not exact keywords.

Examples:

HR:
- PTO
- paid time off
- vacation
- sick leave
- employee absence
- benefits
- workplace policies

IT Support:
- password
- login
- VPN
- computer
- software
- account access
- technical problem

Billing & Payments:
- refund
- payment
- invoice
- charge
- billing
- duplicate payment

Shipping & Delivery:
- package
- shipment
- tracking
- delivery
- parcel
- arrival

3. SCOPE

Choose exactly one:

- In-Scope
- Out-of-Scope

The query is In-Scope when it is about ShopUNow
or one of its supported departments.

The query is Out-of-Scope when it is unrelated to
ShopUNow services, policies, employees, customers,
IT support, billing, payments, shipping, delivery,
or other ShopUNow operations.

Examples of Out-of-Scope:

"What is the capital of France?"
"Write me a Python program."
"Who won the World Cup?"
"Tell me a joke."

IMPORTANT:

An In-Scope query can still have NO answer in the
ShopUNow knowledge base.

That does NOT make it Out-of-Scope.

Return only the structured classification.
"""

    result = structured_llm.invoke(prompt)

    print(
        f"[ROUTER] "
        f"Department={result.department} "
        f"Sentiment={result.sentiment} "
        f"Scope={result.scope}"
    )

    return {
        "sentiment": result.sentiment,
        "department": result.department,
        "scope": result.scope
    }

# HUMAN ESCALATION

def human_escalation(state: GraphState) -> GraphState:

    return {
        "response": (
            "Your query has been escalated to a "
            "human support agent. They will reach "
            "out to you shortly."
        ),
        "needs_escalation": True
    }


# OUT-OF-SCOPE RESPONSE

def out_of_scope_response(state: GraphState) -> GraphState:

    return {
        "response": (
            "I'm the ShopUNow AI assistant. I can help "
            "with HR, IT Support, Billing & Payments, "
            "and Shipping & Delivery questions. "
            "I can't help with questions outside "
            "ShopUNow's supported areas."
        ),
        "needs_escalation": False
    }

# RAG GENERATION

def rag_generation(state: GraphState) -> GraphState:

    context = retrieve_context(
        state["query"],
        state["department"]
    )

    # KB DOES NOT CONTAIN SUFFICIENT INFORMATION
    #
    # IMPORTANT:
    # This is NOT human escalation.

    if context == ABSTENTION_MESSAGE:

        print(
            "[RAG] No sufficiently relevant "
            "knowledge found in ShopUNow KB."
        )

        return {
            "context": context,
            "response": ABSTENTION_MESSAGE,
            "needs_escalation": False
        }

    print(
        "[RAG] Relevant context found. "
        "Calling Groq generation model."
    )

    llm = get_rag_llm()

    system_prompt = f"""
You are the ShopUNow AI assistant.

DEPARTMENT:
{state["department"]}

USER QUESTION:
{state["query"]}

SHOPUNOW KNOWLEDGE BASE:
{context}

Your task is to answer the user's question naturally
using the ShopUNow knowledge provided above.

RULES:

1. Understand the user's intent, even if the wording
   is different from the wording in the knowledge base.

2. Use ONLY the provided ShopUNow knowledge.

3. You may paraphrase, summarize, combine, and explain
   relevant information from the retrieved knowledge.

4. Do NOT invent policies, procedures, dates, prices,
   limits, eligibility rules, or other facts.

5. Do NOT use outside knowledge to fill gaps.

6. If the knowledge does not contain enough information
   to answer the user's specific question, respond
   exactly:

I don't have enough information in the ShopUNow
knowledge base to answer this accurately.

7. Do not mention Chroma, embeddings, vector databases,
   retrieval, prompts, or internal implementation details.

8. Be concise, helpful, and conversational.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["query"])
    ]

    response = llm.invoke(messages)

    response_text = response.content.strip()

    if response_text == ABSTENTION_MESSAGE:

        return {
            "context": context,
            "response": response_text,
            "needs_escalation": False
        }

    return {
        "context": context,
        "response": response_text,
        "needs_escalation": False
    }

# OPTIONAL REFLECTION

def reflection_node(state: GraphState) -> GraphState:

    llm = get_rag_llm()

    system_prompt = f"""
You are a quality reviewer for ShopUNow.

Review the answer against the provided knowledge.

CONTEXT:
{state["context"]}

ANSWER:
{state["response"]}

Make sure:

- The answer is supported by the context.
- Nothing was invented.
- The answer addresses the user's question.
- The answer is clear and concise.

If the answer is correct, return the same answer.

If it contains unsupported information, rewrite it
using ONLY the provided context.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content="Review and return the final verified answer."
        )
    ]

    refined_response = llm.invoke(messages)

    return {
        "response": refined_response.content.strip(),
        "reflection_feedback": "Reflection Applied"
    }

# ROUTING AFTER CATEGORIZATION

def route_query(state: GraphState) -> str:

    # First determine whether the query belongs
    # to ShopUNow at all.
    if state["scope"].lower() == "out-of-scope":
        return "out_of_scope"

    # Only escalate when an IN-SCOPE ShopUNow query
    # is genuinely negative/complaint-oriented.
    if (
        state["scope"].lower() == "in-scope"
        and state["sentiment"].lower() == "negative"
    ):
        return "escalate"

    # Unknown department should not automatically
    # become a human escalation.
    if state["department"] == "Unknown":
        return "out_of_scope"

    return "rag"

# AFTER RAG

def after_rag(state: GraphState) -> str:

    # Retrieval failure is NOT escalation.
    if state.get("needs_escalation", False):
        return "end"

    if ENABLE_REFLECTION:
        return "reflect"

    return "end"

# LANGGRAPH WORKFLOW

workflow = StateGraph(GraphState)

workflow.add_node(
    "categorizer",
    categorize_query
)

workflow.add_node(
    "escalation",
    human_escalation
)

workflow.add_node(
    "out_of_scope",
    out_of_scope_response
)

workflow.add_node(
    "rag",
    rag_generation
)

workflow.add_node(
    "reflection",
    reflection_node
)


workflow.add_edge(
    START,
    "categorizer"
)


workflow.add_conditional_edges(
    "categorizer",
    route_query,
    {
        "escalate": "escalation",
        "out_of_scope": "out_of_scope",
        "rag": "rag"
    }
)


workflow.add_edge(
    "escalation",
    END
)


workflow.add_edge(
    "out_of_scope",
    END
)


workflow.add_conditional_edges(
    "rag",
    after_rag,
    {
        "reflect": "reflection",
        "end": END
    }
)


workflow.add_edge(
    "reflection",
    END
)
graph_app = workflow.compile()   
