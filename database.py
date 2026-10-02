import os
import json
import uuid
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from config import CHROMA_PERSIST_DIR, DATASET_PATH, EMBEDDING_MODEL_NAME

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

def get_embeddings_model():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def initialize_database():
    """Reads the JSON dataset and populates ChromaDB."""
    if not os.path.exists(DATASET_PATH):
        print(f"Dataset not found at {DATASET_PATH}. Please run data_generation.py first.")
        return

    with open(DATASET_PATH, "r") as f:
        qa_data = json.load(f)

    client = get_chroma_client()
    # We use a single collection for simplicity, using metadata filtering to isolate departments
    collection = client.get_or_create_collection(name="shopunow_faqs")
    
    # Check if already populated to avoid duplicates
    if collection.count() > 0:
        print(f"Database already populated with {collection.count()} documents. Skipping initialization.")
        return

    embeddings_model = get_embeddings_model()
    
    documents = []
    metadatas = []
    ids = []
    
    for item in qa_data:
        # We do not chunk. Each QA pair is one complete document.
        doc_text = f"Question: {item['question']}\nAnswer: {item['answer']}"
        documents.append(doc_text)
        
        # Metadata must include record_id, department, audience, source
        record_id = str(uuid.uuid4())
        metadatas.append({
            "record_id": record_id,
            "department": item["department"],
            "audience": item["audience"],
            "source": "synthetic_dataset"
        })
        
        ids.append(record_id)
        
    # Generate embeddings and add to Chroma
    print("Generating local embeddings (this might take a moment the first time)...")
    embeddings = embeddings_model.embed_documents(documents)
    
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Successfully initialized ChromaDB with {len(documents)} documents at {CHROMA_PERSIST_DIR}")

if __name__ == "__main__":
    initialize_database()
