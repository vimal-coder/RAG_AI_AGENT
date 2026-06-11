import os

# Database configurations
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "zcare_rag")
DB_DIR_NAME = os.getenv("CHROMA_DB_DIR_NAME", "chroma_db")

# Ingestion configurations
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

# Model configurations
EMBEDDING_MODEL_NAME = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/paraphrase-MiniLM-L3-v2")
GROQ_MODEL_NAME = os.getenv("RAG_GROQ_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("RAG_LLM_TEMPERATURE", "0.3"))

# Support details
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@zautomate.in")
SUPPORT_PHONE = os.getenv("SUPPORT_PHONE", "+91 8589088985")

# Memory configurations
MAX_MEMORY_TURNS = int(os.getenv("RAG_MAX_MEMORY_TURNS", "5"))

