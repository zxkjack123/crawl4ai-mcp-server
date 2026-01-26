import asyncio

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_request_coalescing_same_query(monkeypatch):
    """Concurrent identical searches should only hit the engine once."""
    monkeypatch.setenv("CRAWL4AI_ENABLE_REQUEST_COALESCING", "true")

    from src.search import SearchEngine, SearchManager, SearchResult

    class DummyEngine(SearchEngine):
        def __init__(self):
            self.calls = 0

        async def search(self, query: str, num_results: int = 10):
            self.calls += 1
            # Simulate a slow upstream call so coalescing has time to kick in.
            await asyncio.sleep(0.2)
            return [
                SearchResult(
                    title=f"{query}-{i}",
                    link=f"https://example.com/{i}",
                    snippet="s",
                    source="dummy",
                )
                for i in range(num_results)
            ]

    manager = SearchManager(
        enable_cache=False,
        enable_rate_limit=False,
        enable_monitoring=False,
    )
    dummy = DummyEngine()
    manager.engines = [dummy]
    manager.fallback_engines = []

    t1 = asyncio.create_task(manager.search("q", num_results=3, engine="auto"))
    t2 = asyncio.create_task(manager.search("q", num_results=3, engine="auto"))

    r1, r2 = await asyncio.gather(t1, t2)

    assert dummy.calls == 1
    assert len(r1) == 3 and len(r2) == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_request_coalescing_different_num_results(monkeypatch):
    """Different num_results should not coalesce."""
    monkeypatch.setenv("CRAWL4AI_ENABLE_REQUEST_COALESCING", "true")

    from src.search import SearchEngine, SearchManager, SearchResult

    class DummyEngine(SearchEngine):
        def __init__(self):
            self.calls = 0

        async def search(self, query: str, num_results: int = 10):
            self.calls += 1
            await asyncio.sleep(0.05)
            return [
                SearchResult(
                    title=f"{query}-{i}",
                    link=f"https://example.com/{i}",
                    snippet="s",
                    source="dummy",
                )
                for i in range(num_results)
            ]

    manager = SearchManager(
        enable_cache=False,
        enable_rate_limit=False,
        enable_monitoring=False,
    )
    dummy = DummyEngine()
    manager.engines = [dummy]
    manager.fallback_engines = []

    r1, r2 = await asyncio.gather(
        manager.search("q", num_results=3, engine="auto"),
        manager.search("q", num_results=4, engine="auto"),
    )

    assert dummy.calls == 2
    assert len(r1) == 3 and len(r2) == 4
