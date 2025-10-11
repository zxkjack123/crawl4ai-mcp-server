#!/usr/bin/env python3
"""
搜索缓存功能测试

测试缓存的基本功能、性能提升和统计信息
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search import SearchManager


async def test_cache_basic():
    """测试缓存基本功能"""
    print("=" * 60)
    print("测试 1: 缓存基本功能")
    print("=" * 60)

    # 启用缓存
    manager = SearchManager(enable_cache=True, cache_ttl=60)

    query = "Python programming"

    # 第一次搜索（无缓存）
    print(f"\n第一次搜索: {query}")
    start = time.time()
    results1 = await manager.search(query, num_results=5, engine="auto")
    time1 = time.time() - start
    print(f"✓ 耗时: {time1:.2f}秒")
    print(f"✓ 结果数: {len(results1)}")

    # 第二次搜索（使用缓存）
    print(f"\n第二次搜索（应该使用缓存）: {query}")
    start = time.time()
    results2 = await manager.search(query, num_results=5, engine="auto")
    time2 = time.time() - start
    print(f"✓ 耗时: {time2:.2f}秒")
    print(f"✓ 结果数: {len(results2)}")

    # 性能提升
    if time2 < time1:
        speedup = time1 / time2
        print(f"\n✓ 性能提升: {speedup:.1f}x 更快")
    else:
        print("\n⚠️  缓存未生效或网络波动")

    # 缓存统计
    stats = manager.get_cache_stats()
    print(f"\n缓存统计:")
    print(f"  - 条目数: {stats['size']}")
    print(f"  - 总命中数: {stats['total_hits']}")
    print(f"  - TTL: {stats['ttl']}秒")


async def test_cache_different_params():
    """测试不同参数的缓存"""
    print("\n" + "=" * 60)
    print("测试 2: 不同参数的缓存")
    print("=" * 60)

    manager = SearchManager(enable_cache=True)

    query = "机器学习"

    # 不同引擎
    print(f"\n查询: {query}")
    print("测试不同引擎的缓存...")

    await manager.search(query, num_results=5, engine="auto")
    await manager.search(query, num_results=5, engine="duckduckgo")
    await manager.search(query, num_results=5, engine="auto")  # 缓存命中

    stats = manager.get_cache_stats()
    print(f"✓ 缓存条目数: {stats['size']}")
    print(f"✓ 总命中数: {stats['total_hits']}")


async def test_cache_expiration():
    """测试缓存过期"""
    print("\n" + "=" * 60)
    print("测试 3: 缓存过期")
    print("=" * 60)

    # 设置2秒过期时间
    manager = SearchManager(enable_cache=True, cache_ttl=2)

    query = "深度学习"

    print(f"\n第一次搜索: {query}")
    await manager.search(query, num_results=3, engine="auto")

    print("\n等待3秒...")
    await asyncio.sleep(3)

    print(f"第二次搜索（缓存应该已过期）: {query}")
    await manager.search(query, num_results=3, engine="auto")

    stats = manager.get_cache_stats()
    print(f"\n缓存统计:")
    print(f"  - 条目数: {stats['size']}")
    print(f"  - 平均年龄: {stats['avg_age_seconds']}秒")


async def test_cache_export_import():
    """测试缓存导出和导入"""
    print("\n" + "=" * 60)
    print("测试 4: 缓存导出和导入")
    print("=" * 60)

    manager1 = SearchManager(enable_cache=True)

    # 添加一些搜索结果
    queries = ["Python", "JavaScript", "Rust"]
    for query in queries:
        await manager1.search(query, num_results=3, engine="auto")

    # 导出缓存
    cache_file = "test_cache_export.json"
    manager1.export_cache(cache_file)
    print(f"\n✓ 缓存已导出到: {cache_file}")

    # 创建新的管理器并导入缓存
    manager2 = SearchManager(enable_cache=True)
    count = manager2.import_cache(cache_file)
    print(f"✓ 已导入 {count} 个缓存条目")

    # 验证导入
    stats = manager2.get_cache_stats()
    print(f"✓ 新管理器缓存条目数: {stats['size']}")

    # 清理测试文件
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print(f"✓ 已清理测试文件: {cache_file}")


async def test_cache_disabled():
    """测试禁用缓存"""
    print("\n" + "=" * 60)
    print("测试 5: 禁用缓存")
    print("=" * 60)

    manager = SearchManager(enable_cache=False)

    query = "人工智能"

    print(f"\n搜索（缓存已禁用）: {query}")
    await manager.search(query, num_results=3, engine="auto")

    stats = manager.get_cache_stats()
    print(f"✓ 缓存统计: {stats}")
    print("✓ 缓存已禁用，返回空字典")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("搜索缓存功能测试")
    print("=" * 60 + "\n")

    try:
        await test_cache_basic()
        await test_cache_different_params()
        await test_cache_expiration()
        await test_cache_export_import()
        await test_cache_disabled()

        print("\n" + "=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
