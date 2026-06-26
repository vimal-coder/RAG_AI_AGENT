import os
import glob
import sys
import shutil
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Import centralized configurations
from rag.config import (
    COLLECTION_NAME, EMBEDDING_MODEL_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, DB_DIR,
    UPDATED_DIR, ARCHIVED_DIR
)

def setup_directories():
    """Ensures that the necessary directories exist."""
    os.makedirs(UPDATED_DIR, exist_ok=True)
    os.makedirs(ARCHIVED_DIR, exist_ok=True)

def get_pdf_files(data_dir: str) -> list:
    """Retrieves all PDF paths from the directory."""
    if not os.path.exists(data_dir):
        return []
    return glob.glob(os.path.join(data_dir, "*.pdf"))

def load_documents(pdf_path: str) -> list:
    """Loads all pages from a single PDF file and adds filename metadata."""
    print(f"Loading document: {os.path.basename(pdf_path)}...")
    try:
        loader = PyPDFLoader(pdf_path)
        loaded_docs = loader.load()
        filename = os.path.basename(pdf_path)
        for doc in loaded_docs:
            doc.metadata["filename"] = filename
        print(f"Loaded {len(loaded_docs)} pages from {filename}")
        return loaded_docs
    except Exception as e:
        print(f"Error loading {pdf_path}: {e}", file=sys.stderr)
        return []

def split_documents(documents: list, chunk_size: int, chunk_overlap: int) -> list:
    """Splits loaded pages/documents into smaller text chunks."""
    if not documents:
        return []
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

def delete_old_embeddings(filename: str, vector_store: Chroma):
    """Deletes existing chunks for a given filename to prevent duplication."""
    try:
        collection = vector_store._collection
        collection.delete(where={"filename": filename})
        print(f"Deleted old embeddings for {filename} from ChromaDB.")
    except Exception as e:
        print(f"Error or no old embeddings found for {filename}: {e}", file=sys.stderr)

def archive_pdf(pdf_path: str):
    """Moves the processed PDF to the archived directory with a timestamp."""
    filename = os.path.basename(pdf_path)
    base, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_filename = f"{base}_{timestamp}{ext}"
    archived_path = os.path.join(ARCHIVED_DIR, archived_filename)
    
    try:
        shutil.move(pdf_path, archived_path)
        print(f"Archived file to: {archived_path}")
    except Exception as e:
        print(f"Error archiving {pdf_path}: {e}", file=sys.stderr)

def ingest_documents():
    """Main orchestrator for the document ingestion pipeline."""
    setup_directories()
    pdf_files = get_pdf_files(UPDATED_DIR)
    
    if not pdf_files:
        print(f"No PDF files found in {UPDATED_DIR}. Ingestion cancelled.")
        return

    print(f"Found {len(pdf_files)} PDF files to process in {UPDATED_DIR}.")
    
    print(f"Initializing embeddings model: {EMBEDDING_MODEL_NAME}...")
    embeddings = initialize_embeddings(EMBEDDING_MODEL_NAME)
    
    # Initialize Vector Store once
    vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory=DB_DIR,
        collection_name=COLLECTION_NAME
    )

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"--- Processing {filename} ---")
        
        # 1. Delete old embeddings for this file
        delete_old_embeddings(filename, vector_store)
        
        # 2. Load and chunk the new document
        documents = load_documents(pdf_path)
        if not documents:
            continue
            
        chunks = split_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # 3. Add new chunks to vector store
        if chunks:
            try:
                vector_store.add_documents(chunks)
                print(f"Added {len(chunks)} new chunks for {filename} to ChromaDB.")
            except Exception as e:
                print(f"Error adding chunks for {filename}: {e}", file=sys.stderr)
                continue
                
        # 4. Archive the processed file
        archive_pdf(pdf_path)
        
    print("Ingestion cycle completed successfully!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    ingest_documents()
