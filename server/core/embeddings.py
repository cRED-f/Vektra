"""EmbeddingClient protocol — generate embeddings via Ollama.

All embedding calls go through this interface so retrieval and ingestion
share the same path. Swap the implementation for a mock in tests.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

import httpx

from server.core.config import get_settings


class EmbeddingClient(Protocol):
    """Protocol that any embedding backend must satisfy."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...

    async def embed_single(self, text: str) -> list[float]:
        """Convenience — embed a single text."""
        ...


class OllamaEmbeddingClient:
    """Embedding client backed by Ollama's /api/embed endpoint."""

    def __init__(self, host: str | None = None, model: str | None = None):
        settings = get_settings()
        self._host = (host or settings.ollama_host).rstrip("/")
        self._model = model or settings.ollama_embedding_model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._host}/api/embed",
                json={"model": self._model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]

    async def embed_single(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]


# ── Singleton ─────────────────────────────────────────────────────────

_client: OllamaEmbeddingClient | None = None


def get_embedding_client() -> OllamaEmbeddingClient:
    global _client
    if _client is None:
        _client = OllamaEmbeddingClient()
    return _client
