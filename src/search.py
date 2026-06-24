from typing import List, Dict, Optional, Any
import inspect
import asyncio
import httpx
import json
import os
import re
import logging
import time
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

# Python 3.10 compatibility: asyncio.timeout was added in 3.11
try:  # pragma: no cover
    from src.compat import *  # noqa: F401,F403
except Exception:  # pragma: no cover
    from compat import *  # noqa: F401,F403
# Prefer the new 'ddgs' package and fall back to the legacy name if needed
try:
    from ddgs import DDGS  # new package name (no deprecation warning)
    try:  # ddgs-only: used to build a safe default backend list (exclude wikipedia)
        from ddgs.engines import ENGINES as _DDGS_ENGINES  # type: ignore
    except Exception:  # pragma: no cover
        _DDGS_ENGINES = None
except Exception:  # pragma: no cover - fallback for environments without ddgs
    from duckduckgo_search import DDGS  # legacy package name
    _DDGS_ENGINES = None

# Prefer absolute imports for tooling; fall back to direct imports for
# ad-hoc script execution contexts.
try:
    from src.cache import SearchCache
    from src.persistent_cache import PersistentCache
    from src.utils import (
        MultiRateLimiter,
        merge_and_deduplicate,
        rewrite_local_proxy_url,
        get_http_proxy_from_env,
    )
    from src.monitor import SearchMetrics, get_monitor
    from src.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
    from src.request_context import get_request_id
except Exception:  # pragma: no cover
    from cache import SearchCache
    from persistent_cache import PersistentCache
    from utils import (
        MultiRateLimiter,
        merge_and_deduplicate,
        rewrite_local_proxy_url,
        get_http_proxy_from_env
    )
    from monitor import (
        SearchMetrics, get_monitor
    )
    from circuit_breaker import CircuitBreaker, CircuitBreakerConfig
    from request_context import get_request_id

logger = logging.getLogger(__name__)


