"""ChromaDB Vector Store management."""
from pathlib import Path
from typing import Dict, List, Any
import chromadb
from chromadb.config import Settings

from backend.rag.embeddings import embed_texts, embed_query

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "resumes"

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def add_chunks_to_vectorstore(chunks: List[Dict[str, Any]]):
    """Insert list of chunks into ChromaDB."""
    if not chunks:
        return

    collection = get_collection()
    ids = [c["chunk_id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    metadatas = [
        {
            "candidate_id": str(c["candidate_id"]),
            "candidate_name": str(c["candidate_name"]),
            "resume_id": str(c["resume_id"]),
            "section": str(c["section"]),
            "page": int(c["page"]),
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )


def search_vectorstore(query: str, top_k: int = 15) -> List[Dict[str, Any]]:
    """Search ChromaDB by natural language query."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    q_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    items = []
    if results and results.get("documents"):
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, dists):
            # cosine distance: similarity = 1 - dist
            similarity = max(0.0, min(1.0, 1.0 - float(dist)))
            items.append({
                "text": doc,
                "metadata": meta,
                "similarity": similarity,
                "distance": dist
            })
    return items


def delete_resume_vectors(resume_id: str):
    """Delete chunks for a specific resume from ChromaDB."""
    collection = get_collection()
    try:
        collection.delete(where={"resume_id": resume_id})
    except Exception:
        pass


def get_total_chunks_count() -> int:
    """Return total number of chunks stored in ChromaDB."""
    try:
        return get_collection().count()
    except Exception:
        return 0
