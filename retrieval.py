import re

from database import get_chroma_client, get_embeddings_model
from config import TOP_K, RELEVANCE_THRESHOLD


SYNONYM_MAP = {
    "pto": [
        "pto", "vacation", "paid time off", "time off",
        "leave", "annual leave", "days off"
    ],
    "vacation": [
        "vacation", "pto", "paid time off", "time off",
        "leave", "annual leave", "days off"
    ],
    "paid time off": [
        "paid time off", "pto", "vacation", "time off",
        "leave", "annual leave", "days off"
    ],
    "leave": [
        "leave", "vacation", "pto", "paid time off",
        "time off", "annual leave", "absence"
    ],
    "parental leave": [
        "parental leave", "maternity leave",
        "paternity leave", "family leave"
    ],
    "maternity leave": [
        "maternity leave", "parental leave", "family leave"
    ],
    "paternity leave": [
        "paternity leave", "parental leave", "family leave"
    ],
    "performance review": [
        "performance review", "performance evaluation",
        "employee review", "annual review", "appraisal"
    ],
    "payroll": [
        "payroll", "pay", "salary", "paycheck",
        "wages", "compensation"
    ],
    "benefits": [
        "benefits", "employee benefits", "benefit plan",
        "health benefits", "insurance benefits"
    ],
    "onboarding": [
        "onboarding", "new employee setup",
        "new hire setup", "joining process",
        "employee orientation"
    ],
    "flexible work": [
        "flexible work", "flexible working",
        "flexible work arrangement", "remote work",
        "hybrid work", "work from home"
    ],
    "password": [
        "password", "passcode", "login password",
        "sign in password", "account password", "credentials"
    ],
    "login": [
        "login", "log in", "sign in", "signin",
        "authentication", "account access"
    ],
    "credentials": [
        "credentials", "login details",
        "login credentials", "username and password",
        "account credentials"
    ],
    "wifi": [
        "wifi", "wi-fi", "wireless network",
        "internet connection", "network connection"
    ],
    "internet": [
        "internet", "wifi", "wi-fi", "network",
        "internet connection", "network connection"
    ],
    "laptop": [
        "laptop", "computer", "work computer",
        "company laptop", "device"
    ],
    "computer": [
        "computer", "laptop", "workstation",
        "device", "work computer"
    ],
    "email": [
        "email", "e-mail", "mailbox",
        "corporate email", "company email", "outlook"
    ],
    "software": [
        "software", "application", "app",
        "program", "business application"
    ],
    "access": [
        "access", "permission", "authorization",
        "account access", "system access"
    ],
    "account locked": [
        "account locked", "locked account",
        "login locked", "access locked", "locked out"
    ],
    "vpn": [
        "vpn", "virtual private network",
        "remote network access", "secure remote access"
    ],
    "refund": [
        "refund", "money back", "reimbursement",
        "refund payment", "return of payment",
        "credit", "payment reversal"
    ],
    "money back": [
        "money back", "refund", "reimbursement",
        "payment reversal", "credit"
    ],
    "reimbursement": [
        "reimbursement", "refund", "money back",
        "repayment", "payment return"
    ],
    "charge": [
        "charge", "payment", "billing charge",
        "transaction", "amount charged"
    ],
    "payment": [
        "payment", "pay", "transaction",
        "billing", "charge", "payment method"
    ],
    "credit card": [
        "credit card", "card", "payment card",
        "debit card", "bank card"
    ],
    "debit card": [
        "debit card", "card", "payment card",
        "credit card", "bank card"
    ],
    "invoice": [
        "invoice", "bill", "billing statement",
        "receipt", "payment statement"
    ],
    "receipt": [
        "receipt", "invoice", "proof of purchase",
        "payment receipt", "transaction receipt"
    ],
    "billing": [
        "billing", "payment", "charge",
        "invoice", "bill", "transaction"
    ],
    "duplicate charge": [
        "duplicate charge", "charged twice",
        "double charge", "duplicate payment", "two charges"
    ],
    "failed payment": [
        "failed payment", "payment failed",
        "declined payment", "payment declined",
        "transaction declined"
    ],
    "shipping": [
        "shipping", "delivery", "shipment",
        "dispatch", "shipping service", "package delivery"
    ],
    "delivery": [
        "delivery", "shipping", "shipment",
        "package delivery", "order delivery"
    ],
    "shipment": [
        "shipment", "shipping", "delivery",
        "package", "parcel", "order"
    ],
    "package": [
        "package", "parcel", "shipment",
        "delivery", "order"
    ],
    "parcel": [
        "parcel", "package", "shipment",
        "delivery", "order"
    ],
    "tracking": [
        "tracking", "track order", "order tracking",
        "shipment tracking", "delivery tracking",
        "tracking number"
    ],
    "tracking number": [
        "tracking number", "tracking id",
        "shipment number", "delivery tracking number",
        "order tracking"
    ],
    "delayed": [
        "delayed", "late", "delayed delivery",
        "late delivery", "shipping delay", "delivery delay"
    ],
    "late": [
        "late", "delayed", "delayed delivery",
        "late shipment", "shipping delay", "delivery delay"
    ],
    "cancel order": [
        "cancel order", "order cancellation",
        "cancel purchase", "stop order", "cancel shipment"
    ],
    "shipping address": [
        "shipping address", "delivery address",
        "shipping location", "delivery location"
    ],
    "express shipping": [
        "express shipping", "expedited shipping",
        "fast shipping", "priority shipping", "rush delivery"
    ],
    "return": [
        "return", "returns", "return policy",
        "return item", "product return", "send back"
    ],
    "returns": [
        "returns", "return", "return policy",
        "return item", "product return", "send back"
    ],
    "return policy": [
        "return policy", "returns policy",
        "return", "returns", "product return",
        "return window"
    ],
    "return window": [
        "return window", "return period",
        "return deadline", "return policy",
        "days to return", "return timeframe"
    ],
    "return shipping": [
        "return shipping", "return shipping fee",
        "return shipping cost", "shipping fee for returns",
        "return postage"
    ]
}


