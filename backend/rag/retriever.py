"""Retrieve and group search results by candidate using hybrid vector + keyword search."""
import re
from typing import Dict, List, Any
from backend.rag.vector_store import search_vectorstore


def _compute_keyword_boost(query: str, text: str) -> float:
    """Calculate keyword overlap boost to ensure exact matches jump to the top."""
    q_words = set(w.lower() for w in re.findall(r"\b[a-zA-Z0-9+#\.\-]{2,}\b", query))
    stop_words = {
        "the", "and", "for", "with", "has", "who", "need", "find",
        "candidates", "candidate", "have", "more", "than", "give",
        "knows", "know", "me", "show", "list", "get", "looking", "want",
        "developer", "developers", "engineer", "engineers", "with", "experience"
    }
    keywords = q_words - stop_words

    if not keywords:
        return 0.0

    text_lower = text.lower()
    matches = 0
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            matches += 1

    return (matches / len(keywords)) * 0.30  # Up to 30% hybrid boost for exact keyword matches


def _normalize_match_score(raw_sim: float, keyword_boost: float) -> float:
    """
    Scale raw vector similarity into human-friendly match relevance percentage.
    SentenceTransformers cosine similarity for multi-word queries vs text chunks
    typically ranges from 0.20 (low) to 0.50 (strong).
    """
    if raw_sim < 0.15:
        base = (raw_sim / 0.15) * 0.25
    elif raw_sim < 0.45:
        base = 0.25 + ((raw_sim - 0.15) / 0.30) * 0.55
    else:
        base = 0.80 + min(0.15, (raw_sim - 0.45) * 0.6)

    total = min(0.99, base + keyword_boost)
    return total


def retrieve_candidates(query: str, top_k: int = 20, min_match_score: int = 50) -> List[Dict[str, Any]]:
    """
    Perform hybrid (vector + keyword) semantic search and group matching chunks by candidate.
    Filters out irrelevant candidates below min_match_score threshold (default 50%).
    Returns list of candidate match cards sorted by overall relevance.
    """
    items = search_vectorstore(query, top_k=top_k)
    if not items:
        return []

    # Group by candidate_id
    grouped: Dict[str, Dict[str, Any]] = {}

    for item in items:
        meta = item["metadata"]
        cid = meta["candidate_id"]
        raw_sim = item["similarity"]
        boost = _compute_keyword_boost(query, item["text"])
        final_sim = _normalize_match_score(raw_sim, boost)

        if cid not in grouped:
            grouped[cid] = {
                "candidate_id": cid,
                "candidate_name": meta["candidate_name"],
                "resume_id": meta["resume_id"],
                "max_similarity": final_sim,
                "chunks": [],
                "matching_sections": set(),
            }

        grouped[cid]["chunks"].append({
            "text": item["text"],
            "section": meta["section"],
            "page": meta["page"],
            "similarity": final_sim
        })
        grouped[cid]["matching_sections"].add(meta["section"])
        if final_sim > grouped[cid]["max_similarity"]:
            grouped[cid]["max_similarity"] = final_sim

    # Sort candidates by top combined similarity score descending
    candidates_list = list(grouped.values())
    candidates_list.sort(key=lambda x: x["max_similarity"], reverse=True)

    formatted_results = []
    for cand in candidates_list:
        cand["chunks"].sort(key=lambda c: c["similarity"], reverse=True)
        top_excerpts = [c["text"] for c in cand["chunks"][:3]]
        match_score = round(cand["max_similarity"] * 100)

        # Filter out low-relevance non-matching candidates (below 50% match threshold)
        if match_score >= min_match_score:
            formatted_results.append({
                "candidate_id": cand["candidate_id"],
                "candidate_name": cand["candidate_name"],
                "resume_id": cand["resume_id"],
                "match_score": match_score,
                "matching_sections": list(cand["matching_sections"]),
                "top_excerpts": top_excerpts,
                "retrieved_chunk_count": len(cand["chunks"])
            })

    return formatted_results
