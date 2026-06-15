import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager
from rag.config import SUPPORT_EMAIL, SUPPORT_PHONE, AUTO_INGEST, ALLOWED_ORIGINS

# Load environment variables
load_dotenv()


# Initialize Jinja2 templates
templates = Jinja2Templates(directory="static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify API key at startup
    if not os.getenv("GROQ_API_KEY"):
        print("CRITICAL: GROQ_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Check if we should auto-ingest new files on startup
    auto_ingest = AUTO_INGEST
    
    if auto_ingest:
        print("Checking for new documents to auto-ingest...")
        try:
            from rag import ingest_documents
            ingest_documents()
        except Exception as e:
            print(f"Error during startup ingestion: {e}", file=sys.stderr)

        # Start the background folder watcher
        import threading
        try:
            from rag.watch_folder import start_watching
            watcher_thread = threading.Thread(target=start_watching, daemon=True)
            watcher_thread.start()
            print("Background folder watcher started successfully.")
        except Exception as e:
            print(f"Error starting background folder watcher: {e}", file=sys.stderr)

    # Pre-warm heavy RAG components in a background thread so first query is instant
    import asyncio
    def pre_warm():
        print("Pre-warming RAG model components (Embeddings, Retriever, LLM, Graph)...")
        try:
            from rag import get_embeddings, get_retriever, get_llm, get_graph
            get_embeddings()
            get_retriever()
            get_llm()
            get_graph()
            print("RAG components pre-warmed successfully and cached.")
        except Exception as e:
            print(f"Warning: RAG pre-warming failed: {e}", file=sys.stderr)

    asyncio.get_event_loop().run_in_executor(None, pre_warm)
    yield

app = FastAPI(title="ZCare AI Assistant Backend", lifespan=lifespan)

# CORS configuration
allowed_origins_str = ALLOWED_ORIGINS
origins = allowed_origins_str.split(",") if allowed_origins_str else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static directory for serving CSS, JS, and icons
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    question: str
    chat_history: List[str] = []

class ChatResponse(BaseModel):
    answer: str
    chat_history: List[str]

@app.get("/")
async def get_index(request: Request):
    """Serves the main application landing page using Jinja2 templates."""
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")
    if not os.path.exists(index_path):
        print(f"index.html not found under static directory at: {index_path}", file=sys.stderr)
        raise HTTPException(status_code=404, detail="index.html not found under static directory")
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "support_email": SUPPORT_EMAIL,
            "support_phone": SUPPORT_PHONE,
            "support_phone_raw": SUPPORT_PHONE.replace(" ", "")
        }
    )

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serves the application favicon to prevent 404 errors."""
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "icon", "medical-symbol.png"))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
        from rag import get_graph
        result = get_graph().invoke({
            "question": question,
            "chat_history": request.chat_history
        })
        
        answer = result.get("answer")
        if not answer:
            raise ValueError("Empty response returned from the RAG graph.")
            
        return ChatResponse(
            answer=answer,
            chat_history=result.get("chat_history", request.chat_history)
        )
    except Exception as e:
        print(f"Error invoking graph: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
