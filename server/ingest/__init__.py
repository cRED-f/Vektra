"""Ingestion pipeline — extract, chunk, embed, insert."""

from server.core.schemas import IngestionReport


async def run(
    paths: list[str] | str,
    *,
    chunk_strategy: str = "recursive",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> IngestionReport:
    """High-level entry point — ingests files and returns a report."""
    from server.ingest.extractor import extract_files
    from server.ingest.chunker import chunk_text
    from server.ingest.embedder import embed_chunks
    from server.ingest.inserter import insert_chunks, upsert_document
    from server.core.db import get_session_factory
    from server.core.embeddings import get_embedding_client
    from server.core.logging import get_logger
    import time

    logger = get_logger("ingest")
    start = time.monotonic()

    if isinstance(paths, str):
        paths = [paths]

    report = IngestionReport()

    # 1. Extract text from all files
    documents = await extract_files(paths)
    logger.info("extracted %d documents", len(documents))

    session_factory = get_session_factory()
    embedding_client = get_embedding_client()

    # 2. Process each document
    for doc_text, filename, content_hash in documents:
        try:
            async with session_factory() as session:
                # Check for duplicate (idempotency)
                from sqlalchemy import select
                from server.core.db import DocumentRow

                existing = await session.execute(
                    select(DocumentRow).where(DocumentRow.content_hash == content_hash)
                )
                if existing.scalar_one_or_none():
                    report.chunks_skipped += 1
                    logger.info("skipping %s (already ingested)", filename)
                    continue

                # Chunk
                chunks = chunk_text(
                    doc_text,
                    strategy=chunk_strategy,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                logger.info("chunked %s into %d chunks", filename, len(chunks))

                # Embed
                embedded = await embed_chunks(chunks, embedding_client, batch_size=32)

                # Insert
                doc_id, chunk_count = await upsert_document(
                    session, filename, content_hash, len(embedded)
                )
                await insert_chunks(session, doc_id, embedded)
                await session.commit()

                report.documents_processed += 1
                report.chunks_created += chunk_count
                logger.info("inserted %s (%d chunks)", filename, chunk_count)

        except Exception as e:
            report.errors.append(f"{filename}: {e}")
            logger.error("failed to ingest %s: %s", filename, e)

    report.duration_seconds = time.monotonic() - start
    logger.info(
        "ingestion complete: %d docs, %d chunks, %d skipped, %d errors in %.1fs",
        report.documents_processed,
        report.chunks_created,
        report.chunks_skipped,
        len(report.errors),
        report.duration_seconds,
    )
    return report
