import re
from database import get_chroma_client, get_embeddings_model
from config import TOP_K, RELEVANCE_THRESHOLD

# Synonyms used to improve semantic retrieval across all departments
SYNONYM_MAP = {
    # HR
    "vacation": [
        "vacation", "pto", "paid time off", "time off",
        "leave", "annual leave", "days off"
    ],
    "pto": [
        "pto", "vacation", "paid time off", "time off",
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
    "dependent": [
        "dependent", "family member", "spouse", "child"
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
    "employment documents": [
        "employment documents", "employee documents",
        "employment letter", "job documents", "hr documents"
    ],

    # IT Support
    "password": [
        "password", "passcode", "login password",
        "sign in password", "account password", "credentials"
    ],
    "login": [
        "login", "log in", "sign in", "signin",
        "authentication", "account access"
    ],
    "credentials": [
        "credentials", "login details", "login credentials",
        "username and password", "account credentials"
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

    # Billing & Payments
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

    # Shipping & Delivery
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

    # Returns
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
    """
    Expands the query with related terms to improve retrieval.
    The original query is preserved.
    """
    query_lower = query.lower()
    matched_terms = []

    # Check longer phrases first
    sorted_terms = sorted(
        SYNONYM_MAP.keys(),
        key=len,
        reverse=True
    )

    for term in sorted_terms:
        pattern = r"\b" + re.escape(term) + r"\b"

        if re.search(pattern, query_lower):
            matched_terms.extend(SYNONYM_MAP[term])

    # Remove duplicate terms
    unique_terms = list(dict.fromkeys(matched_terms))

    if not unique_terms:
        return query

    return (
        f"{query} "
        f"Related terms: {', '.join(unique_terms)}"
    )


def retrieve_context(query: str, department: str) -> str:
    """
    Retrieves context for a given query, filtered by the specified department.
    Returns the context as a single string, or a specific abstention message
    if no results meet the RELEVANCE_THRESHOLD.
    """
    client = get_chroma_client()

    try:
        collection = client.get_collection(name="shopunow_faqs")
    except Exception:
        # Collection might not exist yet if database.py hasn't run
        return "I don't have enough information in the ShopUNow knowledge base to answer this accurately."

    # Check if database is empty
    if collection.count() == 0:
        return "I don't have enough information in the ShopUNow knowledge base to answer this accurately."

    embeddings_model = get_embeddings_model()

    # Expand the query before embedding for better retrieval
    retrieval_query = expand_query_with_synonyms(query)

    # Embed the expanded retrieval query
    query_embedding = embeddings_model.embed_query(retrieval_query)

    # Query ChromaDB with strict metadata filter on department
    # Chroma returns distance (L2 by default). Lower distance = higher relevance.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        where={"department": department},
        include=["documents", "distances", "metadatas"]
    )

    if not results["documents"] or not results["documents"][0]:
        return "I don't have enough information in the ShopUNow knowledge base to answer this accurately."

    documents = results["documents"][0]
    distances = results["distances"][0]

    valid_context_blocks = []

    for doc, distance in zip(documents, distances):
        # Convert L2 distance to a basic similarity score (0 to 1)
        similarity = 1 / (1 + distance)

        # Only include documents that meet the relevance threshold
        if similarity >= RELEVANCE_THRESHOLD:
            valid_context_blocks.append(doc)

    # If no documents met the threshold, abort and abstain
    if not valid_context_blocks:
        return "I don't have enough information in the ShopUNow knowledge base to answer this accurately."

    return "\n\n---\n\n".join(valid_context_blocks)
