#!/usr/bin/env python3
"""
Brave Search 测试脚本

测试 Brave Search 集成和自动回退功能
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search import SearchManager


async def test_brave_search():
    """测试 Brave Search 基本功能"""
    print("=" * 60)
    print("测试 1: Brave Search 基本搜索")
    print("=" * 60)
    
    manager = SearchManager()
    
    # 检查引擎初始化
    print(f"\n✓ 已初始化的搜索引擎: {[type(e).__name__ for e in manager.engines]}")
    print(f"✓ 回退引擎列表: {[type(e).__name__ for e in manager.fallback_engines]}")
    
    # 测试 Brave Search
    query = "Python programming language"
    print(f"\n搜索查询: {query}")
    print("使用引擎: brave")
    
    results = await manager.search(query, num_results=5, engine="brave")
    
    if results:
        print(f"\n✓ 成功获取 {len(results)} 个结果:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['link']}")
            print(f"   来源: {result['source']}")
            print(f"   摘要: {result['snippet'][:100]}...")
            print()
    else:
        print("\n✗ 未获取到结果")


async def test_auto_fallback():
    """测试自动回退功能"""
    print("=" * 60)
    print("测试 2: 自动回退机制")
    print("=" * 60)
    
    manager = SearchManager()
    
    # 使用 auto 模式
    query = "人工智能最新进展"
    print(f"\n搜索查询: {query}")
    print("使用引擎: auto (自动选择，支持回退)")
    
    results = await manager.search(query, num_results=5, engine="auto")
    
    if results:
        print(f"\n✓ 成功获取 {len(results)} 个结果:")
        
        # 统计结果来源
        sources = {}
        for result in results:
            source = result['source']
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n结果来源统计:")
        for source, count in sources.items():
            print(f"  - {source}: {count} 个结果")
        
        print(f"\n前 3 个结果:")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   来源: {result['source']}")
            print(f"   URL: {result['link']}")
    else:
        print("\n✗ 未获取到结果")


async def test_all_engines():
    """测试所有引擎模式"""
    print("=" * 60)
    print("测试 3: 所有引擎聚合搜索")
    print("=" * 60)
    
    manager = SearchManager()
    
    query = "machine learning"
    print(f"\n搜索查询: {query}")
    print("使用引擎: all (聚合所有引擎)")
    
    results = await manager.search(query, num_results=10, engine="all")
    
    if results:
        print(f"\n✓ 成功获取 {len(results)} 个结果")
        
        # 统计结果来源
        sources = {}
        for result in results:
            source = result['source']
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n结果来源统计:")
        for source, count in sources.items():
            print(f"  - {source}: {count} 个结果")
    else:
        print("\n✗ 未获取到结果")


async def test_invalid_engine():
    """测试无效引擎时的回退"""
    print("=" * 60)
    print("测试 4: 无效引擎自动回退")
    print("=" * 60)
    
    manager = SearchManager()
    
    query = "test query"
    print(f"\n搜索查询: {query}")
    print("使用引擎: nonexistent (不存在的引擎)")
    
    results = await manager.search(query, num_results=3, engine="nonexistent")
    
    if results:
        print(f"\n✓ 自动回退成功，获取 {len(results)} 个结果")
        print(f"结果来源: {results[0]['source'] if results else 'N/A'}")
    else:
        print("\n✗ 回退失败")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Brave Search 集成测试")
    print("=" * 60 + "\n")
    
    # 检查配置文件
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if not os.path.exists(config_path):
        print("⚠️  警告: config.json 文件不存在")
        print(f"请创建配置文件: {config_path}")
        print("\n示例配置:")
        print(json.dumps({
            "brave": {
                "api_key": "YOUR_BRAVE_API_KEY"
            }
        }, indent=2))
        return
    
    try:
        # 运行测试
        await test_brave_search()
        print("\n")
        
        await test_auto_fallback()
        print("\n")
        
        await test_all_engines()
        print("\n")
        
        await test_invalid_engine()
        print("\n")
        
        print("=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
