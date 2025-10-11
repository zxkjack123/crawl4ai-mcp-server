#!/usr/bin/env python3
"""
真实性能对比测试 - 并发 vs 串行搜索
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.search import SearchManager


async def benchmark_concurrent():
    """并发搜索基准测试"""
    print("=" * 60)
    print("并发搜索基准测试")
    print("=" * 60)
    
    sm = SearchManager()
    query = "artificial intelligence"
    num_results = 5
    
    # 预热
    print("预热...")
    await sm.search(query, 1, "google")
    
    # 基准测试
    print(f"\n测试查询: {query}")
    print(f"请求结果数: {num_results}")
    print("\n开始基准测试...")
    
    start_time = time.time()
    results = await sm.search(query, num_results, "all")
    duration = time.time() - start_time
    
    engines = set(r.get('engine', 'unknown') for r in results)
    
    print(f"\n结果:")
    print(f"  耗时: {duration:.3f}s")
    print(f"  结果数: {len(results)}")
    print(f"  引擎数: {len(engines)}")
    print(f"  使用引擎: {', '.join(engines)}")
    
    return duration


async def simulate_serial():
    """模拟串行搜索（手动等待模式）"""
    print("\n" + "=" * 60)
    print("串行搜索模拟")
    print("=" * 60)
    
    sm = SearchManager()
    query = "artificial intelligence"
    num_results = 5
    
    # 模拟串行：逐个执行工作的引擎
    working_engines = []
    total_time = 0
    
    print("\n测试各个引擎...")
    
    for engine_name in ['google', 'duckduckgo']:
        try:
            start = time.time()
            results = await sm.search(query, num_results, engine_name)
            duration = time.time() - start
            
            if results:
                working_engines.append(engine_name)
                total_time += duration
                print(f"  {engine_name}: {duration:.3f}s ({len(results)} 结果)")
        except Exception as e:
            print(f"  {engine_name}: 失败 ({e})")
    
    print(f"\n总耗时: {total_time:.3f}s")
    print(f"成功引擎: {len(working_engines)}")
    
    return total_time


async def main():
    print("\n🚀 真实性能基准测试\n")
    
    # 运行并发测试
    concurrent_time = await benchmark_concurrent()
    
    # 运行串行模拟
    serial_time = await simulate_serial()
    
    # 性能对比
    print("\n" + "=" * 60)
    print("性能对比")
    print("=" * 60)
    
    if serial_time > 0 and concurrent_time > 0:
        speedup = serial_time / concurrent_time
        time_saved = serial_time - concurrent_time
        percent_saved = (1 - concurrent_time/serial_time) * 100
        
        print(f"并发搜索: {concurrent_time:.3f}s")
        print(f"串行搜索: {serial_time:.3f}s")
        print(f"速度提升: {speedup:.2f}x")
        print(f"时间节省: {time_saved:.3f}s ({percent_saved:.1f}%)")
        
        if speedup >= 1.5:
            print("\n✅ 并发搜索显著提升性能！")
        elif speedup >= 1.1:
            print("\n✅ 并发搜索有一定提升")
        else:
            print("\n⚠️ 性能提升不明显（可能引擎较少）")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
