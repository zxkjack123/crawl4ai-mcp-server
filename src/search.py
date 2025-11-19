from typing import List, Dict, Optional, Any
import inspect
import asyncio
import httpx
import json
import os
import logging
import time
from abc import ABC, abstractmethod
# Prefer the new 'ddgs' package and fall back to the legacy name if needed
try:
    from ddgs import DDGS  # new package name (no deprecation warning)
except Exception:  # pragma: no cover - fallback for environments without ddgs
    from duckduckgo_search import DDGS  # legacy package name

# Use relative import or direct import depending on context
try:
    from .cache import SearchCache
    from .utils import (
        async_retry, MultiRateLimiter,
        merge_and_deduplicate,
        rewrite_local_proxy_url
    )
    from .monitor import (
        SearchMetrics, get_monitor
    )
except ImportError:
    from cache import SearchCache
    from utils import (
        async_retry, MultiRateLimiter,
        merge_and_deduplicate,
        rewrite_local_proxy_url
    )
    from monitor import (
        SearchMetrics, get_monitor
    )

logger = logging.getLogger(__name__)


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
    def __init__(self, proxy: Optional[str] = None):
        self.ddgs = DDGS()
        self.proxy = proxy

    async def search(
        self, query: str, num_results: int = 10
    ) -> List[SearchResult]:
        def _env_proxy() -> Optional[str]:
            https_proxy = (
                os.environ.get('HTTPS_PROXY') or
                os.environ.get('https_proxy')
            )
            http_proxy = (
                os.environ.get('HTTP_PROXY') or
                os.environ.get('http_proxy')
            )
            for p in (https_proxy, http_proxy):
                if p and (
                    p.startswith('http://') or
                    p.startswith('https://')
                ):
                    return rewrite_local_proxy_url(p)
            return None

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

        # 1) direct attempt
        try:
            raw_results = self.ddgs.text(
                query,
                region="wt-wt",
                safesearch="moderate",
                max_results=num_results
            )
            results = _collect(raw_results)
            if results:
                logger.info(
                    f"DuckDuckGo search successful for query: {query}"
                )
                return results
        except Exception as e:
            logger.warning(
                "DuckDuckGo direct search failed: %s", str(e)
            )

        # 2) retry via configured proxy
        proxy_to_use = self.proxy or _env_proxy()
        if proxy_to_use:
            try:
                ddgs_proxy = _new_ddgs_with_proxy(proxy_to_use)
                if ddgs_proxy is not None:
                    raw_results = ddgs_proxy.text(
                        query,
                        region="wt-wt",
                        safesearch="moderate",
                        max_results=num_results
                    )
                    results = _collect(raw_results)
                    if results:
                        logger.info(
                            "DuckDuckGo search via proxy successful for "
                            "query: %s", query
                        )
                        return results
            except Exception as e:
                logger.error(
                    "DuckDuckGo search via proxy failed: %s", str(e)
                )

        # 3) give up
        logger.warning("DuckDuckGo returned no results for query: %s", query)
        return []


