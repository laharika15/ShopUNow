from typing import TypedDict

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from langchain_groq import ChatGroq

from langgraph.graph import (
    StateGraph,
    START,
    END
)

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


class GraphState(TypedDict, total=False):
    query: str
    sentiment: str
    department: str
    context: str
    response: str
    reflection_feedback: str
    needs_escalation: bool


class CategoryOutput(BaseModel):
    sentiment: str = Field(
        description=(
            "The sentiment of the user query: "
            "Positive, Neutral, or Negative."
        )
    )

    department: str = Field(
        description=(
            "The target department. Must be one of: "
            "HR, IT Support, Billing & Payments, "
            "Shipping & Delivery, or Unknown."
        )
    )


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


def categorize_query(
    state: GraphState
) -> GraphState:

    """Categorize query by sentiment and department."""

    llm = get_router_llm()

    structured_llm = (
        llm.with_structured_output(
            CategoryOutput
        )
    )

    prompt = f"""
You are the routing assistant for ShopUNow.

Analyze the user's query.

User query:
"{state['query']}"

Determine:

1. Sentiment:
   - Positive
   - Neutral
   - Negative

2. Department:
   - HR
   - IT Support
   - Billing & Payments
   - Shipping & Delivery
   - Unknown

Use the meaning of the query, not just exact keywords.

For example:
- PTO, vacation, sick leave, employee leave
  → HR
- password, VPN, laptop, login
  → IT Support
- refund, invoice, charge, payment
  → Billing & Payments
- package, shipment, tracking, delivery
  → Shipping & Delivery

If the department is genuinely unclear,
return Unknown.
"""

    result = structured_llm.invoke(
        prompt
    )

    print(
        f"[ROUTER] Department={result.department} "
        f"Sentiment={result.sentiment}"
    )

    return {
        "sentiment": result.sentiment,
        "department": result.department
    }


def human_escalation(
    state: GraphState
) -> GraphState:

    """Return the human escalation response."""

    return {
        "response": (
            "Your query has been escalated to a "
            "human support agent. They will reach "
            "out to you shortly."
        )
    }


def rag_generation(
    state: GraphState
) -> GraphState:

    """
    Retrieve relevant ShopUNow knowledge and let
    the Groq LLM reason over that knowledge.
    """

    context = retrieve_context(
        state["query"],
        state["department"]
    )

    if context == ABSTENTION_MESSAGE:

        print(
            "[RAG] No sufficiently relevant "
            "knowledge found."
        )

        return {
            "context": context,
            "response": context,
            "needs_escalation": True
        }

    print(
        "[RAG] Relevant context found. "
        "Calling Groq generation model."
    )

    llm = get_rag_llm()

    system_prompt = f"""
You are the ShopUNow AI assistant for the
{state['department']} department.

Your job is to understand the user's intent and
answer naturally using ONLY the provided
ShopUNow knowledge.

IMPORTANT:

1. Understand the meaning of the user's question,
   even when the wording differs from the FAQ.

2. Use the retrieved context as the authoritative
   source of ShopUNow policies and procedures.

3. You may synthesize and explain relevant
   information from the retrieved context.

4. Do NOT invent policies, procedures, dates,
   prices, eligibility requirements, or facts.

5. Do NOT use general world knowledge to fill gaps.

6. If the context does not actually contain enough
   information to answer the user's specific
   question, respond exactly:

I don't have enough information in the ShopUNow
knowledge base to answer this accurately.

7. Answer conversationally and directly.

8. Do not mention embeddings, vector databases,
   retrieval, Chroma, or internal system details.

SHOPUNOW KNOWLEDGE:
{context}
"""

    messages = [
        SystemMessage(
            content=system_prompt
        ),
        HumanMessage(
            content=state["query"]
        )
    ]

    response = llm.invoke(messages)

    response_text = response.content.strip()

    # Safety check: if the LLM itself determines that
    # the context is insufficient, escalate.
    if response_text == ABSTENTION_MESSAGE:
        return {
            "context": context,
            "response": response_text,
            "needs_escalation": True
        }

    return {
        "context": context,
        "response": response_text,
        "needs_escalation": False
    }


def reflection_node(
    state: GraphState
) -> GraphState:

    """Optional grounded-response quality check."""

    if state.get(
        "needs_escalation",
        False
    ):
        return {
            "reflection_feedback":
                "Skipped (Escalation)"
        }

    llm = get_rag_llm()

    system_prompt = f"""
You are a quality reviewer for ShopUNow.

Review the answer against the provided context.

Make sure:

- The answer is fully supported by the context.
- No policy or factual information was invented.
- The answer directly addresses the user's question.
- The final answer is clear and concise.

If the answer is correct, return the same answer.

If it contains unsupported information,
rewrite it using ONLY the context.

CONTEXT:
{state['context']}

ANSWER:
{state['response']}
"""

    messages = [
        SystemMessage(
            content=system_prompt
        ),
        HumanMessage(
            content=(
                "Review and output the final "
                "verified answer."
            )
        )
    ]

    refined_response = llm.invoke(
        messages
    )

    return {
        "response": refined_response.content,
        "reflection_feedback":
            "Reflection Applied"
    }


def route_query(
    state: GraphState
) -> str:

    """
    Initial routing.

    Negative sentiment is escalated immediately.
    Unknown departments are escalated.
    Otherwise continue to RAG.
    """

    if state["sentiment"].lower() == "negative":
        return "escalate"

    if state["department"] == "Unknown":
        return "escalate"

    return "rag"


def after_rag(
    state: GraphState
) -> str:

    """
    Decide what happens after RAG generation.
    """

    if state.get(
        "needs_escalation",
        False
    ):
        return "escalate"

    if ENABLE_REFLECTION:
        return "reflect"

    return "end"


workflow = StateGraph(
    GraphState
)

workflow.add_node(
    "categorizer",
    categorize_query
)

workflow.add_node(
    "escalation",
    human_escalation
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
        "rag": "rag"
    }
)

workflow.add_edge(
    "escalation",
    END
)

workflow.add_conditional_edges(
    "rag",
    after_rag,
    {
        "escalate": "escalation",
        "reflect": "reflection",
        "end": END
    }
)

workflow.add_edge(
    "reflection",
    END
)

graph_app = workflow.compile()

# Compile Graph
graph_app = workflow.compile()