class EngineSearchError(RuntimeError):
    """Raised when an engine call fails.

    Used to power retries and engine-level circuit breaker decisions.
    """

    def __init__(
        self,
        message: str,
        *,
        retriable: bool = True,
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.retriable = bool(retriable)
        self.status_code = status_code


_PLACEHOLDER_SECRET_MARKERS = {
    "YOUR_BRAVE_API_KEY",
    "YOUR_BRAVE_API_KEY_HERE",
    "YOUR_BRAVE_API_KEY_HERE",
    "YOUR_GOOGLE_API_KEY",
    "YOUR_GOOGLE_API_KEY_HERE",
    "YOUR_CUSTOM_SEARCH_ENGINE_ID_HERE",
    "YOUR_CSE_ID",
    "YOUR_CSE_ID_HERE",
    "YOUR_GOOGLE_CSE_ID",
    "YOUR_GOOGLE_CSE_ID_HERE",
    "your-brave-api-key-here",
    "your-google-api-key-here",
    "your-cse-id-here",
}


def _normalize_secret_value(value: Any) -> Optional[str]:
    """Normalize a secret-like value from config/env.

    Returns None for empty/placeholder values.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    v = value.strip()
    if not v:
        return None
    v_upper = v.upper()
    if v in _PLACEHOLDER_SECRET_MARKERS or v_upper in _PLACEHOLDER_SECRET_MARKERS:
        return None
    if v_upper.startswith("YOUR_"):
        return None
    if v.lower().startswith("your-"):
        return None
    if v.lower() in {"none", "null", "nil"}:
        return None
    return v


def _resolve_secret(config_value: Any, env_value: Any) -> Optional[str]:
    """Resolve a secret from env (preferred) or config.json.

    This protects against committed config examples that contain placeholder
    strings (e.g. YOUR_GOOGLE_API_KEY_HERE).
    """
    env_v = _normalize_secret_value(env_value)
    if env_v:
        return env_v
    return _normalize_secret_value(config_value)


class HttpClientPool:
    """Reuse httpx.AsyncClient instances across requests.

    We keep a small pool keyed by proxy URL (including direct/None).
    This enables connection reuse (keep-alive), reduces TLS handshakes,
    and improves throughput/latency under concurrency.
    """

    def __init__(
        self,
        timeout_s: float = 30.0,
        max_connections: int = 50,
        max_keepalive_connections: int = 20,
        keepalive_expiry_s: float = 30.0,
        http2: bool = True,
    ):
        self._timeout = httpx.Timeout(timeout_s)
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=keepalive_expiry_s,
        )
        self._http2 = http2
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _key(proxy_url: Optional[str]) -> str:
        return proxy_url or "<direct>"

    async def get_client(self, proxy_url: Optional[str]) -> httpx.AsyncClient:
        key = self._key(proxy_url)
        client = self._clients.get(key)
        if client is not None:
            return client
        async with self._lock:
            client = self._clients.get(key)
            if client is not None:
                return client
            client = httpx.AsyncClient(
                timeout=self._timeout,
                proxy=proxy_url,
                trust_env=False,
                limits=self._limits,
                http2=self._http2,
            )
            self._clients[key] = client
            return client

    async def aclose(self) -> None:
        # Close all clients best-effort.
        async with self._lock:
            clients = list(self._clients.values())
            self._clients.clear()
        for c in clients:
            try:
                await c.aclose()
            except Exception:
                pass


_DDGS_REGION_RE = re.compile(r"^[a-z]{2}-[a-z]{2,3}$")


def normalize_ddgs_region(region: Optional[str]) -> str:
    """Normalize/validate ddgs region to avoid known-bad values.

    ddgs expects a string like "us-en" (country-language). Some legacy/special
    values used in other tooling (e.g. "wt-wt") are *not* valid Wikipedia
    language subdomains and can trigger requests to non-existent hosts like
    "wt.wikipedia.org".
    """
    raw = (region or "").strip().lower()
    if not raw:
        return "us-en"

    # Explicitly disallow the legacy worldwide code.
    if raw == "wt-wt":
        return "us-en"

    # ddgs wikipedia engine splits on '-', so we only allow a single delimiter.
    if not _DDGS_REGION_RE.match(raw):
        return "us-en"

    country, lang = raw.split("-", 1)
    # Some proxies/DNS setups may synthesize records for non-existent lang
    # subdomains; keep a small denylist for known-invalid values.
    if lang in {"wt", "all"}:
        return "us-en"
    return f"{country}-{lang}"


def _ddgs_text_backends_without_wikipedia() -> Optional[str]:
    """Return a comma-delimited ddgs backend list for text searches.

    When ddgs backend is "auto" (default), ddgs always includes the Wikipedia
    engine for text searches. This is great for "instant answers" but can hurt
    stability in environments where Wikipedia domains are blocked or DNS is
    polluted. Returning an explicit backend list avoids Wikipedia entirely.
    """
    if not _DDGS_ENGINES:
        return None
    try:
        keys = list(_DDGS_ENGINES.get("text", {}).keys())
        keys = [k for k in keys if k != "wikipedia"]
        if not keys:
            return None
        # Deterministic order; ddgs itself shuffles internally anyway.
        return ",".join(sorted(keys))
    except Exception:
        return None


class SearchResult:
    def __init__(
        self, title: str, link: str, snippet: str, source: str
    ):
        self.title = title
        self.link = link
        self.snippet = snippet
        self.source = source

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet,
            "source": self.source
        }


class SearchEngine(ABC):
    @abstractmethod
    async def search(
        self, query: str, num_results: int = 10
    ) -> List[SearchResult]:
        pass


class DuckDuckGoSearch(SearchEngine):
    def __init__(
        self,
        proxy: Optional[str] = None,
        region: Optional[str] = None,
        backend: Optional[str] = None,
        include_wikipedia: Optional[bool] = None,
        fetch_k: Optional[int] = None,
    ):
        self.ddgs = DDGS()
        self.proxy = proxy
        self.region = region
        # ddgs "backend" selects which internal engines to use (e.g. "auto",
        # "duckduckgo", or a comma-delimited list like "duckduckgo,brave").
        # NOTE: In ddgs, "backend" is NOT "html/lite/api".
        self.backend = backend
        # If False, we will avoid ddgs' Wikipedia engine by using an explicit
        # backend list; this prevents issues caused by Wikipedia being blocked
        # or by invalid/wrongly-resolved subdomains.
        self.include_wikipedia = include_wikipedia
        # ddgs ranks results based on the *candidate pool* it gathers from
        # upstream providers. With small max_results (<10), ddgs often queries
        # only one provider and can over-rank generic landing pages.
        # We can fetch a slightly larger pool and then trim/rerank locally.
        self.fetch_k = fetch_k

    @staticmethod
    def _query_terms(query: str) -> List[str]:
        # Lightweight tokenization for reranking; designed to work for typical
        # English technical queries. We keep it conservative to avoid breaking
        # non-English queries.
        parts = re.split(r"[^a-zA-Z0-9]+", (query or "").lower())
        stop = {
            "the", "a", "an", "and", "or", "for", "to", "in", "of",
            "with", "on", "at", "by", "from"
        }
        out: List[str] = []
        for p in parts:
            if not p or p in stop:
                continue
            # keep short but meaningful tokens like 'n8n'
            if len(p) <= 2 and not p.isdigit():
                continue
            out.append(p)
        # de-dupe while preserving order
        seen = set()
        deduped: List[str] = []
        for t in out:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        return deduped

    @classmethod
    def _rerank_results(
        cls,
        results: List[SearchResult],
        query: str,
    ) -> List[SearchResult]:
        terms = cls._query_terms(query)
        # If there are no meaningful terms (or only a single term), keep ddgs
        # native ranking.
        if len(terms) < 2:
            return results

        def _score(r: SearchResult) -> int:
            title = (r.title or "").lower()
            link = (r.link or "").lower()
            snippet = (r.snippet or "").lower()
            s = 0
            for t in terms:
                if t in title:
                    s += 3
                if t in link:
                    s += 2
                if t in snippet:
                    s += 1
            # If query contains 'langchain', strongly prefer results that
            # actually mention it (common complaint: generic n8n pages win).
            if "langchain" in terms and "langchain" in (title + link + snippet):
                s += 5
            return s

        scored = [(_score(r), i, r) for i, r in enumerate(results)]
        # Only rerank if at least one item got a non-zero score.
        if not any(s > 0 for s, _, _ in scored):
            return results
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [r for _, _, r in scored]

    async def search(
        self, query: str, num_results: int = 10
    ) -> List[SearchResult]:
        def _ddg_region() -> str:
            # Prefer explicit ctor override, then env vars; normalize to avoid
            # known-bad values like "wt-wt".
            raw = (
                self.region or
                os.environ.get('DDG_REGION') or
                os.environ.get('DDGS_REGION') or
                os.environ.get('DUCKDUCKGO_REGION')
            )
            return normalize_ddgs_region(raw)

        def _parse_bool(value: Optional[str]) -> Optional[bool]:
            if value is None:
                return None
            v = value.strip().lower()
            if v in {"1", "true", "yes", "y", "on"}:
                return True
            if v in {"0", "false", "no", "n", "off"}:
                return False
            return None

        def _ddg_backend() -> Optional[str]:
            # 1) explicit override from ctor/env
            explicit = (
                self.backend or
                os.environ.get('DDGS_TEXT_BACKEND') or
                os.environ.get('DDG_BACKEND') or
                os.environ.get('DDGS_BACKEND')
            )
            if explicit:
                return explicit

            # 2) default: avoid Wikipedia unless explicitly enabled.
            include_wiki = self.include_wikipedia
            if include_wiki is None:
                include_wiki = _parse_bool(
                    os.environ.get('DDG_INCLUDE_WIKIPEDIA') or
                    os.environ.get('DDGS_INCLUDE_WIKIPEDIA')
                )
            if include_wiki is True:
                return None

            return _ddgs_text_backends_without_wikipedia()

        def _env_proxy() -> Optional[str]:
            return get_http_proxy_from_env()

        def _new_ddgs_with_proxy(proxy_url: str) -> Optional[DDGS]:
            try:
                sig = inspect.signature(DDGS)
                params = sig.parameters
                if 'proxies' in params:
                    return DDGS(proxies={
                        'http': proxy_url,
                        'https': proxy_url
                    })
                if 'proxy' in params:
                    return DDGS(proxy=proxy_url)
            except Exception:
                pass
            return None

        def _fetch_k() -> int:
            # Allow users to tune this (trade-off quality vs latency).
            # - config.json can pass fetch_k via SearchManager initialization.
            # - env var DDG_FETCH_K provides a runtime override.
            env_v = os.environ.get('DDG_FETCH_K') or os.environ.get('DDGS_FETCH_K')
            try:
                env_k = int(env_v) if env_v else None
            except Exception:
                env_k = None

            base = self.fetch_k or env_k or 20
            # Always at least the requested number; keep a reasonable cap.
            return max(num_results, min(base, 50))

        def _collect(raw_results_iter) -> List[SearchResult]:
            results: List[SearchResult] = []
            for item in raw_results_iter:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    link=item.get('href', ''),
                    snippet=item.get('body', ''),
                    source='duckduckgo'
                ))
            return results

        # Strategy:
        # - If a proxy is configured, try it *first*. In some regions the direct
        #   path does not error but yields heavily degraded/censored results.
        # - Fetch a larger pool (fetch_k) and then trim/rerank locally.
        proxy_to_use = self.proxy or _env_proxy()
        candidates: List[tuple[str, Any]] = []
        if proxy_to_use:
            ddgs_proxy = _new_ddgs_with_proxy(proxy_to_use)
            if ddgs_proxy is not None:
                candidates.append(("proxy", ddgs_proxy))
        candidates.append(("direct", self.ddgs))

        last_error: Optional[str] = None
        for mode, ddgs_client in candidates:
            try:
                ddg_kwargs = {}
                backend = _ddg_backend()
                if backend:
                    ddg_kwargs['backend'] = backend

                # ddgs is synchronous; run in a thread to avoid blocking the event loop.
                def _call_ddgs_text():
                    return list(ddgs_client.text(
                        query,
                        region=_ddg_region(),
                        safesearch="moderate",
                        max_results=_fetch_k(),
                        **ddg_kwargs,
                    ))

                raw_items = await asyncio.to_thread(_call_ddgs_text)
                results = _collect(raw_items)
                if results:
                    # Rerank to better respect multi-term technical queries.
                    results = self._rerank_results(results, query)
                    results = results[:num_results]
                    logger.info(
                        "DuckDuckGo search successful (%s) for query: %s",
                        mode,
                        query
                    )
                    return results
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "DuckDuckGo search failed (%s): %s",
                    mode,
                    last_error
                )

        # give up
        if last_error:
            logger.warning(
                "DuckDuckGo returned no results for query: %s (last error: %s)",
                query,
                last_error
            )
            raise EngineSearchError(
                f"DuckDuckGo search failed: {last_error}",
                retriable=True,
            )
        else:
            logger.warning(
                "DuckDuckGo returned no results for query: %s",
                query
            )
        return []


class GoogleSearch(SearchEngine):
    def __init__(
        self,
        api_key: str,
        cse_id: str,
        proxy: Optional[str] = None,
        client_pool: Optional[HttpClientPool] = None,
    ):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        # Optional proxy URL from config.json (has priority over env)
        self.proxy = proxy
        self._client_pool = client_pool

    async def search(
        self, query: str, num_results: int = 10
    ) -> List[SearchResult]:
        if not self.api_key or not self.cse_id:
            logger.warning("Google search credentials not configured")
            return []

        # Prepare request params once
        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': min(num_results, 10)
        }

        # Strategy: try direct first; on network error, retry via proxy
        async def _request_with_proxy(proxy_url: Optional[str]):
            if self._client_pool is not None:
                client = await self._client_pool.get_client(proxy_url)
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                return response.json()

            async with httpx.AsyncClient(
                timeout=30.0, proxy=proxy_url, trust_env=False
            ) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                return response.json()

        def _env_proxy() -> Optional[str]:
            return get_http_proxy_from_env()

        try:
            logger.info(f"Sending Google request (direct): {query}")
            data = await _request_with_proxy(None)
        except (httpx.RequestError, httpx.TimeoutException, ValueError) as e:
            if self.proxy:
                logger.warning(
                    "Direct Google request failed (%s); retrying via proxy",
                    e.__class__.__name__
                )
                try:
                    data = await _request_with_proxy(self.proxy)
                except Exception as e2:
                    logger.error(f"Google search failed via proxy: {str(e2)}")
                    raise EngineSearchError(
                        f"Google search failed via proxy: {str(e2)}",
                        retriable=True,
                    )
            else:
                # Try environment proxy as a fallback
                env_p = _env_proxy()
                if env_p:
                    logger.warning(
                        "Direct Google request failed (%s); "
                        "retrying via env proxy",
                        e.__class__.__name__
                    )
                    try:
                        data = await _request_with_proxy(env_p)
                    except Exception as e2:
                        logger.error(
                            "Google search failed via env proxy: %s",
                            str(e2)
                        )
                        raise EngineSearchError(
                            f"Google search failed via env proxy: {str(e2)}",
                            retriable=True,
                        )
                else:
                    logger.error(
                        "Google search failed (no proxy configured): %s",
                        str(e)
                    )
                    raise EngineSearchError(
                        f"Google search failed (no proxy configured): {str(e)}",
                        retriable=True,
                    )
        except httpx.HTTPStatusError as e:
            # HTTP errors like 4xx/5xx won't be fixed by proxy; don't retry
            logger.error(
                "Google search HTTP error: %s - %s",
                e.response.status_code,
                e.response.text[:200]
            )
            code = int(getattr(e.response, "status_code", 0) or 0)
            retriable = bool(code >= 500 or code == 429)
            raise EngineSearchError(
                f"Google search HTTP error: {code}",
                retriable=retriable,
                status_code=code,
            )
        except Exception as e:
            logger.error(f"Google search failed: {str(e)}")
            raise EngineSearchError(
                f"Google search failed: {str(e)}",
                retriable=True,
            )

        results = []
        for item in data.get('items', []):
            results.append(SearchResult(
                title=item.get('title', ''),
                link=item.get('link', ''),
                snippet=item.get('snippet', ''),
                source='google'
            ))

        logger.info("Google search request successful")
        return results


class BraveSearch(SearchEngine):
    def __init__(
        self,
        api_key: str,
        proxy: Optional[str] = None,
        client_pool: Optional[HttpClientPool] = None,
    ):
        """
        初始化 Brave Search 搜索引擎

        Args:
            api_key: Brave Search API 密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.proxy = proxy
        self._client_pool = client_pool

    async def search(
        self, query: str, num_results: int = 10
    ) -> List[SearchResult]:
        """
        使用 Brave Search API 进行搜索

        Args:
            query: 搜索查询字符串
            num_results: 需要返回的结果数量

        Returns:
            搜索结果列表
        """
        if not self.api_key:
            logger.warning("Brave Search API key not configured")
            return []

        try:
            headers = {
                'Accept': 'application/json',
                'X-Subscription-Token': self.api_key
            }

            params = {
                'q': query,
                'count': min(num_results, 20)
            }

            async def _do_request(proxy_url: Optional[str]):
                if self._client_pool is not None:
                    client = await self._client_pool.get_client(proxy_url)
                    return await client.get(
                        self.base_url, headers=headers, params=params
                    )

                async with httpx.AsyncClient(
                    timeout=30.0, proxy=proxy_url, trust_env=False
                ) as client:
                    return await client.get(
                        self.base_url, headers=headers, params=params
                    )

            async def _do_request_json(proxy_url: Optional[str]) -> Dict[str, Any]:
                resp = await _do_request(proxy_url)
                resp.raise_for_status()
                return resp.json()

            def _env_proxy() -> Optional[str]:
                return get_http_proxy_from_env()

            logger.info(f"Sending request to Brave Search (direct): {query}")
            try:
                data = await _do_request_json(None)
            except (httpx.RequestError, httpx.TimeoutException, ValueError) as e:
                if self.proxy:
                    logger.warning(
                        "Direct Brave request failed (%s); "
                        "retrying via proxy",
                        e.__class__.__name__
                    )
                    data = await _do_request_json(self.proxy)
                else:
                    env_p = _env_proxy()
                    if env_p:
                        logger.warning(
                            "Direct Brave request failed (%s); "
                            "retrying via env proxy",
                            e.__class__.__name__
                        )
                        data = await _do_request_json(env_p)
                    else:
                        raise

            results = []
            web_results = data.get('web', {}).get('results', [])
            logger.info(
                f"Brave Search successful, "
                f"got {len(web_results)} results"
            )

            for item in web_results[:num_results]:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    link=item.get('url', ''),
                    snippet=item.get('description', ''),
                    source='brave'
                ))

            return results

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Brave Search API key is invalid or expired")
            elif e.response.status_code == 429:
                logger.error("Brave Search API rate limit exceeded")
            else:
                logger.error(
                    f"Brave Search HTTP error: "
                    f"{e.response.status_code}"
                )
            code = int(getattr(e.response, "status_code", 0) or 0)
            retriable = bool(code >= 500 or code == 429)
            raise EngineSearchError(
                f"Brave Search HTTP error: {code}",
                retriable=retriable,
                status_code=code,
            )
        except Exception as e:
            logger.error(f"Brave Search failed: {str(e)}")
            raise EngineSearchError(
                f"Brave Search failed: {str(e)}",
                retriable=True,
            )


