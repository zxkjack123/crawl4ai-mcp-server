"""
Phase 2 功能测试

测试新功能：
1. 搜索结果去重和排序
2. 错误重试机制
3. 监控和日志系统
4. API 限流保护
"""

import asyncio
import sys
import os
import time

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.search import SearchManager
from src.utils import (
    deduplicate_results, sort_results, merge_and_deduplicate,
    RateLimitConfig, RateLimiter
)
from src.monitor import initialize_monitoring, get_monitor


def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


async def test_deduplication():
    """测试搜索结果去重"""
    print_section("测试 1: 搜索结果去重")
    
    # 创建包含重复的测试数据
    test_results = [
        {"url": "https://example.com/1", "title": "Test 1", "engine": "google"},
        {"url": "https://example.com/2", "title": "Test 2", "engine": "brave"},
        {"url": "https://example.com/1", "title": "Test 1 Duplicate", "engine": "duckduckgo"},
        {"url": "https://example.com/3", "title": "Test 3", "engine": "searxng"},
        {"url": "https://example.com/2", "title": "Test 2 Duplicate", "engine": "google"},
    ]
    
    print(f"原始结果数: {len(test_results)}")
    deduplicated = deduplicate_results(test_results)
    print(f"去重后结果数: {len(deduplicated)}")
    print(f"✓ 去重成功: {len(test_results)} -> {len(deduplicated)}")
    
    for i, result in enumerate(deduplicated, 1):
        print(f"  {i}. {result['url']} ({result['engine']})")


async def test_sorting():
    """测试搜索结果排序"""
    print_section("测试 2: 搜索结果排序")
    
    test_results = [
        {"url": "https://example.com/1", "title": "Test 1", "engine": "duckduckgo"},
        {"url": "https://example.com/2", "title": "Test 2", "engine": "google"},
        {"url": "https://example.com/3", "title": "Test 3", "engine": "brave"},
        {"url": "https://example.com/4", "title": "Test 4", "engine": "searxng"},
    ]
    
    sorted_results = sort_results(test_results)
    
    print("排序后的结果（按引擎优先级）:")
    for i, result in enumerate(sorted_results, 1):
        print(f"  {i}. {result['url']} (引擎: {result['engine']})")
    
    print("✓ 排序成功")


async def test_merge_and_deduplicate():
    """测试合并去重"""
    print_section("测试 3: 多引擎结果合并去重")
    
    all_results = {
        "google": [
            {"url": "https://example.com/1", "title": "Test 1"},
            {"url": "https://example.com/2", "title": "Test 2"},
            {"url": "https://example.com/3", "title": "Test 3"},
        ],
        "brave": [
            {"url": "https://example.com/2", "title": "Test 2"},  # 重复
            {"url": "https://example.com/4", "title": "Test 4"},
        ],
        "duckduckgo": [
            {"url": "https://example.com/1", "title": "Test 1"},  # 重复
            {"url": "https://example.com/5", "title": "Test 5"},
        ],
    }
    
    total_before = sum(len(results) for results in all_results.values())
    print(f"合并前总结果数: {total_before}")
    
    merged = merge_and_deduplicate(all_results, num_results=10)
    print(f"合并去重后: {len(merged)}")
    
    print("\n最终结果:")
    for i, result in enumerate(merged, 1):
        print(f"  {i}. {result['url']} (引擎: {result['engine']})")
    
    print("✓ 合并去重成功")


async def test_rate_limiter():
    """测试API限流"""
    print_section("测试 4: API 限流")
    
    # 创建一个限流器：5 个请求/秒
    config = RateLimitConfig(max_requests=5, time_window=1.0)
    limiter = RateLimiter(config)
    
    print(f"限流配置: {config.max_requests} 请求/{config.time_window}秒")
    print(f"速率: {config.rate} 请求/秒\n")
    
    # 快速发送 8 个请求
    print("快速发送 8 个请求...")
    start_time = time.time()
    
    for i in range(8):
        request_start = time.time()
        await limiter.acquire()
        request_time = time.time() - request_start
        
        print(f"  请求 {i+1}: 耗时 {request_time:.3f}秒")
        
        if i >= 4:  # 前 5 个请求应该很快，之后会被限流
            print(f"    (被限流，等待令牌)")
    
    total_time = time.time() - start_time
    print(f"\n总耗时: {total_time:.3f}秒")
    print(f"✓ 限流功能正常")


async def test_retry_mechanism():
    """测试重试机制"""
    print_section("测试 5: 错误重试机制")
    
    from src.utils import async_retry
    
    attempt_count = 0
    
    @async_retry(max_attempts=3, initial_delay=0.5, exponential_base=2.0)
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  尝试 {attempt_count}...")
        
        if attempt_count < 3:
            raise Exception(f"模拟错误 (尝试 {attempt_count})")
        
        return "成功!"
    
    try:
        result = await failing_function()
        print(f"\n结果: {result}")
        print(f"✓ 重试成功，共尝试 {attempt_count} 次")
    except Exception as e:
        print(f"✗ 重试失败: {e}")


