#!/usr/bin/env python3
"""
测试健康检查端点
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.index import health_check, readiness_check, metrics, initialize_search_manager


async def test_health_check():
    """测试健康检查端点"""
    print("=" * 60)
    print("测试 health_check 端点")
    print("=" * 60)
    
    # 初始化搜索管理器
    await initialize_search_manager()
    
    # 调用健康检查
    result = await health_check()
    data = json.loads(result)
    
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    # 验证返回数据
    assert "status" in data, "缺少 status 字段"
    assert "version" in data, "缺少 version 字段"
    assert "uptime_seconds" in data, "缺少 uptime_seconds 字段"
    assert "components" in data, "缺少 components 字段"
    
    print("\n✅ health_check 测试通过")


async def test_readiness_check():
    """测试就绪检查端点"""
    print("\n" + "=" * 60)
    print("测试 readiness_check 端点")
    print("=" * 60)
    
    # 调用就绪检查
    result = await readiness_check()
    data = json.loads(result)
    
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    # 验证返回数据
    assert "ready" in data, "缺少 ready 字段"
    assert "checks" in data, "缺少 checks 字段"
    assert "timestamp" in data, "缺少 timestamp 字段"
    
    print("\n✅ readiness_check 测试通过")


async def test_metrics():
    """测试指标端点"""
    print("\n" + "=" * 60)
    print("测试 metrics 端点")
    print("=" * 60)
    
    # 调用指标端点
    result = await metrics()
    data = json.loads(result)
    
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    # 验证返回数据
    assert "service" in data, "缺少 service 字段"
    assert "system" in data, "缺少 system 字段"
    assert "components" in data, "缺少 components 字段"
    assert "timestamp" in data, "缺少 timestamp 字段"
    
    # 验证系统资源信息
    assert "cpu_percent" in data["system"], "缺少 CPU 使用率"
    assert "memory" in data["system"], "缺少内存信息"
    
    print("\n✅ metrics 测试通过")


async def main():
    """运行所有测试"""
    print("\n🚀 开始测试健康检查端点...")
    
    try:
        await test_health_check()
        await test_readiness_check()
        await test_metrics()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
