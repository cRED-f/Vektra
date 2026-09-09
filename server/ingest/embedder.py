"""Batch embedding of chunks via OllamaEmbeddingClient."""

from __future__ import annotations

from server.core.embeddings import OllamaEmbeddingClient
from server.core.logging import get_logger

logger = get_logger("ingest.embedder")


async def embed_chunks(
    chunks: list,  # list[Chunk] from chunker
    client: OllamaEmbeddingClient,
    batch_size: int = 32,
) -> list[dict]:
    """Embed all chunks in batches.

    Returns list of dicts: {text, index, embedding}.
    """
    results: list[dict] = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c.text for c in batch]

        try:
            embeddings = await client.embed(texts)
            for chunk, embedding in zip(batch, embeddings):
                results.append({
                    "text": chunk.text,
                    "index": chunk.index,
                    "embedding": embedding,
                })
            logger.info(
                "embedded batch %d-%d / %d",
                i, min(i + batch_size, len(chunks)), len(chunks)
            )
        except Exception as e:
            logger.error("embedding batch failed at chunk %d: %s", i, e)
            # Skip failed batch — don't insert without embeddings

    return results
