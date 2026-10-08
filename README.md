# ShopUNow Agentic AI Assistant

## Overview

ShopUNow Agentic AI Assistant is a quota-efficient Agentic Retrieval-Augmented Generation (RAG) system designed to support both internal employees and external customers of a retail organization.

The assistant handles questions across four departments:

- HR
- IT Support
- Billing & Payments
- Shipping & Delivery

The system combines LangGraph-based agent orchestration, Groq LLMs, ChromaDB, local Hugging Face embeddings, department-aware retrieval, deterministic semantic query expansion, controlled abstention, and human escalation.

The project was built with a strong focus on:

- Grounded RAG
- Hallucination prevention
- Conversational query handling with multi-user session memory
- Department-aware retrieval
- Human escalation with interactive forms
- Controlled abstention
- Free-tier / quota-efficient development
- Modernized, branded Streamlit UI

## Live Demo

Try the deployed Streamlit application:

https://shopunow-demo-assistant.streamlit.app

The application provides a conversational interface for interacting with the ShopUNow agent.

## System Architecture

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
```
The system uses a graph-based workflow powered by LangGraph:
1. **Categorization**: The user query is sent to a Groq LLM to determine the sentiment (Positive/Neutral/Negative) and the target Department.
2. **Conditional Routing**:
   - *Escalation*: If sentiment is Negative OR the department is Unknown, it routes to a Human Escalation node.
   - *RAG*: Otherwise, it routes to the Department-Aware RAG workflow.
3. **Department-Aware Retrieval**: Queries a local ChromaDB instance using local Hugging Face embeddings (`sentence-transformers/all-MiniLM-L6-v2`). The categorized department is applied as a metadata filter to prevent cross-department retrieval and knowledge leakage.
4. **Relevance Threshold & Controlled Abstention**: If retrieved documents do not meet the configured relevance threshold, the system skips LLM generation and returns a controlled abstention response to reduce hallucinations.
5. **Grounded Generation**: If relevant context is found, it uses Groq to generate a final answer *strictly* grounded in the retrieved documents. Conversational history is injected into the prompt, allowing for stateful multi-turn interactions.
6. **Reflection (Optional)**: Can be toggled on to re-verify the output against the context.

## Local Setup & Installation

### 1. Prerequisites
- Python 3.10+
- A Groq API Key

### 2. Environment Setup
Create a virtual environment and install the dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```
### 3. Configuration
Rename the provided environment template:
```bash
cp .env.example .env
```
Edit the `.env` file to include your API key:
```env
GROQ_API_KEY=your_groq_api_key_here
TOP_K=3
RELEVANCE_THRESHOLD=0.35
ENABLE_REFLECTION=False
```
### 4. Data Generation & Database Initialization
Generate the dataset once when the knowledge base needs to be created or updated.
Then run database.py to rebuild the Chroma collection from the current dataset.

Generate the synthetic QA dataset:
```bash
python data_generation.py
```
*(This will create a JSON file in the `data/` directory with 20 QA pairs per department).*

Initialize and populate the local ChromaDB vector database:
```bash
python database.py
```
*(This will embed the data using local Hugging Face models and persist it to `chroma_db/`).*

## Knowledge Base

The project uses a synthetic retail support dataset containing 80 QA records:

| Department | QA Records |
|---|---:|
| HR | 20 |
| IT Support | 20 |
| Billing & Payments | 20 |
| Shipping & Delivery | 20 |
| **Total** | **80** |

Each record includes department and audience metadata, enabling department-aware retrieval and preventing cross-department knowledge leakage.

## Running the Application

### Streamlit Web Interface
Run the conversational UI:
```bash
streamlit run ui.py
```
### Command Line Interface
Test the agent using the simple CLI:
```bash
python main.py --query "How do I apply for paid time off?"
```

### FastAPI Web Server
Run the FastAPI wrapper to expose a REST endpoint:
```bash
python app.py
```
Then send a POST request to `http://localhost:8000/query`:
```json
{
  "query": "My laptop screen is flickering."
}
```

## Running Evaluations
The project includes a deterministic evaluation suite that does not consume excessive LLM tokens. Run it to verify routing, abstention, and escalation behaviors:
```bash
python evaluation.py
```
**Current evaluation result: 5/5 tests passed.**

The evaluation validates:
- Department-aware retrieval
- Correct RAG responses
- Controlled abstention
- Negative-sentiment escalation
- Routing behavior

## Technology Stack

- **Python**
- **LangGraph** — agent workflow and conditional routing
- **LangChain** — LLM and RAG integration
- **Groq** — LLM inference
- **ChromaDB** — vector database
- **Hugging Face Sentence Transformers** — local embeddings
- **FastAPI** — REST API
- **Streamlit** — conversational web interface
- **Pydantic** — structured data validation
- **GitHub** — version control and deployment source
