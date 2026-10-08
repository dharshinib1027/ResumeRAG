"""Search service orchestrating hybrid semantic search and RAG direct answer synthesis."""
from typing import Dict, List, Any
from backend.rag.retriever import retrieve_candidates
from backend.rag.generator import generate_search_answer
from backend.services.resume_service import get_candidate_by_id


def search_candidates_with_rag(query: str) -> Dict[str, Any]:
    """
    Perform hybrid search and return candidate match cards along with a synthesized AI Direct Answer.
    """
    if not query.strip():
        return {"query": query, "count": 0, "ai_answer": "", "results": []}

    results = retrieve_candidates(query, top_k=20)
    enriched_results = []

    for res in results:
        cid = res["candidate_id"]
        profile = get_candidate_by_id(cid)

        if profile:
            skills = profile.get("skills", [])
            sec_dict = profile.get("section_dict", {})

            # Extract brief summary or experience snippet
            exp_text = sec_dict.get("experience") or sec_dict.get("summary") or ""
            exp_snippet = exp_text.strip().split("\n")[0] if exp_text else "No experience details available"

            enriched_results.append({
                "candidate_id": cid,
                "candidate_name": profile["candidate_name"],
                "filename": profile["filename"],
                "match_score": res["match_score"],
                "skills": skills,
                "contact_info": profile.get("contact_info", {}),
                "experience_snippet": exp_snippet,
                "top_excerpts": res["top_excerpts"],
                "matching_sections": res["matching_sections"]
            })
        else:
            enriched_results.append(res)

    # Synthesize RAG direct answer for the specific query
    try:
        ai_answer = generate_search_answer(query, enriched_results)
    except Exception as err:
        ai_answer = f"AI direct answer unavailable: {err}"

    return {
        "query": query,
        "count": len(enriched_results),
        "ai_answer": ai_answer,
        "results": enriched_results
    }
