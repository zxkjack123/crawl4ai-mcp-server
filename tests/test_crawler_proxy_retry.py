#!/usr/bin/env python3
"""
Unit tests for crawler proxy retry behavior in read_url using mocks.
- Simulate direct attempt failing with net::ERR_CONNECTION_CLOSED
- Verify proxied retry succeeds when proxy is resolvable
- Also verify direct success path does not initialize proxied crawler
"""

import os
import sys
import pytest

# Ensure project root is on path (like other tests do)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.index as index  # noqa: E402


class FakeMarkdownV2:
    def __init__(self, content: str):
        self.raw_markdown = content
        self.markdown_with_citations = content
        self.references_markdown = "[1] https://example.com"
        self.fit_markdown = content
        self.fit_html = "<p>" + content + "</p>"


class FakeResult:
    def __init__(self, content: str):
        self.markdown_v2 = FakeMarkdownV2(content)


class FakeAsyncWebCrawler:
    """A fake AsyncWebCrawler that raises on direct and succeeds on proxy.

    Behavior is controlled via class variables:
    - fail_direct: if True, direct arun raises; if False, returns direct content
    - created_instances: records instances constructed with their proxy
    """

    fail_direct: bool = True
    created_instances: list = []

    def __init__(self, config=None, **kwargs):
        self.config = config
        # BrowserConfig has attribute 'proxy'; default None for direct
        self.proxy = getattr(config, 'proxy', None)
        if not self.proxy and hasattr(config, 'proxy_config'):
             self.proxy = config.proxy_config
        FakeAsyncWebCrawler.created_instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def arun(self, url: str, config=None):
        # If proxy present, always succeed
        if self.proxy:
            return FakeResult("proxied content: " + url)
        # Direct path
        if FakeAsyncWebCrawler.fail_direct:
            raise RuntimeError("net::ERR_CONNECTION_CLOSED")
        else:
            return FakeResult("direct content: " + url)


@pytest.mark.asyncio
async def test_read_url_retries_via_proxy_and_succeeds(monkeypatch):
    # Arrange: patch crawler class and proxy resolver
    monkeypatch.setattr(index, "AsyncWebCrawler", FakeAsyncWebCrawler)
    monkeypatch.setattr(index, "_resolve_crawler_proxy_url", lambda: "http://127.0.0.1:7890")

    # Reset module state
    index.crawler = None
    index.crawler_proxy = None
    index.crawler_proxy_url = None
    FakeAsyncWebCrawler.created_instances.clear()
    FakeAsyncWebCrawler.fail_direct = True

    # Act
    url = "https://example.com/page"
    content = await index.read_url(url, format="markdown_with_citations")

    # Assert: content came from proxied path and contains URL
    assert isinstance(content, str)
    assert "proxied content" in content
    assert url in content

    # Two crawler instances should be created: direct (no proxy) then proxied
    assert len(FakeAsyncWebCrawler.created_instances) >= 2
    proxies = [inst.proxy for inst in FakeAsyncWebCrawler.created_instances]
    print(f"DEBUG: proxies found: {proxies}")
    assert proxies[0] in (None, "")  # direct first
    
    def get_proxy_url(p):
        if hasattr(p, 'server'):
            return p.server
        return p

    assert any(get_proxy_url(p) == "http://127.0.0.1:7890" for p in proxies)


@pytest.mark.asyncio
async def test_read_url_direct_succeeds_no_proxy(monkeypatch):
    # Arrange
    monkeypatch.setattr(index, "AsyncWebCrawler", FakeAsyncWebCrawler)
    # Even if resolver returns a proxy, direct should succeed and avoid using it
    monkeypatch.setattr(index, "_resolve_crawler_proxy_url", lambda: "http://127.0.0.1:7890")

    # Reset state
    index.crawler = None
    index.crawler_proxy = None
    index.crawler_proxy_url = None
    FakeAsyncWebCrawler.created_instances.clear()
    FakeAsyncWebCrawler.fail_direct = False

    # Act
    url = "https://example.com/ok"
    content = await index.read_url(url, format="markdown_with_citations")

    # Assert: direct content and no proxied arun
    assert isinstance(content, str)
    assert content.startswith("direct content")

    # Only one crawler instance (direct) should be created
    assert len(FakeAsyncWebCrawler.created_instances) == 1
    assert FakeAsyncWebCrawler.created_instances[0].proxy in (None, "")
