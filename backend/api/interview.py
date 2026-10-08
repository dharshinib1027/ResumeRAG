"""Interview Question Generation API route."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.interview_service import generate_candidate_interview

router = APIRouter(prefix="/api", tags=["Interview Questions"])


class InterviewRequest(BaseModel):
    candidate_id: str


@router.post("/interview/generate")
def generate_interview(body: InterviewRequest):
    """Generate personalized, resume-grounded interview questions for a candidate."""
    try:
        return generate_candidate_interview(body.candidate_id)
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Interview question generation failed: {str(exc)}")


@router.get("/interview/{candidate_id}")
def get_interview(candidate_id: str):
    """GET endpoint to generate/retrieve interview questions for candidate_id."""
    try:
        return generate_candidate_interview(candidate_id)
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Interview question generation failed: {str(exc)}")
