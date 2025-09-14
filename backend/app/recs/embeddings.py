# backend/app/recs/embeddings.py
from __future__ import annotations
import numpy as np
from functools import lru_cache
from sentence_transformers import SentenceTransformer

DIM = 384

@lru_cache(maxsize=1)
def _model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n == 0 else (v / n)

def embed_text(text: str) -> np.ndarray:
    t = (text or "").strip()
    if not t:
        return np.zeros(DIM, dtype=np.float32)
    v = _model().encode([t])[0].astype(np.float32)
    return _normalize(v)
