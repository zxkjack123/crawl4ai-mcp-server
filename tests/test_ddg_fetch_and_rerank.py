import pytest

from src.search import DuckDuckGoSearch


class _DummyDDGS:
    def __init__(self, items):
        self.items = items
        self.calls = []

    def text(self, query: str, **kwargs):
        self.calls.append((query, kwargs))
        return list(self.items)


@pytest.mark.asyncio
async def test_ddg_fetch_pool_is_larger_than_requested_and_reranks_for_multi_term_queries(monkeypatch):
    # Build a result list where the first few items are generic "n8n" pages,
    # and the relevant LangChain/agent/tool page appears later.
    items = []
    for i in range(12):
        items.append({
            "title": f"AI Workflow Automation Platform - n8n ({i})",
            "href": f"https://n8n.io/{i}",
            "body": "Generic landing page",
        })

    items.append({
        "title": "AI Agent Tool node documentation | n8n Docs",
        "href": "https://docs.n8n.io/advanced-ai/agent-tool/",
        "body": "Use the AI Agent Tool node to integrate external tools.",
    })
    items.append({
        "title": "n8n LangChain integration guide",
        "href": "https://docs.n8n.io/advanced-ai/langchain/overview/",
        "body": "LangChain agent/tool integration in n8n.",
    })

    dummy = _DummyDDGS(items)

    search = DuckDuckGoSearch()
    # Inject dummy ddgs client so the test stays offline and deterministic.
    search.ddgs = dummy

    query = "n8n LangChain agent tool integration"
    results = await search.search(query, num_results=8)

    assert results and len(results) == 8

    # Ensure we asked ddgs for a larger candidate pool than the requested 8.
    _q, kwargs = dummy.calls[0]
    assert kwargs["max_results"] >= 20

    # Ensure reranking surfaced an agent/tool or langchain-specific result.
    titles = [r.title.lower() for r in results]
    assert any("langchain" in t or "agent tool" in t for t in titles)
