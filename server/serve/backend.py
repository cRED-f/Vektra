"""Thin backend abstraction — Ollama and vLLM share this interface."""

from __future__ import annotations

import abc
from typing import AsyncIterator


class GenerationBackend(abc.ABC):
    """Abstract base for LLM serving backends."""

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate text from a prompt.

        Returns a string if stream=False, or an async iterator of tokens if stream=True.
        """
        ...

    @abc.abstractmethod
    async def list_models(self) -> list[dict]:
        """List available models on this backend."""
        ...

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Return True if the backend is reachable."""
        ...
