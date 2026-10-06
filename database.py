import os
import json
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from config import (
    CHROMA_PERSIST_DIR,
    DATASET_PATH,
    EMBEDDING_MODEL_NAME
)


COLLECTION_NAME = "shopunow_faqs"


def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def get_embeddings_model():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME
    )


def initialize_database():
    """Rebuilds the ShopUNow Chroma collection from the JSON dataset."""

    if not os.path.exists(DATASET_PATH):
        print(
            f"Dataset not found at {DATASET_PATH}. "
            "Please run data_generation.py first."
        )
        return

    # Load dataset
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        qa_data = json.load(f)

    if not isinstance(qa_data, list):
        raise ValueError(
            "Dataset must be a JSON list of QA records."
        )

    print(f"Loaded {len(qa_data)} records from dataset.")

    # Validate records
    required_fields = {
        "question",
        "answer",
        "department",
        "audience"
    }

    for index, item in enumerate(qa_data):
        missing = required_fields - set(item.keys())

        if missing:
            raise ValueError(
                f"Record {index} is missing fields: {missing}"
            )

    # Show department counts
    from collections import Counter

    department_counts = Counter(
        item["department"] for item in qa_data
    )

    print("\nDataset department counts:")

    for department, count in department_counts.items():
        print(f"  {department}: {count}")

    # Create Chroma client
    client = get_chroma_client()

    # IMPORTANT:
    # Delete the old collection so the new dataset is actually loaded.
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(
            f"\nDeleted existing Chroma collection: "
            f"{COLLECTION_NAME}"
        )
    except Exception:
        print(
            f"\nNo existing collection found. "
            f"Creating: {COLLECTION_NAME}"
        )

    collection = client.create_collection(
        name=COLLECTION_NAME
    )

    embeddings_model = get_embeddings_model()

    documents = []
    metadatas = []
    ids = []

    for index, item in enumerate(qa_data):

        # Keep each complete QA pair as one document.
        doc_text = (
            f"Question: {item['question']}\n"
            f"Answer: {item['answer']}"
        )

        documents.append(doc_text)

        metadatas.append({
            "record_id": str(index),
            "department": item["department"],
            "audience": item["audience"],
            "source": "synthetic_dataset"
        })

        ids.append(f"shopunow_{index}")

    print(
        "\nGenerating local embeddings. "
        "This may take a moment..."
    )

    embeddings = embeddings_model.embed_documents(
        documents
    )

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    final_count = collection.count()

    print("\n" + "=" * 60)
    print("ChromaDB initialization complete.")
    print(f"Documents loaded: {final_count}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Location: {CHROMA_PERSIST_DIR}")
    print("=" * 60)

    if final_count == 80:
        print("\nSUCCESS: ChromaDB contains exactly 80 records.")
    else:
        print(
            f"\nWARNING: Expected 80 records, "
            f"but ChromaDB contains {final_count}."
        )


if __name__ == "__main__":
    initialize_database()
