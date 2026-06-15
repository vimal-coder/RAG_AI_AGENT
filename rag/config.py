import os
import configparser

# Determine project root path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load init.ini
init_parser = configparser.ConfigParser()
init_ini_path = os.path.join(PROJECT_ROOT, "init.ini")
if os.path.exists(init_ini_path):
    init_parser.read(init_ini_path)

# Load config.ini
config_parser = configparser.ConfigParser()
config_ini_path = os.path.join(PROJECT_ROOT, "config.ini")
if os.path.exists(config_ini_path):
    config_parser.read(config_ini_path)

# Database configurations
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME") or init_parser.get("Initialization", "COLLECTION_NAME", fallback="zcare_rag")
DB_DIR_NAME = os.getenv("CHROMA_DB_DIR_NAME") or init_parser.get("Initialization", "DB_DIR_NAME", fallback="chroma_db")

# Ingestion configurations
AUTO_INGEST_RAW = os.getenv("AUTO_INGEST") or init_parser.get("Initialization", "AUTO_INGEST", fallback="true")
AUTO_INGEST = AUTO_INGEST_RAW.lower() in ("true", "1", "yes")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE") or init_parser.get("Initialization", "CHUNK_SIZE", fallback="500"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP") or init_parser.get("Initialization", "CHUNK_OVERLAP", fallback="50"))

# Model configurations
EMBEDDING_MODEL_NAME = os.getenv("RAG_EMBEDDING_MODEL") or init_parser.get("Initialization", "EMBEDDING_MODEL_NAME", fallback="sentence-transformers/paraphrase-MiniLM-L3-v2")
VECTOR_SIZE = int(os.getenv("RAG_VECTOR_SIZE") or init_parser.get("Initialization", "VECTOR_SIZE", fallback="384"))
GROQ_MODEL_NAME = os.getenv("RAG_GROQ_MODEL") or config_parser.get("Model", "GROQ_MODEL_NAME", fallback="llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("RAG_LLM_TEMPERATURE") or config_parser.get("Model", "LLM_TEMPERATURE", fallback="0.3"))
CONTEXT_LENGTH = int(os.getenv("RAG_CONTEXT_LENGTH") or config_parser.get("Model", "CONTEXT_LENGTH", fallback="4096"))
MAX_TOKENS = int(os.getenv("RAG_MAX_TOKENS") or config_parser.get("Model", "MAX_TOKENS", fallback="1024"))
RETRIEVER_K = int(os.getenv("RAG_RETRIEVER_K") or config_parser.get("Model", "RETRIEVER_K", fallback="3"))

# Support details
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL") or config_parser.get("Support", "SUPPORT_EMAIL", fallback="support@zautomate.in")
SUPPORT_PHONE = os.getenv("SUPPORT_PHONE") or config_parser.get("Support", "SUPPORT_PHONE", fallback="+91 8589088985")

# Memory configurations
MAX_MEMORY_TURNS = int(os.getenv("RAG_MAX_MEMORY_TURNS") or config_parser.get("Memory", "MAX_MEMORY_TURNS", fallback="5"))

# CORS configurations
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS") or config_parser.get("CORS", "ALLOWED_ORIGINS", fallback="")
