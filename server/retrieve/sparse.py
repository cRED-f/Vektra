"""Sparse retrieval via BM25 (rank_bm25)."""

from __future__ import annotations

import re
from typing import Any

from rank_bm25 import BM25Okapi
from server.core.logging import get_logger

logger = get_logger("retrieve.sparse")


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercasing tokenizer."""
    return re.findall(r"\w+", text.lower())


class BM25Index:
    """In-memory BM25 index built lazily from the chunk corpus."""

    def __init__(self):
        self._index: BM25Okapi | None = None
        self._chunk_ids: list[str] = []
        self._documents: list[dict[str, Any]] = []

    def build(self, documents: list[dict[str, Any]]):
        """Build index from documents.

        Each doc must have at least 'chunk_id' and 'text'.
        """
        self._documents = documents
        self._chunk_ids = [d["chunk_id"] for d in documents]
        tokenized = [_tokenize(d["text"]) for d in documents]
        self._index = BM25Okapi(tokenized)
        logger.info("BM25 index built with %d documents", len(documents))

    def search(self, query: str, top_k: int = 20) -> list[dict]:
        """Search the index. Returns list of {chunk_id, bm25_score}."""
        if self._index is None or not self._documents:
            return []

        tokenized_query = _tokenize(query)
        scores = self._index.get_scores(tokenized_query)

        # Get top-k indices sorted by score descending
        ranked = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]

        return [
            {
                "chunk_id": self._chunk_ids[idx],
                "bm25_score": float(score),
            }
            for idx, score in ranked
            if score > 0
        ]

    @property
    def is_built(self) -> bool:
        return self._index is not None


# ── Global singleton ──────────────────────────────────────────────────

_bm25_index: BM25Index | None = None


def get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index()
    return _bm25_index
