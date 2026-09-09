"""Cross-encoder re-ranking via sentence-transformers."""

from __future__ import annotations

from server.core.config import get_settings
from server.core.logging import get_logger

logger = get_logger("retrieve.reranker")

_cross_encoder = None


def _get_cross_encoder():
    """Lazy-load the cross-encoder model (singleton).

    sentence-transformers pulls in PyTorch (~2GB), so we import it only on
    first use. This keeps the Docker serving image light and lets the rest
    of the retrieval path work even when the reranker isn't installed.
    """
    global _cross_encoder
    if _cross_encoder is None:
        settings = get_settings()
        logger.info("loading cross-encoder: %s", settings.cross_encoder_model)
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as e:
            raise RuntimeError(
                "cross-encoder reranking requires 'sentence-transformers' "
                "(not installed in this environment)"
            ) from e
        _cross_encoder = CrossEncoder(settings.cross_encoder_model)
        logger.info("cross-encoder loaded")
    return _cross_encoder


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Re-rank candidates using a cross-encoder.

    Expects each candidate to have a 'text' field.
    Returns top_k results sorted by rerank_score descending.
    """
    if not candidates:
        return []

    encoder = _get_cross_encoder()

    # Build query-document pairs
    pairs = [(query, c["text"]) for c in candidates]
    scores = encoder.predict(pairs)

    # Attach scores and sort
    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]
