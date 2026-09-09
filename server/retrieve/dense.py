"""Dense retrieval via pgvector cosine similarity."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import ChunkRow
from server.core.logging import get_logger

logger = get_logger("retrieve.dense")


async def dense_search(
    session: AsyncSession,
    query_embedding: list[float],
    top_k: int = 20,
) -> list[dict]:
    """Find nearest chunks by cosine distance in pgvector.

    Returns list of {chunk_id, document_id, text, dense_score}.
    """
    # pgvector cosine distance operator: embedding <=> query
    # Lower distance = more similar; score = 1 - distance
    stmt = (
        select(
            ChunkRow.id.label("chunk_id"),
            ChunkRow.document_id,
            ChunkRow.text,
            (ChunkRow.embedding.cosine_distance(query_embedding)).label("distance"),
        )
        .order_by("distance")
        .limit(top_k)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        {
            "chunk_id": row.chunk_id,
            "document_id": row.document_id,
            "text": row.text,
            "dense_score": 1.0 - row.distance,  # convert distance → similarity
        }
        for row in rows
    ]