def expand_query_with_synonyms(query: str) -> str:
    query_lower = query.lower()
    matched_terms = []

    sorted_terms = sorted(
        SYNONYM_MAP.keys(),
        key=len,
        reverse=True
    )

    for term in sorted_terms:
        pattern = r"\b" + re.escape(term) + r"\b"

        if re.search(pattern, query_lower):
            matched_terms.extend(SYNONYM_MAP[term])

    unique_terms = list(dict.fromkeys(matched_terms))

    if not unique_terms:
        return query

    return (
        f"{query} "
        f"Related terms: {', '.join(unique_terms)}"
    )


def retrieve_context(query: str, department: str) -> str:
    client = get_chroma_client()

    abstention_message = (
        "I don't have enough information in the "
        "ShopUNow knowledge base to answer this accurately."
    )

    try:
        collection = client.get_collection(
            name="shopunow_faqs"
        )
    except Exception:
        return abstention_message

    if collection.count() == 0:
        return abstention_message

    embeddings_model = get_embeddings_model()

    def search_chroma(search_query: str):
        query_embedding = embeddings_model.embed_query(
            search_query
        )

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
            where={"department": department},
            include=[
                "documents",
                "distances",
                "metadatas"
            ]
        )

        if (
            not results["documents"]
            or not results["documents"][0]
        ):
            return []

        documents = results["documents"][0]
        distances = results["distances"][0]

        valid_documents = []

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
                valid_documents.append(
                    (doc, similarity)
                )

        return valid_documents

    valid_results = search_chroma(query)

    if valid_results:
        print(
            f"[RAG] Original query matched "
            f"{len(valid_results)} document(s)."
        )
        print(f"[RAG] Department: {department}")

        return "\n\n---\n\n".join(
            doc
            for doc, score in valid_results
        )

    expanded_query = expand_query_with_synonyms(query)

    if expanded_query != query:
        print(
            "[RAG] Original query did not meet "
            "the relevance threshold."
        )
        print(
            f"[RAG] Trying synonym-expanded query: "
            f"{expanded_query}"
        )

        valid_results = search_chroma(
            expanded_query
        )

        if valid_results:
            print(
                f"[RAG] Synonym-expanded query matched "
                f"{len(valid_results)} document(s)."
            )
            print(f"[RAG] Department: {department}")

            return "\n\n---\n\n".join(
                doc
                for doc, score in valid_results
            )

    print(
        "[RAG] No sufficiently relevant Chroma "
        "documents found."
    )
    print(f"[RAG] Query: {query}")
    print(f"[RAG] Department: {department}")

    return abstention_message
 
