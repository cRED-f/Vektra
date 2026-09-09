"""High-level Retriever — orchestrates dense + BM25 + RRF + reranking."""

from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.config import get_settings
from server.core.db import ChunkRow, get_session_factory
from server.core.embeddings import get_embedding_client
from server.core.errors import EmptyCorpusError, RetrievalError
from server.core.logging import get_logger
from server.core.metrics import (
    rerank_latency_seconds,
    retrieve_candidates_total,
    retrieve_latency_seconds,
)
from server.core.schemas import RetrievalQuery, RetrievalResult
from server.retrieve.dense import dense_search
from server.retrieve.fusion import rrf_fuse
from server.retrieve.reranker import rerank
from server.retrieve.sparse import get_bm25_index
from server.retrieve.rewriter import decompose_query, rewrite_query

logger = get_logger("retrieve")


class Retriever:
    """Hybrid retrieval engine."""

    def __init__(self, session: AsyncSession | None = None):
        self._session = session
        self._own_session = session is None

    async def _get_session(self) -> AsyncSession:
        if self._session is None:
            factory = get_session_factory()
            self._session = factory()
            self._own_session = True
        return self._session

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_reranker: bool = True,
        use_rewrite: bool = False,
        use_multi_hop: bool = False,
    ) -> list[RetrievalResult]:
        """Full hybrid retrieval pipeline.

        dense + BM25 → RRF fusion → cross-encoder rerank → top_k results.
        """
        start = time.monotonic()

        try:
            session = await self._get_session()
            settings = get_settings()

            # Optional query rewriting
            search_query = query
            if use_rewrite:
                search_query = await rewrite_query(query)

            # Multi-hop decomposition
            queries = [search_query]
            if use_multi_hop:
                queries = await decompose_query(search_query)

            # Embed all queries
            client = get_embedding_client()
            all_results: list[dict] = []

            for q in queries:
                embedding = await client.embed_single(q)

                # Dense search
                dense = await dense_search(session, embedding, top_k=settings.retrieval_top_k)

                # Build/refresh BM25 index if needed
                bm25_idx = get_bm25_index()
                if not bm25_idx.is_built:
                    await self._build_bm25_index(session, bm25_idx)

                # BM25 search
                bm25 = bm25_idx.search(q, top_k=settings.retrieval_top_k)

                # RRF fusion
                fused = rrf_fuse(dense, bm25)
                retrieve_candidates_total.observe(len(fused))
                all_results.extend(fused)

            # Dedup across multi-hop sub-queries
            seen: set[str] = set()
            unique: list[dict] = []
            for r in all_results:
                if r["chunk_id"] not in seen:
                    seen.add(r["chunk_id"])
                    unique.append(r)

            # Rerank
            candidates = unique[:50]  # cap candidate set
            if use_reranker and candidates:
                rerank_start = time.monotonic()
                candidates = rerank(query, candidates, top_k=top_k)
                rerank_latency_seconds.observe(time.monotonic() - rerank_start)
            else:
                candidates = candidates[:top_k]

            # Convert to schema
            results = [
                RetrievalResult(
                    chunk_id=c["chunk_id"],
                    document_id=c.get("document_id", ""),
                    text=c["text"],
                    dense_score=c.get("dense_score", 0.0),
                    bm25_score=c.get("bm25_score", 0.0),
                    rrf_score=c.get("rrf_score", 0.0),
                    rerank_score=c.get("rerank_score", 0.0),
                    rank=i + 1,
                )
                for i, c in enumerate(candidates)
            ]

            elapsed = time.monotonic() - start
            retrieve_latency_seconds.observe(elapsed)
            logger.info(
                "retrieved %d results for query in %.3fs (candidates: %d)",
                len(results), elapsed, len(unique),
            )
            return results

        except (EmptyCorpusError, RetrievalError):
            raise
        except Exception as e:
            raise RetrievalError(f"retrieval failed: {e}") from e

    async def _build_bm25_index(self, session: AsyncSession, bm25_idx):
        """Load all chunks into the BM25 index."""
        result = await session.execute(
            select(ChunkRow.id, ChunkRow.document_id, ChunkRow.text)
        )
        rows = result.all()
        if not rows:
            raise EmptyCorpusError("no chunks found — run ingestion first")

        documents = [
            {"chunk_id": row.id, "document_id": row.document_id, "text": row.text}
            for row in rows
        ]
        bm25_idx.build(documents)

    async def close(self):
        if self._own_session and self._session:
            await self._session.close()
