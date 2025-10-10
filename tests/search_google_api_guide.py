#!/usr/bin/env python
"""
使用 Crawl4AI MCP Server 搜索如何获得 Google API key 和 CSE ID
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search import SearchManager
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai import CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def search_google_api_setup():
    """搜索 Google API key 和 CSE ID 的获取方法"""
    
    print("=" * 80)
    print("搜索：如何获得 Google API Key 和 CSE ID")
    print("=" * 80)
    print()
    
    # Initialize search manager
    search_manager = SearchManager()
    
    # 搜索查询
    queries = [
        "how to get Google Custom Search API key",
        "Google CSE ID setup tutorial",
        "Google Custom Search Engine API configuration"
    ]
    
    all_results = {}
    
    for query in queries:
        print(f"🔍 搜索: '{query}'")
        print("-" * 80)
        
        try:
            results = await search_manager.search(
                query, 
                num_results=3, 
                engine="duckduckgo"
            )
            
            if results:
                print(f"✅ 找到 {len(results)} 个结果\n")
                
                for i, result in enumerate(results, 1):
                    print(f"  结果 #{i}")
                    print(f"  标题: {result['title']}")
                    print(f"  URL: {result['link']}")
                    snippet = result['snippet']
                    if len(snippet) > 150:
                        snippet = snippet[:150] + "..."
                    print(f"  摘要: {snippet}")
                    print()
                
                all_results[query] = results
            else:
                print("❌ 未找到结果\n")
                
        except Exception as e:
            print(f"❌ 搜索错误: {str(e)}\n")
    
    # 提取最相关的URL进行详细内容提取
    print()
    print("=" * 80)
    print("提取详细内容")
    print("=" * 80)
    print()
    
    # 选择最相关的URL
    target_urls = []
    for query_results in all_results.values():
        for result in query_results[:2]:  # 每个查询取前2个结果
            url = result['link']
            if url not in target_urls and 'google' in url.lower():
                target_urls.append(url)
    
    # 限制只提取前3个URL
    target_urls = target_urls[:3]
    
    extracted_contents = {}
    
    for url in target_urls:
        print(f"📖 正在提取: {url}")
        try:
            browser_config = BrowserConfig(headless=True)
            md_generator = DefaultMarkdownGenerator(
                options={"citations": True}
            )
            
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=10,
                excluded_tags=["nav", "footer", "header"],
                markdown_generator=md_generator
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)
                
                if result and result.markdown_v2:
                    content = result.markdown_v2.fit_markdown
                    if content:
                        print(f"  ✅ 成功提取内容 ({len(content)} 字符)")
                        extracted_contents[url] = content
                    else:
                        print(f"  ⚠️  内容为空")
                else:
                    print(f"  ❌ 提取失败")
        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")
        print()
    
    # 保存结果
    print("=" * 80)
    print("保存结果")
    print("=" * 80)
    
    # 保存搜索结果
    search_file = "google_api_search_results.json"
    with open(search_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"💾 搜索结果已保存: {search_file}")
    
    # 保存提取的内容
    if extracted_contents:
        content_file = "google_api_guide.md"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write("# 如何获得 Google API Key 和 CSE ID\n\n")
            f.write("## 搜索结果汇总\n\n")
            
            for query, results in all_results.items():
                f.write(f"### 查询: {query}\n\n")
                for i, result in enumerate(results, 1):
                    f.write(f"{i}. **{result['title']}**\n")
                    f.write(f"   - URL: {result['link']}\n")
                    f.write(f"   - 摘要: {result['snippet']}\n\n")
            
            f.write("\n---\n\n")
            f.write("## 详细内容提取\n\n")
            
            for url, content in extracted_contents.items():
                f.write(f"### 来源: {url}\n\n")
                f.write(content)
                f.write("\n\n---\n\n")
        
        print(f"💾 详细指南已保存: {content_file}")
    
    print()
    print("=" * 80)
    print("✅ 搜索完成！")
    print("=" * 80)
    print()
    print("📊 摘要:")
    print(f"  - 总查询数: {len(queries)}")
    print(f"  - 总结果数: {sum(len(r) for r in all_results.values())}")
    print(f"  - 提取内容数: {len(extracted_contents)}")


if __name__ == "__main__":
    asyncio.run(search_google_api_setup())
