"""Request-scoped context helpers.

This module provides a lightweight request-id propagation mechanism using
`contextvars`, which works across async tasks and is compatible with FastAPI.

Design goals:
- stdlib-only
- safe default when no request id is set
- can be used by both HTTP Bridge (FastAPI) and MCP tool calls
"""

from __future__ import annotations

import contextlib
import contextvars
from uuid import uuid4


_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "crawl4ai_request_id", default="-"
)


def new_request_id() -> str:
    """Generate a new request id."""

    # 32 hex chars; stable, URL-safe, and easy to grep.
    return uuid4().hex


def get_request_id() -> str:
    """Return current request id, or '-' if not set."""

    try:
        rid = _request_id_var.get()
    except Exception:
        rid = "-"
    return rid or "-"


def set_request_id(request_id: str) -> contextvars.Token:
    """Set request id in current context and return the token for reset()."""

    rid = (request_id or "").strip()
    if not rid:
        rid = "-"
    return _request_id_var.set(rid)


def reset_request_id(token: contextvars.Token) -> None:
    """Reset request id to the previous value using the provided token."""

    try:
        _request_id_var.reset(token)
    except Exception:
        pass


@contextlib.contextmanager
def request_id_context(request_id: str | None = None):
    """Context manager to temporarily set request id."""

    token = set_request_id(request_id or "-")
    try:
        yield
    finally:
        reset_request_id(token)
