# ZCare AI Assistant - RAG Chatbot

ZCare AI Assistant is a modern, responsive, and intelligent virtual assistant designed for ZCare Hospital. It leverages Retrieval-Augmented Generation (RAG) to answer user questions about doctor timings, appointment booking, visitor policies, and general hospital information. 

The application features a sleek, premium web interface on the frontend, and a powerful Python backend orchestrated by FastAPI, LangGraph, ChromaDB, and Groq API.

---

## Table of Contents
1. [Key Features](#key-features)
2. [Project Architecture & File Structure](#project-architecture--file-structure)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
   - [Step 1: Navigate to Project Directory](#step-1-navigate-to-project-directory)
   - [Step 2: Create a Python Virtual Environment](#step-2-create-a-python-virtual-environment)
   - [Step 3: Activate the Virtual Environment](#step-3-activate-the-virtual-environment)
   - [Step 4: Install Dependencies](#step-4-install-dependencies)
   - [Step 5: Configure Environment Variables & Configuration Files](#step-5-configure-environment-variables-and-configuration-files)
   - [Step 6: Document Ingestion (Data Vectorization)](#step-6-document-ingestion-data-vectorization)
   - [Step 7: Run the FastAPI Server](#step-7-run-the-fastapi-server)
   - [Step 8: Access the Application](#step-8-access-the-application)
5. [How to Use the Chat Interface](#how-to-use-the-chat-interface)
6. [API Endpoints](#api-endpoints)

---

## Key Features

- **Dynamic Chat Interface**: A rich, premium frontend UI built with HTML5, CSS3, and Vanilla JavaScript using modern typography (Inter, Outfit), responsive layouts, clean card grids, modals, and transition animations.
- **State-Graph Routing**: Leverages LangGraph to orchestrate RAG workflow states (`retrieve` -> `generate`).
- **Semantic Vector Search**: Uses HuggingFace's embedding model (`sentence-transformers/paraphrase-MiniLM-L3-v2`) and ChromaDB vector store to fetch relevant contexts from hospital PDF guides.
- **Strict Grounding Rules**: System prompts enforce answering queries only when supported by the retrieved contexts, preventing AI hallucinations. If information is missing, users are guided to direct email or phone support.
- **Automatic Document Ingestion & Versioning**: Features a built-in background watcher that continuously monitors the `DataSource/updated/` directory. New PDFs are automatically chunked, ingested, and their older versions are purged from the vector database before being safely moved to `DataSource/archived/` with timestamping.
- **Conversational Memory**: Retains memory of the chat up to a configurable number of turns (default: 5).
- **Interactive Feedback System**: Built-in rating buttons (Helpful/Not Helpful) and a custom feedback form popup modal.

---

## Project Architecture & File Structure

```text
RAG_AI_AGENT/
├── DataSource/             # Source documents (PDFs) containing hospital information
│   ├── updated/            # Drop new PDF files here for automatic ingestion
│   └── archived/           # Automatically archived PDFs with timestamp versioning
├── chroma_db/              # Vector database storage folder (generated automatically)
├── rag/                    # Core RAG python module
│   ├── __init__.py
│   ├── config.py           # Configuration parameters and defaults
│   ├── graph.py            # LangGraph agent definition & LLM logic
│   ├── ingest.py           # Text splitting, embedding creation & database ingestion
│   └── watch_folder.py     # Background daemon monitoring the updated directory
├── static/                 # Frontend assets served statically
│   ├── icon/               # Graphic assets (stethoscopes, mail icons, etc.)
│   ├── index.html          # Main HTML structure template
│   ├── index.js            # Chat UI logic, event listeners, and API calls
│   └── style.css           # Styling rules (color palette, animations, layouts)
├── .env                    # Environment variables (API keys and secrets)
├── init.ini                # Initialization configuration parameters (database, chunking, etc.)
├── config.ini              # Runtime configuration parameters (model details, support, CORS, etc.)
├── .gitignore              # Files and directories ignored by Git
├── requirements.txt        # Python package dependencies list
└── main.py                 # FastAPI application server entrypoint
```

---

## Prerequisites

Ensure you have the following installed on your system:
- **Python 3.10** or higher
- A browser (Chrome, Edge, Firefox, etc.)
- A **Groq API Key** (Get one from the [Groq Console](https://console.groq.com/))

---

## Step-by-Step Setup Guide

Follow these instructions to run the project locally.

### Step 1: Navigate to Project Directory
Open your terminal (PowerShell or Command Prompt on Windows, Terminal on macOS/Linux) and navigate to the project directory:
```bash
cd c:\Users\Vimal\Documents\RAG_AI_AGENT
```

### Step 2: Create a Python Virtual Environment
It is recommended to run the project in a virtual environment to isolate the dependencies:
```bash
# Windows
python -m venv .venv

# macOS / Linux
python3 -m venv .venv
```

### Step 3: Activate the Virtual Environment
Activate the environment to start using it:
- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

Once activated, your terminal prompt should display `(.venv)` at the beginning.

### Step 4: Install Dependencies
Upgrade pip and install the required libraries:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*(This will install FastAPI, Uvicorn, LangChain, LangGraph, ChromaDB, HuggingFace embeddings, Groq connectors, PyPDF, and other utility packages).*

### Step 5: Configure Environment Variables and Configuration Files

The project separates configuration parameters into environment variables (for secrets) and configuration files (for settings).

1. **Environment Variables (`.env`)**:
   Create or open the `.env` file in the root directory and add your secret API key:
   ```env
   GROQ_API_KEY="your_actual_groq_api_key_here"
   ```

2. **Initialization Configurations (`init.ini`)**:
   Configure parameters related to initialization of the vector store and database chunking in `init.ini`:
   ```ini
   [Initialization]
   COLLECTION_NAME = zcare_rag
   DB_DIR_NAME = chroma_db
   AUTO_INGEST = true
   CHUNK_SIZE = 500
   CHUNK_OVERLAP = 50
   EMBEDDING_MODEL_NAME = sentence-transformers/paraphrase-MiniLM-L3-v2
   VECTOR_SIZE = 384
   ```

3. **Runtime Configurations (`config.ini`)**:
   Configure general parameters, model settings, and support details in `config.ini`:
   ```ini
   [Model]
   GROQ_MODEL_NAME = llama-3.3-70b-versatile
   LLM_TEMPERATURE = 0.3
   CONTEXT_LENGTH = 4096
   MAX_TOKENS = 1024
   RETRIEVER_K = 3

   [Memory]
   MAX_MEMORY_TURNS = 5

   [Support]
   SUPPORT_EMAIL = support@zautomate.in
   SUPPORT_PHONE = +91 8589088985

   [CORS]
   # Comma-separated list of allowed origins (leave blank for none, or list them)
   ALLOWED_ORIGINS = 
   ```

#### Configuration Priority & Fallback Order:
The configuration system resolves values in the following order of precedence:
1. **Environment Variables** (e.g. `RAG_CHUNK_SIZE` or `CHUNK_SIZE` loaded via `.env`)
2. **Configuration Files** (from `init.ini` or `config.ini`)
3. **Built-in Defaults** (pre-coded default values)

### Step 6: Document Ingestion (Data Vectorization & Versioning)
The application reads hospital information from the PDF files dropped into the `DataSource/updated/` folder. 

- **Automatic Continuous Ingestion**: You do not need to manually run any scripts. When you launch the FastAPI server, a background folder-watcher daemon is automatically started. Any new PDFs dropped into `DataSource/updated/` will be:
  1. Instantly detected.
  2. Checked for older versions (old vector chunks are automatically deleted from ChromaDB).
  3. Chunked and saved into the `chroma_db/` vector database.
  4. Moved automatically into `DataSource/archived/` with a timestamp to prevent clutter and maintain history.
- **Startup Ingestion**: Additionally, any files left in the `updated` folder while the server was offline will be automatically processed on the next startup.

### Step 7: Run the FastAPI Server
Launch the backend server using the following command:
```bash
python main.py
```
Or run directly via uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Upon launching:
1. It validates your `GROQ_API_KEY`.
2. It automatically checks and runs PDF ingestion if the database does not exist.
3. It pre-warms the heavy embeddings models in the background to speed up your first prompt.

### Step 8: Access the Application
Open your web browser and navigate to:
```text
http://localhost:8000
```

---

## How to Use the Chat Interface

1. **Ask a Question**: Type any question into the input box at the bottom of the page (e.g., *"When is Dr. Vimal available?"* or *"What is the hospital visiting hours policy?"*) and hit Enter or click the send button.
2. **Quick Action Cards**: Click on any of the preloaded action cards (e.g. **Find a Doctor**, **Book Appointment**, **Doctor Timings**) to automatically send a query and fetch immediate details.
3. **Clear Conversation**: Click the **"clear and start a new conversation"** link at the bottom of the screen to start fresh and reset memory.
4. **Submit Feedback**:
   - Use the **Helpful** or **Not Helpful** buttons in the footer to rate your experience.
   - Click the green **Feedback** button to open the feedback popup and write a comment.
5. **Direct Actions**:
   - Click **Email Us** to open your default mail client prepopulated with the ZCare support address.
   - Click **Call Support** to place a direct phone call.

---

## API Endpoints

The backend exposes the following API routes:
- **`GET /`**: Renders the main dashboard page using Jinja2 templates.
- **`POST /chat`**: The primary conversational route.
  - *Request Body*:
    ```json
    {
      "question": "What is the policy for cancellation?",
      "chat_history": []
    }
    ```
  - *Response Body*:
    ```json
    {
      "answer": "Cancellation of appointments must be done...",
      "chat_history": ["user: What is the...", "assistant: Cancellation of..."]
    }
    ```
- **`GET /favicon.ico`**: Serves the hospital medical symbol icon.
- **`/static/*`**: Serves UI stylesheets (`style.css`), page scripts (`index.js`), and asset graphics.
