#!/usr/bin/env python

import asyncio
import ipaddress
import json
import time
import psutil
import os
import httpx
import socket
from typing import Any, Dict, List
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from mcp.server.fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai import CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Use relative import or direct import depending on context
try:
    from .search import SearchManager
    from .utils import rewrite_local_proxy_url, get_http_proxy_from_env
except ImportError:
    from search import SearchManager
    from utils import rewrite_local_proxy_url, get_http_proxy_from_env

mcp = FastMCP("Crawl4AI")

crawler = None
# Lazily-created proxied crawler (used as fallback when direct fetch fails)
crawler_proxy = None
# Cache of resolved proxy URL for crawler (from config.json or env)
crawler_proxy_url = None
search_manager = None
start_time = time.time()  # 记录服务启动时间

# Locks for thread-safe initialization
crawler_lock = asyncio.Lock()
search_lock = asyncio.Lock()


async def initialize_search_manager():
    global search_manager
    async with search_lock:
        if search_manager is None:
            search_manager = SearchManager()
            print(
                "Search manager initialized with engines:",
                [type(e).__name__ for e in search_manager.engines]
            )


def _config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config.json"


def _extract_proxy_from_cfg(cfg: dict) -> str | None:
    """Extract a proxy URL from a config dict.

    Accepts either a string or an object with {"https": ..., "http": ...}.
    Prefers https over http. Returns None if not found/invalid.
    """
    if not cfg:
        return None
    proxy_cfg = cfg.get("proxy")
    if not proxy_cfg:
        return None

    proxy_value: str | None
    if isinstance(proxy_cfg, str):
        proxy_value = proxy_cfg
    elif isinstance(proxy_cfg, dict):
        https_p = proxy_cfg.get("https")
        http_p = proxy_cfg.get("http")
        if isinstance(https_p, str) and https_p:
            proxy_value = https_p
        elif isinstance(http_p, str) and http_p:
            proxy_value = http_p
        else:
            proxy_value = None
    else:
        proxy_value = None

    if not proxy_value:
        return None

    return rewrite_local_proxy_url(proxy_value)


def _env_proxy_http_https() -> str | None:
    """Return http/https proxy from env if available (http/https only)."""
    return get_http_proxy_from_env()


def _resolve_crawler_proxy_url() -> str | None:
    """
    Resolve the crawler proxy from config.json with global fallback,
    else use environment variables.
    """
    try:
        cfg_path = _config_path()
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # Per-crawler override
            crawler_p = _extract_proxy_from_cfg(cfg.get("crawler", {}))
            if crawler_p:
                return crawler_p
            # Global proxy fallback
            global_p = _extract_proxy_from_cfg(cfg)
            if global_p:
                return global_p
    except Exception as e:
        print(
            "Warning: failed to resolve crawler proxy from config.json: "
            f"{e}"
        )
    # Lastly, try env
    return _env_proxy_http_https()


