#!/usr/bin/env python

import asyncio
import json
import time
import psutil
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP, Context
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai import CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Use relative import or direct import depending on context
try:
    from .search import SearchManager
except ImportError:
    from search import SearchManager

mcp = FastMCP("Crawl4AI")

crawler = None
search_manager = None
start_time = time.time()  # 记录服务启动时间

async def initialize_search_manager():
    global search_manager
    if search_manager is None:
        search_manager = SearchManager()
        print("Search manager initialized with engines:", [type(e).__name__ for e in search_manager.engines])

async def initialize_crawler():
    global crawler
    browser_config = BrowserConfig(headless=True)
    md_generator = DefaultMarkdownGenerator(
        options={"citations": True}
    )

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,
        excluded_tags=["nav", "footer", "header"],
        markdown_generator=md_generator
    )
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()

async def close_crawler():
    global crawler
    if crawler:
        await crawler.__aexit__(None, None, None)

@mcp.tool()
async def read_url(url: str, format: str = "markdown_with_citations") -> str:
    """Crawl a webpage and return its content in a specified format.
    
    Args:
        url: The URL to crawl
        format: The format of the content to return. Options:
            - raw_markdown: The basic HTML→Markdown conversion
            - markdown_with_citations: Markdown including inline citations that reference links at the end
            - references_markdown: The references/citations themselves (if citations=True)
            - fit_markdown: The filtered/"fit" markdown if a content filter was used
            - fit_html: The filtered HTML that generated fit_markdown
            - markdown: The default markdown format
    """
    global crawler
    if not crawler:
        await initialize_crawler()
    
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,
        excluded_tags=["nav", "footer", "header"],
        markdown_generator=DefaultMarkdownGenerator(
            options={"citations": True}
        )
    )

    try:
        result = await crawler.arun(url=url, config=run_config)
        
        content = None
        if format == "raw_markdown":
            content = result.markdown_v2.raw_markdown
        elif format == "markdown_with_citations":
            content = result.markdown_v2.markdown_with_citations
        elif format == "references_markdown":
            content = result.markdown_v2.references_markdown
        elif format == "fit_markdown":
            content = result.markdown_v2.fit_markdown
        elif format == "fit_html":
            content = result.markdown_v2.fit_html
        else:
            content = result.markdown_v2.markdown_with_citations
        
        # 确保内容是UTF-8编码的字符串
        if content is not None:
            # 如果内容已经是字符串，确保它是UTF-8编码的
            if isinstance(content, str):
                # 在Windows系统上，处理可能的编码问题
                try:
                    # 尝试将内容编码为UTF-8，然后解码回字符串
                    # 这样可以确保内容是有效的UTF-8字符串
                    content = content.encode('utf-8', errors='replace').decode('utf-8')
                except Exception as e:
                    print(f"Warning: Error handling content encoding: {str(e)}")
            else:
                # 如果内容不是字符串，尝试将其转换为字符串
                try:
                    content = str(content)
                    content = content.encode('utf-8', errors='replace').decode('utf-8')
                except Exception as e:
                    print(f"Warning: Error converting content to string: {str(e)}")
                    content = f"Error: Could not convert content to string: {str(e)}"
        
        return content
    except Exception as e:
        error_msg = f"Error crawling URL: {str(e)}"
        print(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)

@mcp.tool()
async def search(query: str, num_results: int = 10, engine: str = "auto") -> str:
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
    global search_manager
    try:
        await initialize_search_manager()
        if not search_manager or not search_manager.engines:
            return json.dumps({"error": "No search engines available"}, ensure_ascii=False)
            
        results = await search_manager.search(query, num_results, engine)
        print(f"Search results: {results}")  # 添加调试日志
        
        # 确保JSON字符串是UTF-8编码的
        try:
            json_str = json.dumps(results, ensure_ascii=False, indent=2)
            # 在Windows系统上，处理可能的编码问题
            json_str = json_str.encode('utf-8', errors='replace').decode('utf-8')
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
async def health_check() -> str:
    """健康检查端点 - 返回服务基本状态。
    
    返回服务的基本健康状态，包括：
    - 服务状态（健康/不健康）
    - 服务版本
    - 运行时长
    - 可用的搜索引擎数量
    - 爬虫状态
    """
    global crawler, search_manager, start_time
    
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
        
        # 检查爬虫状态
        crawler_status = "initialized" if crawler else "not_initialized"
        
        health_data = {
            "status": "healthy",
            "version": "0.5.1",
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_hours": round(uptime_hours, 2),
            "components": {
                "crawler": {
                    "status": crawler_status,
                    "ready": crawler is not None
                },
                "search": {
                    "status": "ready" if engines_count > 0 else "no_engines",
                    "engines_count": engines_count,
                    "engines": engines_list
                }
            },
            "timestamp": time.time()
        }
        
        return json.dumps(health_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_health = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }
        return json.dumps(error_health, ensure_ascii=False, indent=2)


@mcp.tool()
async def readiness_check() -> str:
    """就绪检查端点 - 检查服务是否准备好接收请求。
    
    返回服务的就绪状态，包括：
    - 是否准备好接收请求
    - 各组件的就绪状态
    - 配置文件检查
    - 依赖服务状态
    """
    global crawler, search_manager
    
    try:
        await initialize_search_manager()
        
        # 检查配置文件
        config_exists = os.path.exists("config.json")
        
        # 检查搜索引擎
        has_engines = search_manager and len(search_manager.engines) > 0
        
        # 检查各组件就绪状态
        is_ready = config_exists and has_engines
        
        readiness_data = {
            "ready": is_ready,
            "checks": {
                "config_file": {
                    "status": "pass" if config_exists else "fail",
                    "message": "Config file exists" if config_exists 
                              else "Config file not found"
                },
                "search_engines": {
                    "status": "pass" if has_engines else "fail",
                    "message": f"{len(search_manager.engines)} engines available" 
                              if has_engines else "No search engines configured"
                },
                "crawler": {
                    "status": "pass",
                    "message": "Crawler can be initialized on demand"
                }
            },
            "timestamp": time.time()
        }
        
        return json.dumps(readiness_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_readiness = {
            "ready": False,
            "error": str(e),
            "timestamp": time.time()
        }
        return json.dumps(error_readiness, ensure_ascii=False, indent=2)


@mcp.tool()
async def metrics() -> str:
    """指标端点 - 返回服务的性能指标和统计信息。
    
    返回详细的服务指标，包括：
    - 系统资源使用情况（CPU、内存）
    - 服务运行统计
    - 搜索引擎性能指标
    - 缓存统计（如果启用）
    """
    global crawler, search_manager, start_time
    
    try:
        await initialize_search_manager()
        
        # 获取系统资源使用情况
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # 计算运行时长
        uptime_seconds = time.time() - start_time
        
        # 获取搜索管理器的监控数据
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
                "version": "0.5.1"
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
                    "engines_count": len(search_manager.engines) 
                                    if search_manager else 0,
                    "monitor": monitor_data
                }
            },
            "timestamp": time.time()
        }
        
        return json.dumps(metrics_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_metrics = {
            "error": str(e),
            "timestamp": time.time()
        }
        return json.dumps(error_metrics, ensure_ascii=False, indent=2)


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
    global search_manager
    
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
    global search_manager
    
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
        export_data = {
            "results": results
        }
        
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
                "version": "0.5.1"
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
    await close_crawler()

if __name__ == "__main__":
    try:
        mcp.run()
    finally:
        asyncio.run(cleanup())