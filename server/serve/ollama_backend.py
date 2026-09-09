"""Ollama serving backend — wraps Ollama's HTTP API."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from server.core.config import get_settings
from server.core.logging import get_logger
from server.serve.backend import GenerationBackend

logger = get_logger("serve.ollama")


class OllamaBackend(GenerationBackend):
    """Serve generation via Ollama's HTTP API."""

    def __init__(self):
        self._settings = get_settings()

    @property
    def _base_url(self) -> str:
        return self._settings.ollama_host

    async def generate(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if stream:
            return self._stream(payload)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/generate", json=payload
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def _stream(self, payload: dict) -> AsyncIterator[str]:
        """Yield tokens from a streaming Ollama response."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/generate",
                json={**payload, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    if "response" in chunk:
                        yield chunk["response"]
                    if chunk.get("done"):
                        break

    async def list_models(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base_url}/api/tags")
            resp.raise_for_status()
            return resp.json().get("models", [])

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
