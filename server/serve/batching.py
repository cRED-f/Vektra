"""Dynamic batching engine for generation requests."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from server.core.logging import get_logger
from server.core.metrics import batch_size, queue_depth

logger = get_logger("serve.batching")


def _new_future() -> asyncio.Future:
    """Create a future bound to the running event loop."""
    return asyncio.get_running_loop().create_future()


@dataclass
class BatchRequest:
    """A single request waiting to be batched."""
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    future: asyncio.Future = field(default_factory=_new_future)
    enqueued_at: float = field(default_factory=time.monotonic)


class DynamicBatcher:
    """Collects in-flight requests into batches for throughput.

    Requests are grouped by (model, temperature, max_tokens) and flushed
    when either the batch size cap or the max wait time is hit.
    """

    def __init__(
        self,
        generate_fn,
        *,
        max_batch_size: int = 8,
        max_wait_ms: float = 50.0,
    ):
        self._generate_fn = generate_fn
        self._max_batch_size = max_batch_size
        self._max_wait_ms = max_wait_ms

        # Key: (model, temperature, max_tokens) -> list[BatchRequest]
        self._queues: dict[tuple, list[BatchRequest]] = {}
        self._flush_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def submit(self, request: BatchRequest) -> str:
        """Submit a request and wait for the batched result."""
        key = (request.model, request.temperature, request.max_tokens)

        async with self._lock:
            if key not in self._queues:
                self._queues[key] = []
            self._queues[key].append(request)

            depth = sum(len(q) for q in self._queues.values())
            queue_depth.set(depth)

            # Start flush timer if not running
            if self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._delayed_flush(key))

            # If batch is full, flush immediately
            if len(self._queues[key]) >= self._max_batch_size:
                await self._flush(key)

        return await request.future

    async def _delayed_flush(self, key: tuple):
        """Wait max_wait_ms then flush."""
        await asyncio.sleep(self._max_wait_ms / 1000.0)
        async with self._lock:
            await self._flush(key)

    async def _flush(self, key: tuple):
        """Flush a batch — generate for each request individually (Ollama doesn't support true batching)."""
        queue = self._queues.pop(key, [])
        if not queue:
            return

        model, temperature, max_tokens = key
        batch_size.observe(len(queue))
        queue_depth.set(sum(len(q) for q in self._queues.values()))

        logger.info("flushing batch of %d requests (model=%s)", len(queue), model)

        # Ollama doesn't natively batch, so we run sequentially.
        # A vLLM backend could batch these into a single forward pass.
        for req in queue:
            try:
                result = await self._generate_fn(
                    req.prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                req.future.set_result(result)
            except Exception as e:
                req.future.set_exception(e)
            finally:
                latency = time.monotonic() - req.enqueued_at
                logger.debug("request served in %.3fs", latency)
