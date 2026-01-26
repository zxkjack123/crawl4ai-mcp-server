import asyncio
import time

import pytest

from src.search import SearchEngine, SearchManager, SearchResult


class _FastEngine(SearchEngine):
    def __init__(self, engine_type: str):
        self._engine_type = engine_type

    async def search(self, query: str, num_results: int = 10):
        return [
            SearchResult(
                title="fast",
                link="https://example.com/fast",
                snippet=query,
                source=self._engine_type,
            )
        ]


class _SlowEngine(SearchEngine):
    def __init__(self, engine_type: str, cancelled: asyncio.Event, delay_s: float = 0.5):
        self._engine_type = engine_type
        self._cancelled = cancelled
        self._delay_s = delay_s

    async def search(self, query: str, num_results: int = 10):
        try:
            await asyncio.sleep(self._delay_s)
        except asyncio.CancelledError:
            self._cancelled.set()
            raise
        return [
            SearchResult(
                title="slow",
                link="https://example.com/slow",
                snippet=query,
                source=self._engine_type,
            )
        ]


@pytest.mark.asyncio
async def test_all_early_return_cancels_slow_engine(monkeypatch):
    monkeypatch.setattr(SearchManager, "_initialize_engines", lambda self: None)

    sm = SearchManager(enable_cache=False, enable_rate_limit=False, enable_monitoring=False)
    sm._get_engine_type = lambda engine: getattr(engine, "_engine_type", "unknown")

    cancelled = asyncio.Event()
    sm.engines = [
        _FastEngine("google"),
        _SlowEngine("duckduckgo", cancelled, delay_s=0.5),
    ]
    sm.fallback_engines = []

    monkeypatch.setenv("CRAWL4AI_ALL_EARLY_RETURN", "1")
    monkeypatch.setenv("CRAWL4AI_ALL_EARLY_RETURN_MIN_ENGINES", "1")
    monkeypatch.setenv("CRAWL4AI_ALL_EARLY_RETURN_GRACE_S", "0")

    t0 = time.monotonic()
    results = await sm.search("q", num_results=1, engine="all")
    dt = time.monotonic() - t0

    assert dt < 0.3
    assert len(results) == 1

    # Give the loop a tick to deliver cancellation.
    await asyncio.sleep(0)
    assert cancelled.is_set()


@pytest.mark.asyncio
async def test_auto_merge_concurrent_early_return(monkeypatch):
    monkeypatch.setattr(SearchManager, "_initialize_engines", lambda self: None)

    sm = SearchManager(enable_cache=False, enable_rate_limit=False, enable_monitoring=False)
    sm._get_engine_type = lambda engine: getattr(engine, "_engine_type", "unknown")

    cancelled = asyncio.Event()
    sm.engines = [
        _FastEngine("google"),
        _SlowEngine("brave", cancelled, delay_s=0.5),
    ]
    sm.fallback_engines = []

    monkeypatch.setenv("CRAWL4AI_AUTO_MERGE", "1")
    monkeypatch.setenv("CRAWL4AI_AUTO_MERGE_MIN_ENGINES", "1")
    monkeypatch.setenv("CRAWL4AI_AUTO_MERGE_MAX_ENGINES", "2")
    monkeypatch.setenv("CRAWL4AI_AUTO_MERGE_CONCURRENT", "1")
    monkeypatch.setenv("CRAWL4AI_AUTO_MERGE_EARLY_RETURN", "1")

    t0 = time.monotonic()
    results = await sm.search("q", num_results=1, engine="auto")
    dt = time.monotonic() - t0

    assert dt < 0.3
    assert len(results) == 1

    await asyncio.sleep(0)
    assert cancelled.is_set()
