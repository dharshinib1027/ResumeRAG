"""Resume management service."""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from backend.rag.loader import parse_resume_file
from backend.rag.chunker import chunk_sections
from backend.rag.vector_store import add_chunks_to_vectorstore, delete_resume_vectors, get_total_chunks_count

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "data" / "resumes"
PROFILES_FILE = BASE_DIR / "data" / "profiles.json"


def _ensure_dirs():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    if not PROFILES_FILE.exists():
        PROFILES_FILE.write_text("{}", encoding="utf-8")


def _load_profiles() -> Dict[str, Any]:
    _ensure_dirs()
    try:
        content = PROFILES_FILE.read_text(encoding="utf-8")
        return json.loads(content) if content.strip() else {}
    except Exception:
        return {}


def _save_profiles(profiles: Dict[str, Any]):
    _ensure_dirs()
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2), encoding="utf-8")


def process_uploaded_resume(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Process single uploaded resume file:
    1. Save raw PDF/DOCX to disk
    2. Extract text, sections, skills, contact info
    3. Chunk text & generate embeddings
    4. Store in ChromaDB
    5. Save profile metadata
    """
    _ensure_dirs()
    resume_id = str(uuid.uuid4())[:8]
    candidate_id = f"cand_{resume_id}"

    saved_path = UPLOADS_DIR / f"{resume_id}_{filename}"
    saved_path.write_bytes(file_bytes)

    # Parse file
    parsed = parse_resume_file(saved_path)
    candidate_name = parsed["candidate_name"]

    # Chunk sections
    chunks = chunk_sections(
        sections=parsed["sections"],
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        resume_id=resume_id,
        max_chars=500
    )

    # Add to ChromaDB
    add_chunks_to_vectorstore(chunks)

    # Save to local profile database
    profiles = _load_profiles()
    profile = {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "resume_id": resume_id,
        "filename": filename,
        "upload_date": datetime.now().isoformat(),
        "contact_info": parsed["contact_info"],
        "skills": parsed["skills"],
        "section_dict": parsed["section_dict"],
        "full_text": parsed["full_text"],
        "chunk_count": len(chunks)
    }
    profiles[candidate_id] = profile
    _save_profiles(profiles)

    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "resume_id": resume_id,
        "filename": filename,
        "skills": parsed["skills"],
        "chunk_count": len(chunks),
        "status": "success"
    }


def get_all_candidates() -> List[Dict[str, Any]]:
    """Return list of all uploaded candidate profiles."""
    profiles = _load_profiles()
    results = []
    for cid, p in profiles.items():
        results.append({
            "candidate_id": cid,
            "candidate_name": p["candidate_name"],
            "resume_id": p["resume_id"],
            "filename": p["filename"],
            "upload_date": p.get("upload_date", ""),
            "contact_info": p.get("contact_info", {}),
            "skills": p.get("skills", []),
            "chunk_count": p.get("chunk_count", 0)
        })
    return results


def get_candidate_by_id(candidate_id: str) -> Optional[Dict[str, Any]]:
    """Get full profile details for a candidate."""
    profiles = _load_profiles()
    return profiles.get(candidate_id)


def delete_candidate(candidate_id: str) -> bool:
    """Delete candidate profile and ChromaDB vectors."""
    profiles = _load_profiles()
    if candidate_id not in profiles:
        return False

    prof = profiles.pop(candidate_id)
    _save_profiles(profiles)

    # Delete vectors from ChromaDB
    delete_resume_vectors(prof["resume_id"])
    return True


def get_stats() -> Dict[str, Any]:
    """Return system dashboard statistics."""
    profiles = _load_profiles()
    all_skills = set()
    for p in profiles.values():
        all_skills.update(p.get("skills", []))

    return {
        "total_resumes": len(profiles),
        "total_candidates": len(profiles),
        "total_unique_skills": len(all_skills),
        "total_vector_chunks": get_total_chunks_count()
    }
