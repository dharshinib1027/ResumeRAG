"""Candidate Details API route."""
from fastapi import APIRouter, HTTPException
from backend.services.resume_service import get_candidate_by_id

router = APIRouter(prefix="/api", tags=["Candidate Details"])


@router.get("/candidate/{candidate_id}")
def get_candidate_details(candidate_id: str):
    """Retrieve complete structured candidate profile details."""
    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found.")
    return candidate
