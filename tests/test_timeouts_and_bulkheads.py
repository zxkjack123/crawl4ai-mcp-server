import asyncio

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_deadline_cleans_inflight(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_ENABLE_REQUEST_COALESCING", "true")
    monkeypatch.setenv("CRAWL4AI_SEARCH_DEADLINE_S", "0.05")

    from src.search import SearchEngine, SearchManager, SearchResult

    class SlowEngine(SearchEngine):
        async def search(self, query: str, num_results: int = 10):
            await asyncio.sleep(0.2)
            return [
                SearchResult(
                    title="t",
                    link="https://example.com/x",
                    snippet="s",
                    source="slow",
                )
            ]

    manager = SearchManager(
        enable_cache=False,
        enable_rate_limit=False,
        enable_monitoring=False,
    )
    manager.engines = [SlowEngine()]
    manager.fallback_engines = []

    res = await manager.search("q", num_results=3, engine="auto")
    assert res == []

    # Ensure inflight registry is cleaned.
    assert getattr(manager, "_inflight_searches", {}) == {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_global_bulkhead_limits_concurrency(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_MAX_CONCURRENT_SEARCHES", "1")
    monkeypatch.setenv("CRAWL4AI_MAX_CONCURRENT_PER_ENGINE", "10")
    monkeypatch.setenv("CRAWL4AI_ENABLE_REQUEST_COALESCING", "false")

    from src.search import SearchEngine, SearchManager, SearchResult

    lock = asyncio.Lock()
    current = 0
    max_seen = 0

    class GoogleDummyEngine(SearchEngine):
        async def search(self, query: str, num_results: int = 10):
            nonlocal current, max_seen
            async with lock:
                current += 1
                max_seen = max(max_seen, current)
            await asyncio.sleep(0.05)
            async with lock:
                current -= 1
            return [
                SearchResult(
                    title=query,
                    link=f"https://example.com/{query}",
                    snippet="s",
                    source="dummy",
                )
            ]

    manager = SearchManager(
        enable_cache=False,
        enable_rate_limit=False,
        enable_monitoring=False,
    )
    manager.engines = [GoogleDummyEngine()]
    manager.fallback_engines = []

    await asyncio.gather(
        manager.search("q1", num_results=1, engine="auto"),
        manager.search("q2", num_results=1, engine="auto"),
    )

    assert max_seen == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_per_engine_bulkhead_limits_concurrency(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_MAX_CONCURRENT_SEARCHES", "10")
    monkeypatch.setenv("CRAWL4AI_MAX_CONCURRENT_PER_ENGINE", "10")
    monkeypatch.setenv("CRAWL4AI_MAX_CONCURRENT_GOOGLE", "1")
    monkeypatch.setenv("CRAWL4AI_ENABLE_REQUEST_COALESCING", "false")

    from src.search import SearchEngine, SearchManager, SearchResult

    lock = asyncio.Lock()
    current = 0
    max_seen = 0

    class GoogleDummyEngine(SearchEngine):
        async def search(self, query: str, num_results: int = 10):
            nonlocal current, max_seen
            async with lock:
                current += 1
                max_seen = max(max_seen, current)
            await asyncio.sleep(0.05)
            async with lock:
                current -= 1
            return [
                SearchResult(
                    title=query,
                    link=f"https://example.com/{query}",
                    snippet="s",
                    source="dummy",
                )
            ]

    manager = SearchManager(
        enable_cache=False,
        enable_rate_limit=False,
        enable_monitoring=False,
    )
    manager.engines = [GoogleDummyEngine()]
    manager.fallback_engines = []

    await asyncio.gather(
        manager.search("q1", num_results=1, engine="auto"),
        manager.search("q2", num_results=1, engine="auto"),
    )

    assert max_seen == 1
