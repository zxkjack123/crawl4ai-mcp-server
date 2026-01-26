from pathlib import Path

import pytest


@pytest.mark.unit
def test_persistent_cache_selected_and_persists(tmp_path, monkeypatch):
    """SearchManager should use PersistentCache when enabled via env.

    We also verify values persist across manager restarts by re-opening
    the same SQLite DB.
    """
    db_path = tmp_path / "search_cache.db"

    monkeypatch.setenv("CRAWL4AI_ENABLE_PERSISTENT_CACHE", "true")
    monkeypatch.setenv("CRAWL4AI_PERSISTENT_CACHE_DB_PATH", str(db_path))
    monkeypatch.setenv("CRAWL4AI_PERSISTENT_CACHE_MAX_SIZE", "100")

    # Import here so env vars are in place before SearchManager init.
    from src.search import SearchManager
    from src.persistent_cache import PersistentCache

    sm1 = SearchManager(enable_cache=True, enable_rate_limit=False, enable_monitoring=False)
    assert isinstance(sm1.cache, PersistentCache)

    # Seed cache and verify immediate hit
    sm1.cache.set("q", "duckduckgo", 3, [{"title": "t", "link": "u", "snippet": "s"}])
    assert sm1.cache.get("q", "duckduckgo", 3) is not None

    # New manager (simulates restart) should still see the cached entry.
    sm2 = SearchManager(enable_cache=True, enable_rate_limit=False, enable_monitoring=False)
    assert isinstance(sm2.cache, PersistentCache)
    got = sm2.cache.get("q", "duckduckgo", 3)
    assert got and got[0]["title"] == "t"

    # Ensure db file exists
    assert Path(db_path).exists()
