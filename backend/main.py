"""Main FastAPI Application Entry Point for ResumeRAG."""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import upload, search, candidate, interview


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm sentence-transformer embedding model on server startup."""
    try:
        from backend.rag.embeddings import get_embedding_model
        print("Pre-warming SentenceTransformer embedding model...")
        get_embedding_model()
        print("Embedding model ready!")
    except Exception as exc:
        print(f"Warning: Model pre-warming deferred: {exc}")
    yield


app = FastAPI(
    title="ResumeRAG – AI-Powered Resume Intelligence System",
    description="Recruitment Assistant API for semantic resume search, candidate profile extraction, and grounded interview question generation.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload.router)
app.include_router(search.router)
app.include_router(candidate.router)
app.include_router(interview.router)


@app.get("/health")
def health_check():
    """System health check endpoint."""
    llm_key_present = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "online" if llm_key_present else "degraded (GEMINI_API_KEY missing)",
        "system": "ResumeRAG Intelligence Engine",
        "llm_available": llm_key_present,
        "llm_provider": os.getenv("LLM_PROVIDER", "gemini")
    }


# Serve static frontend files if frontend directory exists
FRONTEND_DIR = ROOT_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