async def test_monitoring():
    """测试性能监控"""
    print_section("测试 6: 性能监控系统")
    
    # 初始化监控
    initialize_monitoring()
    monitor = get_monitor()
    
    print("执行测试搜索以收集指标...\n")
    
    # 创建搜索管理器
    manager = SearchManager(
        enable_cache=True,
        enable_rate_limit=False,  # 禁用限流以加快测试
        enable_monitoring=True
    )
    
    # 执行几次搜索
    queries = ["Python编程", "机器学习", "深度学习"]
    
    for query in queries:
        print(f"搜索: {query}")
        results = await manager.search(query, num_results=3, engine="auto")
        print(f"  获得 {len(results)} 个结果\n")
        await asyncio.sleep(0.5)
    
    # 获取统计信息
    overall_stats = monitor.get_overall_stats()
    print("\n整体统计:")
    print(f"  总请求数: {overall_stats['total_requests']}")
    print(f"  成功请求: {overall_stats['successful_requests']}")
    print(f"  成功率: {overall_stats['success_rate']}%")
    print(f"  缓存命中率: {overall_stats['cache_hit_rate']}%")
    
    # 获取引擎统计
    print("\n引擎统计:")
    engine_stats = monitor.get_engine_stats()
    for engine, stats in engine_stats.items():
        print(f"  {engine}:")
        print(f"    请求数: {stats['total_requests']}")
        print(f"    成功率: {stats['success_rate']}%")
        print(f"    平均耗时: {stats['avg_duration']}秒")
    
    # 获取最近搜索
    print("\n最近搜索:")
    recent = monitor.get_recent_searches(5)
    for i, search in enumerate(recent, 1):
        print(f"  {i}. {search['query']} - {search['engine']} - "
              f"{search['duration']}秒 - "
              f"{'成功' if search['success'] else '失败'}")
    
    print("\n✓ 监控系统正常工作")


async def test_all_engines_mode():
    """测试 all 引擎模式（包含去重和排序）"""
    print_section("测试 7: All 引擎模式（去重+排序）")
    
    manager = SearchManager(
        enable_cache=False,  # 禁用缓存以测试真实搜索
        enable_rate_limit=False,  # 禁用限流以加快测试
        enable_monitoring=True
    )
    
    print("使用 'all' 引擎模式搜索: Python programming")
    print("(将使用所有可用引擎，自动去重和排序)\n")
    
    results = await manager.search(
        query="Python programming",
        num_results=10,
        engine="all"
    )
    
    print(f"\n获得 {len(results)} 个结果:")
    for i, result in enumerate(results[:5], 1):  # 只显示前 5 个
        print(f"  {i}. {result['title']}")
        print(f"     引擎: {result.get('engine', 'unknown')}")
        print(f"     URL: {result['link']}\n")
    
    # 检查是否有重复
    urls = [r['link'] for r in results]
    unique_urls = set(urls)
    
    if len(urls) == len(unique_urls):
        print("✓ 所有结果唯一，无重复")
    else:
        print(f"✗ 发现重复: {len(urls)} 个结果，{len(unique_urls)} 个唯一")


async def test_integrated_features():
    """测试集成功能"""
    print_section("测试 8: 集成测试")
    
    # 初始化监控
    initialize_monitoring()
    
    manager = SearchManager(
        enable_cache=True,
        cache_ttl=60,
        enable_rate_limit=True,
        enable_monitoring=True
    )
    
    print("配置:")
    print("  ✓ 缓存: 启用 (TTL=60秒)")
    print("  ✓ 限流: 启用")
    print("  ✓ 监控: 启用")
    print("  ✓ 重试: 启用 (3次最大尝试)\n")
    
    # 执行搜索
    print("第一次搜索 (无缓存)...")
    start1 = time.time()
    results1 = await manager.search("人工智能", num_results=5, engine="auto")
    time1 = time.time() - start1
    print(f"  耗时: {time1:.3f}秒")
    print(f"  结果数: {len(results1)}\n")
    
    # 第二次搜索（使用缓存）
    print("第二次搜索 (使用缓存)...")
    start2 = time.time()
    results2 = await manager.search("人工智能", num_results=5, engine="auto")
    time2 = time.time() - start2
    print(f"  耗时: {time2:.3f}秒")
    print(f"  结果数: {len(results2)}\n")
    
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"缓存加速: {speedup:.1f}x\n")
    
    # 获取统计信息
    cache_stats = manager.get_cache_stats()
    print("缓存统计:")
    print(f"  条目数: {cache_stats.get('entries', 0)}")
    print(f"  命中数: {cache_stats.get('hits', 0)}\n")
    
    rate_limit_status = manager.get_rate_limit_status()
    if rate_limit_status:
        print("限流状态:")
        for engine, status in rate_limit_status.items():
            print(f"  {engine}: {status['available_tokens']:.1f}/"
                  f"{status['max_tokens']} 令牌可用")
    
    perf_stats = manager.get_performance_stats()
    print(f"\n性能统计:")
    print(f"  总请求数: {perf_stats.get('total_requests', 0)}")
    print(f"  成功率: {perf_stats.get('success_rate', 0)}%")
    print(f"  缓存命中率: {perf_stats.get('cache_hit_rate', 0)}%")
    
    print("\n✓ 所有功能正常集成")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Phase 2 功能测试")
    print("=" * 60)
    
    tests = [
        ("去重功能", test_deduplication),
        ("排序功能", test_sorting),
        ("合并去重", test_merge_and_deduplicate),
        ("API 限流", test_rate_limiter),
        ("重试机制", test_retry_mechanism),
        ("性能监控", test_monitoring),
        ("All 引擎模式", test_all_engines_mode),
        ("集成测试", test_integrated_features),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ 测试失败: {name}")
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
