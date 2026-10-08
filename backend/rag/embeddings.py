"""Embedding generation using sentence-transformers."""
import os
from typing import List

_model_instance = None
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def get_embedding_model():
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer

        _model_instance = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model_instance


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed list of texts into vector floats."""
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """Embed single query text."""
    return embed_texts([query])[0]
