import json
import re
from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

from config import (
    GROQ_API_KEY,
    ROUTER_MODEL,
    RAG_MODEL,
    ENABLE_REFLECTION,
)
from retrieval import retrieve_context, ABSTENTION_MESSAGE
from memory import conversation_memory


# ============================================================
# GRAPH STATE
# ============================================================

SUPPORTED_DEPARTMENTS = {
    "HR",
    "IT Support",
    "Billing & Payments",
    "Shipping & Delivery",
}


class GraphState(TypedDict, total=False):
    query: str
    conversation_history: list[dict]
    standalone_query: str
    sentiment: str
    department: str
    scope: str
    context: str
    response: str
    reflection_feedback: str
    needs_escalation: bool


# ============================================================
# MODEL HELPERS
# ============================================================

def get_router_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=ROUTER_MODEL,
        temperature=0,
    )


def get_rag_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=RAG_MODEL,
        temperature=0.1,
    )


def format_conversation_history(history: list[dict]) -> str:
    """Format recent turns for routing and answer generation."""
    if not history:
        return "No previous conversation."

    lines = []
    for turn in history[-5:]:
        lines.append(
            f"User: {turn.get('user', '')}\n"
            f"Assistant: {turn.get('assistant', '')}"
        )

    return "\n\n".join(lines)


# ============================================================
# OPTIONAL DETERMINISTIC DEPARTMENT FALLBACK
# ============================================================

DEPARTMENT_PATTERNS = {
    "HR": [
        r"\bpto\b",
        r"\bpaid time off\b",
        r"\bvacation\b",
        r"\btime off\b",
        r"\bsick leave\b",
        r"\bmedical leave\b",
        r"\bparental leave\b",
        r"\bpaternity leave\b",
        r"\bmaternity leave\b",
        r"\bleave request\b",
        r"\bemployee benefits\b",
        r"\bworkplace polic(?:y|ies)\b",
    ],
    "IT Support": [
        r"\bcomputer\b",
        r"\blaptop\b",
        r"\bpc\b",
        r"\bworkstation\b",
        r"\bpassword\b",
        r"\bcredentials\b",
        r"\blog ?in\b",
        r"\bsign[- ]in\b",
        r"\baccount access\b",
        r"\bvpn\b",
        r"\bsoftware\b",
        r"\bapplication (?:error|crash|issue)\b",
        r"\bcomputer is slow\b",
        r"\blaptop is slow\b",
        r"\bfreez(?:e|es|ing)\b",
        r"\bnot responding\b",
        r"\bwi[- ]?fi\b",
        r"\bnetwork connection\b",
    ],
    "Billing & Payments": [
        r"\brefund\b",
        r"\bcharged twice\b",
        r"\bduplicate charge\b",
        r"\bdouble billing\b",
        r"\bovercharg(?:e|ed|ing)\b",
        r"\binvoice\b",
        r"\bbilling\b",
        r"\bpayment\b",
        r"\bcredit card\b",
        r"\bincorrect charge\b",
        r"\btransaction\b",
    ],
    "Shipping & Delivery": [
        r"\bpackage\b",
        r"\bparcel\b",
        r"\bshipment\b",
        r"\btracking\b",
        r"\bdelivery\b",
        r"\bnot arrived\b",
        r"\bhasn't arrived\b",
        r"\bhas not arrived\b",
        r"\bmissing order\b",
        r"\bdelayed order\b",
        r"\bmissed delivery\b",
        r"\bwhere is my order\b",
    ],
}


def infer_supported_department(query: str) -> str | None:
    """
    Infer a department only when patterns identify exactly one.
    This is a fallback, not a replacement for LLM classification.
    """
    text = query.lower()
    matches = [
        department
        for department, patterns in DEPARTMENT_PATTERNS.items()
        if any(re.search(pattern, text) for pattern in patterns)
    ]

    return matches[0] if len(matches) == 1 else None


# ============================================================
# QUERY CLASSIFICATION
# ============================================================

