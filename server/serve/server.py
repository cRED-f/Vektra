"""ModelServer — high-level API for generation and benchmarking."""

from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

from server.core.config import get_settings
from server.core.errors import ModelNotFoundError, ServingError
from server.core.logging import get_logger
from server.core.metrics import (
    generate_latency_seconds,
    generate_tokens_total,
    generate_ttft_seconds,
)
from server.core.schemas import BenchmarkRequest, BenchmarkResult, ChatRequest
from server.serve.batching import BatchRequest, DynamicBatcher
from server.serve.ollama_backend import OllamaBackend

logger = get_logger("serve.server")


class ModelServer:
    """High-level model serving interface."""

    def __init__(self):
        self._settings = get_settings()
        self._backend = OllamaBackend()
        self._batcher = DynamicBatcher(
            self._backend.generate,
            max_batch_size=self._settings.batch_max_size,
            max_wait_ms=self._settings.batch_max_wait_ms,
        )

    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate text. Uses dynamic batching for non-streaming requests."""
        model = model or self._settings.ollama_generation_model

        if stream:
            return await self._generate_stream(prompt, model=model,
                                              temperature=temperature,
                                              max_tokens=max_tokens)

        start = time.monotonic()

        # Use batching for non-streaming
        request = BatchRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        result = await self._batcher.submit(request)

        elapsed = time.monotonic() - start
        generate_latency_seconds.observe(elapsed)
        logger.info("generation completed in %.3fs", elapsed)
        return result

    async def _generate_stream(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        """Stream tokens one by one with TTFT tracking."""
        ttft_start = time.monotonic()
        first_token = True
        token_count = 0

        token_iter = await self._backend.generate(
            prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for token in token_iter:
            if first_token:
                ttft = time.monotonic() - ttft_start
                generate_ttft_seconds.observe(ttft)
                logger.info("TTFT: %.3fs", ttft)
                first_token = False

            token_count += 1
            yield token

        generate_tokens_total.labels(type="completion").inc(token_count)

    async def benchmark(
        self,
        config: BenchmarkRequest,
    ) -> BenchmarkResult:
        """Run a benchmark: TTFT, TPOT, tokens/sec, cost."""
        model = config.model or self._settings.ollama_generation_model
        prompt = config.prompt or "Explain what RAG is in one paragraph."

        logger.info("starting benchmark on model=%s (runs=%d)", model, config.num_runs)

        ttfts: list[float] = []
        tpots: list[float] = []
        token_counts: list[int] = []
        total_times: list[float] = []

        for i in range(config.num_runs):
            run_start = time.monotonic()
            ttft_start = time.monotonic()
            first_token = True
            last_token_time = time.monotonic()
            token_count = 0
            inter_token_times: list[float] = []

            token_iter = await self._backend.generate(
                prompt,
                model=model,
                temperature=0.0,
                max_tokens=config.max_tokens,
                stream=True,
            )

            async for token in token_iter:
                if first_token:
                    ttfts.append(time.monotonic() - ttft_start)
                    first_token = False
                    last_token_time = time.monotonic()
                else:
                    inter_token_times.append(time.monotonic() - last_token_time)
                    last_token_time = time.monotonic()

                token_count += 1

            total_times.append(time.monotonic() - run_start)
            token_counts.append(token_count)
            if inter_token_times:
                tpots.append(sum(inter_token_times) / len(inter_token_times))

            logger.info("benchmark run %d/%d: %d tokens in %.3fs",
                       i + 1, config.num_runs, token_count, total_times[-1])

        avg_ttft = sum(ttfts) / len(ttfts) if ttfts else 0.0
        avg_tpot = sum(tpots) / len(tpots) if tpots else 0.0
        avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0.0
        avg_total = sum(total_times) / len(total_times) if total_times else 1.0
        tokens_per_sec = avg_tokens / avg_total if avg_total > 0 else 0.0

        return BenchmarkResult(
            model=model,
            prompt=prompt,
            avg_ttft_ms=avg_ttft * 1000,
            avg_tpot_ms=avg_tpot * 1000,
            tokens_per_sec=round(tokens_per_sec, 2),
            total_tokens=int(avg_tokens),
            num_runs=config.num_runs,
            max_tokens=config.max_tokens,
        )

    async def health_check(self) -> bool:
        return await self._backend.health_check()

    async def list_models(self) -> list[dict]:
        return await self._backend.list_models()
