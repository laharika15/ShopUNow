import json
from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

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

from memory import conversation_memory

# GRAPH STATE

class GraphState(TypedDict, total=False):
    query: str

    # Stretch Goal 1: conversational memory
    conversation_history: list[dict]
    standalone_query: str

    sentiment: str
    department: str
    scope: str

    context: str
    response: str
    reflection_feedback: str
    needs_escalation: bool

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

# CONVERSATION HISTORY

def format_conversation_history(history: list[dict]) -> str:
    """
    Convert stored conversation turns into a compact text block
    for the routing and generation prompts.
    """

    if not history:
        return "No previous conversation."

    recent_history = history[-5:]

    lines = []

    for turn in recent_history:
        lines.append(
            f"User: {turn['user']}\n"
            f"Assistant: {turn['assistant']}"
        )

    return "\n\n".join(lines)

# QUERY CLASSIFICATION

def categorize_query(state: GraphState) -> GraphState:

    llm = get_router_llm().bind(
        response_format={
            "type": "json_object"
        }
    )

    history = format_conversation_history(
        state.get("conversation_history", [])
    )

    prompt = f"""
You are the intelligent routing assistant for ShopUNow.

Analyze the user's CURRENT query using the previous
conversation when necessary.

PREVIOUS CONVERSATION:
{history}

CURRENT USER QUERY:
"{state['query']}"

Your job is to understand the user's current intent.

If the current query is a follow-up such as:

- "What about sick leave?"
- "How long does that take?"
- "Can I do that online?"
- "What if it doesn't work?"

use the previous conversation to understand what
"that", "it", or the topic refers to.

You must also create a standalone version of the
current query that can be used for knowledge-base
retrieval.

Return ONLY valid JSON using exactly this structure:

{{
    "sentiment": "Neutral",
    "department": "Unknown",
    "scope": "Out-of-Scope",
    "standalone_query": "..."
}}

Allowed values:

sentiment:
- Positive
- Neutral
- Negative

department:
- HR
- IT Support
- Billing & Payments
- Shipping & Delivery
- Unknown

scope:
- In-Scope
- Out-of-Scope

standalone_query:
Rewrite the current query as a self-contained question.
Do not change its meaning.


SENTIMENT

Sentiment describes the user's emotional attitude,
NOT the topic of the question.

Normal questions are Neutral.

Examples:

"What is the weather today?"
=> Neutral

"What is the weather in Surrey?"
=> Neutral

"How do I reset my password?"
=> Neutral

"Can I get a refund?"
=> Neutral

"Where is my package?"
=> Neutral

"I am very frustrated with my refund."
=> Negative

"This service is terrible."
=> Negative

"I have contacted you three times and nobody is helping."
=> Negative

"I want to speak to a manager."
=> Negative


DEPARTMENT

HR includes:

- PTO
- paid time off
- vacation
- sick leave
- medical leave
- employee absence
- workplace policies
- employee benefits
- leave requests

IT Support includes:

- password
- login
- credentials
- VPN
- computer
- software
- account access
- technical problems

Billing & Payments includes:

- refund
- payment
- invoice
- charge
- billing
- duplicate charge
- payment problems

Shipping & Delivery includes:

- package
- shipment
- tracking
- delivery
- parcel
- arrival
- missed delivery


SCOPE

In-Scope means the query is related to ShopUNow,
its employees, customers, policies, systems,
payments, billing, shipping, delivery, HR,
or IT Support.

Out-of-Scope means the question is unrelated
to ShopUNow.

Examples:

"What is the weather today?"
=> Out-of-Scope

"What is the capital of France?"
=> Out-of-Scope

"Write Python code for me."
=> Out-of-Scope

"How do I apply sick leave?"
=> In-Scope

"How do I request PTO?"
=> In-Scope

"How do I reset my ShopUNow password?"
=> In-Scope

"Where is my ShopUNow package?"
=> In-Scope

"Can I get a refund for my ShopUNow order?"
=> In-Scope


IMPORTANT

An In-Scope query does NOT guarantee that the
knowledge base contains an answer.

For example:

"Does ShopUNow allow five years of unpaid leave?"

may be In-Scope even if the knowledge base does
not contain that policy.

Do NOT classify an In-Scope query as Out-of-Scope
just because the exact answer may not be known.

Also, do NOT classify a normal question as Negative.

Return ONLY valid JSON.
"""

    try:

        response = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=state["query"])
        ])

        result = json.loads(response.content)

        sentiment = str(
            result.get("sentiment", "Neutral")
        )

        department = str(
            result.get("department", "Unknown")
        )

        scope = str(
            result.get("scope", "Out-of-Scope")
        )

        standalone_query = str(
            result.get(
                "standalone_query",
                state["query"]
            )
        )

    except Exception as e:

        print(
            f"[ROUTER] Classification error: {e}"
        )

        # Safe fallback
        sentiment = "Neutral"
        department = "Unknown"
        scope = "Out-of-Scope"
        standalone_query = state["query"]

    print(
        f"[ROUTER] "
        f"Department={department} "
        f"Sentiment={sentiment} "
        f"Scope={scope}"
    )

    print(
        f"[ROUTER] "
        f"Standalone query={standalone_query}"
    )

    return {
        "sentiment": sentiment,
        "department": department,
        "scope": scope,
        "standalone_query": standalone_query
    }