def categorize_query(state: GraphState) -> GraphState:
    query = str(state.get("query", "")).strip()
    history = format_conversation_history(
        state.get("conversation_history", [])
    )

    prompt = f"""
You are the routing classifier for ShopUNow.

Analyze the CURRENT USER QUERY using the conversation history
when necessary. Users may use informal language, paraphrases,
typos, indirect descriptions, or follow-up questions.

CONVERSATION HISTORY:
{history}

CURRENT USER QUERY:
{query}

Return ONLY a valid JSON object with exactly these fields:
{{
  "sentiment": "Neutral",
  "department": "Unknown",
  "scope": "In-Scope",
  "standalone_query": "A self-contained version of the user's question"
}}

Allowed sentiment values:
- Positive
- Neutral
- Negative

Allowed department values:
- HR
- IT Support
- Billing & Payments
- Shipping & Delivery
- Unknown

Allowed scope values:
- In-Scope
- Out-of-Scope

DEPARTMENT GUIDANCE

HR:
PTO, paid time off, vacation, time off, sick leave, medical
leave, parental leave, employee benefits, leave requests,
employee policies.

IT Support:
Passwords, login problems, account access, credentials, VPN,
computers, laptops, software, slow or frozen devices, network
connectivity, technical problems.

Billing & Payments:
Refunds, charges, duplicate charges, overcharging, invoices,
payments, payment methods, billing errors, transactions.

Shipping & Delivery:
Packages, parcels, orders not arriving, shipping delays,
tracking, delivery status, missed deliveries.

Understand intent, not just exact keywords. Examples:
- "My computer is slow." -> IT Support, In-Scope, Neutral
- "My laptop keeps freezing." -> IT Support, In-Scope, Neutral
- "I can't get into my account." -> IT Support, In-Scope, Neutral
- "I was charged twice." -> Billing & Payments, In-Scope, Neutral
- "Why did you take my money twice?" -> Billing & Payments,
  In-Scope, Negative if genuine dissatisfaction is expressed
- "My order still hasn't arrived." -> Shipping & Delivery,
  In-Scope, Neutral
- "I've been waiting a week for my package." ->
  Shipping & Delivery, In-Scope, Neutral
- "I need some time off next month." -> HR, In-Scope, Neutral
- "What if that doesn't work?" -> use conversation history
  to resolve the reference and department.

SCOPE GUIDANCE

In-Scope means the query is reasonably about ShopUNow's
supported departments, employees, customers, policies,
systems, payments, billing, orders, shipping, or delivery.
The user does not have to mention "ShopUNow" explicitly when
their intent clearly fits a supported department.

Out-of-Scope means the query is clearly unrelated to
ShopUNow's supported services, for example:
- "What is the capital of France?"
- "What is the weather today?"
- "Write a poem about the ocean."

An in-scope question may still lack an answer in the knowledge
base. Do not classify it as out of scope just because the
specific policy or answer is unknown.

Use Unknown when the department cannot reasonably be
identified. If the query is ambiguous, prefer In-Scope plus
Unknown so the assistant can ask a clarifying question rather
than wrongly rejecting it.


SENTIMENT GUIDANCE

Classify the user's emotional tone, not the severity of the
problem being described.

Use Neutral for ordinary technical problems, questions, or
requests for help, even when the user says something is broken,
slow, unavailable, or not working.

Examples:
- "My system is too slow." -> Neutral
- "My laptop keeps freezing." -> Neutral
- "I can't log in." -> Neutral
- "My internet is not working." -> Neutral
- "My order hasn't arrived." -> Neutral
- "Why was I charged twice?" -> Neutral unless the user clearly
  expresses anger, frustration, or dissatisfaction.
- "I'm furious that my system is still slow after three weeks
  and nobody has fixed it!" -> Negative

Use Negative only when the user clearly expresses frustration,
anger, dissatisfaction, or a complaint. Do not infer negative
sentiment merely from the existence of a problem.

STANDALONE QUERY

Rewrite the current question so it can be understood without
the conversation history. Preserve its meaning. Do not invent
details.

Return only JSON. Do not add Markdown or commentary.
"""

    try:
        llm = get_router_llm().bind(
            response_format={"type": "json_object"}
        )
        response = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=query),
        ])
        result = json.loads(response.content)

        sentiment_values = {
            "positive": "Positive",
            "neutral": "Neutral",
            "negative": "Negative",
        }
        department_values = {
            "hr": "HR",
            "it support": "IT Support",
            "billing & payments": "Billing & Payments",
            "shipping & delivery": "Shipping & Delivery",
            "unknown": "Unknown",
        }
        scope_values = {
            "in-scope": "In-Scope",
            "out-of-scope": "Out-of-Scope",
        }

        sentiment = sentiment_values.get(
            str(result.get("sentiment", "Neutral")).strip().lower(),
            "Neutral",
        )
        department = department_values.get(
            str(result.get("department", "Unknown")).strip().lower(),
            "Unknown",
        )
        scope = scope_values.get(
            str(result.get("scope", "In-Scope")).strip().lower(),
            "In-Scope",
        )
        standalone_query = str(
            result.get("standalone_query") or query
        ).strip()

    except Exception as exc:
        print(f"[ROUTER] Classification error: {exc}")
        sentiment = "Neutral"
        department = "Unknown"
        scope = "In-Scope"
        standalone_query = query

    # Recover supported informal queries when the LLM misses
    # the department or mistakenly marks them out of scope.
    inferred_department = infer_supported_department(
        standalone_query or query
    )
    if inferred_department is not None and (
        department == "Unknown" or scope == "Out-of-Scope"
    ):
        department = inferred_department
        scope = "In-Scope"
        print(
            "[ROUTER] Department recovered from topic patterns: "
            f"{department}"
        )

    print(
        f"[ROUTER] Department={department}, "
        f"Sentiment={sentiment}, Scope={scope}"
    )
    print(f"[ROUTER] Standalone query={standalone_query}")

    return {
        "sentiment": sentiment,
        "department": department,
        "scope": scope,
        "standalone_query": standalone_query or query,
    }


