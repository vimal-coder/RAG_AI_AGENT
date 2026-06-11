import os
import glob
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Import centralized configurations
from rag.config import (
    COLLECTION_NAME, DB_DIR_NAME, EMBEDDING_MODEL_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP
)

# Resolve absolute paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(PROJECT_ROOT, DB_DIR_NAME)
DATA_SOURCE_DIR = os.path.join(PROJECT_ROOT, "DataSource")

def get_pdf_files(data_source_dir: str) -> list:
    """Checks if the data source directory exists and retrieves all PDF paths."""
    if not os.path.exists(data_source_dir):
        print(f"Warning: Data source directory '{data_source_dir}' not found. Creating it...", file=sys.stderr)
        os.makedirs(data_source_dir, exist_ok=True)
        return []
        
    return glob.glob(os.path.join(data_source_dir, "*.pdf"))

def load_documents(pdf_files: list) -> list:
    """Loads all pages from the list of PDF files."""
    documents = []
    for pdf_path in pdf_files:
        print(f"Loading document: {os.path.basename(pdf_path)}...")
        try:
            loader = PyPDFLoader(pdf_path)
            loaded_docs = loader.load()
            print(f"Loaded {len(loaded_docs)} pages from {os.path.basename(pdf_path)}")
            documents.extend(loaded_docs)
        except Exception as e:
            print(f"Error loading {pdf_path}: {e}", file=sys.stderr)
    return documents

def split_documents(documents: list, chunk_size: int, chunk_overlap: int) -> list:
    """Splits loaded pages/documents into smaller text chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks from loaded pages.")
    return chunks

def initialize_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    """Initializes and returns the HuggingFace embeddings model."""
    return HuggingFaceEmbeddings(model_name=model_name)

def save_to_vector_store(chunks: list, embeddings: HuggingFaceEmbeddings, db_dir: str, collection_name: str) -> Chroma:
    """Stores the text chunks in ChromaDB vector store."""
    try:
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=db_dir,
            collection_name=collection_name
        )
        if hasattr(vector_store, "persist"):
            vector_store.persist()
        return vector_store
    except Exception as e:
        print(f"Error saving to ChromaDB: {e}", file=sys.stderr)
        raise e

def ingest_documents():
    """Main orchestrator for the document ingestion pipeline."""
    pdf_files = get_pdf_files(DATA_SOURCE_DIR)
    if not pdf_files:
        print("No PDF files found to process. Ingestion cancelled.")
        return

    print(f"Found {len(pdf_files)} PDF files to process.")
    documents = load_documents(pdf_files)
    if not documents:
        print("No document pages loaded. Ingestion cancelled.")
        return

    print("Splitting documents into chunks...")
    chunks = split_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP)

    print(f"Initializing embeddings model: {EMBEDDING_MODEL_NAME}...")
    embeddings = initialize_embeddings(EMBEDDING_MODEL_NAME)

    print(f"Indexing chunks to ChromaDB at '{DB_DIR}'...")
    save_to_vector_store(chunks, embeddings, DB_DIR, COLLECTION_NAME)
    print("Ingestion completed successfully! Vector database is ready.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    ingest_documents()
