import pytest

from src.search import DuckDuckGoSearch, normalize_ddgs_region


class _DummyDDGS:
    def __init__(self):
        self.calls = []

    def text(self, query: str, **kwargs):
        self.calls.append((query, kwargs))
        # Return the minimal schema our adapter expects
        return [{"title": "t", "href": "https://example.com", "body": "b"}]


def test_normalize_ddgs_region_defaults_and_rejects_invalid():
    assert normalize_ddgs_region(None) == "us-en"
    assert normalize_ddgs_region("") == "us-en"
    assert normalize_ddgs_region("wt-wt") == "us-en"
    assert normalize_ddgs_region("WT-WT") == "us-en"

    # Invalid formats should fall back
    assert normalize_ddgs_region("us") == "us-en"
    assert normalize_ddgs_region("us-en-us") == "us-en"
    assert normalize_ddgs_region("us_en") == "us-en"

    # A sane region should pass through
    assert normalize_ddgs_region("cn-zh") == "cn-zh"


@pytest.mark.asyncio
async def test_ddgs_region_is_normalized_and_wikipedia_excluded_by_default(monkeypatch):
    # Force a deterministic backend list and ensure it doesn't include wikipedia
    monkeypatch.setattr(
        "src.search._ddgs_text_backends_without_wikipedia",
        lambda: "duckduckgo,brave",
    )

    search = DuckDuckGoSearch(region="wt-wt")
    dummy = _DummyDDGS()
    search.ddgs = dummy

    results = await search.search("q", 1)
    assert results and results[0].title == "t"

    _query, kwargs = dummy.calls[0]
    assert kwargs["region"] == "us-en"
    assert "backend" in kwargs
    assert "wikipedia" not in kwargs["backend"]


@pytest.mark.asyncio
async def test_ddgs_can_include_wikipedia_when_explicitly_enabled(monkeypatch):
    # Even if we could generate a no-wiki backend, include_wikipedia=True should
    # prefer ddgs defaults (backend omitted) unless user explicitly overrides.
    monkeypatch.setattr(
        "src.search._ddgs_text_backends_without_wikipedia",
        lambda: "duckduckgo,brave",
    )

    search = DuckDuckGoSearch(region="wt-wt", include_wikipedia=True)
    dummy = _DummyDDGS()
    search.ddgs = dummy

    await search.search("q", 1)
    _query, kwargs = dummy.calls[0]
    assert kwargs["region"] == "us-en"
    assert "backend" not in kwargs
