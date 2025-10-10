#!/usr/bin/env python
"""
测试 Google 和 DuckDuckGo 搜索引擎同时工作
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search import SearchManager


async def test_both_engines():
    """测试两个搜索引擎"""
    
    print("=" * 80)
    print("测试 Crawl4AI MCP Server - 双搜索引擎配置")
    print("=" * 80)
    print()
    
    # 初始化搜索管理器
    search_manager = SearchManager()
    
    # 检查可用的搜索引擎
    engines = [type(e).__name__ for e in search_manager.engines]
    print(f"✅ 已加载的搜索引擎: {engines}")
    print(f"   总计: {len(search_manager.engines)} 个引擎")
    print()
    
    # 测试查询
    test_query = "Python FastAPI tutorial"
    
    # 测试 1: DuckDuckGo 搜索
    print("=" * 80)
    print("测试 1: DuckDuckGo 搜索")
    print("=" * 80)
    print(f"查询: {test_query}")
    print()
    
    try:
        ddg_results = await search_manager.search(
            test_query,
            num_results=3,
            engine="duckduckgo"
        )
        
        if ddg_results:
            print(f"✅ DuckDuckGo 返回 {len(ddg_results)} 个结果")
            print()
            for i, result in enumerate(ddg_results, 1):
                print(f"{i}. {result['title']}")
                print(f"   URL: {result['link']}")
                snippet = result['snippet'][:100] + "..." if len(result['snippet']) > 100 else result['snippet']
                print(f"   摘要: {snippet}")
                print()
        else:
            print("❌ DuckDuckGo 未返回结果")
    except Exception as e:
        print(f"❌ DuckDuckGo 搜索失败: {str(e)}")
    
    print()
    
    # 测试 2: Google 搜索
    print("=" * 80)
    print("测试 2: Google 搜索")
    print("=" * 80)
    print(f"查询: {test_query}")
    print()
    
    try:
        google_results = await search_manager.search(
            test_query,
            num_results=3,
            engine="google"
        )
        
        if google_results:
            print(f"✅ Google 返回 {len(google_results)} 个结果")
            print()
            for i, result in enumerate(google_results, 1):
                print(f"{i}. {result['title']}")
                print(f"   URL: {result['link']}")
                snippet = result['snippet'][:100] + "..." if len(result['snippet']) > 100 else result['snippet']
                print(f"   摘要: {snippet}")
                print()
        else:
            print("❌ Google 未返回结果")
    except Exception as e:
        print(f"❌ Google 搜索失败: {str(e)}")
        print(f"   错误详情: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 测试 3: 使用 "all" 引擎（同时使用两个）
    print("=" * 80)
    print("测试 3: 同时使用两个搜索引擎")
    print("=" * 80)
    print(f"查询: {test_query}")
    print()
    
    try:
        all_results = await search_manager.search(
            test_query,
            num_results=3,
            engine="all"
        )
        
        if all_results:
            print(f"✅ 总共返回 {len(all_results)} 个结果")
            print()
            
            # 按来源统计
            sources = {}
            for result in all_results:
                source = result['source']
                sources[source] = sources.get(source, 0) + 1
            
            print("结果来源统计:")
            for source, count in sources.items():
                print(f"  - {source}: {count} 个结果")
            print()
            
            print("前 5 个结果:")
            for i, result in enumerate(all_results[:5], 1):
                print(f"{i}. [{result['source']}] {result['title']}")
                print(f"   URL: {result['link']}")
                print()
        else:
            print("❌ 未返回结果")
    except Exception as e:
        print(f"❌ 搜索失败: {str(e)}")
    
    # 总结
    print()
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    
    summary = {
        "available_engines": len(search_manager.engines),
        "engine_names": engines,
        "duckduckgo_works": 'ddg_results' in locals() and len(ddg_results) > 0,
        "google_works": 'google_results' in locals() and len(google_results) > 0,
        "combined_works": 'all_results' in locals() and len(all_results) > 0
    }
    
    print(f"可用引擎数: {summary['available_engines']}")
    print(f"引擎列表: {', '.join(summary['engine_names'])}")
    print()
    print("功能测试:")
    print(f"  DuckDuckGo: {'✅ 正常' if summary['duckduckgo_works'] else '❌ 失败'}")
    print(f"  Google: {'✅ 正常' if summary['google_works'] else '❌ 失败'}")
    print(f"  组合搜索: {'✅ 正常' if summary['combined_works'] else '❌ 失败'}")
    print()
    
    if summary['duckduckgo_works'] and summary['google_works']:
        print("🎉 恭喜！两个搜索引擎都已成功配置并正常工作！")
    elif summary['duckduckgo_works']:
        print("⚠️  DuckDuckGo 正常，但 Google 搜索可能需要检查配置")
    elif summary['google_works']:
        print("⚠️  Google 搜索正常，但 DuckDuckGo 可能有问题")
    else:
        print("❌ 两个搜索引擎都未能正常工作，请检查配置")
    
    print()
    print("=" * 80)
    
    # 保存测试结果
    if 'ddg_results' in locals() or 'google_results' in locals():
        test_results = {
            "duckduckgo": ddg_results if 'ddg_results' in locals() else [],
            "google": google_results if 'google_results' in locals() else [],
            "combined": all_results if 'all_results' in locals() else []
        }
        
        with open('dual_engine_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print("💾 测试结果已保存到: dual_engine_test_results.json")


if __name__ == "__main__":
    asyncio.run(test_both_engines())
