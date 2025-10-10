#!/usr/bin/env python
"""
使用更具体的关键词搜索 Google API 配置指南
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search import SearchManager
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai import CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def search_google_api_detailed():
    """详细搜索 Google API 配置"""
    
    print("=" * 80)
    print("搜索：Google Custom Search API 配置教程")
    print("=" * 80)
    print()
    
    search_manager = SearchManager()
    
    # 更具体的搜索查询
    queries = [
        "Google Cloud Console Custom Search API key tutorial",
        "get Google Custom Search Engine ID programmable search",
        "Google CSE API credentials setup guide"
    ]
    
    all_results = {}
    best_urls = []
    
    for query in queries:
        print(f"🔍 搜索: '{query}'")
        print("-" * 80)
        
        try:
            results = await search_manager.search(
                query,
                num_results=5,
                engine="duckduckgo"
            )
            
            if results:
                print(f"✅ 找到 {len(results)} 个结果\n")
                
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['title']}")
                    print(f"     URL: {result['link']}")
                    snippet = result['snippet'][:120] + "..." if len(result['snippet']) > 120 else result['snippet']
                    print(f"     摘要: {snippet}")
                    print()
                    
                    # 收集看起来有用的URL
                    url = result['link']
                    if any(keyword in url.lower() for keyword in ['tutorial', 'guide', 'setup', 'how-to', 'docs', 'documentation']):
                        if url not in best_urls:
                            best_urls.append(url)
                
                all_results[query] = results
            else:
                print("❌ 未找到结果\n")
                
        except Exception as e:
            print(f"❌ 搜索错误: {str(e)}\n")
    
    # 保存搜索结果
    search_file = "google_api_search_results.json"
    with open(search_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 搜索结果已保存到: {search_file}")
    
    # 提取最有用的URL内容
    if best_urls:
        print()
        print("=" * 80)
        print(f"找到 {len(best_urls)} 个可能有用的教程URL")
        print("=" * 80)
        print()
        
        extracted = {}
        
        for i, url in enumerate(best_urls[:3], 1):  # 只提取前3个
            print(f"{i}. 正在提取: {url}")
            try:
                browser_config = BrowserConfig(headless=True)
                md_generator = DefaultMarkdownGenerator(
                    options={"citations": True}
                )
                
                run_config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    word_count_threshold=10,
                    excluded_tags=["nav", "footer", "header", "aside"],
                    markdown_generator=md_generator
                )
                
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    result = await crawler.arun(url=url, config=run_config)
                    
                    if result and result.markdown_v2:
                        content = result.markdown_v2.fit_markdown or result.markdown_v2.markdown_with_citations
                        if content and len(content) > 100:
                            print(f"   ✅ 成功提取 {len(content)} 字符")
                            extracted[url] = content
                        else:
                            print(f"   ⚠️  内容太少或为空")
                    else:
                        print(f"   ❌ 提取失败")
            except Exception as e:
                print(f"   ❌ 错误: {str(e)}")
            print()
        
        # 创建指南文档
        if extracted:
            guide_file = "google_api_setup_guide.md"
            with open(guide_file, 'w', encoding='utf-8') as f:
                f.write("# Google Custom Search API 配置指南\n\n")
                f.write("## 概述\n\n")
                f.write("本指南整合了多个来源的信息，帮助您获取 Google Custom Search API Key 和 CSE ID。\n\n")
                f.write("---\n\n")
                
                f.write("## 搜索结果汇总\n\n")
                for query, results in all_results.items():
                    f.write(f"### 查询: {query}\n\n")
                    for i, result in enumerate(results, 1):
                        f.write(f"{i}. **[{result['title']}]({result['link']})**\n")
                        f.write(f"   {result['snippet']}\n\n")
                
                f.write("\n---\n\n")
                f.write("## 详细教程内容\n\n")
                
                for i, (url, content) in enumerate(extracted.items(), 1):
                    f.write(f"### 教程 {i}: {url}\n\n")
                    f.write(content[:3000])  # 限制每个内容的长度
                    if len(content) > 3000:
                        f.write("\n\n...(内容已截断)...\n")
                    f.write("\n\n---\n\n")
                
                # 添加快速步骤总结
                f.write("## 快速步骤总结\n\n")
                f.write("根据搜索结果，获取 Google Custom Search API 的一般步骤如下：\n\n")
                f.write("### 获取 API Key:\n\n")
                f.write("1. 访问 [Google Cloud Console](https://console.cloud.google.com/)\n")
                f.write("2. 创建新项目或选择现有项目\n")
                f.write("3. 启用 Custom Search API\n")
                f.write("4. 转到 **APIs & Services** > **Credentials**\n")
                f.write("5. 点击 **Create Credentials** > **API Key**\n")
                f.write("6. 复制生成的 API Key\n\n")
                f.write("### 获取 CSE ID (Custom Search Engine ID):\n\n")
                f.write("1. 访问 [Google Programmable Search Engine](https://programmablesearchengine.google.com/)\n")
                f.write("2. 点击 **Get Started** 或 **New Search Engine**\n")
                f.write("3. 配置搜索引擎:\n")
                f.write("   - 指定要搜索的网站（或选择搜索整个网络）\n")
                f.write("   - 设置语言和地区\n")
                f.write("   - 给搜索引擎命名\n")
                f.write("4. 创建后，进入搜索引擎的控制面板\n")
                f.write("5. 在 **Setup** 或 **Overview** 页面找到 **Search engine ID (cx)**\n")
                f.write("6. 复制这个 ID，这就是您的 CSE ID\n\n")
                f.write("### 配置 Crawl4AI MCP Server:\n\n")
                f.write("编辑 `config.json` 文件:\n\n")
                f.write("```json\n")
                f.write("{\n")
                f.write('  "google": {\n')
                f.write('    "api_key": "your-api-key-here",\n')
                f.write('    "cse_id": "your-cse-id-here"\n')
                f.write("  }\n")
                f.write("}\n")
                f.write("```\n\n")
                f.write("### 注意事项:\n\n")
                f.write("- API Key 需要妥善保管，不要泄露\n")
                f.write("- 免费版 Custom Search API 每天有配额限制（通常是 100 次查询/天）\n")
                f.write("- 如需更多查询次数，需要设置计费账户\n")
                f.write("- CSE 可以配置为搜索特定网站或整个互联网\n")
            
            print(f"💾 配置指南已保存到: {guide_file}")
            print()
            print("=" * 80)
            print("✅ 搜索完成！请查看生成的指南文件。")
            print("=" * 80)
        else:
            print("\n⚠️  未能提取到有用的教程内容，但搜索结果已保存。")
    else:
        print("\n⚠️  未找到明显的教程URL，请查看搜索结果JSON文件。")
    
    print()
    print("📊 统计:")
    print(f"  - 搜索查询数: {len(queries)}")
    print(f"  - 总结果数: {sum(len(r) for r in all_results.values())}")
    print(f"  - 提取教程数: {len(extracted) if 'extracted' in locals() else 0}")


if __name__ == "__main__":
    asyncio.run(search_google_api_detailed())
