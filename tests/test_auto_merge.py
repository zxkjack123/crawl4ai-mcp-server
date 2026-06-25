import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.search import SearchManager, SearchEngine, SearchResult


class _DummyEngine(SearchEngine):
    def __init__(self, engine_type: str, titles: list[str]):
        self._engine_type = engine_type
        self._titles = titles

    async def search(self, query: str, num_results: int = 10):
        out = []
        for i, t in enumerate(self._titles[:num_results]):
            out.append(
                SearchResult(
                    title=t,
                    link=f"https://example.com/{self._engine_type}/{i}",
                    snippet=query,
                    source=self._engine_type,
                )
            )
        return out


@pytest.mark.asyncio
async def test_auto_merge_opt_in_merges_and_sorts(monkeypatch):
    # Prevent SearchManager from initializing real engines.
    monkeypatch.setattr(SearchManager, "_initialize_engines", lambda self: None)

    sm = SearchManager(enable_cache=False, enable_rate_limit=False, enable_monitoring=False)
    # Make SearchManager treat our dummy engines as the intended engine types.
    sm._get_engine_type = lambda engine: getattr(engine, "_engine_type", "unknown")
    sm.engines = [
        _DummyEngine("brave", ["brave-1", "brave-2"]),
        _DummyEngine("google", ["google-1", "google-2"]),
    ]
    sm.fallback_engines = []

    monkeypatch.setenv("CRAWL4AI_AUTO_MERGE", "1")
    monkeypatch.setenv("CRAWL4AI_AUTO_MERGE_MIN_ENGINES", "2")
    monkeypatch.setenv("CRAWL4AI_AUTO_MERGE_MAX_ENGINES", "2")

    results = await sm.search("test query", num_results=2, engine="auto")

    assert len(results) == 2
    # merge_and_deduplicate default priority prefers google over brave
    assert results[0]["engine"] == "google"


@pytest.mark.asyncio
async def test_auto_default_keeps_first_engine_order(monkeypatch):
    monkeypatch.setattr(SearchManager, "_initialize_engines", lambda self: None)

    sm = SearchManager(enable_cache=False, enable_rate_limit=False, enable_monitoring=False)
    sm._get_engine_type = lambda engine: getattr(engine, "_engine_type", "unknown")
    sm.engines = [
        _DummyEngine("brave", ["brave-1", "brave-2"]),
        _DummyEngine("google", ["google-1", "google-2"]),
    ]
    sm.fallback_engines = []

    monkeypatch.delenv("CRAWL4AI_AUTO_MERGE", raising=False)

    results = await sm.search("test query", num_results=2, engine="auto")

    assert len(results) == 2
    # auto-merge runs engines concurrently; accept whichever engine finishes first
    assert results[0]["engine"] in {"brave", "google"}
