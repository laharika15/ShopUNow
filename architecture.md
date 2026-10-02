# Architecture: ShopUNow Agentic AI Assistant

## System Overview
The ShopUNow Agentic AI Assistant is a strong, quota-efficient RAG system built for a retail company. It handles internal employee queries (HR, IT) and external customer queries (Billing, Shipping). The system minimizes API usage by leveraging local Hugging Face embeddings, metadata filtering in ChromaDB, deterministic evaluation, and limiting Groq LLM calls.

## Core Components and Data Flow

1. **User Input**: The user submits a query.
2. **Query Categorizer (Groq LLM)**: Analyzes the query to determine:
   - **Sentiment**: Positive, Neutral, or Negative.
   - **Department**: HR, IT Support, Billing & Payments, Shipping & Delivery, or Unknown.
3. **Query Router (LangGraph)**: 
   - **Human Escalation Route**: Triggered if sentiment is Negative OR if the department is Unknown. Returns a simple message indicating a human agent will reach out (stretch goal: interactive form).
   - **Department-Aware RAG Route**: Triggered if sentiment is Positive/Neutral AND the department is recognized.
4. **Strong RAG Workflow**:
   - **Retrieval**: Uses local `sentence-transformers/all-MiniLM-L6-v2` embeddings to query ChromaDB.
   - **Metadata Filtering**: Strictly filters ChromaDB using the categorized department to prevent cross-department leakage.
   - **Relevance Check**: Retrieves `TOP_K` candidates and filters them based on a `RELEVANCE_THRESHOLD`.
   - **Controlled Abstention**: If no context meets the threshold, the system aborts LLM generation and returns: *"I don't have enough information in the ShopUNow knowledge base to answer this accurately."*
   - **Grounded Generation (Groq LLM)**: If relevant context exists, generates a response using ONLY the provided context.
   - **Optional Reflection**: If `ENABLE_REFLECTION` is True, a single Groq call reflects on the answer and refines it if necessary.
5. **Final Response**: The generated answer, abstention message, or human escalation message is returned.

## Quota Optimization Strategy
- **Embeddings**: Local Hugging Face models (zero API cost).
- **Database**: Local ChromaDB instance.
- **Dataset**: Generated ONCE and saved as `shopunow_qa_dataset.json`.
- **RAG Generation**: Strict grounding and controlled abstention prevents unnecessary LLM calls when context is poor.
- **Evaluation**: Mostly deterministic string matching and metadata checks, avoiding LLM-as-a-judge for every test.
- **Reflection**: Disabled during normal development mode.

## Directory Structure
```
shopunow/
├── app.py                   # FastAPI wrapper
├── main.py                  # CLI test entrypoint
├── agent.py                 # LangGraph logic (Router, Nodes, State)
├── database.py              # ChromaDB initialization and population
├── retrieval.py             # RAG logic (Embeddings, Metadata filtering, Thresholds)
├── data_generation.py       # Script to generate the QA dataset once
├── evaluation.py            # Deterministic test suite
├── config.py                # Environment configuration & constants
├── data/
│   └── shopunow_qa_dataset.json # Static QA dataset
├── architecture.md          # Architecture overview
├── implementation_plan.md   # Step-by-step plan
├── README.md                # Project documentation
├── requirements.txt         # Dependencies
├── .env.example             # Env var template
└── .gitignore               # Ignored files
```

## Technology Stack
- **Agent Orchestration**: LangGraph, LangChain
- **LLM**: Groq API
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (Local Hugging Face)
- **Vector Store**: ChromaDB (Local)
- **API Wrapping**: FastAPI
