"""Search API route for hybrid semantic vector search and RAG direct answer synthesis."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.search_service import search_candidates_with_rag

router = APIRouter(prefix="/api", tags=["Search"])


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
def post_search(body: SearchRequest):
    """Semantic vector search across all candidate resumes with RAG AI direct answer synthesis."""
    if not body.query or not body.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    return search_candidates_with_rag(body.query.strip())


@router.get("/search")
def get_search(q: str = Query(..., description="Natural language search query")):
    """GET endpoint for natural language query search."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query parameter 'q' cannot be empty.")

    return search_candidates_with_rag(q.strip())
