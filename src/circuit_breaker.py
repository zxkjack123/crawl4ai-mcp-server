"""Engine-level circuit breaker.

We use a classic consecutive-failure circuit breaker:
- CLOSED: calls are allowed; failures increment a counter
- OPEN: calls are rejected fast for `open_seconds`
- HALF_OPEN: after cooldown, allow one probe call; success closes, failure re-opens

This is intentionally in-memory and process-local.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class CircuitBreakerConfig:
    enabled: bool = True
    failure_threshold: int = 5
    open_seconds: float = 30.0


class CircuitState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        *,
        config: CircuitBreakerConfig,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self._cfg = config
        self._time = time_fn or time.monotonic
        self._lock = asyncio.Lock()

        self._state: str = CircuitState.CLOSED
        self._consecutive_failures: int = 0
        self._opened_at: float | None = None
        self._half_open_in_flight: bool = False

    @property
    def state(self) -> str:
        return self._state

    async def allow(self) -> tuple[bool, Optional[float]]:
        """Return (allowed, retry_after_seconds)."""

        if not self._cfg.enabled:
            return True, None

        now = self._time()
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True, None

            if self._state == CircuitState.OPEN:
                opened_at = self._opened_at or now
                remaining = (opened_at + float(self._cfg.open_seconds)) - now
                if remaining > 0:
                    return False, max(0.0, remaining)
                # cooldown over -> HALF_OPEN
                self._state = CircuitState.HALF_OPEN
                self._half_open_in_flight = False

            # HALF_OPEN
            if self._half_open_in_flight:
                return False, 0.0
            self._half_open_in_flight = True
            return True, None

    async def record_success(self) -> None:
        if not self._cfg.enabled:
            return
        async with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None
            self._half_open_in_flight = False
            self._state = CircuitState.CLOSED

    async def record_failure(self) -> None:
        if not self._cfg.enabled:
            return
        async with self._lock:
            # Any failure in HALF_OPEN re-opens.
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = self._time()
                self._half_open_in_flight = False
                self._consecutive_failures = int(self._cfg.failure_threshold)
                return

            # CLOSED -> increment counter
            self._consecutive_failures += 1
            if self._consecutive_failures >= int(self._cfg.failure_threshold):
                self._state = CircuitState.OPEN
                self._opened_at = self._time()
                self._half_open_in_flight = False

    async def snapshot(self) -> dict:
        async with self._lock:
            return {
                "enabled": self._cfg.enabled,
                "state": self._state,
                "consecutive_failures": self._consecutive_failures,
                "failure_threshold": self._cfg.failure_threshold,
                "open_seconds": self._cfg.open_seconds,
                "opened_at": self._opened_at,
            }
