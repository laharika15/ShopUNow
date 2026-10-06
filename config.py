import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# RAG Configuration
TOP_K = int(os.getenv("TOP_K", 3))
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.35))

# Application Mode
ENABLE_REFLECTION = os.getenv("ENABLE_REFLECTION", "False").lower() in ["true", "1", "yes"]

# LLM Models
ROUTER_MODEL = "openai/gpt-oss-20b"  # Recommended robust model for Groq categorization
RAG_MODEL = "openai/gpt-oss-20b"      # Smaller, faster model for simple grounded generation

# Paths
CHROMA_PERSIST_DIR = "./chroma_db"
DATASET_PATH = "./data/shopunow_qa_dataset.json"

# Embedding Model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