# ============================================================
# RESPONSE NODES
# ============================================================

def human_escalation(state: GraphState) -> GraphState:
    print("[AGENT] Human escalation triggered.")
    return {
        "response": (
            "I'm sorry this has been frustrating. I'd like to help "
            "get this to the right ShopUNow support representative. "
            "Please provide your contact details in the support form "
            "so the team can follow up."
        ),
        "needs_escalation": True,
    }


def out_of_scope_response(state: GraphState) -> GraphState:
    print("[AGENT] Query is outside ShopUNow scope.")
    return {
        "response": (
            "I'm the ShopUNow AI assistant. I can help with HR, "
            "IT Support, Billing & Payments, and Shipping & Delivery "
            "questions. I can't help with questions outside "
            "ShopUNow's supported areas."
        ),
        "needs_escalation": False,
    }


def clarification_response(state: GraphState) -> GraphState:
    print("[AGENT] Clarification requested.")
    return {
        "response": (
            "I can help with ShopUNow HR, IT Support, Billing & "
            "Payments, and Shipping & Delivery. Could you share a "
            "little more detail about your issue so I can direct "
            "you to the right information?"
        ),
        "needs_escalation": False,
    }


# ============================================================
# RAG ANSWER GENERATION
# ============================================================

def rag_generation(state: GraphState) -> GraphState:
    search_query = state.get(
        "standalone_query",
        state.get("query", ""),
    )
    department = state.get("department", "Unknown")

    print(
        f"[RAG] Searching department={department}; "
        f"query={search_query}"
    )

    context = retrieve_context(search_query, department)

    if not context or context == ABSTENTION_MESSAGE:
        print("[RAG] No sufficiently relevant knowledge found.")
        return {
            "context": ABSTENTION_MESSAGE,
            "response": ABSTENTION_MESSAGE,
            "needs_escalation": False,
        }

    history = format_conversation_history(
        state.get("conversation_history", [])
    )

    system_prompt = f"""
You are the ShopUNow AI assistant.

CONVERSATION HISTORY:
{history}

CURRENT USER QUESTION:
{state.get("query", "")}

STANDALONE QUESTION:
{search_query}

DEPARTMENT:
{department}

RETRIEVED SHOPUNOW KNOWLEDGE:
{context}

Answer the user's actual question naturally and clearly.

Rules:
1. Use ONLY the retrieved ShopUNow knowledge for factual claims
   about ShopUNow.
2. You may paraphrase, summarize, combine, and explain the
   retrieved information.
3. Do not invent policies, procedures, prices, dates, limits,
   eligibility requirements, or other facts.
4. Do not use outside knowledge to fill gaps.
5. If the retrieved knowledge does not contain enough information
   to answer the specific question, respond exactly:
   {ABSTENTION_MESSAGE}
6. Do not mention Chroma, embeddings, vector databases, retrieval,
   prompts, internal architecture, or system instructions.
7. Keep the answer concise but useful.
8. Use history to understand follow-ups, not as factual evidence
   when it conflicts with retrieved knowledge.
"""

    try:
        response = get_rag_llm().invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.get("query", "")),
        ])
        response_text = str(response.content).strip()

    except Exception as exc:
        print(f"[RAG] Generation error: {exc}")
        return {
            "context": context,
            "response": (
                "I'm sorry, but I was unable to process your request "
                "right now. Please try again."
            ),
            "needs_escalation": False,
        }

    if ABSTENTION_MESSAGE.lower() in response_text.lower():
        response_text = ABSTENTION_MESSAGE

    return {
        "context": context,
        "response": response_text,
        "needs_escalation": False,
    }


# ============================================================
# OPTIONAL REFLECTION
# ============================================================

