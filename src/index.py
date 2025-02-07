#!/usr/bin/env python

import asyncio
import json
from typing import List, Dict
from mcp.server.fastmcp import FastMCP, Context
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai import CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from search import SearchManager

mcp = FastMCP("Crawl4AI")

crawler = None
search_manager = None

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
    
    result = await crawler.arun(url=url, config=run_config)
    
    if format == "raw_markdown":
        return result.markdown_v2.raw_markdown
    elif format == "markdown_with_citations":
        return result.markdown_v2.markdown_with_citations
    elif format == "references_markdown":
        return result.markdown_v2.references_markdown
    elif format == "fit_markdown":
        return result.markdown_v2.fit_markdown
    elif format == "fit_html":
        return result.markdown_v2.fit_html
    else:
        return result.markdown_v2.markdown_with_citations

@mcp.tool()
async def search(query: str, num_results: int = 10, engine: str = "duckduckgo") -> str:
    """执行网络搜索并返回结果。

    Args:
        query: 搜索查询字符串
        num_results: 返回结果的数量,默认为10
        engine: 使用的搜索引擎,可选值:
            - "duckduckgo": 使用DuckDuckGo搜索(默认)
            - "google": 使用Google搜索(需要配置API密钥)
    """
    global search_manager
    try:
        await initialize_search_manager()
        if not search_manager or not search_manager.engines:
            return json.dumps({"error": "No search engines available"})
            
        results = await search_manager.search(query, num_results, engine)
        print(f"Search results: {results}")  # 添加调试日志
        
        # 直接返回字符串
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        print(error_msg)  # 添加错误日志
        return json.dumps({"error": error_msg})

async def cleanup():
    await close_crawler()

if __name__ == "__main__":
    try:
        mcp.run()
    finally:
        asyncio.run(cleanup())