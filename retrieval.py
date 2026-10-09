import re

from database import (
    get_chroma_client,
    get_embeddings_model,
)
from config import TOP_K, RELEVANCE_THRESHOLD


ABSTENTION_MESSAGE = (
    "I don't have enough information in the ShopUNow "
    "knowledge base to answer this accurately."
)


# ============================================================
# QUERY SYNONYMS
# ============================================================

SYNONYM_MAP = {
    # HR
    "pto": [
        "paid time off",
        "vacation",
        "time off",
        "leave request",
        "annual leave",
    ],
    "paid time off": [
        "pto",
        "vacation",
        "time off",
        "leave request",
    ],
    "vacation": [
        "pto",
        "paid time off",
        "holiday leave",
        "annual leave",
    ],
    "time off": [
        "pto",
        "paid time off",
        "vacation",
        "leave request",
    ],
    "sick leave": [
        "sick",
        "medical leave",
        "employee absence",
        "leave request",
    ],
    "medical leave": [
        "sick leave",
        "employee absence",
        "medical absence",
    ],
    "parental leave": [
        "paternity leave",
        "maternity leave",
        "family leave",
    ],
    "employee benefits": [
        "benefits",
        "benefits eligibility",
        "workplace benefits",
    ],
    "leave request": [
        "time off",
        "pto",
        "paid time off",
        "vacation",
    ],

    # IT Support
    "password": [
        "credentials",
        "login",
        "sign-in",
        "account access",
        "password reset",
    ],
    "password reset": [
        "reset password",
        "change password",
        "account credentials",
        "login access",
    ],
    "login": [
        "password",
        "credentials",
        "sign-in",
        "account access",
        "cannot log in",
    ],
    "can't log in": [
        "cannot log in",
        "login issue",
        "sign-in problem",
        "account access",
        "password problem",
    ],
    "account access": [
        "login",
        "credentials",
        "sign-in",
        "password",
    ],
    "laptop": [
        "computer",
        "pc",
        "work computer",
        "work laptop",
        "device performance",
    ],
    "computer": [
        "laptop",
        "pc",
        "work computer",
        "device performance",
        "slow computer",
    ],
    "slow": [
        "running slowly",
        "poor performance",
        "sluggish",
        "performance issue",
    ],
    "freezing": [
        "not responding",
        "computer hangs",
        "application freezes",
        "system becomes unresponsive",
    ],
    "not responding": [
        "freezing",
        "application hangs",
        "system unresponsive",
    ],
    "vpn": [
        "virtual private network",
        "remote access",
        "remote connection",
    ],
    "wifi": [
        "wi-fi",
        "wireless connection",
        "network connection",
        "internet connectivity",
    ],
    "wi-fi": [
        "wifi",
        "wireless connection",
        "network connection",
    ],
    "software": [
        "application",
        "app",
        "program",
        "software issue",
    ],
    "application error": [
        "software error",
        "app problem",
        "program issue",
    ],

    # Billing & Payments
    "refund": [
        "money back",
        "refund status",
        "return payment",
        "refund processing",
    ],
    "charged twice": [
        "duplicate charge",
        "double billing",
        "duplicate payment",
        "charged two times",
    ],
    "duplicate charge": [
        "charged twice",
        "double billing",
        "duplicate payment",
    ],
    "overcharged": [
        "incorrect charge",
        "billing error",
        "wrong amount charged",
    ],
    "invoice": [
        "bill",
        "billing statement",
        "payment details",
    ],
    "payment": [
        "payment method",
        "payment options",
        "payment failure",
        "transaction",
    ],
    "credit card": [
        "payment method",
        "card payment",
        "Visa",
        "MasterCard",
    ],
    "billing error": [
        "incorrect charge",
        "overcharged",
        "wrong amount",
        "duplicate charge",
    ],

    # Shipping & Delivery
    "tracking": [
        "shipment tracking",
        "delivery status",
        "package status",
        "track an order",
    ],
    "package": [
        "shipment",
        "parcel",
        "delivery",
        "order delivery",
    ],
    "shipment": [
        "package",
        "parcel",
        "delivery",
        "shipping status",
    ],
    "delivery": [
        "shipment",
        "package",
        "parcel",
        "delivery status",
    ],
    "late": [
        "delayed delivery",
        "late shipment",
        "order has not arrived",
    ],
    "not arrived": [
        "delayed shipment",
        "missing package",
        "delivery delay",
    ],
    "hasn't arrived": [
        "has not arrived",
        "delayed shipment",
        "missing package",
        "delivery delay",
    ],
    "missed delivery": [
        "failed delivery attempt",
        "delivery was missed",
        "delivery attempt",
    ],
    "where is my order": [
        "order tracking",
        "shipment tracking",
        "delivery status",
        "package location",
    ],
}