class SearXNGSearch(SearchEngine):
    def __init__(
        self,
        base_url: str = "http://localhost:28981",
        language: str = "zh-CN",
        proxy: Optional[str] = None,
        client_pool: Optional[HttpClientPool] = None,
    ):
        """
        初始化 SearXNG 搜索引擎

        Args:
            base_url: SearXNG 实例的基础 URL
                (例如: http://localhost:28981 或
                https://searx.example.com)
            language: 搜索语言，默认为 zh-CN (中文)
        """
        self.base_url = base_url.rstrip('/')
        self.language = language
        self.proxy = proxy
        self._client_pool = client_pool

    async def search(
        self, query: str, num_results: int = 10
    ) -> List[SearchResult]:
        """
        使用 SearXNG 进行搜索

        Args:
            query: 搜索查询字符串
            num_results: 需要返回的结果数量

        Returns:
            搜索结果列表
        """
        try:
            params: Dict[str, str] = {
                'q': query,
                'format': 'json',
                'language': self.language,
                'pageno': '1'
            }

            search_url = f"{self.base_url}/search"
            logger.info(
                "Sending request to SearXNG (direct): %s with query: %s",
                search_url,
                query
            )

            trusted_ip = os.environ.get('SEARXNG_TRUSTED_IP', '127.0.0.1')
            default_headers = {
                'User-Agent': os.environ.get(
                    'SEARXNG_USER_AGENT',
                    'Crawl4AI-HTTP-Bridge/0.5.9'
                ),
                'Accept': 'application/json',
                'X-Forwarded-For': trusted_ip,
                'X-Real-IP': trusted_ip,
            }

            async def _do_request(proxy_url: Optional[str]):
                if self._client_pool is not None:
                    client = await self._client_pool.get_client(proxy_url)
                    return await client.get(
                        search_url,
                        params=params,
                        headers=default_headers,
                    )

                async with httpx.AsyncClient(
                    timeout=30.0, proxy=proxy_url, trust_env=False
                ) as client:
                    return await client.get(
                        search_url,
                        params=params,
                        headers=default_headers
                    )

            async def _do_request_json(proxy_url: Optional[str]) -> Dict[str, Any]:
                resp = await _do_request(proxy_url)
                resp.raise_for_status()
                return resp.json()

            def _env_proxy() -> Optional[str]:
                return get_http_proxy_from_env()

            try:
                data = await _do_request_json(None)
            except (httpx.RequestError, httpx.TimeoutException, ValueError) as e:
                if self.proxy:
                    logger.warning(
                        "Direct SearXNG request failed (%s); "
                        "retrying via proxy",
                        e.__class__.__name__
                    )
                    data = await _do_request_json(self.proxy)
                else:
                    env_p = _env_proxy()
                    if env_p:
                        logger.warning(
                            "Direct SearXNG request failed (%s); "
                            "retrying via env proxy",
                            e.__class__.__name__
                        )
                        data = await _do_request_json(env_p)
                    else:
                        raise

            results_count = len(data.get('results', []))
            logger.info(
                f"SearXNG search successful, got {results_count} results"
            )

            results = []
            for item in data.get('results', [])[:num_results]:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    link=item.get('url', ''),
                    snippet=item.get('content', ''),
                    source='searxng'
                ))

            return results

        except httpx.HTTPStatusError as e:
            code = int(getattr(e.response, "status_code", 0) or 0)
            logger.error(f"SearXNG HTTP error: {code}")
            logger.warning(
                "如果 SearXNG 未运行，请使用 "
                "'docker run -d -p 28981:8080 searxng/searxng' 启动"
            )
            retriable = bool(code >= 500 or code == 429)
            raise EngineSearchError(
                f"SearXNG HTTP error: {code}",
                retriable=retriable,
                status_code=code,
            )
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"SearXNG request failed: {e.__class__.__name__}")
            logger.warning(
                "如果 SearXNG 未运行，请使用 "
                "'docker run -d -p 28981:8080 searxng/searxng' 启动"
            )
            raise EngineSearchError(
                f"SearXNG request failed: {e.__class__.__name__}",
                retriable=True,
            )
        except Exception as e:
            logger.error(f"SearXNG search failed: {str(e)}")
            raise EngineSearchError(
                f"SearXNG search failed: {str(e)}",
                retriable=True,
            )


