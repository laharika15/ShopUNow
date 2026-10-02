from database import get_chroma_client, get_embeddings_model
from config import TOP_K, RELEVANCE_THRESHOLD

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
    
    # Embed the query
    query_embedding = embeddings_model.embed_query(query)
    
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