# ============================================================
# QUERY EXPANSION
# ============================================================

def expand_query_with_synonyms(query: str) -> str:
    """
    Add deterministic related terms to improve matching when a
    user phrases a question differently from the knowledge base.

    This function does not make an LLM call.
    """
    query = query.strip()
    if not query:
        return query

    query_lower = query.lower()
    related_terms = []

    # Match longer phrases first, e.g. "charged twice" before "charge".
    for term in sorted(SYNONYM_MAP, key=len, reverse=True):
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, query_lower):
            related_terms.extend(SYNONYM_MAP[term])

    # Preserve order while removing duplicates and terms already present.
    unique_terms = []
    seen = set(query_lower.split())

    for term in related_terms:
        normalized = term.lower()
        if normalized not in seen:
            unique_terms.append(term)
            seen.add(normalized)

    # Limit expansion to avoid making the query excessively broad.
    unique_terms = unique_terms[:12]

    if not unique_terms:
        return query

    return f"{query} Related terms: {', '.join(unique_terms)}"


# ============================================================
# CHROMA RETRIEVAL
# ============================================================

def retrieve_context(query: str, department: str) -> str:
    """
    Retrieve relevant FAQ documents from the ShopUNow Chroma
    collection, filtered by department metadata.

    The existing configured relevance threshold is preserved.
    """
    query = query.strip()
    department = department.strip()

    if not query or not department:
        return ABSTENTION_MESSAGE

    print(f"[RAG] Retrieving knowledge for department={department}")

    try:
        client = get_chroma_client()
        collection = client.get_collection(name="shopunow_faqs")

        if collection.count() == 0:
            print("[RAG] Chroma collection is empty.")
            return ABSTENTION_MESSAGE

        embeddings_model = get_embeddings_model()

    except Exception as exc:
        print(f"[RAG] Could not initialize retrieval: {exc}")
        return ABSTENTION_MESSAGE

    def search_chroma(search_query: str) -> list[tuple[str, float]]:
        print(f"[RAG] Searching: {search_query}")

        try:
            query_embedding = embeddings_model.embed_query(search_query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=max(1, int(TOP_K)),
                where={"department": department},
                include=["documents", "distances", "metadatas"],
            )
        except Exception as exc:
            print(f"[RAG] Chroma search error: {exc}")
            return []

        documents_list = results.get("documents") or []
        distances_list = results.get("distances") or []

        if not documents_list or not documents_list[0]:
            return []

        documents = documents_list[0]
        distances = distances_list[0] if distances_list else []

        valid_results = []

        for document, distance in zip(documents, distances):
            if not document or distance is None:
                continue

            # Keep the project's original distance-to-score conversion.
            similarity = 1.0 / (1.0 + float(distance))

            print(
                f"[RAG] Similarity={similarity:.4f} "
                f"for query='{search_query}'"
            )

            if similarity >= RELEVANCE_THRESHOLD:
                valid_results.append((document, similarity))

        return valid_results

    # Search the original query first.
    original_results = search_chroma(query)

    # Also search an expanded query to improve paraphrase handling.
    expanded_query = expand_query_with_synonyms(query)
    expanded_results = []

    if expanded_query != query:
        print(f"[RAG] Expanded query: {expanded_query}")
        expanded_results = search_chroma(expanded_query)

    # Combine duplicates, keeping the highest similarity for each document.
    combined_results: dict[str, float] = {}

    for document, similarity in original_results + expanded_results:
        if (
            document not in combined_results
            or similarity > combined_results[document]
        ):
            combined_results[document] = similarity

    if not combined_results:
        print("[RAG] No sufficiently relevant knowledge found.")
        return ABSTENTION_MESSAGE

    ranked_results = sorted(
        combined_results.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:max(1, int(TOP_K))]

    context_blocks = []
    for document, similarity in ranked_results:
        print(f"[RAG] Selected context similarity={similarity:.4f}")
        context_blocks.append(document)

    context = "\n\n---\n\n".join(context_blocks)
    print(f"[RAG] Prepared {len(context_blocks)} context document(s).")

    return context
