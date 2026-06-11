import os
import sys
from typing import TypedDict, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END

# Import centralized configurations
from rag.config import (
    COLLECTION_NAME, DB_DIR_NAME, EMBEDDING_MODEL_NAME, 
    GROQ_MODEL_NAME, LLM_TEMPERATURE, 
    SUPPORT_EMAIL, SUPPORT_PHONE, MAX_MEMORY_TURNS
)

# Define Graph State
class GraphState(TypedDict):
    question: str
    chat_history: List[str]
    context: str
    answer: str

# Shared singletons for performance optimization
_embeddings = None
_retriever = None
_llm = None
_graph = None

def get_db_dir() -> str:
    """Resolves and returns the database directory path dynamically."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, DB_DIR_NAME)

def get_embeddings():
    """Lazily initializes and reuses HuggingFaceEmbeddings instance."""
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings

def get_retriever():
    """Lazily initializes the Chroma vector store and returns a retriever singleton."""
    global _retriever
    if _retriever is None:
        from langchain_chroma import Chroma
        _retriever = Chroma(
            persist_directory=get_db_dir(),
            embedding_function=get_embeddings(),
            collection_name=COLLECTION_NAME
        ).as_retriever(search_kwargs={"k": 3})
    return _retriever

def get_llm():
    """Lazily initializes and reuses the LLM instance."""
    global _llm
    if _llm is None:
        from langchain_groq import ChatGroq
        _llm = ChatGroq(
            model=GROQ_MODEL_NAME,
            temperature=LLM_TEMPERATURE,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    return _llm

def format_retrieved_documents(docs: list) -> str:
    """Combines documents content and metadata into formatted text for the prompt."""
    return "\n\n".join(
        f"--- Document: {os.path.basename(doc.metadata.get('source', 'Unknown'))} (Page {doc.metadata.get('page', 0) + 1}) ---\n{doc.page_content}"
        for doc in docs
    )

def parse_chat_history(chat_history: List[str]) -> list:
    """Parses raw text chat history into LangChain Message objects."""
    messages = []
    for msg in chat_history:
        if msg.startswith("user: "):
            messages.append(HumanMessage(content=msg[6:]))
        elif msg.startswith("assistant: "):
            messages.append(AIMessage(content=msg[11:]))
        else:
            messages.append(HumanMessage(content=msg))
    return messages

def get_system_prompt(context: str) -> str:
    """Returns the formatted system instructions with context."""
    return f"""You are ZCare AI Assistant, the friendly, professional, and intelligent virtual assistant for ZCare Hospital.
Your goal is to assist users with their questions about doctor timings, appointments, hospital policies, and general information based on the provided documents.

RULES FOR RESPONSE GENERATION:
1. Ground your answers strictly on the retrieved context below. Do not make up facts.
2. If the context does not contain enough information to answer a question:
   - Politely state that you do not have that specific information in your records.
   - Guide the user to contact ZCare Support via email at {SUPPORT_EMAIL} or by calling {SUPPORT_PHONE}.
3. If the user asks about rating their experience, giving feedback, or sharing thoughts:
   - Guide them to the interactive rating screen: "Rate your experience" buttons (Helpful/Not Helpful thumbs) located at the bottom of the screen.
   - They can also submit comments by clicking the green "Feedback" button in the secondary actions row (with the speech bubble icon) which opens the "Share Your Feedback" modal.
   - Inside the feedback modal, they can also find options to "Call Support" directly.
4. If the user asks how to email support or connect via email, instruct them:
   - They can click the green "Email Us" button in the actions row to open their mail client directly to {SUPPORT_EMAIL}.
   - Or they can compose an email manually to {SUPPORT_EMAIL}.
5. If the user asks for support contact details:
   - Email: {SUPPORT_EMAIL}
   - Mobile: {SUPPORT_PHONE}
6. Maintain a helpful, empathetic, and clear medical assistant persona. Use markdown formatting (bold, bullet points) to structure your responses for readability.

Retrieved Context:
{context}
"""

# Retrieve Node
def retrieve_node(state: GraphState) -> dict:
    """Retrieves relevant documents from ChromaDB based on the user question."""
    question = state.get("question", "").strip()
    if not question:
        return {"context": ""}
    
    try:
        docs = get_retriever().invoke(question)
        return {"context": format_retrieved_documents(docs)}
    except Exception as e:
        print(f"Error during document retrieval: {e}", file=sys.stderr)
        return {"context": ""}

def trim_chat_history(chat_history: List[str], max_turns: int = MAX_MEMORY_TURNS) -> List[str]:
    """Trims raw text chat history to a specified context window of last N turns.
    Each turn consists of a user message and an assistant response, which corresponds to 2 list items.
    """
    max_messages = max_turns * 2
    if len(chat_history) > max_messages:
        return chat_history[-max_messages:]
    return chat_history

# Generate Node
def generate_node(state: GraphState) -> dict:
    """Generates a response using the selected LLM and the retrieved context."""
    question = state.get("question", "")
    chat_history = state.get("chat_history", [])
    context = state.get("context", "")
    
    trimmed_history = trim_chat_history(chat_history)
    messages = parse_chat_history(trimmed_history)
    system_prompt = get_system_prompt(context)
    full_messages = [SystemMessage(content=system_prompt)] + messages + [HumanMessage(content=question)]
    
    try:
        response = get_llm().invoke(full_messages)
        answer = response.content
    except Exception as e:
        print(f"Error during LLM generation: {e}", file=sys.stderr)
        answer = f"I'm sorry, I encountered an error generating the response. Please contact our support team at {SUPPORT_EMAIL} or {SUPPORT_PHONE}."

    return {
        "answer": answer,
        "chat_history": chat_history + [f"user: {question}", f"assistant: {answer}"]
    }

def get_graph():
    """Lazily compiles and returns the LangGraph workflow singleton."""
    global _graph
    if _graph is None:
        workflow = StateGraph(GraphState)
        workflow.add_node("retrieve", retrieve_node)
        workflow.add_node("generate", generate_node)
        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        _graph = workflow.compile()
    return _graph