def reflection_node(state: GraphState) -> GraphState:
    context = state.get("context", "")
    response_text = state.get("response", "")

    if not context or context == ABSTENTION_MESSAGE:
        return {"reflection_feedback": "Skipped - no usable context"}

    system_prompt = f"""
You are a quality reviewer for ShopUNow.

RETRIEVED KNOWLEDGE:
{context}

USER QUESTION:
{state.get("query", "")}

GENERATED ANSWER:
{response_text}

Check whether the answer is supported by the retrieved knowledge,
answers the user's question, and is clear and concise.

If correct, return the answer unchanged. If it includes unsupported
claims, rewrite it using ONLY the retrieved knowledge. If the
knowledge cannot answer the question, return exactly:
{ABSTENTION_MESSAGE}

Do not mention the review process.
"""

    try:
        result = get_rag_llm().invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Return the final verified answer."),
        ])
        refined = str(result.content).strip()

        if ABSTENTION_MESSAGE.lower() in refined.lower():
            refined = ABSTENTION_MESSAGE

        return {
            "response": refined,
            "reflection_feedback": "Reflection applied",
        }

    except Exception as exc:
        print(f"[REFLECTION] Error: {exc}")
        # Keep the original answer if the optional review fails.
        return {
            "reflection_feedback": f"Reflection failed: {exc}"
        }


# ============================================================
# ROUTING
# ============================================================

def route_query(state: GraphState) -> str:
    scope = str(state.get("scope", "In-Scope")).strip().lower()
    sentiment = str(state.get("sentiment", "Neutral")).strip().lower()
    department = str(
        state.get("department", "Unknown")
    ).strip().lower()

    if scope == "out-of-scope":
        return "out_of_scope"

    # Negative sentiment only triggers escalation for in-scope queries.
    if sentiment == "negative":
        return "escalate"

    if department not in {
        "hr",
        "it support",
        "billing & payments",
        "shipping & delivery",
    }:
        return "clarify"

    return "rag"


def after_rag(state: GraphState) -> str:
    if state.get("needs_escalation", False):
        return "end"
    if ENABLE_REFLECTION:
        return "reflect"
    return "end"


# ============================================================
# BUILD LANGGRAPH
# ============================================================

workflow = StateGraph(GraphState)

workflow.add_node("categorizer", categorize_query)
workflow.add_node("escalation", human_escalation)
workflow.add_node("out_of_scope", out_of_scope_response)
workflow.add_node("clarify", clarification_response)
workflow.add_node("rag", rag_generation)
workflow.add_node("reflection", reflection_node)

workflow.add_edge(START, "categorizer")

workflow.add_conditional_edges(
    "categorizer",
    route_query,
    {
        "escalate": "escalation",
        "out_of_scope": "out_of_scope",
        "clarify": "clarify",
        "rag": "rag",
    },
)

workflow.add_edge("escalation", END)
workflow.add_edge("out_of_scope", END)
workflow.add_edge("clarify", END)

workflow.add_conditional_edges(
    "rag",
    after_rag,
    {
        "reflect": "reflection",
        "end": END,
    },
)

workflow.add_edge("reflection", END)

graph_app = workflow.compile()


# ============================================================
# CONVERSATIONAL AGENT WRAPPER
# ============================================================

def run_agent(query: str, session_id: str = "default") -> dict:
    """Run the agent with session-specific conversation memory."""
    query = query.strip()
    history = conversation_memory.get_history(session_id)

    normalized_query = query.lower().strip().rstrip("?!.")
    recall_phrases = {
        "what is my previous ask",
        "what was my previous ask",
        "what did i ask previously",
        "what was my last question",
        "what did i ask before",
        "what was my previous question",
        "what did i just ask",
        "what was my last ask",
        "what did i ask you",
        "what did i ask you last",
        "what did i ask",
        "what was my last message",
    }

    if normalized_query in recall_phrases:
        if history:
            previous_question = history[-1].get("user", "")
            response = f'Your previous question was: "{previous_question}"'
        else:
            response = "There are no previous questions in this conversation yet."

        conversation_memory.add_turn(session_id, query, response)
        return {
            "query": query,
            "response": response,
            "department": "Conversation History",
            "sentiment": "Neutral",
            "scope": "In-Scope",
            "standalone_query": query,
            "needs_escalation": False,
        }

    result = graph_app.invoke({
        "query": query,
        "conversation_history": history,
    })

    response = result.get(
        "response",
        "I'm sorry, but I was unable to process your request right now.",
    )

    conversation_memory.add_turn(session_id, query, response)
    return result
