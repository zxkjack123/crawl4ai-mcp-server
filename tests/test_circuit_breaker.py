#!/usr/bin/env python3
"""Unit tests for per-engine circuit breaker."""

import asyncio

import pytest

from src.circuit_breaker import CircuitBreaker, CircuitBreakerConfig


@pytest.mark.asyncio
async def test_circuit_breaker_allows_initially():
    cb = CircuitBreaker(
        config=CircuitBreakerConfig(enabled=True, failure_threshold=2, open_seconds=10.0)
    )
    allowed, retry_after = await cb.allow()
    assert allowed is True
    assert retry_after is None


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold_failures():
    cb = CircuitBreaker(
        config=CircuitBreakerConfig(enabled=True, failure_threshold=2, open_seconds=10.0)
    )

    await cb.record_failure()
    allowed1, _ = await cb.allow()
    assert allowed1 is True

    await cb.record_failure()
    allowed2, retry_after2 = await cb.allow()
    assert allowed2 is False
    assert retry_after2 is not None
    assert retry_after2 > 0


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_allows_single_probe_then_closes_on_success():
    cb = CircuitBreaker(
        config=CircuitBreakerConfig(enabled=True, failure_threshold=1, open_seconds=0.02)
    )

    await cb.record_failure()
    allowed_open, _ = await cb.allow()
    assert allowed_open is False

    await asyncio.sleep(0.03)

    # First call after cooldown is the half-open probe
    allowed_probe, _ = await cb.allow()
    assert allowed_probe is True

    # Probe budget consumed: next allow should be blocked until success/failure recorded
    allowed_second, _ = await cb.allow()
    assert allowed_second is False

    await cb.record_success()

    allowed_closed, _ = await cb.allow()
    assert allowed_closed is True


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure_reopens():
    cb = CircuitBreaker(
        config=CircuitBreakerConfig(enabled=True, failure_threshold=1, open_seconds=0.02)
    )

    await cb.record_failure()
    await asyncio.sleep(0.03)

    allowed_probe, _ = await cb.allow()
    assert allowed_probe is True

    await cb.record_failure()

    allowed_after, _ = await cb.allow()
    assert allowed_after is False


@pytest.mark.asyncio
async def test_circuit_breaker_disabled_always_allows():
    cb = CircuitBreaker(
        config=CircuitBreakerConfig(enabled=False, failure_threshold=1, open_seconds=10.0)
    )

    await cb.record_failure()
    await cb.record_failure()

    allowed, retry_after = await cb.allow()
    assert allowed is True
    assert retry_after is None
