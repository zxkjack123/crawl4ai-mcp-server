#!/usr/bin/env python3
"""Tests for the FastAPI HTTP bridge (rest_server)."""

import json
import os
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import rest_server  # noqa: E402


@pytest.fixture(name="client")
def client_fixture(monkeypatch):
    """Provide a TestClient with underlying MCP functions mocked."""

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
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["engine"] == "brave"


def test_read_url_endpoint_returns_content(client):
    payload = {"url": "https://example.com", "format": "markdown"}
    resp = client.post("/read_url", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["content"].startswith("content:https://example.com")


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["health"]["status"] == "healthy"
