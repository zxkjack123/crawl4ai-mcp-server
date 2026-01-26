import pytest

from src import index


@pytest.mark.asyncio
async def test_ssrf_blocks_non_http_schemes(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_READ_URL_SSRF_PROTECTION", "1")
    err = await index._validate_read_url_target("file:///etc/passwd")
    assert err is not None
    assert "http" in err.lower()


@pytest.mark.asyncio
async def test_ssrf_blocks_url_with_credentials(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_READ_URL_SSRF_PROTECTION", "1")
    err = await index._validate_read_url_target("http://user:pass@example.com/")
    assert err is not None
    assert "credentials" in err.lower()


@pytest.mark.asyncio
async def test_ssrf_blocks_localhost_and_private_ip_by_default(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_READ_URL_SSRF_PROTECTION", "1")
    monkeypatch.delenv("CRAWL4AI_READ_URL_ALLOW_PRIVATE", raising=False)

    err_local = await index._validate_read_url_target("http://localhost/")
    assert err_local is not None

    err_ip = await index._validate_read_url_target("http://127.0.0.1/")
    assert err_ip is not None


@pytest.mark.asyncio
async def test_ssrf_allow_private_opt_in(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_READ_URL_SSRF_PROTECTION", "1")
    monkeypatch.setenv("CRAWL4AI_READ_URL_ALLOW_PRIVATE", "1")

    # With allow-private enabled, we should not block localhost/private.
    assert await index._validate_read_url_target("http://127.0.0.1/") is None
    assert await index._validate_read_url_target("http://localhost/") is None


class _FakeStreamResponse:
    def __init__(self, *, url: str, headers: dict[str, str], body_chunks: list[bytes]):
        self.url = url
        self.headers = headers
        self._chunks = body_chunks

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        return None

    async def aiter_bytes(self):
        for c in self._chunks:
            yield c


class _FakeAsyncClient:
    def __init__(
        self,
        *,
        response: _FakeStreamResponse | None = None,
        raise_too_many: bool = False,
    ):
        self._response = response
        self._raise_too_many = raise_too_many

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def stream(self, method: str, url: str):
        import httpx

        if self._raise_too_many:
            raise httpx.TooManyRedirects("too many")
        assert self._response is not None
        return self._response


@pytest.mark.asyncio
async def test_preflight_blocks_content_type(monkeypatch):
    # Ensure redirect-target validation is bypassed via allowlist (no DNS).
    monkeypatch.setenv("CRAWL4AI_READ_URL_ALLOWED_HOSTS", "example.com")
    monkeypatch.setenv("CRAWL4AI_READ_URL_ALLOWED_CONTENT_TYPES", "text/html")

    resp = _FakeStreamResponse(
        url="https://example.com/final",
        headers={"content-type": "video/mp4"},
        body_chunks=[b"x"],
    )

    def fake_client(*args, **kwargs):
        return _FakeAsyncClient(response=resp)

    monkeypatch.setattr(index.httpx, "AsyncClient", fake_client)

    final, err = await index._preflight_url("https://example.com", proxy_url=None)
    assert final is None
    assert err is not None
    assert "content-type" in err.lower()


@pytest.mark.asyncio
async def test_preflight_blocks_large_response(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_READ_URL_ALLOWED_HOSTS", "example.com")
    monkeypatch.setenv("CRAWL4AI_READ_URL_PREFLIGHT_MAX_BYTES", "10")

    resp = _FakeStreamResponse(
        url="https://example.com/final",
        headers={"content-type": "text/html"},
        body_chunks=[b"0123456789", b"X"],
    )

    def fake_client(*args, **kwargs):
        return _FakeAsyncClient(response=resp)

    monkeypatch.setattr(index.httpx, "AsyncClient", fake_client)

    final, err = await index._preflight_url("https://example.com", proxy_url=None)
    assert final is None
    assert err is not None
    assert "too large" in err.lower()


@pytest.mark.asyncio
async def test_preflight_too_many_redirects(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_READ_URL_ALLOWED_HOSTS", "example.com")

    def fake_client(*args, **kwargs):
        return _FakeAsyncClient(response=None, raise_too_many=True)

    monkeypatch.setattr(index.httpx, "AsyncClient", fake_client)

    final, err = await index._preflight_url("https://example.com", proxy_url=None)
    assert final is None
    assert err is not None
    assert "redirect" in err.lower()
