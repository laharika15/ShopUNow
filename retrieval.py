import re

from database import (
    get_chroma_client,
    get_embeddings_model
)

from config import (
    TOP_K,
    RELEVANCE_THRESHOLD
)


ABSTENTION_MESSAGE = (
    "I don't have enough information in the ShopUNow "
    "knowledge base to answer this accurately."
)


SYNONYM_MAP = {
    "pto": [
        "paid time off",
        "vacation",
        "time off",
        "leave"
    ],
    "paid time off": [
        "pto",
        "vacation",
        "time off",
        "leave"
    ],
    "vacation": [
        "pto",
        "paid time off",
        "time off",
        "leave"
    ],
    "sick": [
        "sick leave",
        "medical leave",
        "absence"
    ],
    "sick leave": [
        "sick",
        "medical leave",
        "absence"
    ],
    "password": [
        "credentials",
        "login",
        "account access"
    ],
    "refund": [
        "money back",
        "reimbursement",
        "return payment"
    ],
    "tracking": [
        "shipment tracking",
        "delivery status",
        "package status"
    ],
    "package": [
        "shipment",
        "parcel",
        "delivery"
    ]
}


def expand_query_with_synonyms(query: str) -> str:
    """
    Adds lightweight deterministic semantic terms.
    No additional LLM call is used.
    """

    query_lower = query.lower()
    related_terms = []

    for term in sorted(
        SYNONYM_MAP.keys(),
        key=len,
        reverse=True
    ):
        if re.search(
            r"\b" + re.escape(term) + r"\b",
            query_lower
        ):
            related_terms.extend(
                SYNONYM_MAP[term]
            )

    if not related_terms:
        return query

    unique_terms = list(
        dict.fromkeys(related_terms)
    )

    return (
        f"{query} "
        f"Related terms: {', '.join(unique_terms)}"
    )


def retrieve_context(
    query: str,
    department: str
) -> str:

    client = get_chroma_client()

    try:
        collection = client.get_collection(
            name="shopunow_faqs"
        )
    except Exception:
        return ABSTENTION_MESSAGE

    if collection.count() == 0:
        return ABSTENTION_MESSAGE

    embeddings_model = get_embeddings_model()

    def search_chroma(search_query: str):

        query_embedding = (
            embeddings_model.embed_query(
                search_query
            )
        )

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
            where={
                "department": department
            },
            include=[
                "documents",
                "distances",
                "metadatas"
            ]
        )

        if (
            not results.get("documents")
            or not results["documents"][0]
        ):
            return []

        documents = results["documents"][0]
        distances = results["distances"][0]

        valid_results = []

        for doc, distance in zip(
            documents,
            distances
        ):
            similarity = 1 / (1 + distance)

            print(
                f"[RAG] Query='{search_query}' "
                f"Similarity={similarity:.4f}"
            )

            if similarity >= RELEVANCE_THRESHOLD:
                valid_results.append(
                    (doc, similarity)
                )

        return valid_results

    # First use the user's original wording.
    results = search_chroma(query)

    # If no sufficiently relevant result is found,
    # retry with deterministic semantic terms.
    if not results:

        expanded_query = (
            expand_query_with_synonyms(query)
        )

        if expanded_query != query:
            print(
                f"[RAG] Semantic fallback: "
                f"{expanded_query}"
            )

            results = search_chroma(
                expanded_query
            )

    if not results:
        return ABSTENTION_MESSAGE

    # Remove duplicate documents while preserving order.
    seen = set()
    context_blocks = []

    for doc, similarity in results:

    if doc in seen:
        continue

    seen.add(doc)
    context_blocks.append(doc)
