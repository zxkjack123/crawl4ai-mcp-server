#!/usr/bin/env python3
"""Tests for the FastAPI HTTP bridge (rest_server)."""

import json
import os
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import rest_server  # noqa: E402


def _reset_http_rate_limiter() -> None:
    """Reset global in-memory rate limiter between tests."""
    import asyncio

    try:
        asyncio.run(rest_server._HTTP_RATE_LIMITER.reset())
    except RuntimeError:
        # If an event loop is already running (uncommon in these sync tests),
        # fall back to best-effort by clearing internal state directly.
        rest_server._HTTP_RATE_LIMITER._buckets.clear()  # type: ignore[attr-defined]


@pytest.fixture(name="client")
def client_fixture(monkeypatch):
    """Provide a TestClient with underlying MCP functions mocked."""

    # Ensure security features are off by default in this fixture.
    monkeypatch.delenv("CRAWL4AI_HTTP_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("CRAWL4AI_HTTP_AUTH_TOKENS", raising=False)
    monkeypatch.delenv("CRAWL4AI_HTTP_PROTECT_HEALTH", raising=False)
    monkeypatch.delenv("CRAWL4AI_HTTP_RATE_LIMIT_RPS", raising=False)
    monkeypatch.delenv("CRAWL4AI_HTTP_RATE_LIMIT_BURST", raising=False)
    monkeypatch.delenv("CRAWL4AI_HTTP_MAX_BODY_BYTES", raising=False)
    monkeypatch.delenv("CRAWL4AI_HTTP_REQUEST_TIMEOUT_S", raising=False)

    async def fake_init():
        return None

    async def fake_search(query: str, num_results: int, engine: str) -> str:
        return json.dumps([
            {"title": "Example", "link": "https://example.com", "snippet": "Hi", "engine": engine}
        ])

    async def fake_read_url(url: str, fmt: str) -> str:
        return f"content:{url}:{fmt}"

    async def fake_system_status(*, check_type: str = "all") -> str:
        return json.dumps({"health": {"status": "healthy"}, "readiness": {}, "metrics": {}})

    monkeypatch.setattr(rest_server.index, "initialize_search_manager", fake_init)
    monkeypatch.setattr(rest_server.index, "search", fake_search)
    monkeypatch.setattr(rest_server.index, "read_url", fake_read_url)
    monkeypatch.setattr(rest_server.index, "system_status", fake_system_status)

    with TestClient(rest_server.app) as client:
        yield client


def test_search_endpoint_returns_results(client):
    payload = {"query": "ai", "num_results": 5, "engine": "brave"}
    resp = client.post("/search", json=payload)
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-Id")
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["engine"] == "brave"


def test_request_id_is_echoed_when_provided(client):
    payload = {"query": "ai", "num_results": 1, "engine": "brave"}
    resp = client.post("/search", json=payload, headers={"X-Request-Id": "rid-test-123"})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-Id") == "rid-test-123"


def test_read_url_endpoint_returns_content(client):
    payload = {"url": "https://example.com", "format": "markdown"}
    resp = client.post("/read_url", json=payload)
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-Id")
    body = resp.json()
    assert body["content"].startswith("content:https://example.com")


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-Id")
    assert resp.json()["health"]["status"] == "healthy"


def test_auth_required_when_token_is_set(monkeypatch):
    _reset_http_rate_limiter()

    async def fake_init():
        return None

    async def fake_search(query: str, num_results: int, engine: str) -> str:
        return json.dumps([{"title": "X", "link": "https://x", "snippet": "", "engine": engine}])

    async def fake_read_url(url: str, fmt: str) -> str:
        return "ok"

    async def fake_system_status(*, check_type: str = "all") -> str:
        return json.dumps({"health": {"status": "healthy"}, "readiness": {}, "metrics": {}})

    monkeypatch.setenv("CRAWL4AI_HTTP_AUTH_TOKEN", "secret")
    monkeypatch.setattr(rest_server.index, "initialize_search_manager", fake_init)
    monkeypatch.setattr(rest_server.index, "search", fake_search)
    monkeypatch.setattr(rest_server.index, "read_url", fake_read_url)
    monkeypatch.setattr(rest_server.index, "system_status", fake_system_status)

    with TestClient(rest_server.app) as client:
        payload = {"query": "ai", "num_results": 5, "engine": "brave"}
        resp = client.post("/search", json=payload)
        assert resp.status_code == 401
        assert resp.headers.get("X-Request-Id")
        resp2 = client.post(
            "/search",
            json=payload,
            headers={"Authorization": "Bearer secret"},
        )
        assert resp2.status_code == 200
        assert resp2.headers.get("X-Request-Id")

        # /health remains open by default.
        h = client.get("/health")
        assert h.status_code == 200
        assert h.headers.get("X-Request-Id")


def test_health_can_be_protected(monkeypatch):
    _reset_http_rate_limiter()

    async def fake_init():
        return None

    async def fake_system_status(*, check_type: str = "all") -> str:
        return json.dumps({"health": {"status": "healthy"}, "readiness": {}, "metrics": {}})

    monkeypatch.setenv("CRAWL4AI_HTTP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("CRAWL4AI_HTTP_PROTECT_HEALTH", "1")
    monkeypatch.setattr(rest_server.index, "initialize_search_manager", fake_init)
    monkeypatch.setattr(rest_server.index, "system_status", fake_system_status)

    with TestClient(rest_server.app) as client:
        resp = client.get("/health")
        assert resp.status_code == 401
        assert resp.headers.get("X-Request-Id")
        ok = client.get("/health", headers={"Authorization": "Bearer secret"})
        assert ok.status_code == 200
        assert ok.headers.get("X-Request-Id")


def test_rate_limit_returns_429(monkeypatch):
    _reset_http_rate_limiter()

    async def fake_init():
        return None

    async def fake_search(query: str, num_results: int, engine: str) -> str:
        return json.dumps([{"title": "X", "link": "https://x", "snippet": "", "engine": engine}])

    monkeypatch.setenv("CRAWL4AI_HTTP_RATE_LIMIT_RPS", "1")
    monkeypatch.setenv("CRAWL4AI_HTTP_RATE_LIMIT_BURST", "1")
    monkeypatch.setattr(rest_server.index, "initialize_search_manager", fake_init)
    monkeypatch.setattr(rest_server.index, "search", fake_search)

    with TestClient(rest_server.app) as client:
        payload = {"query": "ai", "num_results": 1, "engine": "duckduckgo"}
        r1 = client.post("/search", json=payload)
        assert r1.status_code == 200
        assert r1.headers.get("X-Request-Id")
        r2 = client.post("/search", json=payload)
        assert r2.status_code == 429
        assert r2.headers.get("X-Request-Id")


def test_body_too_large_returns_413(monkeypatch):
    _reset_http_rate_limiter()

    async def fake_init():
        return None

    async def fake_search(query: str, num_results: int, engine: str) -> str:
        return json.dumps([{"title": "X", "link": "https://x", "snippet": "", "engine": engine}])

    monkeypatch.setenv("CRAWL4AI_HTTP_MAX_BODY_BYTES", "64")
    monkeypatch.setattr(rest_server.index, "initialize_search_manager", fake_init)
    monkeypatch.setattr(rest_server.index, "search", fake_search)

    with TestClient(rest_server.app) as client:
        payload = {
            "query": "x" * 200,
            "num_results": 1,
            "engine": "duckduckgo",
        }
        resp = client.post("/search", json=payload)
        assert resp.status_code == 413
        assert resp.headers.get("X-Request-Id")


def test_request_timeout_returns_504(monkeypatch):
    _reset_http_rate_limiter()

    async def fake_init():
        return None

    async def slow_search(query: str, num_results: int, engine: str) -> str:
        # Ensure we exceed the middleware timeout.
        await asyncio_sleep(0.05)
        return json.dumps([{"title": "X", "link": "https://x", "snippet": "", "engine": engine}])

    async def asyncio_sleep(dt: float) -> None:
        # Local helper to avoid importing asyncio at module top (keep tests minimal).
        import asyncio

        await asyncio.sleep(dt)

    monkeypatch.setenv("CRAWL4AI_HTTP_REQUEST_TIMEOUT_S", "0.01")
    monkeypatch.setattr(rest_server.index, "initialize_search_manager", fake_init)
    monkeypatch.setattr(rest_server.index, "search", slow_search)

    with TestClient(rest_server.app) as client:
        payload = {"query": "ai", "num_results": 1, "engine": "duckduckgo"}
        resp = client.post("/search", json=payload)
        assert resp.status_code == 504
        assert resp.headers.get("X-Request-Id")
