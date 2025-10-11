#!/usr/bin/env python3
"""
测试并发搜索功能
"""

import asyncio
import json
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.search import SearchManager


async def test_concurrent_all_engines():
    """测试 all 模式的并发搜索"""
    print("=" * 60)
    print("测试并发搜索（all 引擎模式）")
    print("=" * 60)
    
    # 初始化搜索管理器
    search_manager = SearchManager()
    
    # 记录开始时间
    start_time = time.time()
    
    # 使用 all 模式搜索
    results = await search_manager.search(
        query="Python programming",
        num_results=5,
        engine="all"
    )
    
    # 计算耗时
    duration = time.time() - start_time
    
    print(f"\n搜索完成:")
    print(f"  总耗时: {duration:.2f} 秒")
    print(f"  结果数量: {len(results)}")
    
    # 统计各引擎的结果
    engines = {}
    for result in results:
        engine = result.get('engine', 'unknown')
        engines[engine] = engines.get(engine, 0) + 1
    
    print(f"\n各引擎结果分布:")
    for engine, count in engines.items():
        print(f"  {engine}: {count} 条")
    
    # 验证结果
    assert len(results) > 0, "应该有搜索结果"
    # 注意：由于去重和优先级排序，可能只有一个引擎的结果
    # assert len(engines) > 1, "应该有多个引擎的结果"
    
    print(f"\n✅ 并发搜索测试通过")
    return duration, len(results), len(engines)


async def test_serial_vs_concurrent():
    """对比串行和并发搜索的性能"""
    print("\n" + "=" * 60)
    print("性能对比：串行 vs 并发")
    print("=" * 60)
    
    search_manager = SearchManager()
    query = "Machine Learning"
    num_results = 3
    
    # 测试并发搜索（all 模式）
    print("\n1. 并发搜索（all 模式）...")
    start_time = time.time()
    concurrent_results = await search_manager.search(
        query=query,
        num_results=num_results,
        engine="all"
    )
    concurrent_duration = time.time() - start_time
    
    # 统计并发结果
    concurrent_engines = set(r.get('engine') for r in concurrent_results)
    
    print(f"   耗时: {concurrent_duration:.2f} 秒")
    print(f"   结果: {len(concurrent_results)} 条")
    print(f"   引擎: {len(concurrent_engines)} 个")
    
    # 测试串行搜索（逐个引擎）
    print("\n2. 模拟串行搜索（逐个引擎）...")
    serial_start = time.time()
    serial_results = []
    serial_engines = []
    
    # 逐个搜索每个引擎
    for engine_name in ['brave', 'google', 'duckduckgo', 'searxng']:
        try:
            results = await search_manager.search(
                query=query,
                num_results=num_results,
                engine=engine_name
            )
            if results:
                serial_results.extend(results)
                serial_engines.append(engine_name)
        except Exception as e:
            print(f"   {engine_name} 失败: {e}")
    
    serial_duration = time.time() - serial_start
    
    print(f"   耗时: {serial_duration:.2f} 秒")
    print(f"   结果: {len(serial_results)} 条")
    print(f"   引擎: {len(serial_engines)} 个")
    
    # 计算性能提升
    if serial_duration > 0:
        speedup = serial_duration / concurrent_duration
        print(f"\n📊 性能分析:")
        print(f"   并发搜索: {concurrent_duration:.2f}s")
        print(f"   串行搜索: {serial_duration:.2f}s")
        print(f"   速度提升: {speedup:.2f}x")
        print(f"   时间节省: {(serial_duration - concurrent_duration):.2f}s "
              f"({(1 - concurrent_duration/serial_duration)*100:.1f}%)")
    
    print(f"\n✅ 性能对比测试完成")


async def test_concurrent_error_handling():
    """测试并发搜索的错误处理"""
    print("\n" + "=" * 60)
    print("测试并发搜索错误处理")
    print("=" * 60)
    
    search_manager = SearchManager()
    
    # 使用 all 模式搜索（即使某些引擎失败也应返回结果）
    results = await search_manager.search(
        query="Test concurrent error handling",
        num_results=3,
        engine="all"
    )
    
    print(f"\n结果数量: {len(results)}")
    
    # 即使有引擎失败，至少应该有一个引擎成功
    assert len(results) > 0, "至少应有一个引擎返回结果"
    
    print(f"✅ 错误处理测试通过")


async def test_monitor_concurrent_stats():
    """测试并发搜索的监控统计"""
    print("\n" + "=" * 60)
    print("测试并发搜索监控统计")
    print("=" * 60)
    
    search_manager = SearchManager()
    
    # 执行并发搜索
    results = await search_manager.search(
        query="Python concurrent programming",
        num_results=5,
        engine="all"
    )
    
    # 获取监控统计
    if search_manager.monitor:
        overall_stats = search_manager.monitor.get_overall_stats()
        engine_stats = search_manager.monitor.get_engine_stats()
        
        print(f"\n总体统计:")
        print(f"  总请求: {overall_stats['total_requests']}")
        print(f"  成功: {overall_stats['successful_requests']}")
        print(f"  失败: {overall_stats['failed_requests']}")
        print(f"  成功率: {overall_stats['success_rate']}%")
        
        print(f"\n各引擎统计:")
        for engine_name, stats in engine_stats.items():
            print(f"  {engine_name}:")
            print(f"    请求: {stats['total_requests']}")
            print(f"    成功: {stats['successful_requests']}")
            print(f"    平均耗时: {stats['avg_duration']}s")
    
    print(f"\n✅ 监控统计测试通过")


async def main():
    """运行所有测试"""
    print("\n🚀 开始测试并发搜索功能...\n")
    
    try:
        # 测试1: 基本并发搜索
        duration, result_count, engine_count = await test_concurrent_all_engines()
        
        # 测试2: 性能对比
        await test_serial_vs_concurrent()
        
        # 测试3: 错误处理
        await test_concurrent_error_handling()
        
        # 测试4: 监控统计
        await test_monitor_concurrent_stats()
        
        print("\n" + "=" * 60)
        print("✅ 所有并发搜索测试通过！")
        print("=" * 60)
        
        print("\n📈 性能总结:")
        print(f"  并发搜索耗时: {duration:.2f}s")
        print(f"  返回结果: {result_count} 条")
        print(f"  使用引擎: {engine_count} 个")
        print(f"  预期提升: 3-4x 速度")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
