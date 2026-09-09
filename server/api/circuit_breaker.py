"""Simple circuit breaker for backend calls."""

from __future__ import annotations

import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Per-backend circuit breaker."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time = 0.0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time > self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def allow(self) -> bool:
        """Check if a request should be allowed."""
        state = self.state
        return state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self):
        """Record a successful call."""
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self):
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN


# ── Global breakers per backend ────────────────────────────────────────

_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(backend: str = "default") -> CircuitBreaker:
    if backend not in _breakers:
        _breakers[backend] = CircuitBreaker()
    return _breakers[backend]
