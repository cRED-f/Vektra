"""Reciprocal Rank Fusion (RRF) — merge dense + BM25 rankings."""

from __future__ import annotations


def rrf_fuse(
    dense_results: list[dict],
    bm25_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """Fuse two ranked lists using Reciprocal Rank Fusion.

    RRF score = sum(1 / (k + rank)) across all lists.
    k=60 is the standard constant from the original RRF paper.

    Input lists must have 'chunk_id' keys.
    Returns merged list sorted by rrf_score descending.
    """
    scores: dict[str, dict] = {}

    # Dense ranking
    for rank, item in enumerate(dense_results):
        cid = item["chunk_id"]
        if cid not in scores:
            scores[cid] = {**item, "rrf_score": 0.0}
        scores[cid]["rrf_score"] += 1.0 / (k + rank + 1)
        scores[cid]["dense_score"] = item.get("dense_score", 0.0)

    # BM25 ranking
    for rank, item in enumerate(bm25_results):
        cid = item["chunk_id"]
        if cid not in scores:
            scores[cid] = {**item, "rrf_score": 0.0}
        scores[cid]["rrf_score"] += 1.0 / (k + rank + 1)
        scores[cid]["bm25_score"] = item.get("bm25_score", 0.0)

    # Sort by RRF score descending
    fused = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)
    return fused
