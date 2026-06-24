"""Python version compatibility shims.

Centralises polyfills so that every module importing ``asyncio`` gets the
same ``asyncio.timeout`` guarantee regardless of interpreter version.
"""

from __future__ import annotations

import asyncio
import sys

if sys.version_info < (3, 11):  # pragma: no cover - exercised on 3.10 only
    from contextlib import asynccontextmanager as _acm

    @_acm
    async def _asyncio_timeout(delay: float):
        """Minimal ``asyncio.timeout`` polyfill for Python 3.10.

        ``asyncio.timeout`` was added in Python 3.11.  This shim reproduces
        the essential behaviour: after *delay* seconds the current task is
        cancelled, which surfaces as a plain :class:`TimeoutError` to the
        caller (matching the 3.11 semantics).
        """
        task = asyncio.current_task()
        loop = asyncio.get_event_loop()
        handle = loop.call_later(delay, task.cancel)
        try:
            yield
        except asyncio.CancelledError:
            raise TimeoutError
        finally:
            handle.cancel()

    asyncio.timeout = _asyncio_timeout  # type: ignore[attr-defined]