class SearchManager:
    def __init__(
        self,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        enable_rate_limit: bool = True,
        enable_monitoring: bool = True
    ):
        """
        初始化搜索管理器

        Args:
            enable_cache: 是否启用搜索缓存
            cache_ttl: 缓存过期时间（秒），默认1小时
            enable_rate_limit: 是否启用API限流保护
            enable_monitoring: 是否启用性能监控
        """
        self.engines: List[SearchEngine] = []
        self.fallback_engines: List[SearchEngine] = []
        self.enable_cache = enable_cache

        def _parse_bool_env(value: Optional[str]) -> Optional[bool]:
            if value is None:
                return None
            v = str(value).strip().lower()
            if v in {"1", "true", "yes", "y", "on"}:
                return True
            if v in {"0", "false", "no", "n", "off"}:
                return False
            return None

        self.cache_backend = "none"
        self.cache = None
        if enable_cache:
            # Cache backend selection:
            # - default: in-memory SearchCache
            # - opt-in: PersistentCache (SQLite) via env
            backend = (
                os.environ.get("CRAWL4AI_CACHE_BACKEND")
                or os.environ.get("CACHE_BACKEND")
                or "memory"
            ).strip().lower()

            persistent_flag = _parse_bool_env(
                os.environ.get("CRAWL4AI_ENABLE_PERSISTENT_CACHE")
                or os.environ.get("ENABLE_PERSISTENT_CACHE")
            )

            use_persistent = (
                backend in {"persistent", "sqlite", "db"}
                or persistent_flag is True
            )

            if use_persistent:
                db_path = (
                    os.environ.get("CRAWL4AI_PERSISTENT_CACHE_DB_PATH")
                    or os.environ.get("PERSISTENT_CACHE_DB_PATH")
                    or "cache/search_cache.db"
                )
                try:
                    max_size = int(
                        os.environ.get("CRAWL4AI_PERSISTENT_CACHE_MAX_SIZE")
                        or os.environ.get("PERSISTENT_CACHE_MAX_SIZE")
                        or "10000"
                    )
                except Exception:
                    max_size = 10000
                mem_enabled = _parse_bool_env(
                    os.environ.get("CRAWL4AI_PERSISTENT_CACHE_MEMORY")
                    or os.environ.get("PERSISTENT_CACHE_MEMORY")
                )
                if mem_enabled is None:
                    mem_enabled = True

                try:
                    self.cache = PersistentCache(
                        db_path=db_path,
                        ttl=cache_ttl,
                        max_size=max_size,
                        enable_memory_cache=bool(mem_enabled),
                    )
                    self.cache_backend = "persistent"
                except Exception as e:
                    # Never fail hard on cache init; fall back to in-memory.
                    logger.warning(
                        "Failed to initialize PersistentCache (%s); "
                        "falling back to in-memory cache",
                        str(e),
                    )
                    self.cache = SearchCache(ttl=cache_ttl)
                    self.cache_backend = "memory"
            else:
                try:
                    max_size = int(
                        os.environ.get("CRAWL4AI_CACHE_MAX_SIZE")
                        or os.environ.get("CACHE_MAX_SIZE")
                        or "1000"
                    )
                except Exception:
                    max_size = 1000
                self.cache = SearchCache(ttl=cache_ttl, max_size=max_size)
                self.cache_backend = "memory"
        
        # 初始化限流器
        self.enable_rate_limit = enable_rate_limit
        self.rate_limiter = MultiRateLimiter() if enable_rate_limit else None
        
        # 初始化监控
        self.enable_monitoring = enable_monitoring
        self.monitor = get_monitor() if enable_monitoring else None

        # Timeout budgets & bulkheads (concurrency limits)
        def _parse_float_env(value: Optional[str]) -> Optional[float]:
            if value is None:
                return None
            try:
                v = float(str(value).strip())
            except Exception:
                return None
            return v if v > 0 else None

        def _parse_int_env(value: Optional[str]) -> Optional[int]:
            if value is None:
                return None
            try:
                v = int(str(value).strip())
            except Exception:
                return None
            return max(0, v)

        def _first_env(*names: str) -> Optional[str]:
            for n in names:
                if n in os.environ:
                    return os.environ.get(n)
            return None

        self.search_deadline_s: Optional[float] = _parse_float_env(
            os.environ.get("CRAWL4AI_SEARCH_DEADLINE_S")
            or os.environ.get("SEARCH_DEADLINE_S")
        )

        # Per-engine overall budget (covers retries + backoff inside _search_with_retry)
        default_engine_timeout = _parse_float_env(
            os.environ.get("CRAWL4AI_ENGINE_TIMEOUT_S")
            or os.environ.get("ENGINE_TIMEOUT_S")
        )
        self.engine_timeout_default_s: Optional[float] = default_engine_timeout
        self.engine_timeout_s: Dict[str, float] = {}
        for name in ("google", "brave", "searxng", "duckduckgo"):
            v = _parse_float_env(
                os.environ.get(f"CRAWL4AI_ENGINE_TIMEOUT_{name.upper()}_S")
            )
            if v is not None:
                self.engine_timeout_s[name] = v

        # Bulkhead limits
        raw_global_limit = _first_env(
            "CRAWL4AI_MAX_CONCURRENT_SEARCHES",
            "MAX_CONCURRENT_SEARCHES",
        )
        parsed_global_limit = _parse_int_env(raw_global_limit) if raw_global_limit else None
        global_limit = 20 if parsed_global_limit is None else parsed_global_limit

        raw_per_engine_default = _first_env(
            "CRAWL4AI_MAX_CONCURRENT_PER_ENGINE",
            "MAX_CONCURRENT_PER_ENGINE",
        )
        parsed_per_engine_default = (
            _parse_int_env(raw_per_engine_default) if raw_per_engine_default else None
        )
        per_engine_default = 5 if parsed_per_engine_default is None else parsed_per_engine_default

        self._global_semaphore: Optional[asyncio.Semaphore] = (
            asyncio.Semaphore(global_limit) if global_limit > 0 else None
        )
        self._engine_semaphores: Dict[str, asyncio.Semaphore] = {}
        for name in ("google", "brave", "searxng", "duckduckgo"):
            raw_override = os.environ.get(f"CRAWL4AI_MAX_CONCURRENT_{name.upper()}")
            override = _parse_int_env(raw_override) if raw_override else None
            limit = per_engine_default if override is None else override
            if limit > 0:
                self._engine_semaphores[name] = asyncio.Semaphore(limit)

        # Request coalescing (in-flight dedup): reduce duplicated upstream calls
        # when multiple concurrent requests ask for the same (query, engine, num_results).
        coalesce_flag = _parse_bool_env(
            os.environ.get("CRAWL4AI_ENABLE_REQUEST_COALESCING")
            or os.environ.get("ENABLE_REQUEST_COALESCING")
        )
        self.enable_request_coalescing = (
            True if coalesce_flag is None else bool(coalesce_flag)
        )
        self._inflight_lock = asyncio.Lock()
        self._inflight_searches: Dict[tuple[str, str, int], asyncio.Task] = {}

        # Shared HTTP client pool (connection reuse) for httpx-based engines.
        self.http_client_pool = HttpClientPool()

        # Engine-level circuit breakers (optional)
        cb_flag = _parse_bool_env(
            os.environ.get("CRAWL4AI_ENGINE_CIRCUIT_BREAKER")
            or os.environ.get("ENGINE_CIRCUIT_BREAKER")
        )
        self.circuit_breaker_enabled = True if cb_flag is None else bool(cb_flag)

        def _cb_failure_threshold(engine_type: str) -> int:
            raw = (
                os.environ.get(f"CRAWL4AI_CB_FAILURE_THRESHOLD_{engine_type.upper()}")
                or os.environ.get("CRAWL4AI_CB_FAILURE_THRESHOLD")
            )
            v = _parse_int_env(raw) if raw is not None else None
            return max(1, v) if v is not None else 5

        def _cb_open_seconds(engine_type: str) -> float:
            raw = (
                os.environ.get(f"CRAWL4AI_CB_OPEN_SECONDS_{engine_type.upper()}")
                or os.environ.get("CRAWL4AI_CB_OPEN_SECONDS")
            )
            v = _parse_float_env(raw) if raw is not None else None
            return max(0.0, v) if v is not None else 30.0

        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        for name in ("google", "brave", "searxng", "duckduckgo"):
            cfg = CircuitBreakerConfig(
                enabled=self.circuit_breaker_enabled,
                failure_threshold=_cb_failure_threshold(name),
                open_seconds=_cb_open_seconds(name),
            )
            self._circuit_breakers[name] = CircuitBreaker(config=cfg)
        
        self._initialize_engines()

        if self.cache:
            logger.info(
                f"Search cache enabled: ttl={cache_ttl}s"
            )
        if self.rate_limiter:
            logger.info("API rate limiting enabled")
        if self.monitor:
            logger.info("Performance monitoring enabled")

        if self.circuit_breaker_enabled:
            logger.info(
                "Engine circuit breaker enabled: %s",
                {
                    k: (v._cfg.failure_threshold, v._cfg.open_seconds)
                    for k, v in self._circuit_breakers.items()
                },
            )

    async def aclose(self) -> None:
        """Close network resources held by this SearchManager."""
        try:
            await self.http_client_pool.aclose()
        except Exception:
            pass

    def _engine_timeout_budget(self, engine_type: str) -> Optional[float]:
        v = self.engine_timeout_s.get(engine_type)
        if v is not None:
            return v
        return self.engine_timeout_default_s

    @asynccontextmanager
    async def _bulkhead(
        self,
        engine_type: Optional[str] = None,
        *,
        use_global: bool = True,
        use_engine: bool = True,
    ):
        acquired: List[asyncio.Semaphore] = []
        try:
            if use_global and self._global_semaphore is not None:
                await self._global_semaphore.acquire()
                acquired.append(self._global_semaphore)
            if use_engine and engine_type:
                sem = self._engine_semaphores.get(engine_type)
                if sem is not None:
                    await sem.acquire()
                    acquired.append(sem)
            yield
        finally:
            for sem in reversed(acquired):
                try:
                    sem.release()
                except Exception:
                    pass

    def _initialize_engines(self):
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config.json'
        )
        config: Dict[str, Any] = {}
        proxy_from_config: Optional[str] = None

        def _extract_proxy(cfg: Dict) -> Optional[str]:
            proxy_cfg = cfg.get('proxy')
            if not proxy_cfg:
                return None
            if isinstance(proxy_cfg, str):
                return rewrite_local_proxy_url(proxy_cfg)
            if isinstance(proxy_cfg, dict):
                https_p = proxy_cfg.get('https')
                http_p = proxy_cfg.get('http')
                return rewrite_local_proxy_url(https_p or http_p)
            return None

        def _env_proxy_var(var_name: str) -> Optional[str]:
            value = os.environ.get(var_name)
            return rewrite_local_proxy_url(value)

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(
                    f"Failed to load search configuration: {e}"
                )
                config = {}

        proxy_from_config = _extract_proxy(config) if config else None

        # Brave Search
        brave_config = config.get('brave', {})
        brave_api_key = _resolve_secret(
            brave_config.get('api_key'),
            os.environ.get('BRAVE_API_KEY'),
        )
        if brave_api_key:
            brave_proxy = (
                _extract_proxy(brave_config) or
                _env_proxy_var('BRAVE_PROXY') or
                proxy_from_config
            )
            brave_engine = BraveSearch(
                api_key=brave_api_key,
                proxy=brave_proxy,
                client_pool=self.http_client_pool,
            )
            self.engines.append(brave_engine)
            logger.info("Brave Search engine initialized")

        # Google Search
        google_config = config.get('google', {})
        google_api_key = _resolve_secret(
            google_config.get('api_key'),
            os.environ.get('GOOGLE_API_KEY'),
        )
        google_cse_id = _resolve_secret(
            google_config.get('cse_id'),
            os.environ.get('GOOGLE_CSE_ID'),
        )
        if google_api_key and google_cse_id:
            google_proxy = (
                _extract_proxy(google_config) or
                _env_proxy_var('GOOGLE_PROXY') or
                proxy_from_config
            )
            google_engine = GoogleSearch(
                api_key=google_api_key,
                cse_id=google_cse_id,
                proxy=google_proxy,
                client_pool=self.http_client_pool,
            )
            self.engines.append(google_engine)
            self.fallback_engines.append(google_engine)
            logger.info("Google search engine initialized")

        # SearXNG Search (only if configured via file or env)
        searxng_config = config.get('searxng', {})
        env_searx_base = os.environ.get('SEARXNG_BASE_URL')
        if searxng_config or env_searx_base:
            base_url = (
                env_searx_base or
                searxng_config.get('base_url') or
                'http://localhost:28981'
            )
            language = (
                searxng_config.get('language') or
                os.environ.get('SEARXNG_LANGUAGE') or
                'zh-CN'
            )
            searxng_proxy = (
                _extract_proxy(searxng_config) or
                _env_proxy_var('SEARXNG_PROXY') or
                proxy_from_config
            )
            searxng_engine = SearXNGSearch(
                base_url=base_url,
                language=language,
                proxy=searxng_proxy,
                client_pool=self.http_client_pool,
            )
            self.engines.append(searxng_engine)
            self.fallback_engines.append(searxng_engine)
            logger.info(
                f"SearXNG search engine initialized: {base_url}"
            )

        # Always ensure DuckDuckGo is available as fallback
        duckduckgo_config = config.get('duckduckgo', {})
        ddg_proxy = (
            _extract_proxy(duckduckgo_config) or
            _env_proxy_var('DUCKDUCKGO_PROXY') or
            proxy_from_config
        )

        ddg_region = (
            duckduckgo_config.get('region') or
            os.environ.get('DDG_REGION') or
            os.environ.get('DDGS_REGION') or
            os.environ.get('DUCKDUCKGO_REGION')
        )
        ddg_backend = (
            duckduckgo_config.get('ddgs_backend') or
            duckduckgo_config.get('text_backend') or
            duckduckgo_config.get('backend') or
            os.environ.get('DDGS_TEXT_BACKEND') or
            os.environ.get('DDG_BACKEND') or
            os.environ.get('DDGS_BACKEND')
        )

        def _parse_bool(value: Any) -> Optional[bool]:
            if value is None:
                return None
            if isinstance(value, bool):
                return value
            if not isinstance(value, str):
                return None
            v = value.strip().lower()
            if v in {"1", "true", "yes", "y", "on"}:
                return True
            if v in {"0", "false", "no", "n", "off"}:
                return False
            return None

        ddg_include_wikipedia = _parse_bool(
            duckduckgo_config.get('include_wikipedia')
        )
        if ddg_include_wikipedia is None:
            ddg_include_wikipedia = _parse_bool(
                os.environ.get('DDG_INCLUDE_WIKIPEDIA') or
                os.environ.get('DDGS_INCLUDE_WIKIPEDIA')
            )

        # ddgs fetch pool tuning (quality vs latency)
        ddg_fetch_k = None
        for k in ('fetch_k', 'fetch_results', 'max_fetch_results'):
            if k in duckduckgo_config:
                try:
                    ddg_fetch_k = int(duckduckgo_config.get(k))
                except Exception:
                    ddg_fetch_k = None
                break
        if ddg_fetch_k is None:
            env_fetch_k = os.environ.get('DDG_FETCH_K') or os.environ.get('DDGS_FETCH_K')
            try:
                ddg_fetch_k = int(env_fetch_k) if env_fetch_k else None
            except Exception:
                ddg_fetch_k = None

        duckduckgo = DuckDuckGoSearch(
            proxy=ddg_proxy,
            region=ddg_region,
            backend=ddg_backend,
            include_wikipedia=ddg_include_wikipedia,
            fetch_k=ddg_fetch_k,
        )
        # Put DuckDuckGo as lowest-priority fallback engine
        self.fallback_engines.append(duckduckgo)
        if not self.engines:
            self.engines.append(duckduckgo)
            logger.info(
                "No engines configured, using DuckDuckGo as default"
            )

    # Note: We don't inject env proxy globally to preserve direct-first
    # policy. Engines will try direct calls first and only use configured
    # proxies (config.json/env) or rewrites on network failure.
                
    async def _search_impl(
        self,
        query: str,
        num_results: int = 10,
        engine: str = "auto",
    ) -> tuple[List[Dict], Optional[str]]:
        """
        执行搜索（不处理 cache hit 与 in-flight coalescing）。

        返回 (results, error_msg)。results 为 List[Dict]。

        Args:
            query: 搜索查询字符串
            num_results: 返回结果数量
            engine: 搜索引擎选择 (auto/brave/google/duckduckgo/searxng/all)
                   - auto: 自动选择，优先使用配置的引擎，失败时自动回退
                   - brave/google/duckduckgo/searxng: 使用指定引擎
                   - all: 使用所有可用引擎，自动去重和排序

        Returns:
            (搜索结果列表, 错误信息)
        """
        error_msg = None

        all_results: List[Dict] = []

        if not self.engines and not self.fallback_engines:
            logger.warning("No search engines available")
            error_msg = "No search engines available"

            return [], error_msg

        logger.info(
            f"Starting search with query: {query}, "
            f"engine: {engine}, num_results: {num_results}"
        )
        
        # 确定要使用的引擎列表
        engines_to_try = []

        if engine.lower() == "all":
            # 使用所有可用的引擎
            all_engines = self.engines + [
                e for e in self.fallback_engines
                if e not in self.engines
            ]
            engines_to_try = all_engines
        elif engine.lower() == "auto":
            # 自动模式：优先使用配置的引擎，失败时自动回退到 fallback_engines
            # 重要：fallback_engines 通常包含 DuckDuckGo 等“兜底”引擎。
            # 如果只尝试 self.engines（例如 Brave/Google/SearXNG），在这些
            # 引擎不可用/返回空结果时会导致整体返回空，违背“自动回退”语义。
            if self.engines:
                engines_to_try = self.engines + [
                    e for e in self.fallback_engines
                    if e not in self.engines
                ]
            else:
                engines_to_try = self.fallback_engines
        else:
            # 指定引擎模式
            for search_engine in self.engines + self.fallback_engines:
                engine_name = search_engine.__class__.__name__.lower()
                if engine_name.startswith('brave'):
                    engine_type = 'brave'
                elif engine_name.startswith('duckduckgo'):
                    engine_type = 'duckduckgo'
                elif engine_name.startswith('google'):
                    engine_type = 'google'
                elif engine_name.startswith('searxng'):
                    engine_type = 'searxng'
                else:
                    engine_type = engine_name

                if engine_type == engine.lower():
                    engines_to_try = [search_engine]
                    break

        # 如果没有找到指定的引擎，使用回退引擎
        if not engines_to_try and engine.lower() not in ["all", "auto"]:
            logger.warning(
                f"Requested engine '{engine}' not available, "
                f"using fallback engines"
            )
            engines_to_try = self.fallback_engines

        # 用于收集所有引擎的结果（all 模式）
        all_engine_results = {}

        # auto 模式质量增强（可选）：即使第一个引擎“够数”，也会再尝试
        # 若干个引擎并做 merge+去重+优先级排序，以避免单一引擎在某些网络/区域
        # 环境下返回“看似正常但质量很差”的结果。
        auto_merge_enabled = False
        auto_merge_min_engines = 2
        auto_merge_max_engines = 3
        if engine.lower() == "auto":
            v = os.environ.get("CRAWL4AI_AUTO_MERGE", "0").strip().lower()
            auto_merge_enabled = v in {"1", "true", "yes", "y", "on"}
            try:
                auto_merge_min_engines = int(
                    os.environ.get("CRAWL4AI_AUTO_MERGE_MIN_ENGINES", "2")
                )
            except Exception:
                auto_merge_min_engines = 2
            try:
                auto_merge_max_engines = int(
                    os.environ.get("CRAWL4AI_AUTO_MERGE_MAX_ENGINES", "3")
                )
            except Exception:
                auto_merge_max_engines = 3
            auto_merge_min_engines = max(1, auto_merge_min_engines)
            auto_merge_max_engines = max(auto_merge_min_engines, auto_merge_max_engines)

        # Merge/fusion strategy for multi-engine modes.
        # Default to RRF when merging results from multiple engines.
        fusion_method = (os.environ.get("CRAWL4AI_FUSION_METHOD") or "").strip().lower()
        if not fusion_method:
            fusion_method = "rrf"
        try:
            rrf_k = int(os.environ.get("CRAWL4AI_RRF_K", "60"))
        except Exception:
            rrf_k = 60
        engine_weights: Optional[Dict[str, float]] = None
        raw_weights = (os.environ.get("CRAWL4AI_RRF_ENGINE_WEIGHTS") or "").strip()
        if raw_weights:
            try:
                if raw_weights.lstrip().startswith("{"):
                    parsed = json.loads(raw_weights)
                    if isinstance(parsed, dict):
                        engine_weights = {
                            str(k).lower(): float(v)
                            for k, v in parsed.items()
                        }
                else:
                    # Format: google=1.0,brave=0.8,searxng=0.7,duckduckgo=0.4
                    engine_weights = {}
                    for part in raw_weights.split(","):
                        part = part.strip()
                        if not part or "=" not in part:
                            continue
                        k, v = part.split("=", 1)
                        engine_weights[str(k).strip().lower()] = float(v)
            except Exception:
                engine_weights = None
        
        # all 模式：使用并发搜索
        if engine.lower() == "all":
            logger.info(
                f"Starting concurrent search with {len(engines_to_try)} "
                f"engines"
            )
            early_return = (
                os.environ.get("CRAWL4AI_ALL_EARLY_RETURN", "0")
                .strip().lower() in {"1", "true", "yes", "y", "on"}
            )
            try:
                min_engines = int(
                    os.environ.get("CRAWL4AI_ALL_EARLY_RETURN_MIN_ENGINES", "1")
                )
            except Exception:
                min_engines = 1
            try:
                grace_s = float(
                    os.environ.get("CRAWL4AI_ALL_EARLY_RETURN_GRACE_S", "0")
                )
            except Exception:
                grace_s = 0.0

            if early_return:
                all_engine_results = await self._concurrent_search_early_return(
                    engines_to_try,
                    query,
                    num_results,
                    min_engines=max(1, min_engines),
                    grace_s=max(0.0, grace_s),
                    fusion_method=fusion_method,
                    rrf_k=rrf_k,
                    engine_weights=engine_weights,
                )
            else:
                all_engine_results = await self._concurrent_search(
                    engines_to_try, query, num_results
                )
        else:
            # auto 或指定引擎模式：串行搜索（支持早停）
            engines_tried = 0

            # Optional: concurrent auto-merge to reduce tail latency.
            auto_merge_concurrent = False
            auto_merge_early_return = True
            if engine.lower() == "auto" and auto_merge_enabled:
                v = os.environ.get("CRAWL4AI_AUTO_MERGE_CONCURRENT", "0").strip().lower()
                auto_merge_concurrent = v in {"1", "true", "yes", "y", "on"}
                v2 = os.environ.get("CRAWL4AI_AUTO_MERGE_EARLY_RETURN", "1").strip().lower()
                auto_merge_early_return = v2 in {"1", "true", "yes", "y", "on"}

            if engine.lower() == "auto" and auto_merge_enabled and auto_merge_concurrent:
                # Take up to max_engines candidates and run concurrently.
                candidates = engines_to_try[:auto_merge_max_engines]
                all_engine_results = await self._concurrent_search_early_return(
                    candidates,
                    query,
                    num_results,
                    min_engines=max(1, auto_merge_min_engines),
                    grace_s=0.2 if auto_merge_early_return else 0.0,
                    fusion_method=fusion_method,
                    rrf_k=rrf_k,
                    engine_weights=engine_weights,
                )
                # Mark results as collected for later merge.
                for _eng, _res in all_engine_results.items():
                    all_results.extend(_res)
            else:
                for search_engine in engines_to_try:
                    engine_name = search_engine.__class__.__name__
                    engine_type = self._get_engine_type(search_engine)
                    engines_tried += 1

                    # Circuit breaker: fail fast when an engine is OPEN.
                    breaker = self._circuit_breakers.get(engine_type)
                    if breaker is not None:
                        allowed, retry_after = await breaker.allow()
                        if not allowed:
                            logger.warning(
                                "Circuit open for engine %s; skipping (retry_after=%.2fs)",
                                engine_type,
                                float(retry_after or 0.0),
                            )
                            error_msg = f"{engine_type}: circuit_open"
                            continue

                    try:
                        # 检查限流
                        if self.rate_limiter:
                            await self.rate_limiter.acquire(engine_type)

                        timeout_budget = self._engine_timeout_budget(engine_type)
                        async with self._bulkhead(
                            engine_type, use_global=False, use_engine=True
                        ):
                            # 执行搜索（自动重试）
                            if timeout_budget is not None:
                                results = await asyncio.wait_for(
                                    self._search_with_retry(
                                        search_engine, query, num_results
                                    ),
                                    timeout=timeout_budget,
                                )
                            else:
                                results = await self._search_with_retry(
                                    search_engine, query, num_results
                                )

                        if breaker is not None:
                            await breaker.record_success()
                        
                        logger.info(
                            f"Got {len(results)} results from {engine_name}"
                        )

                        if results:
                            converted_results = [r.to_dict() for r in results]
                            
                            # 为结果添加引擎标识
                            for result in converted_results:
                                if 'engine' not in result:
                                    result['engine'] = engine_type
                            
                            all_results.extend(converted_results)

                            # auto merge 需要保留按引擎分组的结果以便后续 merge/sort
                            if engine.lower() == "auto" and auto_merge_enabled:
                                all_engine_results[engine_type] = converted_results

                            # auto 模式：默认行为是“够数就停”。若开启 auto_merge，
                            # 会尝试更多引擎以提升质量（仍有上限）。
                            auto_mode = engine.lower() == "auto"
                            enough_results = len(all_results) >= num_results
                            if auto_mode and enough_results:
                                if auto_merge_enabled:
                                    # 尝试至少 min_engines 个引擎；到达 max_engines 或
                                    # 已满足 min_engines 后即可停止。
                                    if (
                                        engines_tried >= auto_merge_max_engines
                                        or engines_tried >= auto_merge_min_engines
                                    ):
                                        logger.info(
                                            "Auto merge: enough results after %s engine(s); "
                                            "stopping",
                                            engines_tried,
                                        )
                                        break
                                else:
                                    logger.info(
                                        f"Got enough results from {engine_name}, "
                                        f"stopping"
                                    )
                                    break
                        else:
                            logger.warning(
                                f"No results from {engine_name}, "
                                f"trying next engine"
                            )

                        # auto merge: 达到引擎尝试上限时提前结束
                        if engine.lower() == "auto" and auto_merge_enabled:
                            if engines_tried >= auto_merge_max_engines:
                                logger.info(
                                    "Auto merge: reached max engines (%s); stopping",
                                    auto_merge_max_engines,
                                )
                                break

                    except Exception as e:
                        if breaker is not None:
                            try:
                                await breaker.record_failure()
                            except Exception:
                                pass
                        logger.error(
                            f"Search failed for {engine_name}: {str(e)}",
                            exc_info=True
                        )
                        error_msg = str(e)
                        # 继续尝试下一个引擎
                        if engine.lower() == "auto":
                            logger.info(
                                f"Trying fallback engines due to "
                                f"{engine_name} failure"
                            )

        # 处理 all 模式：合并去重和排序
        if engine.lower() == "all":
            if all_engine_results:
                logger.info(
                    f"Merging results from {len(all_engine_results)} engines"
                )
                all_results = merge_and_deduplicate(
                    all_engine_results,
                    num_results=num_results,
                    fusion_method=fusion_method,
                    rrf_k=rrf_k,
                    engine_weights=engine_weights,
                    canonicalize_links=True,
                )
            else:
                logger.warning("No results from any engine in all mode")
                all_results = []
        elif engine.lower() != "all":
            if engine.lower() == "auto" and auto_merge_enabled:
                if all_engine_results:
                    logger.info(
                        "Auto merge enabled: merging results from %s engine(s)",
                        len(all_engine_results),
                    )
                    all_results = merge_and_deduplicate(
                        all_engine_results,
                        num_results=num_results,
                        fusion_method=fusion_method,
                        rrf_k=rrf_k,
                        engine_weights=engine_weights,
                        canonicalize_links=True,
                    )
                else:
                    all_results = []
            else:
                # 非 all 模式：简单截取
                final_results = all_results[:num_results]
                all_results = final_results
        
        # 缓存结果
        if self.cache and all_results:
            self.cache.set(query, engine, num_results, all_results)

        return all_results, error_msg

    async def _concurrent_search_early_return(
        self,
        engines: List[SearchEngine],
        query: str,
        num_results: int,
        *,
        min_engines: int = 1,
        grace_s: float = 0.0,
        fusion_method: str = "priority",
        rrf_k: int = 60,
        engine_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, List[Dict]]:
        """Concurrent search with incremental merge and early return.

        Once we have enough merged results (>= num_results) and at least
        min_engines engines returned non-empty results, we will wait an optional
        grace period and then cancel remaining engine tasks.
        """

        tasks: List[asyncio.Task] = []
        for eng in engines:
            tasks.append(
                asyncio.create_task(self._search_single_engine(eng, query, num_results))
            )

        all_engine_results: Dict[str, List[Dict]] = {}
        succeeded = 0

        async def _merged_len() -> int:
            if not all_engine_results:
                return 0
            merged = merge_and_deduplicate(
                all_engine_results,
                num_results=num_results,
                fusion_method=fusion_method,
                rrf_k=rrf_k,
                engine_weights=engine_weights,
                canonicalize_links=True,
            )
            return len(merged)

        pending: set[asyncio.Future[Any]] = set(tasks)
        try:
            for fut in asyncio.as_completed(tasks):
                try:
                    result = await fut
                except asyncio.CancelledError:
                    continue
                except Exception as e:
                    logger.error("Concurrent engine task failed: %s", str(e))
                    continue

                engine_type, engine_results, error = result
                if error:
                    logger.warning(
                        "Engine %s failed during concurrent search: %s",
                        engine_type,
                        error,
                    )
                if engine_results:
                    all_engine_results[engine_type] = engine_results
                    succeeded += 1

                pending.discard(fut)

                if succeeded >= max(1, min_engines):
                    try:
                        if await _merged_len() >= num_results:
                            # Optionally wait a bit for other tasks to finish.
                            if grace_s > 0 and pending:
                                done, still = await asyncio.wait(
                                    pending,
                                    timeout=grace_s,
                                    return_when=asyncio.ALL_COMPLETED,
                                )
                                for d in done:
                                    try:
                                        r = d.result()
                                    except Exception:
                                        continue
                                    et, er, _err = r
                                    if er:
                                        all_engine_results[et] = er
                                pending = still

                            # Cancel remaining.
                            for t in pending:
                                try:
                                    t.cancel()
                                except Exception:
                                    pass
                            break
                    except Exception:
                        # If merge fails, keep collecting.
                        pass
        finally:
            # Ensure no pending tasks leak.
            for t in pending:
                try:
                    t.cancel()
                except Exception:
                    pass
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

        logger.info(
            "Concurrent early-return completed: %s/%s engines succeeded",
            len(all_engine_results),
            len(engines),
        )
        return all_engine_results

    async def _coalesced_task(
        self,
        inflight_key: tuple[str, str, int],
        query: str,
        num_results: int,
        engine: str,
    ) -> tuple[List[Dict], Optional[str]]:
        """Run a single search computation and clean up inflight registry."""
        try:
            async with self._bulkhead(None, use_global=True, use_engine=False):
                if self.search_deadline_s is not None:
                    try:
                        async with asyncio.timeout(self.search_deadline_s):
                            return await self._search_impl(
                                query, num_results=num_results, engine=engine
                            )
                    except TimeoutError:
                        return [], "Search deadline exceeded"
                return await self._search_impl(
                    query, num_results=num_results, engine=engine
                )
        except Exception as e:
            logger.error("Search task failed: %s", str(e), exc_info=True)
            return [], str(e)
        finally:
            try:
                me = asyncio.current_task()
                async with self._inflight_lock:
                    if self._inflight_searches.get(inflight_key) is me:
                        del self._inflight_searches[inflight_key]
            except Exception:
                pass

    async def search(
        self,
        query: str,
        num_results: int = 10,
        engine: str = "auto",
    ) -> List[Dict]:
        """Public search API with cache + request coalescing + monitoring."""
        start_time = time.time()

        # Cache hit (fast path)
        if self.cache:
            cached_results = self.cache.get(query, engine, num_results)
            if cached_results is not None:
                logger.info("Returning cached results")
                if self.monitor:
                    metrics = SearchMetrics(
                        query=query,
                        engine=engine,
                        start_time=start_time,
                        end_time=time.time(),
                        request_id=get_request_id(),
                        success=True,
                        cached=True,
                        num_results=len(cached_results),
                        coalesced=False,
                    )
                    self.monitor.record_search(metrics)
                return cached_results

        # Request coalescing (in-flight dedup)
        inflight_key = (query, engine, int(num_results))
        coalesced = False
        task: Optional[asyncio.Task] = None

        if self.enable_request_coalescing:
            async with self._inflight_lock:
                task = self._inflight_searches.get(inflight_key)
                if task is None:
                    task = asyncio.create_task(
                        self._coalesced_task(
                            inflight_key, query, int(num_results), engine
                        )
                    )
                    self._inflight_searches[inflight_key] = task
                else:
                    coalesced = True

        if not self.enable_request_coalescing:
            # Fall back to direct execution
            task = asyncio.create_task(
                self._coalesced_task(inflight_key, query, int(num_results), engine)
            )

        # Await shared computation. Shield to prevent one cancelled caller from
        # cancelling the shared in-flight task.
        assert task is not None
        results, error_msg = await asyncio.shield(task)
        success = len(results) > 0

        if self.monitor:
            metrics = SearchMetrics(
                query=query,
                engine=engine,
                start_time=start_time,
                end_time=time.time(),
                request_id=get_request_id(),
                success=success,
                cached=False,
                num_results=len(results),
                error=error_msg if not success else None,
                coalesced=coalesced,
            )
            self.monitor.record_search(metrics)

        # Return a shallow copy to reduce accidental cross-request mutation.
        return list(results)
    
    def _get_engine_type(self, search_engine: SearchEngine) -> str:
        """
        获取引擎类型标识
        
        Args:
            search_engine: 搜索引擎实例
            
        Returns:
            引擎类型字符串
        """
        engine_name = search_engine.__class__.__name__.lower()
        
        if 'brave' in engine_name:
            return 'brave'
        elif 'duckduckgo' in engine_name:
            return 'duckduckgo'
        elif 'google' in engine_name:
            return 'google'
        elif 'searxng' in engine_name:
            return 'searxng'
        else:
            return engine_name
    
    async def _search_single_engine(
        self,
        search_engine: SearchEngine,
        query: str,
        num_results: int
    ) -> tuple[str, List[Dict], Optional[str]]:
        """
        搜索单个引擎（用于并发搜索）
        
        Args:
            search_engine: 搜索引擎实例
            query: 搜索查询
            num_results: 结果数量
            
        Returns:
            (engine_type, results, error_message)
        """
        engine_name = search_engine.__class__.__name__
        engine_type = self._get_engine_type(search_engine)

        breaker = self._circuit_breakers.get(engine_type)
        
        try:
            # Circuit breaker: fail fast when an engine is OPEN.
            if breaker is not None:
                allowed, retry_after = await breaker.allow()
                if not allowed:
                    logger.warning(
                        "Circuit open for engine %s; skipping (retry_after=%.2fs)",
                        engine_type,
                        float(retry_after or 0.0),
                    )
                    return engine_type, [], f"{engine_type}: circuit_open"

            # 检查限流
            if self.rate_limiter:
                await self.rate_limiter.acquire(engine_type)

            timeout_budget = self._engine_timeout_budget(engine_type)
            async with self._bulkhead(engine_type, use_global=False, use_engine=True):
                # 执行搜索（自动重试）
                if timeout_budget is not None:
                    results = await asyncio.wait_for(
                        self._search_with_retry(search_engine, query, num_results),
                        timeout=timeout_budget,
                    )
                else:
                    results = await self._search_with_retry(
                        search_engine, query, num_results
                    )

            if breaker is not None:
                await breaker.record_success()
            
            logger.info(
                f"Got {len(results)} results from {engine_name}"
            )
            
            if results:
                converted_results = [r.to_dict() for r in results]
                
                # 为结果添加引擎标识
                for result in converted_results:
                    if 'engine' not in result:
                        result['engine'] = engine_type
                
                return engine_type, converted_results, None
            else:
                logger.warning(f"No results from {engine_name}")
                return engine_type, [], None
                
        except Exception as e:
            if breaker is not None:
                try:
                    await breaker.record_failure()
                except Exception:
                    pass
            logger.error(
                f"Search failed for {engine_name}: {str(e)}",
                exc_info=True
            )
            return engine_type, [], str(e)
    
    async def _concurrent_search(
        self,
        engines: List[SearchEngine],
        query: str,
        num_results: int
    ) -> Dict[str, List[Dict]]:
        """
        并发搜索多个引擎
        
        Args:
            engines: 搜索引擎列表
            query: 搜索查询
            num_results: 每个引擎的结果数量
            
        Returns:
            {engine_type: [results]} 字典
        """
        # 创建并发任务
        tasks = [
            self._search_single_engine(engine, query, num_results)
            for engine in engines
        ]
        
        # 并发执行所有搜索
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集结果
        all_engine_results = {}
        errors = []
        
        for result in results:
            # asyncio.gather(return_exceptions=True) may yield BaseException
            # instances (e.g. CancelledError in newer Python versions).
            if isinstance(result, BaseException):
                logger.error(f"Concurrent search task failed: {result}")
                errors.append(str(result))
            else:
                engine_type, engine_results, error = result
                if error:
                    errors.append(f"{engine_type}: {error}")
                if engine_results:
                    all_engine_results[engine_type] = engine_results
        
        if errors:
            logger.warning(
                f"Some engines failed during concurrent search: "
                f"{', '.join(errors)}"
            )
        
        logger.info(
            f"Concurrent search completed: "
            f"{len(all_engine_results)}/{len(engines)} engines succeeded"
        )
        
        return all_engine_results
    
    async def _search_with_retry(
        self,
        search_engine: SearchEngine,
        query: str,
        num_results: int
    ) -> List[SearchResult]:
        """
        带重试机制的搜索
        
        Args:
            search_engine: 搜索引擎实例
            query: 搜索查询
            num_results: 结果数量
            
        Returns:
            搜索结果列表
        """
        max_attempts = 3
        delay_s = 1.0
        exponential_base = 2.0

        last_exc: Optional[BaseException] = None
        for attempt in range(1, max_attempts + 1):
            try:
                return await search_engine.search(query, num_results)
            except EngineSearchError as e:
                last_exc = e
                if (not e.retriable) or attempt >= max_attempts:
                    raise
                logger.warning(
                    "Retriable engine error (attempt %s/%s): %s",
                    attempt,
                    max_attempts,
                    str(e),
                )
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exc = e
                if attempt >= max_attempts:
                    raise
                logger.warning(
                    "Transient HTTP error (attempt %s/%s): %s",
                    attempt,
                    max_attempts,
                    str(e),
                )
            except Exception as e:
                # Default: do not retry unknown exceptions.
                last_exc = e
                raise

            await asyncio.sleep(delay_s)
            delay_s *= exponential_base

        # Should be unreachable, but keeps type-checkers happy.
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("search_with_retry reached unexpected state")

    def get_cache_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典，如果缓存未启用则返回空字典
        """
        if self.cache:
            return self.cache.get_stats()
        return {}

    def clear_cache(self) -> None:
        """清空搜索缓存"""
        if self.cache:
            self.cache.clear()

    def export_cache(self, filepath: str) -> None:
        """
        导出缓存到文件

        Args:
            filepath: 导出文件路径
        """
        if self.cache:
            self.cache.export_to_file(filepath)

    def import_cache(self, filepath: str) -> int:
        """
        从文件导入缓存

        Args:
            filepath: 导入文件路径

        Returns:
            导入的条目数
        """
        if self.cache:
            return self.cache.import_from_file(filepath)
        return 0
    
    def get_rate_limit_status(self) -> Dict:
        """
        获取所有引擎的限流状态
        
        Returns:
            限流状态字典，如果限流未启用则返回空字典
        """
        if self.rate_limiter:
            return self.rate_limiter.get_all_status()
        return {}
    
    def get_performance_stats(
        self,
        engine: Optional[str] = None
    ) -> Dict:
        """
        获取性能统计信息
        
        Args:
            engine: 引擎名（可选，None 表示所有引擎）
            
        Returns:
            性能统计字典
        """
        if self.monitor:
            if engine:
                return self.monitor.get_engine_stats(engine)
            else:
                return self.monitor.get_overall_stats()
        return {}
    
    def get_engine_stats(self, engine: Optional[str] = None) -> Dict:
        """
        获取引擎级别的统计信息
        
        Args:
            engine: 引擎名（可选）
            
        Returns:
            引擎统计字典
        """
        if self.monitor:
            return self.monitor.get_engine_stats(engine)
        return {}
    
    def export_performance_report(self, filepath: str) -> None:
        """
        导出性能报告到文件
        
        Args:
            filepath: 输出文件路径
        """
        if self.monitor:
            self.monitor.export_report(filepath)
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """
        获取最近的搜索记录
        
        Args:
            limit: 返回的记录数量
            
        Returns:
            最近搜索列表
        """
        if self.monitor:
            return self.monitor.get_recent_searches(limit)
        return []
