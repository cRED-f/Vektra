"""Query rewriting and multi-hop decomposition via Ollama LLM."""

from __future__ import annotations

import httpx

from server.core.config import get_settings
from server.core.logging import get_logger

logger = get_logger("retrieve.rewriter")


async def _ollama_generate(prompt: str, model: str | None = None) -> str:
    """Call Ollama /api/generate for text completion."""
    settings = get_settings()
    model = model or settings.ollama_generation_model

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.ollama_host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["response"]


async def rewrite_query(query: str) -> str:
    """Rewrite a query for better retrieval.

    Expands abbreviations, fixes spelling, adds context.
    Falls back to original query on failure.
    """
    prompt = (
        "Rewrite the following user query to improve document retrieval. "
        "Keep it concise. Return ONLY the rewritten query, nothing else.\n\n"
        f"Query: {query}\n\nRewritten:"
    )

    try:
        rewritten = await _ollama_generate(prompt)
        rewritten = rewritten.strip().strip('"').strip("'")
        if rewritten:
            logger.info("rewritten query: %r -> %r", query, rewritten)
            return rewritten
    except Exception as e:
        logger.warning("query rewrite failed: %s", e)

    return query


async def decompose_query(query: str) -> list[str]:
    """Decompose a complex query into sub-queries for multi-hop retrieval.

    Returns a list of simpler queries. Falls back to [original_query].
    """
    prompt = (
        "Break the following complex question into 2-4 simpler sub-questions "
        "that together would answer it. Return ONLY the sub-questions, "
        "one per line, no numbering.\n\n"
        f"Question: {query}\n\nSub-questions:"
    )

    try:
        response = await _ollama_generate(prompt)
        sub_queries = [
            line.strip().lstrip("0123456789. )-")
            for line in response.strip().split("\n")
            if line.strip()
        ]
        if sub_queries:
            logger.info("decomposed into %d sub-queries", len(sub_queries))
            return sub_queries
    except Exception as e:
        logger.warning("query decomposition failed: %s", e)

    return [query]
