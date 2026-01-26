"""Logging filters used across the project."""

from __future__ import annotations

import logging

try:  # pragma: no cover
    from src.request_context import get_request_id
except Exception:  # pragma: no cover
    from request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """Inject request_id into LogRecord.

    This allows log formats like '%(request_id)s' without KeyError.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        try:
            rid = get_request_id()
        except Exception:
            rid = "-"
        # Always provide the attribute to keep formatters safe.
        setattr(record, "request_id", rid)
        return True