def _parse_bool_env(value: str | None) -> bool | None:
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _parse_int_env(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _parse_float_env(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _read_url_security_enabled() -> bool:
    # Default: enabled (safe baseline)
    v = _parse_bool_env(os.environ.get("CRAWL4AI_READ_URL_SSRF_PROTECTION"))
    return True if v is None else bool(v)


def _read_url_allow_private() -> bool:
    # Default: block private/loopback
    v = _parse_bool_env(os.environ.get("CRAWL4AI_READ_URL_ALLOW_PRIVATE"))
    return False if v is None else bool(v)


def _read_url_allowed_hosts() -> set[str]:
    raw = (os.environ.get("CRAWL4AI_READ_URL_ALLOWED_HOSTS") or "").strip()
    if not raw:
        return set()
    return {h.strip().lower() for h in raw.split(",") if h.strip()}


def _read_url_max_url_length() -> int:
    v = _parse_int_env(os.environ.get("CRAWL4AI_READ_URL_MAX_URL_LENGTH"))
    if v is None:
        return 4096
    return max(256, v)


def _read_url_preflight_enabled() -> bool:
    # Default: disabled to avoid extra network calls / false negatives.
    v = _parse_bool_env(os.environ.get("CRAWL4AI_READ_URL_PREFLIGHT"))
    return False if v is None else bool(v)


def _read_url_preflight_timeout_s() -> float:
    v = _parse_float_env(os.environ.get("CRAWL4AI_READ_URL_PREFLIGHT_TIMEOUT_S"))
    if v is None:
        return 5.0
    return max(0.5, v)


def _read_url_max_redirects() -> int:
    v = _parse_int_env(os.environ.get("CRAWL4AI_READ_URL_MAX_REDIRECTS"))
    if v is None:
        return 5
    return max(0, v)


def _read_url_preflight_max_bytes() -> int:
    v = _parse_int_env(os.environ.get("CRAWL4AI_READ_URL_PREFLIGHT_MAX_BYTES"))
    if v is None:
        return 2 * 1024 * 1024
    return max(0, v)


def _read_url_allowed_content_type_prefixes() -> tuple[str, ...]:
    raw = (os.environ.get("CRAWL4AI_READ_URL_ALLOWED_CONTENT_TYPES") or "").strip()
    if not raw:
        return (
            "text/html",
            "application/xhtml+xml",
            "text/plain",
            "application/json",
        )
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    return tuple(parts)


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except Exception:
        return False
    # is_global excludes private/loopback/link-local/multicast/reserved/unspecified.
    return bool(getattr(addr, "is_global", False))


def _hostname_is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except Exception:
        return False


def _resolve_host_ips(host: str) -> set[str]:
    ips: set[str] = set()
    # getaddrinfo may return multiple families/records
    for fam, _typ, _proto, _canon, sockaddr in socket.getaddrinfo(host, None):
        try:
            if fam == socket.AF_INET:
                ips.add(str(sockaddr[0]))
            elif fam == socket.AF_INET6:
                ips.add(str(sockaddr[0]))
        except Exception:
            continue
    return ips


async def _validate_read_url_target(url: str) -> str | None:
    """Validate a user-provided URL to reduce SSRF risk.

    Returns an error message string if blocked, otherwise None.
    """
    if not _read_url_security_enabled():
        return None

    raw = str(url or "").strip()
    if not raw:
        return "URL is required"
    if len(raw) > _read_url_max_url_length():
        return "URL is too long"

    try:
        parts = urlsplit(raw)
    except Exception:
        return "Invalid URL"

    scheme = (parts.scheme or "").lower()
    if scheme not in {"http", "https"}:
        return "Only http/https URLs are allowed"

    # Block credentials in URL (userinfo), common SSRF trick.
    if parts.username or parts.password:
        return "URL must not contain credentials"

    host = (parts.hostname or "").strip()
    if not host:
        return "URL host is missing"

    host_l = host.lower()
    allowed_hosts = _read_url_allowed_hosts()
    allow_private = _read_url_allow_private()

    if host_l in allowed_hosts:
        return None

    # Fast-path for obvious localhost names.
    if not allow_private:
        if host_l in {"localhost", "localhost.localdomain"}:
            return "Blocked localhost URL"
        if host_l.endswith(".localhost"):
            return "Blocked localhost URL"

    # Validate resolved IPs.
    if _hostname_is_ip_literal(host_l):
        if allow_private:
            return None
        if not _is_public_ip(host_l):
            return "Blocked non-public IP address"
        return None

    try:
        ips = await asyncio.to_thread(_resolve_host_ips, host)
    except Exception:
        return "Failed to resolve hostname"

    if not ips:
        return "Hostname did not resolve"

    if not allow_private:
        for ip in ips:
            if not _is_public_ip(ip):
                return "Blocked non-public IP address"

    return None


async def _preflight_url(url: str, *, proxy_url: str | None) -> tuple[str | None, str | None]:
    """Optional preflight to enforce redirect/content-type/size caps.

    Returns (final_url, error). If error is not None, caller should fail.
    """
    max_redirects = _read_url_max_redirects()
    max_bytes = _read_url_preflight_max_bytes()
    timeout_s = _read_url_preflight_timeout_s()
    allowed_ct = _read_url_allowed_content_type_prefixes()

    async with httpx.AsyncClient(
        timeout=timeout_s,
        follow_redirects=True,
        max_redirects=max_redirects,
        trust_env=False,
        proxy=proxy_url,
        headers={"User-Agent": "Crawl4AI-Preflight/0.8.0", "Accept": "text/html,*/*"},
    ) as client:
        try:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                final_url = str(resp.url)

                # Re-validate the final URL (redirect target) for SSRF safety.
                err = await _validate_read_url_target(final_url)
                if err:
                    return None, f"Redirect target blocked: {err}"

                ctype = (resp.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
                if ctype:
                    if not any(ctype.startswith(p) for p in allowed_ct):
                        return None, f"Blocked content-type: {ctype}"

                if max_bytes > 0:
                    # Fast reject using Content-Length if available.
                    clen = (resp.headers.get("content-length") or "").strip()
                    if clen:
                        try:
                            if int(clen) > max_bytes:
                                return None, "Response is too large"
                        except Exception:
                            pass
                    read = 0
                    async for chunk in resp.aiter_bytes():
                        read += len(chunk)
                        if read > max_bytes:
                            return None, "Response is too large"

                return final_url, None
        except httpx.TooManyRedirects:
            return None, "Too many redirects"
        except httpx.HTTPStatusError as e:
            return None, f"Preflight HTTP error: {e.response.status_code}"
        except (httpx.RequestError, httpx.TimeoutException) as e:
            return None, f"Preflight request failed: {e.__class__.__name__}"
        except Exception as e:
            return None, f"Preflight failed: {str(e)}"


async def initialize_crawler():
    global crawler, crawler_proxy_url
    async with crawler_lock:
        if crawler is not None:
            return
        # Always initialize a direct (no-proxy) crawler first to honor
        # direct-first policy
        browser_config = BrowserConfig(headless=True)
        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.__aenter__()
        # Resolve proxy URL for possible later fallback use
        # (lazy init of proxied crawler)
        if crawler_proxy_url is None:
            crawler_proxy_url = _resolve_crawler_proxy_url()


async def initialize_crawler_proxy():
    """Initialize the proxied crawler lazily when needed."""
    global crawler_proxy
    async with crawler_lock:
        if crawler_proxy is not None:
            return
        if crawler_proxy_url:
            proxy_cfg = BrowserConfig(headless=True, proxy=crawler_proxy_url)
            crawler_proxy = AsyncWebCrawler(config=proxy_cfg)
            await crawler_proxy.__aenter__()


async def close_crawler():
    if crawler:
        await crawler.__aexit__(None, None, None)
    if crawler_proxy:
        await crawler_proxy.__aexit__(None, None, None)


@mcp.tool()
async def read_url(url: str, format: str = "markdown_with_citations") -> str:
    """
    Crawl a webpage and return its content in a specified format.

    Args:
        url: The URL to crawl
        format: The format of the content to return. Options:
            - raw_markdown: The basic HTML→Markdown conversion
                        - markdown_with_citations: Markdown including inline
                            citations that reference links at the end
                        - references_markdown: The references/citations
                            themselves (if citations=True)
                        - fit_markdown: The filtered/"fit" markdown if a
                            content filter was used
            - fit_html: The filtered HTML that generated fit_markdown
            - markdown: The default markdown format
    """
    global crawler_proxy_url

    # SSRF protection (fail fast before initializing browser/crawler).
    err = await _validate_read_url_target(url)
    if err:
        return json.dumps({"error": err}, ensure_ascii=False)

    # Optional preflight checks (redirect/content-type/size caps).
    if _read_url_preflight_enabled():
        # Try direct first; then try configured proxy (if any) on failure.
        final_url, pre_err = await _preflight_url(url, proxy_url=None)
        if pre_err:
            resolved_proxy = _resolve_crawler_proxy_url()
            if resolved_proxy:
                final_url, pre_err = await _preflight_url(url, proxy_url=resolved_proxy)
        if pre_err:
            return json.dumps({"error": pre_err}, ensure_ascii=False)
        if final_url:
            url = final_url

    await initialize_crawler()

    if crawler is None:
        return json.dumps(
            {"error": "Failed to initialize crawler"}, ensure_ascii=False
        )

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=5,
        excluded_tags=["nav", "footer", "header", "aside", "script", "style", "noscript", "iframe", "form"],
        markdown_generator=DefaultMarkdownGenerator(
            options={"citations": True}
        )
    )

    def _extract_content(res_obj):
        """Safely extract the requested markdown variant from crawler result."""

        if res_obj is None:
            raise ValueError(
                "Crawler returned no content. The target site may be unreachable "
                "or blocked (check network/proxy settings)."
            )

        # Try to get markdown_v2 (newer versions)
        markdown_v2 = getattr(res_obj, "markdown_v2", None)
        
        # Fallback to markdown (older versions like 0.4.248)
        if markdown_v2 is None:
            markdown_legacy = getattr(res_obj, "markdown", None)
            if markdown_legacy:
                # In some versions, markdown is an object with raw_markdown
                if hasattr(markdown_legacy, "raw_markdown"):
                    # For legacy, we might not support all formats, so return raw
                    return markdown_legacy.raw_markdown
                # In others, it might be the string itself
                if isinstance(markdown_legacy, str):
                    return markdown_legacy
            
            # If both are missing, raise error
            raise ValueError(
                "Crawler result missing markdown data (checked 'markdown_v2' and 'markdown'). "
                "Ensure the Crawl4AI markdown generator is enabled and the "
                "target responded with HTML."
            )

        if format == "raw_markdown":
            return markdown_v2.raw_markdown
        elif format == "markdown_with_citations":
            return markdown_v2.markdown_with_citations
        elif format == "references_markdown":
            return markdown_v2.references_markdown
        elif format == "fit_markdown":
            return markdown_v2.fit_markdown
        elif format == "fit_html":
            return markdown_v2.fit_html
        else:
            return markdown_v2.markdown_with_citations

    async def _run_with(cwlr):
        if cwlr is None:
            raise ValueError("Crawler instance is not initialized")
        res = await cwlr.arun(url=url, config=run_config)
        content = _extract_content(res)
        # ensure UTF-8 string
        if content is not None:
            if isinstance(content, str):
                try:
                    content = (
                        content.encode('utf-8', errors='replace')
                        .decode('utf-8')
                    )
                except Exception as e:
                    print(
                        f"Warning: Error handling content encoding: {str(e)}"
                    )
            else:
                try:
                    content = str(content)
                    content = (
                        content.encode('utf-8', errors='replace')
                        .decode('utf-8')
                    )
                except Exception as e:
                    print(
                        "Warning: Error converting content to string: "
                        f"{str(e)}"
                    )
                    content = (
                        "Error: Could not convert content to string: "
                        f"{str(e)}"
                    )
        return content

    # 1) Direct attempt (no proxy)
    try:
        return await _run_with(crawler)
    except Exception as e:
        # 2) Retry via configured/env proxy if available
        msg = str(e)
        print(f"Direct crawl failed, considering proxy retry: {msg}")

        # Check if we have a proxy to try (either already init or available in config/env)
        has_proxy_config = crawler_proxy_url or _env_proxy_http_https()

        if crawler_proxy is not None or has_proxy_config:
            if crawler_proxy_url is None:
                # resolve once if not done earlier
                # note: this will also consider env
                resolved = _resolve_crawler_proxy_url()
                if resolved:
                    # cache it
                    crawler_proxy_url = resolved
            try:
                await initialize_crawler_proxy()
                return await _run_with(crawler_proxy)
            except Exception as e2:
                error_msg = f"Error crawling URL via proxy: {str(e2)}"
                print(error_msg)
                return json.dumps({"error": error_msg}, ensure_ascii=False)
        else:
            error_msg = f"Error crawling URL: {msg}"
            print(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def search(
    query: str, num_results: int = 10, engine: str = "auto"
) -> str:
    """执行网络搜索并返回结果。

    Args:
        query: 搜索查询字符串
        num_results: 返回结果的数量,默认为10
        engine: 使用的搜索引擎,可选值:
            - "auto": 自动选择最佳引擎,失败时自动回退(默认,推荐)
            - "brave": 使用Brave搜索(需要API密钥,2000次/月免费)
            - "duckduckgo": 使用DuckDuckGo搜索(完全免费)
            - "google": 使用Google搜索(需要配置API密钥,100次/天免费)
            - "searxng": 使用SearXNG搜索(需要部署实例,完全免费无限制)
            - "all": 使用所有已配置的搜索引擎
    """
    if num_results < 1:
        num_results = 10

    try:
        await initialize_search_manager()
        if not search_manager or not search_manager.engines:
            return json.dumps(
                {"error": "No search engines available"}, ensure_ascii=False
            )
            
        results = await search_manager.search(query, num_results, engine)
        
        # 确保JSON字符串是UTF-8编码的
        try:
            json_str = json.dumps(results, ensure_ascii=False, indent=2)
            # 在Windows系统上，处理可能的编码问题
            json_str = (
                json_str.encode('utf-8', errors='replace')
                .decode('utf-8')
            )
            return json_str
        except Exception as e:
            error_msg = f"Error encoding search results: {str(e)}"
            print(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        print(error_msg)  # 添加错误日志
        try:
            return json.dumps({"error": error_msg}, ensure_ascii=False)
        except Exception as json_e:
            # 如果JSON序列化失败，返回简单的错误消息
            return f"Error: {error_msg}. JSON encoding failed: {str(json_e)}"


@mcp.tool()
async def system_status(check_type: str = "health") -> str:
    """系统状态检查 - 统一的监控端点
    
    Args:
        check_type: 检查类型，可选值：
            - "health": 基本健康状态（默认）
            - "readiness": 就绪状态检查
            - "metrics": 详细性能指标
            - "all": 返回所有状态信息
    
    Returns:
        JSON格式的状态信息
    """
    # Using module-level state (crawler, search_manager, start_time)
    
    try:
        # 初始化搜索管理器（如果还未初始化）
        await initialize_search_manager()
        
        # 计算运行时长
        uptime_seconds = time.time() - start_time
        uptime_hours = uptime_seconds / 3600
        
        # 获取搜索引擎状态
        engines_count = len(search_manager.engines) if search_manager else 0
        engines_list = [type(e).__name__ for e in search_manager.engines] \
            if search_manager else []
        
        # Health check data
        if check_type in ["health", "all"]:
            crawler_status = "initialized" if crawler else "not_initialized"
            
            health_data = {
                "status": "healthy",
                "version": "0.8.0",
                "uptime_seconds": round(uptime_seconds, 2),
                "uptime_hours": round(uptime_hours, 2),
                "components": {
                    "crawler": {
                        "status": crawler_status,
                        "ready": crawler is not None
                    },
                    "search": {
                        "status": (
                            "ready" if engines_count > 0 else "no_engines"
                        ),
                        "engines_count": engines_count,
                        "engines": engines_list
                    }
                },
                "timestamp": time.time()
            }
            
            if check_type == "health":
                return json.dumps(health_data, ensure_ascii=False, indent=2)
        
        # Readiness check data
        if check_type in ["readiness", "all"]:
            config_file = Path("config.json")
            
            checks = {
                "config_file": {
                    "status": "pass" if config_file.exists() else "fail",
                    "message": "Config file exists" if config_file.exists()
                              else "Config file not found"
                },
                "search_engines": {
                    "status": "pass" if engines_count > 0 else "fail",
                    "message": f"{engines_count} engines available"
                              if engines_count > 0
                              else "No search engines configured"
                },
                "crawler": {
                    "status": "pass",
                    "message": "Crawler can be initialized on demand"
                }
            }
            
            all_passed = all(c["status"] == "pass" for c in checks.values())

            diagnostics: Dict[str, Any] = {}
            warnings: List[str] = []
            readiness_data = {
                "ready": all_passed,
                "checks": checks,
                "diagnostics": diagnostics,
                "warnings": warnings,
                "timestamp": time.time(),
            }

            # -----------------------------
            # Extra diagnostics (non-blocking)
            # -----------------------------
            try:
                in_docker = Path("/.dockerenv").exists() or (
                    os.environ.get("RUNNING_IN_DOCKER", "").strip().lower()
                    in {"1", "true", "yes"}
                )
                proxy_rewrite_enabled = (
                    os.environ.get("CRAWL4AI_ALLOW_PROXY_REWRITE", "0")
                    .strip().lower() in {"1", "true", "yes"}
                )
                env_proxy = get_http_proxy_from_env()

                def _redact_proxy(value: str | None) -> str | None:
                    if not value:
                        return None
                    try:
                        # Strip userinfo if present: scheme://user:pass@host:port
                        from urllib.parse import urlsplit, urlunsplit

                        parts = urlsplit(value)
                        netloc = parts.hostname or ""
                        if parts.port:
                            netloc = f"{netloc}:{parts.port}"
                        return urlunsplit((parts.scheme, netloc, "", "", ""))
                    except Exception:
                        return "<redacted>"

                diagnostics.update({
                    "runtime": {
                        "in_docker": in_docker,
                        "proxy_rewrite_enabled": proxy_rewrite_enabled,
                    },
                    "proxy": {
                        "env_proxy_configured": bool(env_proxy),
                        "env_proxy": _redact_proxy(env_proxy),
                    },
                })

                # Engine-level snapshots (best-effort)
                engine_diag = {}
                ddg_impl = None
                searxng_ping = None

                if search_manager:
                    engines_all = list(search_manager.engines) + list(
                        getattr(search_manager, "fallback_engines", [])
                    )
                    for e in engines_all:
                        name = type(e).__name__
                        e_type = name.lower()
                        proxy_val = getattr(e, "proxy", None)
                        engine_diag[name] = {
                            "proxy_configured": bool(proxy_val),
                            "proxy": (
                                _redact_proxy(proxy_val)
                                if isinstance(proxy_val, str)
                                else None
                            ),
                        }
                        # detect DDGS implementation
                        if "duckduckgo" in e_type and hasattr(e, "ddgs"):
                            try:
                                ddg_impl = getattr(e.ddgs.__class__, "__module__", None)
                                engine_diag[name]["ddgs_impl"] = ddg_impl
                                engine_diag[name]["region"] = getattr(e, "region", None)
                            except Exception:
                                pass
                        if "searxng" in e_type:
                            engine_diag[name]["base_url"] = getattr(e, "base_url", None)
                            engine_diag[name]["language"] = getattr(e, "language", None)

                diagnostics["engines"] = engine_diag

                # Warn about common docker localhost pitfalls
                if in_docker:
                    # Localhost proxy inside container is usually wrong unless rewrite is enabled
                    if not proxy_rewrite_enabled:
                        # Check typical proxy env vars too
                        for k in (
                            "CRAWL4AI_HTTP_PROXY",
                            "CRAWL4AI_HTTPS_PROXY",
                            "HTTP_PROXY",
                            "HTTPS_PROXY",
                        ):
                            v = os.environ.get(k)
                            if v and ("127.0.0.1" in v or "localhost" in v):
                                warnings.append(
                                    f"{k} points to localhost inside a container; "
                                    "enable CRAWL4AI_ALLOW_PROXY_REWRITE=true "
                                    "or use host.docker.internal"
                                )
                                break

                    # If SearXNG is configured as localhost, it's usually wrong in compose
                    for _, ed in engine_diag.items():
                        base_url = ed.get("base_url")
                        if isinstance(base_url, str) and (
                            "localhost" in base_url
                            or "127.0.0.1" in base_url
                        ):
                            warnings.append(
                                "SearXNG base_url points to localhost inside container; "
                                "in docker-compose it should typically be http://searxng:8080 "
                                "(or set SEARXNG_BASE_URL)"
                            )
                            break

                # Warn if we're on the legacy duckduckgo_search package
                if ddg_impl and "duckduckgo_search" in ddg_impl:
                    warnings.append(
                        "DuckDuckGo backend is using legacy 'duckduckgo_search' "
                        "package; installing 'ddgs' improves stability and backend selection"
                    )

                # Report cache settings (cache can preserve degraded results)
                try:
                    if search_manager and getattr(search_manager, "cache", None):
                        cache_obj = search_manager.cache
                        cache_type = None
                        cache_db_path = None
                        try:
                            stats = (
                                cache_obj.get_stats()
                                if hasattr(cache_obj, "get_stats")
                                else None
                            )
                            if isinstance(stats, dict):
                                cache_type = stats.get("type")
                                cache_db_path = stats.get("db_path")
                        except Exception:
                            cache_type = None
                        diagnostics["cache"] = {
                            "enabled": True,
                            "ttl_seconds": getattr(cache_obj, "ttl", None),
                            "type": cache_type,
                            "db_path": cache_db_path,
                        }
                    else:
                        diagnostics["cache"] = {"enabled": False}
                except Exception:
                    pass

                # Best-effort ping for SearXNG (only checks local reachability, not internet)
                try:
                    searxng_base = None
                    searxng_lang = None
                    for _, ed in engine_diag.items():
                        if ed.get("base_url"):
                            searxng_base = ed.get("base_url")
                            searxng_lang = ed.get("language") or "auto"
                            break
                    if searxng_base:
                        url = str(searxng_base).rstrip("/") + "/search"
                        async with httpx.AsyncClient(timeout=3.0, trust_env=False) as client:
                            r = await client.get(url, params={
                                "q": "test",
                                "format": "json",
                                "language": searxng_lang,
                                "pageno": "1",
                            })
                            r.raise_for_status()
                            _ = r.json()
                        searxng_ping = {"ok": True}
                    if searxng_ping is not None:
                        diagnostics["searxng_ping"] = searxng_ping
                except Exception as e:
                    diagnostics["searxng_ping"] = {
                        "ok": False,
                        "error": str(e),
                    }
            except Exception as e:
                diagnostics["diagnostics_error"] = str(e)
            
            if check_type == "readiness":
                return json.dumps(readiness_data, ensure_ascii=False, indent=2)
        
        # Metrics data
        if check_type in ["metrics", "all"]:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            monitor_data = {}
            if search_manager and hasattr(search_manager, 'monitor'):
                monitor = search_manager.monitor
                overall_stats = monitor.get_overall_stats()
                engine_stats = monitor.get_engine_stats()
                
                monitor_data = {
                    "overall": overall_stats,
                    "engines": engine_stats,
                    "recent_searches_count": len(monitor.recent_searches)
                }
            
            metrics_data = {
                "service": {
                    "uptime_seconds": round(uptime_seconds, 2),
                    "version": "0.8.0"
                },
                "system": {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory": {
                        "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                        "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                        "percent": process.memory_percent()
                    }
                },
                "components": {
                    "crawler": {
                        "initialized": crawler is not None
                    },
                    "search": {
                        "engines_count": engines_count,
                        "monitor": monitor_data
                    }
                },
                "timestamp": time.time()
            }
            
            if check_type == "metrics":
                return json.dumps(metrics_data, ensure_ascii=False, indent=2)
        
        # Return all data
        if check_type == "all":
            return json.dumps({
                "health": health_data,
                "readiness": readiness_data,
                "metrics": metrics_data
            }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "error": f"Invalid check_type: {check_type}",
            "valid_types": ["health", "readiness", "metrics", "all"]
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def manage_cache(
    action: str,
    export_path: str = "output/cache_export.json"
) -> str:
    """缓存管理工具。
    
    支持的操作：
    - stats: 获取缓存统计信息
    - clear: 清空所有缓存
    - export: 导出缓存到 JSON 文件
    - cleanup: 清理过期的缓存条目
    - vacuum: 优化数据库（仅持久化缓存）
    
    Args:
        action: 操作类型 (stats/clear/export/cleanup/vacuum)
        export_path: 导出路径（仅用于 export 操作）
    
    Returns:
        操作结果信息
    """
    try:
        await initialize_search_manager()
        
        if not search_manager or not search_manager.cache:
            return json.dumps({
                "success": False,
                "error": "Cache not available"
            }, ensure_ascii=False, indent=2)
        
        cache = search_manager.cache
        
        if action == "stats":
            # 获取统计信息
            stats = cache.get_stats()
            result = {
                "success": True,
                "action": "stats",
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        elif action == "clear":
            # 清空缓存
            if hasattr(cache, 'clear'):
                count = cache.clear()
                result = {
                    "success": True,
                    "action": "clear",
                    "message": f"Cleared {count} cache entries",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "success": False,
                    "error": "Clear operation not supported"
                }
                
        elif action == "export":
            # 导出缓存
            if hasattr(cache, 'export_to_json'):
                count = cache.export_to_json(export_path)
                result = {
                    "success": True,
                    "action": "export",
                    "message": f"Exported {count} entries",
                    "export_path": export_path,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "success": False,
                    "error": "Export operation not supported"
                }
                
        elif action == "cleanup":
            # 清理过期条目
            if hasattr(cache, 'remove_expired'):
                count = cache.remove_expired()
                result = {
                    "success": True,
                    "action": "cleanup",
                    "message": f"Removed {count} expired entries",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "success": False,
                    "error": "Cleanup operation not supported"
                }
                
        elif action == "vacuum":
            # 优化数据库
            if hasattr(cache, 'vacuum'):
                cache.vacuum()
                result = {
                    "success": True,
                    "action": "vacuum",
                    "message": "Database optimized",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "success": False,
                    "error": "Vacuum operation not supported (only for persistent cache)"
                }
        else:
            result = {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": ["stats", "clear", "export", "cleanup", "vacuum"]
            }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@mcp.tool()
async def export_search_results(
    query: str,
    num_results: int = 10,
    engine: str = "auto",
    output_file: str = "search_results.json",
    include_metadata: bool = True
) -> str:
    """导出搜索结果到 JSON 文件。
    
    Args:
        query: 搜索查询字符串
        num_results: 返回结果的数量,默认为10
        engine: 使用的搜索引擎 (auto/brave/duckduckgo/google/searxng/all)
        output_file: 输出文件路径（相对于 output/ 目录）
        include_metadata: 是否包含元数据（时间戳、引擎信息等）
    
    Returns:
        导出操作的结果信息
    """
    try:
        # 确保搜索管理器已初始化
        await initialize_search_manager()
        if not search_manager or not search_manager.engines:
            return json.dumps({
                "success": False,
                "error": "No search engines available"
            }, ensure_ascii=False, indent=2)
        
        # 执行搜索
        search_start = time.time()
        results = await search_manager.search(query, num_results, engine)
        search_duration = time.time() - search_start
        
        # 检查结果类型（应该是列表）
        if not isinstance(results, list):
            return json.dumps({
                "success": False,
                "error": f"Unexpected result type: {type(results)}"
            }, ensure_ascii=False, indent=2)
        
        # 确定使用的引擎
        actual_engine = "unknown"
        if results and len(results) > 0 and isinstance(results[0], dict):
            actual_engine = results[0].get("engine", engine)
        
        # 准备导出数据
        export_data: Dict[str, Any] = {"results": results}
        
        # 添加元数据
        if include_metadata:
            export_data["metadata"] = {
                "query": query,
                "num_results": num_results,
                "requested_engine": engine,
                "actual_engine": actual_engine,
                "search_duration_seconds": round(search_duration, 3),
                "timestamp": datetime.now().isoformat(),
                "total_results": len(results),
                "version": "0.8.0"
            }
        
        # 确保输出目录存在
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建完整输出路径
        output_path = output_dir / output_file
        
        # 确保父目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # 返回成功信息
        result_info = {
            "success": True,
            "message": "Search results exported successfully",
            "output_file": str(output_path.absolute()),
            "file_size_bytes": output_path.stat().st_size,
            "total_results": len(results),
            "search_duration_seconds": round(search_duration, 3),
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result_info, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


async def cleanup():
    global search_manager
    try:
        if search_manager and hasattr(search_manager, "aclose"):
            await search_manager.aclose()
    finally:
        await close_crawler()

if __name__ == "__main__":
    try:
        mcp.run()
    finally:
        asyncio.run(cleanup())
