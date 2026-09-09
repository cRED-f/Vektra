"""In-memory token-bucket rate limiter."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class _TokenBucket:
    tokens: float
    last_refill: float
    capacity: float
    refill_rate: float  # tokens per second


class RateLimiter:
    """Per-client token-bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self._capacity = float(burst)
        self._refill_rate = requests_per_minute / 60.0  # per second
        self._buckets: dict[str, _TokenBucket] = {}

    def _get_bucket(self, key: str) -> _TokenBucket:
        now = time.monotonic()
        if key not in self._buckets:
            self._buckets[key] = _TokenBucket(
                tokens=self._capacity,
                last_refill=now,
                capacity=self._capacity,
                refill_rate=self._refill_rate,
            )

        bucket = self._buckets[key]
        elapsed = now - bucket.last_refill
        bucket.tokens = min(
            bucket.capacity,
            bucket.tokens + elapsed * bucket.refill_rate,
        )
        bucket.last_refill = now
        return bucket

    def allow(self, key: str = "default") -> bool:
        """Check if a request is allowed. Consumes one token if allowed."""
        bucket = self._get_bucket(key)
        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True
        return False

    def remaining(self, key: str = "default") -> float:
        bucket = self._get_bucket(key)
        return bucket.tokens


# ── Global instance ────────────────────────────────────────────────────

_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
