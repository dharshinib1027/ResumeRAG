"""Upload API route for multiple resume uploads and resume management."""
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.services.resume_service import (
    process_uploaded_resume,
    get_all_candidates,
    delete_candidate,
    get_stats
)

router = APIRouter(prefix="/api", tags=["Upload & Resumes"])


@router.post("/upload")
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Upload multiple candidate PDF or DOCX resumes."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    results = []
    errors = []

    for file in files:
        filename = file.filename
        if not filename.lower().endswith((".pdf", ".docx")):
            errors.append(f"'{filename}' skipped: Only PDF and DOCX formats are supported.")
            continue

        try:
            content = await file.read()
            res = process_uploaded_resume(content, filename)
            results.append(res)
        except Exception as exc:
            errors.append(f"Failed to process '{filename}': {str(exc)}")

    return {
        "message": f"Successfully processed {len(results)} resume(s).",
        "uploaded_count": len(results),
        "results": results,
        "errors": errors
    }


@router.get("/resumes")
def list_resumes():
    """List all uploaded candidate profiles."""
    return get_all_candidates()


@router.delete("/resumes/{candidate_id}")
def remove_candidate(candidate_id: str):
    """Delete a candidate profile and their vector index."""
    success = delete_candidate(candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return {"message": "Candidate removed successfully.", "candidate_id": candidate_id}


@router.get("/stats")
def get_dashboard_stats():
    """Return stats for recruiter dashboard."""
    return get_stats()
