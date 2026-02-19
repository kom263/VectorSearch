import logging
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading sentence-transformer model: {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded successfully.")
    return _model


def encode_text(text: str) -> List[float]:
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def encode_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    model = get_model()
    embeddings = model.encode(texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=True)
    return [emb.tolist() for emb in embeddings]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
