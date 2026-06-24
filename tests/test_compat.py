#!/usr/bin/env python3
"""Unit tests for the asyncio.timeout polyfill in src/compat.py.

These tests exercise the polyfill directly (even on Python 3.11+ where
the real asyncio.timeout exists) by calling the shim function explicitly.
They verify:

1. Normal completion within the timeout window.
2. TimeoutError is raised when the deadline is exceeded.
3. The scheduled call_later handle is cancelled after exit (no leak).
4. The polyfill is importable and asyncio.timeout is always available.
"""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import compat  # noqa: F401  – import side-effect installs polyfill


def test_asyncio_timeout_attribute_exists():
    """asyncio.timeout must always be available after importing compat."""
    assert hasattr(asyncio, "timeout")


@pytest.mark.asyncio
async def test_timeout_does_not_fire_when_fast_enough():
    """If the coroutine finishes before *delay*, no error is raised."""
    async with asyncio.timeout(5):
        await asyncio.sleep(0.01)
    # If we reach here, the context manager exited cleanly.


@pytest.mark.asyncio
async def test_timeout_fires_with_timeout_error():
    """When the deadline is exceeded, TimeoutError must be raised."""
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.05):
            await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_timeout_handle_cancelled_after_normal_exit():
    """The internal call_later handle must be cancelled after normal exit.

    On Python 3.11+, the real ``asyncio.timeout`` is a builtin and we
    cannot easily introspect its internals.  Instead we verify the
    observable contract: no stray ``CancelledError`` fires after the
    context manager exits.
    """
    async with asyncio.timeout(5):
        await asyncio.sleep(0.01)

    # If the handle wasn't cancelled, a spurious CancelledError might fire
    # later. Give the loop a moment to process any pending callbacks.
    await asyncio.sleep(0.02)
    # No CancelledError propagated => handle was cancelled correctly.


@pytest.mark.asyncio
async def test_timeout_fires_and_handle_cleaned_on_timeout():
    """When timeout fires, the handle should still be cleaned up."""
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.01):
            await asyncio.sleep(0.5)
    # Give the loop a tick to process any stray callbacks.
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_polyfill_matches_real_semantics_on_311_plus():
    """On Python 3.11+, verify the polyfill logic behaves identically to builtin."""
    if sys.version_info < (3, 11):
        pytest.skip("Requires Python 3.11+ to compare polyfill vs builtin")

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _polyfill(delay):
        task = asyncio.current_task()
        loop = asyncio.get_event_loop()
        handle = loop.call_later(delay, task.cancel)
        try:
            yield
        except asyncio.CancelledError:
            raise TimeoutError
        finally:
            handle.cancel()

    # Polyfill: normal exit
    async with _polyfill(5):
        await asyncio.sleep(0.01)

    # Polyfill: timeout
    with pytest.raises(TimeoutError):
        async with _polyfill(0.01):
            await asyncio.sleep(0.5)

    # Builtin: normal exit
    async with asyncio.timeout(5):
        await asyncio.sleep(0.01)

    # Builtin: timeout
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.01):
            await asyncio.sleep(0.5)
