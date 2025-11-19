#!/usr/bin/env python3
"""Integration smoke tests for the FastAPI HTTP bridge."""

from __future__ import annotations

import json
import socket
import threading
import time

import httpx
import pytest
import uvicorn

from src import rest_server


@pytest.fixture(scope="module")
def live_server():
    """Run the FastAPI app in a background uvicorn server on a free port."""

    monkeypatch = pytest.MonkeyPatch()

    async def fake_init():
        return None

    async def fake_search(query: str, num_results: int, engine: str) -> str:
        return json.dumps([
            {
                "title": "Example Live",
                "link": f"https://example.com/{engine}",
                "snippet": "Hello",
                "engine": engine,
            }
        ])

    async def fake_read_url(url: str, fmt: str) -> str:
        return f"live-content:{url}:{fmt}"

    async def fake_system_status(*, check_type: str = "all") -> str:
        return json.dumps({"health": {"status": "healthy"}, "readiness": {}, "metrics": {}})

    monkeypatch.setattr(rest_server.index, "initialize_search_manager", fake_init)
    monkeypatch.setattr(rest_server.index, "search", fake_search)
    monkeypatch.setattr(rest_server.index, "read_url", fake_read_url)
    monkeypatch.setattr(rest_server.index, "system_status", fake_system_status)

    port = _get_free_port()
    config = uvicorn.Config(rest_server.app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 5
    while not server.started:
        if not thread.is_alive():
            raise RuntimeError("uvicorn thread exited before startup")
        if time.time() > deadline:
            server.should_exit = True
            thread.join(timeout=1)
            raise TimeoutError("uvicorn server did not start in time")
        time.sleep(0.05)

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.should_exit = True
    thread.join(timeout=5)
    monkeypatch.undo()


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_live_search_endpoint(live_server):
    payload = {"query": "ai", "num_results": 3, "engine": "duckduckgo"}
    with _http_client(live_server) as client:
        resp = client.post("/search", json=payload)
        body = resp.json()
    assert body["count"] == 1
    assert body["results"][0]["engine"] == "duckduckgo"


def test_live_read_url_endpoint(live_server):
    payload = {"url": "https://integration.test", "format": "markdown"}
    with _http_client(live_server) as client:
        resp = client.post("/read_url", json=payload)
        body = resp.json()
    assert body["content"].startswith("live-content:https://integration.test")


def test_live_health_endpoint(live_server):
    with _http_client(live_server) as client:
        resp = client.get("/health")
        data = resp.json()
    assert data["health"]["status"] == "healthy"


def _http_client(base_url: str) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=5.0, trust_env=False)
