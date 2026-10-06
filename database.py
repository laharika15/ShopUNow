import os
import json
import chromadb
from collections import Counter
from langchain_huggingface import HuggingFaceEmbeddings

from config import (
    CHROMA_PERSIST_DIR,
    DATASET_PATH,
    EMBEDDING_MODEL_NAME
)


COLLECTION_NAME = "shopunow_faqs"


def get_chroma_client():
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR
    )


def get_embeddings_model():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME
    )


def initialize_database():
    """Rebuild the Chroma collection from the JSON dataset."""

    if not os.path.exists(DATASET_PATH):
        print(
            f"Dataset not found at {DATASET_PATH}. "
            "Please run data_generation.py first."
        )
        return

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        qa_data = json.load(f)

    if not isinstance(qa_data, list):
        raise ValueError(
            "Dataset must be a JSON list."
        )

    print(
        f"Loaded {len(qa_data)} records "
        f"from {DATASET_PATH}"
    )

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
                f"Record {index} is missing: {missing}"
            )

    counts = Counter(
        item["department"]
        for item in qa_data
    )

    print("\nDepartment counts:")

    for department, count in counts.items():
        print(f"  {department}: {count}")

    client = get_chroma_client()

    # Rebuild the collection so the latest dataset is indexed.
    try:
        client.delete_collection(
            name=COLLECTION_NAME
        )
        print(
            f"\nDeleted existing collection: "
            f"{COLLECTION_NAME}"
        )
    except Exception:
        print(
            f"\nNo existing collection found. "
            f"Creating {COLLECTION_NAME}."
        )

    collection = client.create_collection(
        name=COLLECTION_NAME
    )

    embeddings_model = get_embeddings_model()

    documents = []
    metadatas = []
    ids = []

    for index, item in enumerate(qa_data):

        document = (
            f"Question: {item['question']}\n"
            f"Answer: {item['answer']}"
        )

        documents.append(document)

        metadatas.append({
            "record_id": str(index),
            "department": item["department"],
            "audience": item["audience"],
            "source": "synthetic_dataset"
        })

        ids.append(
            f"shopunow_{index}"
        )

    print(
        "\nGenerating local embeddings..."
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
    print("CHROMA INITIALIZATION COMPLETE")
    print("=" * 60)
    print(f"Documents loaded: {final_count}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Database: {CHROMA_PERSIST_DIR}")

    if final_count == 80:
        print("\nSUCCESS: Chroma contains 80 records.")
    else:
        print(
            f"\nWARNING: Expected 80 records, "
            f"but Chroma contains {final_count}."
        )


if __name__ == "__main__":
    initialize_database()
