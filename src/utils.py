"""
工具模块 - 搜索结果处理、重试机制、限流保护

提供以下功能：
1. 搜索结果去重和排序
2. 错误重试装饰器（指数退避）
3. API 限流保护（令牌桶算法）
"""

import asyncio
import logging
import os
import time
from typing import List, Dict, Any, Callable, Optional
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================
# 搜索结果去重和排序
# ============================================================

def deduplicate_results(
    results: List[Dict[str, Any]],
    key: str = "link",
    key_fn: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    对搜索结果去重
    
    Args:
        results: 搜索结果列表
        key: 用于去重的键（默认为 "link"）
        
    Returns:
        去重后的结果列表
    """
    seen = set()
    deduplicated = []
    
    for result in results:
        identifier = key_fn(result) if key_fn else result.get(key)
        if identifier and identifier not in seen:
            seen.add(identifier)
            deduplicated.append(result)
    
    logger.debug(
        f"Deduplicated results: {len(results)} -> {len(deduplicated)}"
    )
    return deduplicated


_TRACKING_QUERY_KEYS = {
    # Google Analytics / UTM
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "utm_name",
    # Ads / click ids
    "gclid",
    "dclid",
    "fbclid",
    "msclkid",
    # Common tracking/referrer params
    "ref",
    "ref_src",
    "ref_url",
    "source",
    "spm",
    "igshid",
    "mc_cid",
    "mc_eid",
    "_hsenc",
    "_hsmi",
    "mkt_tok",
    "yclid",
}


def canonicalize_url(url: Optional[str]) -> Optional[str]:
    """Canonicalize URLs for deduplication.

    - Normalize scheme (http/https -> https)
    - Lowercase host, drop leading www.
    - Drop default ports
    - Strip fragments
    - Remove common tracking query parameters (utm_*, gclid, fbclid, ...)
    - Normalize trailing slash for non-root paths
    """
    if url is None:
        return None
    raw = str(url).strip()
    if not raw:
        return None

    try:
        parts = urlsplit(raw)
    except Exception:
        return raw

    scheme = (parts.scheme or "").lower()
    if scheme in {"http", "https"}:
        scheme = "https"

    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]

    port = parts.port
    if scheme == "https" and port == 443:
        port = None
    if scheme == "http" and port == 80:
        port = None

    netloc = host
    if port:
        netloc = f"{host}:{port}"

    path = parts.path or ""
    if path == "/":
        path = ""
    if path not in {"", "/"}:
        path = path.rstrip("/")

    # Filter tracking query parameters.
    query_pairs = parse_qsl(parts.query or "", keep_blank_values=True)
    filtered_pairs: List[tuple[str, str]] = []
    for k, v in query_pairs:
        kl = (k or "").lower()
        if kl.startswith("utm_"):
            continue
        if kl in _TRACKING_QUERY_KEYS:
            continue
        filtered_pairs.append((k, v))
    query = urlencode(filtered_pairs, doseq=True)

    # Strip fragment.
    fragment = ""

    return urlunsplit((scheme, netloc, path, query, fragment))


def sort_results(
    results: List[Dict[str, Any]],
    engine_priority: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """
    对搜索结果排序
    
    排序规则：
    1. 首先按引擎优先级排序
    2. 同一引擎内保持原始顺序
    
    Args:
        results: 搜索结果列表
        engine_priority: 引擎优先级字典 {引擎名: 优先级分数}
                        分数越高优先级越高
                        
    Returns:
        排序后的结果列表
    """
    if not engine_priority:
        # 默认优先级：Google > Brave > SearXNG > DuckDuckGo
        engine_priority = {
            "google": 4,
            "brave": 3,
            "searxng": 2,
            "duckduckgo": 1,
        }
    
    # Keep stable ordering within each engine without O(n^2) list.index lookups.
    indexed = list(enumerate(results))

    def get_priority(item: tuple[int, Dict[str, Any]]) -> tuple[int, int]:
        idx, result = item
        engine = result.get("engine", "unknown")
        priority = engine_priority.get(str(engine).lower(), 0)
        # 返回负数使高优先级排在前面；idx 用于稳定排序
        return (-priority, idx)

    sorted_results = [r for _, r in sorted(indexed, key=get_priority)]
    logger.debug(f"Sorted {len(results)} results by engine priority")
    return sorted_results


def merge_and_deduplicate(
    all_results: Dict[str, List[Dict[str, Any]]],
    num_results: int = 10,
    engine_priority: Optional[Dict[str, int]] = None,
    fusion_method: str = "priority",
    rrf_k: int = 60,
    engine_weights: Optional[Dict[str, float]] = None,
    canonicalize_links: bool = True,
) -> List[Dict[str, Any]]:
    """
    合并多个引擎的结果，去重并排序
    
    Args:
        all_results: 所有引擎的结果 {引擎名: [结果列表]}
        num_results: 最终返回的结果数量
        engine_priority: 引擎优先级字典
        
    Returns:
        合并、去重、排序后的结果列表
    """
    method = (fusion_method or "priority").strip().lower()

    if not engine_priority:
        # 默认优先级：Google > Brave > SearXNG > DuckDuckGo
        engine_priority = {
            "google": 4,
            "brave": 3,
            "searxng": 2,
            "duckduckgo": 1,
        }

    if method in {"rrf", "reciprocal_rank_fusion"}:
        # Reciprocal Rank Fusion across engines.
        weights = engine_weights or {}
        scores: Dict[str, float] = {}
        best: Dict[str, tuple[int, int, Dict[str, Any]]] = {}
        first_seen = 0

        for engine, results in all_results.items():
            w = float(weights.get(str(engine).lower(), 1.0))
            if w <= 0:
                continue
            for rank, result in enumerate(results, start=1):
                # Ensure engine field exists.
                if "engine" not in result:
                    result["engine"] = engine
                link = result.get("link")
                key = (
                    canonicalize_url(link)
                    if canonicalize_links
                    else (str(link) if link else "")
                )
                if not key:
                    # If link is missing, fall back to a weak identifier.
                    key = f"no-link:{engine}:{rank}:{first_seen}"
                # Score update
                denom = float(max(0, int(rrf_k)) + rank)
                if denom <= 0:
                    denom = float(rank)
                scores[key] = scores.get(key, 0.0) + (w / denom)

                # Representative selection (prefer higher engine priority)
                eng = str(result.get("engine", engine)).lower()
                pri = int(engine_priority.get(eng, 0))
                prev = best.get(key)
                if prev is None:
                    best[key] = (pri, first_seen, result)
                else:
                    prev_pri, prev_seen, _prev_r = prev
                    if pri > prev_pri:
                        best[key] = (pri, prev_seen, result)
                first_seen += 1

        ranked = sorted(
            scores.keys(),
            key=lambda k: (
                -scores.get(k, 0.0),
                -best.get(k, (0, 0, {}))[0],
                best.get(k, (0, 0, {}))[1],
            ),
        )

        final_results: List[Dict[str, Any]] = []
        for k in ranked:
            _pri, _seen, r = best[k]
            final_results.append(r)
            if len(final_results) >= num_results:
                break

        logger.info(
            "Merged results via RRF: engines=%s, unique=%s, final=%s",
            len(all_results),
            len(best),
            len(final_results),
        )
        return final_results

    # 合并所有结果 (priority-based)
    merged: List[Dict[str, Any]] = []
    for engine, results in all_results.items():
        for result in results:
            # 确保每个结果都有 engine 字段
            if "engine" not in result:
                result["engine"] = engine
            merged.append(result)
    
    # 去重
    if canonicalize_links:
        # Pick the best representative per canonical URL, preferring higher
        # engine priority (more reliable engines) and stable within-engine order.
        best: Dict[str, tuple[int, int, Dict[str, Any]]] = {}
        for idx, r in enumerate(merged):
            link = r.get("link")
            key = canonicalize_url(link) or str(link or "")
            eng = str(r.get("engine", "unknown")).lower()
            pri = int(engine_priority.get(eng, 0))
            prev = best.get(key)
            if prev is None:
                best[key] = (pri, idx, r)
                continue
            prev_pri, prev_idx, _prev_r = prev
            if pri > prev_pri:
                best[key] = (pri, idx, r)
            elif pri == prev_pri and idx < prev_idx:
                best[key] = (pri, idx, r)

        # Preserve approximate original ordering before applying final sort.
        deduplicated = [t[2] for t in sorted(best.values(), key=lambda x: x[1])]
    else:
        deduplicated = deduplicate_results(merged)
    
    # 排序
    sorted_results = sort_results(deduplicated, engine_priority)
    
    # 截取指定数量
    final_results = sorted_results[:num_results]
    
    logger.info(
        f"Merged results: {len(merged)} -> "
        f"deduplicated: {len(deduplicated)} -> "
        f"final: {len(final_results)}"
    )
    
    return final_results


# ============================================================
# 错误重试机制
# ============================================================

def async_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    异步函数重试装饰器（指数退避）
    
    Args:
        max_attempts: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数退避基数
        exceptions: 需要重试的异常类型元组
        
    Usage:
        @async_retry(max_attempts=3, initial_delay=1.0)
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试失败，抛出异常
                        logger.error(
                            f"{func.__name__} failed after "
                            f"{max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # 计算延迟时间（指数退避）
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # 理论上不会到达这里
            raise last_exception
        
        return wrapper
    return decorator


# ============================================================
# API 限流保护（令牌桶算法）
# ============================================================

@dataclass
class RateLimitConfig:
    """限流配置"""
    max_requests: int  # 时间窗口内最大请求数
    time_window: float  # 时间窗口（秒）
    
    @property
    def rate(self) -> float:
        """每秒生成的令牌数"""
        return self.max_requests / self.time_window


class RateLimiter:
    """
    API 限流器（令牌桶算法）
    
    实现了令牌桶算法来限制 API 调用频率
    每个时间窗口内允许的最大请求数是固定的
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        初始化限流器
        
        Args:
            config: 限流配置
        """
        self.config = config
        self.tokens = float(config.max_requests)  # 当前令牌数
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        
        logger.info(
            f"RateLimiter initialized: "
            f"{config.max_requests} requests per {config.time_window}s "
            f"(rate: {config.rate:.2f} req/s)"
        )
    
    def _add_tokens(self):
        """添加令牌（基于时间流逝）"""
        now = time.time()
        elapsed = now - self.last_update
        
        # 根据经过的时间添加令牌
        new_tokens = elapsed * self.config.rate
        self.tokens = min(
            self.config.max_requests,
            self.tokens + new_tokens
        )
        self.last_update = now
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        获取令牌（阻塞直到获得令牌）
        
        Args:
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取令牌
        """
        async with self.lock:
            while True:
                self._add_tokens()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    logger.debug(
                        f"Token acquired. Remaining: {self.tokens:.2f}"
                    )
                    return True
                
                # 计算需要等待的时间
                needed_tokens = tokens - self.tokens
                wait_time = needed_tokens / self.config.rate
                
                logger.debug(
                    f"Rate limit reached. Waiting {wait_time:.2f}s..."
                )
                
                await asyncio.sleep(wait_time)
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌（非阻塞）
        
        Args:
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取令牌
        """
        async with self.lock:
            self._add_tokens()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(
                    f"Token acquired. Remaining: {self.tokens:.2f}"
                )
                return True
            
            logger.debug(
                f"Rate limit reached. Tokens available: {self.tokens:.2f}"
            )
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取限流器状态
        
        Returns:
            状态字典
        """
        self._add_tokens()
        return {
            "available_tokens": round(self.tokens, 2),
            "max_tokens": self.config.max_requests,
            "rate": round(self.config.rate, 2),
            "utilization": round(
                (1 - self.tokens / self.config.max_requests) * 100, 2
            ),
        }


def rewrite_local_proxy_url(proxy_url: Optional[str]) -> Optional[str]:
    """Rewrite localhost proxies to a host gateway when requested.

    When running inside the Dockerized HTTP bridge, users often keep their
    proxy (e.g., Clash) bound to the host loopback address. Accessing that
    proxy from inside the container requires reaching the host gateway, not
    127.0.0.1 inside the container. When the environment variable
    CRAWL4AI_ALLOW_PROXY_REWRITE is set ("1", "true", "yes"), this helper
    rewrites any proxy URL pointing to localhost/127.0.0.1 to use the
    configured gateway host and optional port override.
    """

    if not proxy_url:
        return proxy_url

    allow = os.environ.get("CRAWL4AI_ALLOW_PROXY_REWRITE", "0").lower()
    if allow not in {"1", "true", "yes"}:
        return proxy_url

    try:
        parsed = urlsplit(proxy_url)
    except Exception:
        return proxy_url

    hostname = parsed.hostname
    if hostname not in {"127.0.0.1", "localhost"}:
        return proxy_url

    gateway_host = (
        os.environ.get("HOST_PROXY_GATEWAY") or
        os.environ.get("HOST_DOCKER_GATEWAY") or
        os.environ.get("HOST_GATEWAY_FALLBACK") or
        "host.docker.internal"
    )

    if not gateway_host:
        return proxy_url

    # Allow overriding the port when the host proxy listens on a
    # non-standard port (e.g., Clash defaults to 7890/7891/7892 or a custom port)
    port_override_raw = os.environ.get("HOST_PROXY_PORT_OVERRIDE")

    # urllib.parse.urlsplit raises ValueError when accessing .port if the
    # original URL used an out-of-range value (e.g., 78900). Guard the access so
    # we can still rewrite the hostname and optionally apply a valid override.
    port: Optional[int] = None
    try:
        port = parsed.port  # may be None if no port in URL
    except ValueError:
        hostinfo = parsed.netloc
        if hostinfo and "@" in hostinfo:
            hostinfo = hostinfo.split("@", 1)[1]
        candidate = hostinfo.rsplit(":", 1)[-1] if hostinfo and ":" in hostinfo else None
        if candidate and candidate.isdigit():
            candidate_int = int(candidate)
            if 0 < candidate_int < 65536:
                port = candidate_int
            else:
                logger.warning(
                    "rewrite_local_proxy_url: ignoring out-of-range port %s from %s",
                    candidate,
                    proxy_url,
                )
        elif candidate:
            logger.warning(
                "rewrite_local_proxy_url: unable to parse port '%s' from %s",
                candidate,
                proxy_url,
            )

    # Apply override if provided and valid
    if port_override_raw:
        candidate = port_override_raw.strip()
        try:
            port_candidate = int(candidate)
            if 0 < port_candidate < 65536:
                port = port_candidate
            else:
                logger.warning(
                    "HOST_PROXY_PORT_OVERRIDE=%s is out of range (1-65535); ignoring",
                    candidate,
                )
        except ValueError:
            logger.warning(
                "HOST_PROXY_PORT_OVERRIDE=%s is not a valid integer; ignoring",
                candidate,
            )

    # Preserve authentication info if present
    netloc_host = gateway_host
    if port:
        netloc_host = f"{netloc_host}:{port}"

    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth += f":{parsed.password}"
        netloc_host = f"{auth}@{netloc_host}"

    rewritten = urlunsplit((
        parsed.scheme,
        netloc_host,
        parsed.path,
        parsed.query,
        parsed.fragment
    ))

    return rewritten


def get_http_proxy_from_env() -> Optional[str]:
    """Resolve an HTTP(S) proxy URL from environment variables.

    This project historically used both standard proxy env vars (HTTP_PROXY,
    HTTPS_PROXY, etc.) and Crawl4AI-prefixed ones (CRAWL4AI_HTTP_PROXY,
    CRAWL4AI_HTTPS_PROXY). Different runtime modes (host vs docker compose)
    may propagate only one set.

    Returns a proxy URL suitable for httpx / ddgs (http/https only). If
    CRAWL4AI_ALLOW_PROXY_REWRITE is enabled, localhost/127.0.0.1 addresses are
    rewritten via rewrite_local_proxy_url().
    """

    keys = [
        # Preferred (Crawl4AI .env)
        "CRAWL4AI_HTTPS_PROXY",
        "CRAWL4AI_HTTP_PROXY",
        # Standard
        "HTTPS_PROXY",
        "https_proxy",
        "HTTP_PROXY",
        "http_proxy",
        # Some environments only expose ALL_PROXY
        "ALL_PROXY",
        "all_proxy",
    ]

    for k in keys:
        v = os.environ.get(k)
        if not v:
            continue
        v = v.strip()
        if not v:
            continue
        if v.startswith("http://") or v.startswith("https://"):
            return rewrite_local_proxy_url(v)

    return None


class MultiRateLimiter:
    """
    多引擎限流管理器
    
    为不同的搜索引擎维护独立的限流器
    """
    
    def __init__(self, configs: Optional[Dict[str, RateLimitConfig]] = None):
        """
        初始化多引擎限流器
        
        Args:
            configs: 引擎限流配置字典 {引擎名: RateLimitConfig}
                    如果为 None，使用默认配置
        """
        if configs is None:
            # 默认配置（基于各引擎的实际限制）
            # 注意：DuckDuckGo 和 SearXNG 如果是自托管，
            # 可以设置很大的限额或完全不限制
            configs = {
                "google": RateLimitConfig(
                    max_requests=100, time_window=86400
                ),  # 100/天 (Google API 限制)
                "brave": RateLimitConfig(
                    max_requests=2000, time_window=2592000
                ),  # 2000/月 (Brave API 限制)
                # DuckDuckGo: 开源免费，无官方限制
                # 设置宽松限制只是为了防止过度请求
                "duckduckgo": RateLimitConfig(
                    max_requests=1000, time_window=60
                ),  # 1000/分钟（非常宽松）
                # SearXNG: 自托管实例，无限制
                # 设置宽松限制只是为了保护服务器
                "searxng": RateLimitConfig(
                    max_requests=1000, time_window=60
                ),  # 1000/分钟（非常宽松）
            }
        
        self.limiters: Dict[str, RateLimiter] = {
            engine: RateLimiter(config)
            for engine, config in configs.items()
        }
        
        logger.info(
            f"MultiRateLimiter initialized with "
            f"{len(self.limiters)} engines"
        )
    
    async def acquire(self, engine: str, tokens: int = 1) -> bool:
        """
        为指定引擎获取令牌
        
        Args:
            engine: 引擎名
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取令牌
        """
        limiter = self.limiters.get(engine.lower())
        if limiter is None:
            logger.warning(f"No rate limiter for engine: {engine}")
            return True  # 没有配置限流器，直接通过
        
        return await limiter.acquire(tokens)
    
    async def try_acquire(self, engine: str, tokens: int = 1) -> bool:
        """
        为指定引擎尝试获取令牌（非阻塞）
        
        Args:
            engine: 引擎名
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取令牌
        """
        limiter = self.limiters.get(engine.lower())
        if limiter is None:
            logger.warning(f"No rate limiter for engine: {engine}")
            return True
        
        return await limiter.try_acquire(tokens)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有引擎的限流状态
        
        Returns:
            所有引擎的状态字典
        """
        return {
            engine: limiter.get_status()
            for engine, limiter in self.limiters.items()
        }
