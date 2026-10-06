# Architecture: ShopUNow Agentic AI Assistant

## System Overview

ShopUNow Agentic AI Assistant is a quota-efficient Agentic RAG system designed to support both internal employees and external customers of a retail organization.

The system combines:

- LangGraph for agent orchestration
- Groq for intent classification and grounded response generation
- ChromaDB for vector retrieval
- Local Hugging Face embeddings for zero-cost semantic search
- Department-aware metadata filtering
- Deterministic semantic query expansion
- Relevance-based controlled abstention
- Human escalation for genuinely negative or escalation-oriented interactions
- Optional reflection for answer verification
- Streamlit for the conversational user interface
- FastAPI for API access

The architecture is designed to minimize unnecessary LLM calls while maintaining grounded and reliable responses.

---

## High-Level Architecture

```mermaid
graph TD

    A[User Query] --> B[Groq Categorizer]

    B --> C{Scope + Sentiment + Department}

    C -->|Out-of-Scope| D[Out-of-Scope Response]

    C -->|In-Scope + Negative| E[Human Escalation]

    C -->|In-Scope + Known Department| F[Department-Aware RAG]

    F --> G[Original Semantic Retrieval]

    G --> H[Deterministic Semantic Expansion]

    H --> I[Expanded Semantic Retrieval]

    I --> J[Combine + Deduplicate + Rank]

    J --> K[Department Metadata Filter]

    K --> L{Relevance Threshold}

    L -->|Insufficient Evidence| M[Controlled Abstention]

    L -->|Relevant Evidence| N[Groq Grounded Generation]

    N --> O{Reflection Enabled?}

    O -->|Yes| P[Groq Reflection]

    O -->|No| Q[Final Response]

    P --> Q
    D --> Q
    E --> Q
    M --> Q
