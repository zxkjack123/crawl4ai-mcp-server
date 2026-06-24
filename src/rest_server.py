"""Simple FastAPI bridge exposing crawl4ai MCP tools as HTTP endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from uuid import uuid4
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

import importlib

# Python 3.10 compatibility: asyncio.timeout was added in 3.11
try:  # pragma: no cover
    from src.compat import *  # noqa: F401,F403  – installs asyncio.timeout on <3.11
except Exception:  # pragma: no cover
    from compat import *  # noqa: F401,F403

try:  # pragma: no cover
    from src.request_context import reset_request_id, set_request_id
except Exception:  # pragma: no cover
    from request_context import reset_request_id, set_request_id

try:  # pragma: no cover - attempt absolute import when package context is available
    index = importlib.import_module("src.index")
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    index = importlib.import_module("index")

app = FastAPI(title="Crawl4AI HTTP Bridge", version="0.6.1")

logger = logging.getLogger(__name__)


def _get_or_create_request_id(request: Request) -> str:
    hdr = request.headers.get("x-request-id")
    if hdr and str(hdr).strip():
        return str(hdr).strip()
    return uuid4().hex


def _request_id_from_scope(scope: dict) -> str:
    # Used by ASGI middleware paths where we don't have Request.
    try:
        headers = dict(scope.get("headers") or [])
        raw = headers.get(b"x-request-id")
        if raw:
            val = raw.decode("utf-8", errors="ignore").strip()
            if val:
                return val
    except Exception:
        pass
    return uuid4().hex


def _parse_bool_env(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _parse_int_env(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _parse_float_env(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip(), parts[1].strip()
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _get_auth_tokens_from_env() -> Optional[Tuple[str, ...]]:
    # Supports single token or a comma-separated list for rotation.
    raw = (
        os.environ.get("CRAWL4AI_HTTP_AUTH_TOKEN")
        or os.environ.get("HTTP_AUTH_TOKEN")
        or ""
    ).strip()
    raw_list = (os.environ.get("CRAWL4AI_HTTP_AUTH_TOKENS") or "").strip()
    tokens = []
    if raw:
        tokens.append(raw)
    if raw_list:
        for t in raw_list.split(","):
            t = t.strip()
            if t:
                tokens.append(t)
    # De-dupe while preserving order
    seen = set()
    out = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return tuple(out) if out else None


def _auth_is_required_for_path(path: str) -> bool:
    # Keep /health open by default (for docker health checks), but allow opt-in.
    protect_health = _parse_bool_env(
        os.environ.get("CRAWL4AI_HTTP_PROTECT_HEALTH")
    )
    if path == "/health":
        return bool(protect_health)
    # Protect core compute endpoints.
    return path in {"/search", "/read_url"}


def _get_max_body_bytes() -> int:
    # Default: 1 MiB, enough for typical JSON payloads.
    raw = os.environ.get("CRAWL4AI_HTTP_MAX_BODY_BYTES") or os.environ.get(
        "HTTP_MAX_BODY_BYTES"
    )
    v = _parse_int_env(raw)
    if v is None:
        return 1 * 1024 * 1024
    return max(0, v)


def _get_request_timeout_s() -> Optional[float]:
    raw = os.environ.get("CRAWL4AI_HTTP_REQUEST_TIMEOUT_S") or os.environ.get(
        "HTTP_REQUEST_TIMEOUT_S"
    )
    v = _parse_float_env(raw)
    if v is None:
        return 60.0
    if v <= 0:
        return None
    return v


def _get_rate_limit_config() -> Tuple[Optional[float], Optional[int]]:
    # Token bucket: rps + burst. If rps is unset/<=0 => disabled.
    raw_rps = os.environ.get("CRAWL4AI_HTTP_RATE_LIMIT_RPS") or os.environ.get(
        "HTTP_RATE_LIMIT_RPS"
    )
    raw_burst = os.environ.get("CRAWL4AI_HTTP_RATE_LIMIT_BURST") or os.environ.get(
        "HTTP_RATE_LIMIT_BURST"
    )
    rps = _parse_float_env(raw_rps)
    if rps is None or rps <= 0:
        return None, None
    burst = _parse_int_env(raw_burst)
    if burst is None:
        burst = 5
    burst = max(1, burst)
    return rps, burst


def _get_rate_limit_key(request: Request) -> str:
    # Prefer auth token identity to avoid punishing shared NAT IPs.
    token = _extract_bearer_token(request.headers.get("authorization"))
    if token:
        return f"token:{token}"
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


@dataclass
class _Bucket:
    tokens: float
    last_refill: float
    last_seen: float


class _InMemoryRateLimiter:
    """Simple in-memory token bucket rate limiter.

    This protects the HTTP bridge itself (distinct from upstream engine rate limits).
    """

    def __init__(self) -> None:
        self._buckets: Dict[str, _Bucket] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> Tuple[bool, Optional[float]]:
        rps, burst = _get_rate_limit_config()
        if rps is None or burst is None:
            return True, None

        now = time.monotonic()
        async with self._lock:
            b = self._buckets.get(key)
            if b is None:
                b = _Bucket(tokens=float(burst), last_refill=now, last_seen=now)
                self._buckets[key] = b

            # refill
            elapsed = max(0.0, now - b.last_refill)
            b.tokens = min(float(burst), b.tokens + elapsed * float(rps))
            b.last_refill = now
            b.last_seen = now

            if b.tokens >= 1.0:
                b.tokens -= 1.0
                return True, None

            retry_after = (1.0 - b.tokens) / float(rps) if rps > 0 else 1.0
            # defensive clamp
            retry_after = max(0.05, min(60.0, retry_after))
            return False, retry_after

    async def prune(self, *, max_idle_s: float = 600.0) -> None:
        now = time.monotonic()
        async with self._lock:
            to_delete = [k for k, v in self._buckets.items() if now - v.last_seen > max_idle_s]
            for k in to_delete:
                self._buckets.pop(k, None)

    async def reset(self) -> None:
        async with self._lock:
            self._buckets.clear()


_HTTP_RATE_LIMITER = _InMemoryRateLimiter()


class _BodyTooLargeError(Exception):
    pass


def _content_length_from_scope(scope: dict) -> Optional[int]:
    try:
        headers = dict(scope.get("headers") or [])
        raw = headers.get(b"content-length")
        if not raw:
            return None
        return int(raw.decode("ascii", errors="ignore").strip())
    except Exception:
        return None


class BodySizeLimitMiddleware:
    """ASGI middleware enforcing a maximum request body size."""

    def __init__(self, app, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max(0, int(max_body_bytes))

    async def __call__(self, scope, receive, send):
        max_body_bytes = _get_max_body_bytes()
        if scope.get("type") != "http" or max_body_bytes <= 0:
            return await self.app(scope, receive, send)

        method = (scope.get("method") or "").upper()
        if method not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)

        cl = _content_length_from_scope(scope)
        if cl is not None and cl > max_body_bytes:
            rid = _request_id_from_scope(scope)
            return await PlainTextResponse(
                "Request body too large",
                status_code=413,
                headers={"X-Request-Id": rid},
            )(scope, receive, send)

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                body = message.get("body") or b""
                received += len(body)
                if received > max_body_bytes:
                    raise _BodyTooLargeError()
            return message

        try:
            return await self.app(scope, limited_receive, send)
        except _BodyTooLargeError:
            rid = _request_id_from_scope(scope)
            return await PlainTextResponse(
                "Request body too large",
                status_code=413,
                headers={"X-Request-Id": rid},
            )(scope, receive, send)


# Install body limit middleware (reads env at import time; default is safe).
app.add_middleware(BodySizeLimitMiddleware, max_body_bytes=_get_max_body_bytes())


@app.middleware("http")
async def _security_and_timeout_middleware(request: Request, call_next):
    # Request id: accept client-provided X-Request-Id or generate one.
    rid = _get_or_create_request_id(request)
    token = set_request_id(rid)

    try:
        # Auth (optional): enabled when a token is configured.
        tokens = _get_auth_tokens_from_env()
        if tokens and _auth_is_required_for_path(request.url.path):
            auth_token = _extract_bearer_token(request.headers.get("authorization"))
            if not auth_token or auth_token not in tokens:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized"},
                    headers={
                        "WWW-Authenticate": "Bearer",
                        "X-Request-Id": rid,
                    },
                )

        # HTTP rate limiting (optional)
        allowed, retry_after = await _HTTP_RATE_LIMITER.check(
            _get_rate_limit_key(request)
        )
        if not allowed:
            headers = {"X-Request-Id": rid}
            if retry_after is not None:
                headers["Retry-After"] = str(int(max(1.0, retry_after)))
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
                headers=headers,
            )

        # Best-effort pruning (keeps memory bounded under many unique clients)
        try:
            await _HTTP_RATE_LIMITER.prune()
        except Exception:
            pass

        timeout_s = _get_request_timeout_s()
        if timeout_s is None:
            resp = await call_next(request)
            resp.headers["X-Request-Id"] = rid
            return resp

        try:
            async with asyncio.timeout(timeout_s):
                resp = await call_next(request)
                resp.headers["X-Request-Id"] = rid
                return resp
        except TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"},
                headers={"X-Request-Id": rid},
            )
    finally:
        reset_request_id(token)


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    num_results: int = Field(10, ge=1, le=50)
    engine: str = Field(
        "auto",
        description="Engine to use (auto, brave, google, duckduckgo, searxng, all)",
    )


class ReadRequest(BaseModel):
    url: str = Field(..., description="URL to crawl")
    format: str = Field("markdown_with_citations", description="Desired output format")


@app.on_event("startup")
async def _startup() -> None:
    # Warm-up search manager to reduce first-request latency.
    await index.initialize_search_manager()

    # Loud warning when running without auth.
    if not _get_auth_tokens_from_env():
        logger.warning(
            "HTTP Bridge auth is NOT configured. "
            "Set CRAWL4AI_HTTP_AUTH_TOKEN (or CRAWL4AI_HTTP_AUTH_TOKENS) to enable Bearer auth."
        )


@app.on_event("shutdown")
async def _shutdown() -> None:
    # Best-effort cleanup of shared resources (crawler, shared http clients).
    if hasattr(index, "cleanup"):
        await index.cleanup()


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Return overall health/readiness information."""
    status_json = await index.system_status(check_type="all")
    return json.loads(status_json)


@app.post("/search")
async def search_endpoint(payload: SearchRequest) -> Dict[str, Any]:
    """Perform a search via the existing MCP search tool."""
    results_json = await index.search(
        payload.query, payload.num_results, payload.engine
    )
    data = json.loads(results_json)
    if isinstance(data, dict) and data.get("error"):
        raise HTTPException(status_code=400, detail=data["error"])
    return {"results": data, "count": len(data)}


@app.post("/read_url")
async def read_url_endpoint(payload: ReadRequest) -> Dict[str, Any]:
    """Crawl a URL and return markdown or other requested format."""
    content = await index.read_url(payload.url, payload.format)
    try:
        maybe_error = json.loads(content)
        if isinstance(maybe_error, dict) and "error" in maybe_error:
            raise HTTPException(status_code=400, detail=maybe_error["error"])
    except json.JSONDecodeError:
        maybe_error = None
    return {
        "url": payload.url,
        "format": payload.format,
        "content": content,
        "error": maybe_error.get("error") if maybe_error else None,
    }


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("src.rest_server:app", host="0.0.0.0", port=8000, reload=False)
