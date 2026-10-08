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


# Deterministic semantic expansion
# No additional LLM call is used.

SYNONYM_MAP = {

    # HR
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
        "absence",
        "leave request"
    ],

    "sick leave": [
        "sick",
        "medical leave",
        "absence",
        "leave request"
    ],

    "paternity": [
        "paternity leave",
        "parental leave",
        "family leave"
    ],

    "paternity leave": [
        "paternity",
        "parental leave",
        "family leave"
    ],

    "parental": [
        "parental leave",
        "paternity leave",
        "family leave"
    ],

    # IT Support
    "password": [
        "credentials",
        "login",
        "account access"
    ],

    "login": [
        "password",
        "credentials",
        "account access"
    ],

    "credentials": [
        "password",
        "login",
        "account access"
    ],
    "laptop": [
        "computer",
        "pc",
        "device",
        "work computer",
        "work laptop",
    ],
    "computer": [
        "laptop",
        "pc",
        "device",
        "work computer",
        "work laptop",
    ],
    "pc": [
        "computer",
        "laptop",
        "device",
    ],
    "device": [
        "computer",
        "laptop",
        "pc",
    ],
    "slow": [
        "running slowly",
        "performance issue",
        "poor performance",
        "sluggish",
    ],
    "password": [
        "login",
        "credentials",
        "sign-in",
    ],
    "vpn": [
        "virtual private network",
        "remote access",
        "remote connection",
    ],

    # Billing & Payments
    "refund": [
        "money back",
        "reimbursement",
        "return payment"
    ],

    "payment": [
        "payment methods",
        "payment options",
        "ways to pay",
        "pay for order"
    ],

    "pay": [
        "payment",
        "payment methods",
        "payment options",
        "ways to pay"
    ],

    "order": [
        "purchase",
        "checkout",
        "payment"
    ],

    "credit card": [
        "payment method",
        "payment option",
        "Visa",
        "MasterCard",
        "American Express"
    ],

    # Shipping & Delivery
    "tracking": [
        "shipment tracking",
        "delivery status",
        "package status"
    ],

    "package": [
        "shipment",
        "parcel",
        "delivery"
    ],

    "shipment": [
        "package",
        "parcel",
        "delivery"
    ],

    "delivery": [
        "shipment",
        "package",
        "parcel"
    ]
}


def expand_query_with_synonyms(query: str) -> str:
    """
    Add deterministic semantic terms to the query.

    This does not use an LLM and therefore does not consume
    Groq API quota.
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

    print(
        f"[RAG] Retrieving knowledge for "
        f"department={department}"
    )

    client = get_chroma_client()

    try:
        collection = client.get_collection(
            name="shopunow_faqs"
        )
    except Exception as e:
        print(
            f"[RAG] Chroma collection error: {e}"
        )
        return ABSTENTION_MESSAGE

    if collection.count() == 0:
        print("[RAG] Chroma collection is empty.")
        return ABSTENTION_MESSAGE

    embeddings_model = get_embeddings_model()

    # Chroma search helper

    def search_chroma(search_query: str):

        print(
            f"[RAG] Searching: {search_query}"
        )

        try:
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

        except Exception as e:
            print(
                f"[RAG] Chroma search error: {e}"
            )
            return []

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

            # Convert Chroma distance into a simple
            # similarity-style score used by the
            # existing threshold.
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

    # 1. Original query search
   
    original_results = search_chroma(query)

    # 2. Deterministic semantic search
    #
    # Important:
    # We perform this even when the original query returns
    # some results. This improves paraphrase handling.

    expanded_query = expand_query_with_synonyms(query)

    expanded_results = []

    if expanded_query != query:

        print(
            f"[RAG] Semantic fallback query: "
            f"{expanded_query}"
        )

        expanded_results = search_chroma(
            expanded_query
        )

    # 3. Combine results
    #
    # If the same document appears in both searches,
    # keep its highest similarity score.

    combined_results = {}

    for doc, similarity in (
        original_results + expanded_results
    ):

        if (
            doc not in combined_results
            or similarity > combined_results[doc]
        ):
            combined_results[doc] = similarity

    # 4. No sufficiently relevant knowledge

    if not combined_results:

        print(
            "[RAG] No sufficiently relevant "
            "knowledge found."
        )

        return ABSTENTION_MESSAGE

    # 5. Rank combined results

    ranked_results = sorted(
        combined_results.items(),
        key=lambda item: item[1],
        reverse=True
    )


    # Keep only the strongest TOP_K documents.
    ranked_results = ranked_results[:TOP_K]

    # 6. Build context for Groq

    context_blocks = []

    for doc, similarity in ranked_results:

        print(
            f"[RAG] Selected context "
            f"Similarity={similarity:.4f}"
        )

        context_blocks.append(doc)


    context = "\n\n---\n\n".join(
        context_blocks
    )

    print(
        f"[RAG] Context prepared using "
        f"{len(context_blocks)} document(s)."
    )

    return context
