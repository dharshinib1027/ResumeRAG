"""Split section text into smaller chunks with metadata."""
from typing import Dict, List, Any


def chunk_sections(
    sections: List[Dict[str, Any]],
    candidate_id: str,
    candidate_name: str,
    resume_id: str,
    max_chars: int = 500
) -> List[Dict[str, Any]]:
    """
    Split resume sections into chunks with rich metadata.
    Returns list of dicts with:
      chunk_id, candidate_id, candidate_name, resume_id, section, page, text
    """
    chunks: List[Dict[str, Any]] = []
    chunk_counter = 0

    for s in sections:
        sec_name = s["section"]
        page_num = s["page"]
        text = s["text"]

        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        if not blocks:
            blocks = [text.strip()]

        current_buf = []
        current_len = 0

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            for line in lines:
                if current_len + len(line) > max_chars and current_buf:
                    chunk_text = "\n".join(current_buf).strip()
                    if chunk_text:
                        chunk_counter += 1
                        chunks.append({
                            "chunk_id": f"{resume_id}_{chunk_counter}",
                            "candidate_id": candidate_id,
                            "candidate_name": candidate_name,
                            "resume_id": resume_id,
                            "section": sec_name,
                            "page": page_num,
                            "text": f"[{sec_name.upper()}] {chunk_text}",
                            "raw_text": chunk_text
                        })
                    current_buf = []
                    current_len = 0
                current_buf.append(line)
                current_len += len(line)

        if current_buf:
            chunk_text = "\n".join(current_buf).strip()
            if chunk_text:
                chunk_counter += 1
                chunks.append({
                    "chunk_id": f"{resume_id}_{chunk_counter}",
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "resume_id": resume_id,
                    "section": sec_name,
                    "page": page_num,
                    "text": f"[{sec_name.upper()}] {chunk_text}",
                    "raw_text": chunk_text
                })

    return chunks
