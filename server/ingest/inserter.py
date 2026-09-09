"""Write documents + chunks to pgvector via SQLAlchemy."""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import ChunkRow, DocumentRow
from server.core.logging import get_logger

logger = get_logger("ingest.inserter")


def _deterministic_id(text: str) -> str:
    """Hash of text content for idempotent upserts."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


async def upsert_document(
    session: AsyncSession,
    filename: str,
    content_hash: str,
    chunk_count: int,
) -> tuple[str, int]:
    """Insert or update a document record. Returns (doc_id, chunk_count)."""
    doc_id = _deterministic_id(content_hash)

    existing = await session.execute(
        select(DocumentRow).where(DocumentRow.id == doc_id)
    )
    row = existing.scalar_one_or_none()

    if row:
        row.chunk_count = chunk_count
        logger.info("updated document %s", doc_id)
    else:
        row = DocumentRow(
            id=doc_id,
            filename=filename,
            content_hash=content_hash,
            chunk_count=chunk_count,
        )
        session.add(row)
        logger.info("created document %s", doc_id)

    return doc_id, chunk_count


async def insert_chunks(
    session: AsyncSession,
    document_id: str,
    embedded_chunks: list[dict],
) -> int:
    """Insert chunks with embeddings. Returns count inserted."""
    count = 0

    for chunk_data in embedded_chunks:
        chunk_id = _deterministic_id(chunk_data["text"])

        # Skip if chunk already exists (idempotent)
        existing = await session.execute(
            select(ChunkRow).where(ChunkRow.id == chunk_id)
        )
        if existing.scalar_one_or_none():
            continue

        row = ChunkRow(
            id=chunk_id,
            document_id=document_id,
            text=chunk_data["text"],
            embedding=chunk_data["embedding"],
            chunk_index=chunk_data["index"],
        )
        session.add(row)
        count += 1

    logger.info("inserted %d chunks for document %s", count, document_id)
    return count