class GoogleSearch(SearchEngine):
    def __init__(self, api_key: str, cse_id: str, proxy: Optional[str] = None):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        # Optional proxy URL from config.json (has priority over env)
        self.proxy = proxy

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
            async with httpx.AsyncClient(
                timeout=30.0, proxy=proxy_url, trust_env=False
            ) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                return response.json()

        def _env_proxy() -> Optional[str]:
            https_proxy = (
                os.environ.get('HTTPS_PROXY') or
                os.environ.get('https_proxy')
            )
            http_proxy = (
                os.environ.get('HTTP_PROXY') or
                os.environ.get('http_proxy')
            )
            for p in (https_proxy, http_proxy):
                if p and (p.startswith('http://') or p.startswith('https://')):
                    return rewrite_local_proxy_url(p)
            return None

        try:
            logger.info(f"Sending Google request (direct): {query}")
            data = await _request_with_proxy(None)
        except (httpx.RequestError, httpx.TimeoutException) as e:
            if self.proxy:
                logger.warning(
                    "Direct Google request failed (%s); retrying via proxy",
                    e.__class__.__name__
                )
                try:
                    data = await _request_with_proxy(self.proxy)
                except Exception as e2:
                    logger.error(f"Google search failed via proxy: {str(e2)}")
                    return []
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
                        return []
                else:
                    logger.error(
                        "Google search failed (no proxy configured): %s",
                        str(e)
                    )
                    return []
        except httpx.HTTPStatusError as e:
            # HTTP errors like 4xx/5xx won't be fixed by proxy; don't retry
            logger.error(
                "Google search HTTP error: %s - %s",
                e.response.status_code,
                e.response.text[:200]
            )
            return []
        except Exception as e:
            logger.error(f"Google search failed: {str(e)}")
            return []

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
    def __init__(self, api_key: str, proxy: Optional[str] = None):
        """
        初始化 Brave Search 搜索引擎

        Args:
            api_key: Brave Search API 密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.proxy = proxy

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
                async with httpx.AsyncClient(
                    timeout=30.0, proxy=proxy_url, trust_env=False
                ) as client:
                    return await client.get(
                        self.base_url, headers=headers, params=params
                    )

            def _env_proxy() -> Optional[str]:
                https_proxy = (
                    os.environ.get('HTTPS_PROXY') or
                    os.environ.get('https_proxy')
                )
                http_proxy = (
                    os.environ.get('HTTP_PROXY') or
                    os.environ.get('http_proxy')
                )
                for p in (https_proxy, http_proxy):
                    if p and (
                        p.startswith('http://') or
                        p.startswith('https://')
                    ):
                        return rewrite_local_proxy_url(p)
                return None

            logger.info(f"Sending request to Brave Search (direct): {query}")
            try:
                response = await _do_request(None)
            except (httpx.RequestError, httpx.TimeoutException) as e:
                if self.proxy:
                    logger.warning(
                        "Direct Brave request failed (%s); "
                        "retrying via proxy",
                        e.__class__.__name__
                    )
                    response = await _do_request(self.proxy)
                else:
                    env_p = _env_proxy()
                    if env_p:
                        logger.warning(
                            "Direct Brave request failed (%s); "
                            "retrying via env proxy",
                            e.__class__.__name__
                        )
                        response = await _do_request(env_p)
                    else:
                        raise

            response.raise_for_status()
            data = response.json()

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
            return []
        except Exception as e:
            logger.error(f"Brave Search failed: {str(e)}")
            return []


class SearXNGSearch(SearchEngine):
    def __init__(
        self,
        base_url: str = "http://localhost:28981",
        language: str = "zh-CN",
        proxy: Optional[str] = None
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
                async with httpx.AsyncClient(
                    timeout=30.0, proxy=proxy_url, trust_env=False
                ) as client:
                    return await client.get(
                        search_url,
                        params=params,
                        headers=default_headers
                    )

            def _env_proxy() -> Optional[str]:
                https_proxy = (
                    os.environ.get('HTTPS_PROXY') or
                    os.environ.get('https_proxy')
                )
                http_proxy = (
                    os.environ.get('HTTP_PROXY') or
                    os.environ.get('http_proxy')
                )
                for p in (https_proxy, http_proxy):
                    if p and (
                        p.startswith('http://') or
                        p.startswith('https://')
                    ):
                        return rewrite_local_proxy_url(p)
                return None

            try:
                response = await _do_request(None)
            except (httpx.RequestError, httpx.TimeoutException) as e:
                if self.proxy:
                    logger.warning(
                        "Direct SearXNG request failed (%s); "
                        "retrying via proxy",
                        e.__class__.__name__
                    )
                    response = await _do_request(self.proxy)
                else:
                    env_p = _env_proxy()
                    if env_p:
                        logger.warning(
                            "Direct SearXNG request failed (%s); "
                            "retrying via env proxy",
                            e.__class__.__name__
                        )
                        response = await _do_request(env_p)
                    else:
                        raise

            response.raise_for_status()
            data = response.json()

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

        except httpx.HTTPError as e:
            logger.error(f"SearXNG HTTP error: {str(e)}")
            logger.warning(
                "如果 SearXNG 未运行，请使用 "
                "'docker run -d -p 28981:8080 searxng/searxng' 启动"
            )
            return []
        except Exception as e:
            logger.error(f"SearXNG search failed: {str(e)}")
            return []


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
        self.cache = SearchCache(ttl=cache_ttl) if enable_cache else None
        
        # 初始化限流器
        self.enable_rate_limit = enable_rate_limit
        self.rate_limiter = MultiRateLimiter() if enable_rate_limit else None
        
        # 初始化监控
        self.enable_monitoring = enable_monitoring
        self.monitor = get_monitor() if enable_monitoring else None
        
        self._initialize_engines()

        if self.cache:
            logger.info(
                f"Search cache enabled: ttl={cache_ttl}s"
            )
        if self.rate_limiter:
            logger.info("API rate limiting enabled")
        if self.monitor:
            logger.info("Performance monitoring enabled")

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
        brave_api_key = (
            brave_config.get('api_key') or
            os.environ.get('BRAVE_API_KEY')
        )
        if brave_api_key:
            brave_proxy = (
                _extract_proxy(brave_config) or
                _env_proxy_var('BRAVE_PROXY') or
                proxy_from_config
            )
            brave_engine = BraveSearch(
                api_key=brave_api_key,
                proxy=brave_proxy
            )
            self.engines.append(brave_engine)
            logger.info("Brave Search engine initialized")

        # Google Search
        google_config = config.get('google', {})
        google_api_key = (
            google_config.get('api_key') or
            os.environ.get('GOOGLE_API_KEY')
        )
        google_cse_id = (
            google_config.get('cse_id') or
            os.environ.get('GOOGLE_CSE_ID')
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
                proxy=google_proxy
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
                proxy=searxng_proxy
            )
            self.engines.append(searxng_engine)
            self.fallback_engines.append(searxng_engine)
            logger.info(
                f"SearXNG search engine initialized: {base_url}"
            )

        # Always ensure DuckDuckGo is available as fallback
        ddg_proxy = (
            _extract_proxy(config.get('duckduckgo', {})) or
            _env_proxy_var('DUCKDUCKGO_PROXY') or
            proxy_from_config
        )

        duckduckgo = DuckDuckGoSearch(proxy=ddg_proxy)
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
                
    async def search(
            self,
            query: str,
            num_results: int = 10,
            engine: str = "auto"
    ) -> List[Dict]:
        """
        执行搜索，支持自动回退机制、缓存、限流和监控

        Args:
            query: 搜索查询字符串
            num_results: 返回结果数量
            engine: 搜索引擎选择 (auto/brave/google/duckduckgo/searxng/all)
                   - auto: 自动选择，优先使用配置的引擎，失败时自动回退
                   - brave/google/duckduckgo/searxng: 使用指定引擎
                   - all: 使用所有可用引擎，自动去重和排序

        Returns:
            搜索结果列表
        """
        start_time = time.time()
        success = False
        error_msg = None
        
        # 检查缓存
        if self.cache:
            cached_results = self.cache.get(query, engine, num_results)
            if cached_results is not None:
                success = True
                logger.info("Returning cached results")
                
                # 记录监控指标（缓存命中）
                if self.monitor:
                    metrics = SearchMetrics(
                        query=query,
                        engine=engine,
                        start_time=start_time,
                        end_time=time.time(),
                        success=True,
                        cached=True,
                        num_results=len(cached_results)
                    )
                    self.monitor.record_search(metrics)
                
                return cached_results

        all_results = []

        if not self.engines and not self.fallback_engines:
            logger.warning("No search engines available")
            error_msg = "No search engines available"
            
            # 记录监控指标（失败）
            if self.monitor:
                metrics = SearchMetrics(
                    query=query,
                    engine=engine,
                    start_time=start_time,
                    end_time=time.time(),
                    success=False,
                    cached=False,
                    error=error_msg
                )
                self.monitor.record_search(metrics)
            
            return []

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
            # 自动模式：优先使用配置的引擎，失败时回退
            if self.engines:
                engines_to_try = self.engines
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
        
        # all 模式：使用并发搜索
        if engine.lower() == "all":
            logger.info(
                f"Starting concurrent search with {len(engines_to_try)} "
                f"engines"
            )
            all_engine_results = await self._concurrent_search(
                engines_to_try, query, num_results
            )
        else:
            # auto 或指定引擎模式：串行搜索（支持早停）
            for search_engine in engines_to_try:
                engine_name = search_engine.__class__.__name__
                engine_type = self._get_engine_type(search_engine)

                try:
                    # 检查限流
                    if self.rate_limiter:
                        await self.rate_limiter.acquire(engine_type)
                    
                    # 执行搜索（自动重试）
                    results = await self._search_with_retry(
                        search_engine, query, num_results
                    )
                    
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

                        # 如果是 auto 模式且已获得足够结果，
                        # 则停止尝试其他引擎
                        auto_mode = engine.lower() == "auto"
                        enough_results = len(all_results) >= num_results
                        if auto_mode and enough_results:
                            logger.info(
                                f"Got enough results from {engine_name}, "
                                f"stopping"
                            )
                            success = True
                            break
                    else:
                        logger.warning(
                            f"No results from {engine_name}, "
                            f"trying next engine"
                        )

                except Exception as e:
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
                    num_results=num_results
                )
                success = len(all_results) > 0
            else:
                logger.warning("No results from any engine in all mode")
                all_results = []
                success = False
        elif engine.lower() != "all":
            # 非 all 模式：简单截取
            final_results = all_results[:num_results]
            all_results = final_results
            success = len(all_results) > 0
        
        # 缓存结果
        if self.cache and all_results:
            self.cache.set(query, engine, num_results, all_results)

        # 记录监控指标
        if self.monitor:
            metrics = SearchMetrics(
                query=query,
                engine=engine,
                start_time=start_time,
                end_time=time.time(),
                success=success,
                cached=False,
                num_results=len(all_results),
                error=error_msg if not success else None
            )
            self.monitor.record_search(metrics)

        return all_results
    
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
        
        try:
            # 检查限流
            if self.rate_limiter:
                await self.rate_limiter.acquire(engine_type)
            
            # 执行搜索（自动重试）
            results = await self._search_with_retry(
                search_engine, query, num_results
            )
            
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
            if isinstance(result, Exception):
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
        # 使用重试装饰器
        @async_retry(max_attempts=3, initial_delay=1.0, exponential_base=2.0)
        async def _do_search():
            return await search_engine.search(query, num_results)
        
        return await _do_search()

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
        engine: str = None
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
    
    def get_engine_stats(self, engine: str = None) -> Dict:
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
