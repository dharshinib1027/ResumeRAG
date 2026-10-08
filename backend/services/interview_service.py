"""Interview question generation service."""
from typing import Dict, Any
from backend.services.resume_service import get_candidate_by_id
from backend.rag.generator import generate_interview_questions


def generate_candidate_interview(candidate_id: str) -> Dict[str, Any]:
    """
    Retrieve candidate profile and generate personalized, grounded interview questions.
    """
    profile = get_candidate_by_id(candidate_id)
    if not profile:
        raise ValueError(f"Candidate with ID '{candidate_id}' not found.")

    candidate_name = profile["candidate_name"]
    full_text = profile.get("full_text", "")

    result = generate_interview_questions(
        candidate_name=candidate_name,
        candidate_profile=profile,
        resume_context=full_text
    )

    result["candidate_id"] = candidate_id
    result["filename"] = profile.get("filename", "")
    result["contact_info"] = profile.get("contact_info", {})
    return result