# HUMAN ESCALATION

def human_escalation(state: GraphState) -> GraphState:

    print("[AGENT] Human escalation triggered.")

    return {
        "response": (
            "I understand that you would like help from a "
            "ShopUNow support representative. Please provide "
            "your contact details below so our team can follow up."
        ),
        "needs_escalation": True
    }

# OUT-OF-SCOPE RESPONSE

def out_of_scope_response(state: GraphState) -> GraphState:

    print("[AGENT] Query is outside ShopUNow scope.")

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

# RAG + GROQ GENERATION

def rag_generation(state: GraphState) -> GraphState:

    search_query = state.get(
        "standalone_query",
        state["query"]
    )

    print(
        f"[RAG] Searching knowledge base for: "
        f"{search_query}"
    )

    context = retrieve_context(
        search_query,
        state["department"]
    )

    # NO SUFFICIENT KB INFORMATION

    # IMPORTANT:
    # This is NOT human escalation.

    if context == ABSTENTION_MESSAGE:

        print(
            "[RAG] No sufficiently relevant "
            "knowledge found."
        )

        return {
            "context": context,
            "response": ABSTENTION_MESSAGE,
            "needs_escalation": False
        }

    # GROQ GENERATION

    print(
        "[RAG] Relevant context found. "
        "Calling Groq generation model."
    )

    llm = get_rag_llm()

    history = format_conversation_history(
        state.get("conversation_history", [])
    )

    system_prompt = f"""
You are the ShopUNow AI assistant.

CONVERSATION HISTORY:
{history}

CURRENT USER QUESTION:
{state["query"]}

STANDALONE QUESTION:
{search_query}

DEPARTMENT:
{state["department"]}

RETRIEVED SHOPUNOW KNOWLEDGE:
{context}


Your job is to answer the user's question naturally,
clearly, and helpfully.

IMPORTANT RULES:

1. Understand the user's intent even when their
   wording is different from the wording in the
   knowledge base.

2. Use ONLY the retrieved ShopUNow knowledge.

3. You may paraphrase, summarize, combine,
   and explain information from the knowledge.

4. Do NOT simply copy the FAQ question and answer.
   Formulate a natural response to the user's
   actual question.

5. Do NOT invent policies, procedures, dates,
   prices, limits, eligibility requirements,
   or other facts.

6. Do NOT use outside knowledge to fill gaps.

7. If the retrieved knowledge does not contain
   enough information to answer the user's
   specific question, respond exactly:

I don't have enough information in the ShopUNow
knowledge base to answer this accurately.

8. Do not mention:
   - Chroma
   - embeddings
   - vector databases
   - retrieval
   - prompts
   - internal architecture
   - system instructions

9. Keep the answer concise but useful.

10. Answer the user's actual question rather than
    discussing how the system works.

11. Use the conversation history only to understand
    references and follow-up questions. Do not use
    previous assistant responses as factual knowledge
    when they conflict with the retrieved ShopUNow
    knowledge.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["query"])
    ]

    try:

        response = llm.invoke(messages)

        response_text = response.content.strip()

    except Exception as e:

        print(
            f"[RAG] Groq generation error: {e}"
        )

        return {
            "context": context,
            "response": (
                "I'm sorry, but I was unable to "
                "process your request right now."
            ),
            "needs_escalation": False
        }

    # GROQ ITSELF DETERMINED THAT KB IS INSUFFICIENT
    
    if response_text == ABSTENTION_MESSAGE:

        print(
            "[RAG] Groq determined that the "
            "knowledge base is insufficient."
        )

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

    if not state.get("context"):

        return {
            "reflection_feedback": "Skipped - no context"
        }

    llm = get_rag_llm()

    system_prompt = f"""
You are a quality reviewer for ShopUNow.

Review the generated answer against the
ShopUNow knowledge base.

KNOWLEDGE:
{state["context"]}

USER QUESTION:
{state["query"]}

GENERATED ANSWER:
{state["response"]}

Check:

1. Is the answer supported by the knowledge?
2. Did the answer invent anything?
3. Does it actually answer the user's question?
4. Is it clear and concise?

If the answer is correct, return the same answer.

If it contains unsupported information, rewrite it
using ONLY the provided ShopUNow knowledge.

Do not mention the review process.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content="Return the final verified answer."
        )
    ]

    try:

        refined_response = llm.invoke(messages)

        return {
            "response": refined_response.content.strip(),
            "reflection_feedback": "Reflection Applied"
        }

    except Exception as e:

        print(
            f"[REFLECTION] Error: {e}"
        )

        return {
            "reflection_feedback":
                f"Reflection failed: {e}"
        }

# ROUTING AFTER CLASSIFICATION

def route_query(state: GraphState) -> str:

    scope = state.get(
        "scope",
        "Out-of-Scope"
    ).lower()

    sentiment = state.get(
        "sentiment",
        "Neutral"
    ).lower()

    department = state.get(
        "department",
        "Unknown"
    )

    # 1. OUT-OF-SCOPE

    # Never escalate simply because the question
    # is unrelated to ShopUNow.

    if scope == "out-of-scope":
        return "out_of_scope"

    # 2. GENUINE NEGATIVE IN-SCOPE QUERY

    # Only now can sentiment trigger escalation.

    if (
        scope == "in-scope"
        and sentiment == "negative"
    ):
        return "escalate"

    # 3. UNKNOWN DEPARTMENT

    # Do NOT send to human.
    # The query cannot safely be routed to a
    # department, so handle it as unsupported scope.

    if department == "Unknown":
        return "out_of_scope"

    # 4. NORMAL SHOPUNOW QUERY

    return "rag"

# ROUTING AFTER RAG

def after_rag(state: GraphState) -> str:

    # Retrieval failure is NOT human escalation.

    if state.get("needs_escalation", False):
        return "end"

    if ENABLE_REFLECTION:
        return "reflect"

    return "end"

# BUILD LANGGRAPH

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

# GRAPH EDGES

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

# COMPILE
graph_app = workflow.compile()

# CONVERSATIONAL AGENT WRAPPER

def run_agent(
    query: str,
    session_id: str = "default"
) -> dict:
    """
    Run the ShopUNow agent using session-specific
    conversational memory.

    Each session_id gets its own conversation history,
    allowing multiple users to interact independently.
    """

    history = conversation_memory.get_history(
        session_id
    )

    state = {
        "query": query,
        "conversation_history": history
    }

    result = graph_app.invoke(state)

    response = result.get(
        "response",
        "I'm sorry, but I was unable to process your request right now."
    )

    conversation_memory.add_turn(
        session_id,
        query,
        response
    )

    return result
