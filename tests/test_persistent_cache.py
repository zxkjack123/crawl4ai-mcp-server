#!/usr/bin/env python3
"""
测试持久化缓存功能
"""

import asyncio
import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.persistent_cache import PersistentCache


def test_basic_operations():
    """测试基本的缓存操作"""
    print("=" * 60)
    print("测试基本缓存操作")
    print("=" * 60)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_cache.db")
    
    try:
        cache = PersistentCache(db_path=db_path, ttl=3600)
        
        # 测试设置缓存
        test_results = [
            {"title": "Test 1", "link": "https://test1.com", "snippet": "test 1"},
            {"title": "Test 2", "link": "https://test2.com", "snippet": "test 2"}
        ]
        
        cache.set("test query", "google", 10, test_results)
        print("✓ 缓存设置成功")
        
        # 测试获取缓存
        cached = cache.get("test query", "google", 10)
        assert cached is not None, "应该获取到缓存"
        assert len(cached) == 2, "结果数量应该是2"
        print("✓ 缓存获取成功")
        
        # 测试缓存未命中
        no_cache = cache.get("non-existent", "google", 10)
        assert no_cache is None, "不存在的查询应该返回 None"
        print("✓ 缓存未命中测试通过")
        
        # 测试统计信息
        stats = cache.get_stats()
        assert stats['size'] == 1, "缓存大小应该是1"
        print(f"✓ 统计信息: {stats}")
        
        print("\n✅ 基本操作测试通过")
        
    finally:
        # 清理
        shutil.rmtree(temp_dir)


def test_persistence():
    """测试缓存持久化"""
    print("\n" + "=" * 60)
    print("测试缓存持久化")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "persist_test.db")
    
    try:
        # 第一次：创建缓存
        cache1 = PersistentCache(db_path=db_path, ttl=3600)
        test_results = [
            {"title": "Persistent Test", "link": "https://persist.com"}
        ]
        cache1.set("persist query", "google", 5, test_results)
        print("✓ 第一次缓存设置完成")
        
        # 模拟重启：创建新的缓存实例
        cache2 = PersistentCache(db_path=db_path, ttl=3600)
        cached = cache2.get("persist query", "google", 5)
        
        assert cached is not None, "重启后应该能获取到缓存"
        assert len(cached) == 1, "结果数量应该是1"
        assert cached[0]['title'] == "Persistent Test"
        print("✓ 重启后缓存恢复成功")
        
        print("\n✅ 持久化测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def test_expiration():
    """测试缓存过期"""
    print("\n" + "=" * 60)
    print("测试缓存过期")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "expire_test.db")
    
    try:
        # 使用很短的 TTL
        cache = PersistentCache(db_path=db_path, ttl=1)
        
        test_results = [{"title": "Expire Test"}]
        cache.set("expire query", "google", 10, test_results)
        print("✓ 缓存设置完成")
        
        # 立即获取应该成功
        cached = cache.get("expire query", "google", 10)
        assert cached is not None, "立即获取应该成功"
        print("✓ 立即获取成功")
        
        # 等待过期
        print("等待2秒...")
        time.sleep(2)
        
        # 过期后获取应该失败
        expired = cache.get("expire query", "google", 10)
        assert expired is None, "过期后应该返回 None"
        print("✓ 过期检测成功")
        
        print("\n✅ 过期测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def test_export_import():
    """测试导出和导入"""
    print("\n" + "=" * 60)
    print("测试缓存导出和导入")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "export_test.db")
    export_path = os.path.join(temp_dir, "cache_export.json")
    
    try:
        # 创建缓存并添加数据
        cache1 = PersistentCache(db_path=db_path, ttl=3600)
        
        for i in range(5):
            cache1.set(
                f"query {i}",
                "google",
                10,
                [{"title": f"Result {i}"}]
            )
        
        print("✓ 创建了5个缓存条目")
        
        # 导出
        exported = cache1.export_to_json(export_path)
        assert exported == 5, "应该导出5个条目"
        print(f"✓ 导出成功: {exported} 条目")
        
        # 创建新缓存并导入
        db_path2 = os.path.join(temp_dir, "import_test.db")
        cache2 = PersistentCache(db_path=db_path2, ttl=3600)
        imported = cache2.import_from_json(export_path)
        assert imported == 5, "应该导入5个条目"
        print(f"✓ 导入成功: {imported} 条目")
        
        # 验证导入的数据
        for i in range(5):
            cached = cache2.get(f"query {i}", "google", 10)
            assert cached is not None, f"query {i} 应该存在"
            assert cached[0]['title'] == f"Result {i}"
        
        print("✓ 导入数据验证成功")
        
        print("\n✅ 导出导入测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def test_max_size():
    """测试最大缓存大小限制"""
    print("\n" + "=" * 60)
    print("测试缓存大小限制")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "size_test.db")
    
    try:
        # 创建小容量缓存
        cache = PersistentCache(db_path=db_path, ttl=3600, max_size=10)
        
        # 添加超过容量的条目
        for i in range(15):
            cache.set(
                f"query {i}",
                "google",
                10,
                [{"title": f"Result {i}"}]
            )
        
        stats = cache.get_stats()
        print(f"✓ 添加了15个条目，实际缓存: {stats['size']}")
        
        # 缓存大小应该不超过最大值
        assert stats['size'] <= 10, "缓存大小应该不超过最大值"
        
        print("\n✅ 大小限制测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def test_memory_cache():
    """测试内存缓存加速"""
    print("\n" + "=" * 60)
    print("测试内存缓存")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "memory_test.db")
    
    try:
        # 启用内存缓存
        cache = PersistentCache(
            db_path=db_path,
            ttl=3600,
            enable_memory_cache=True
        )
        
        test_results = [{"title": "Memory Test"}]
        cache.set("memory query", "google", 10, test_results)
        
        # 第一次获取（从数据库）
        start1 = time.time()
        cached1 = cache.get("memory query", "google", 10)
        time1 = time.time() - start1
        
        # 第二次获取（从内存缓存）
        start2 = time.time()
        cached2 = cache.get("memory query", "google", 10)
        time2 = time.time() - start2
        
        print(f"第一次获取耗时: {time1*1000:.2f}ms")
        print(f"第二次获取耗时: {time2*1000:.2f}ms")
        
        assert cached1 is not None
        assert cached2 is not None
        
        # 内存缓存应该更快（但差异可能很小）
        print("✓ 内存缓存工作正常")
        
        stats = cache.get_stats()
        print(f"内存缓存大小: {stats['memory_cache_size']}")
        
        print("\n✅ 内存缓存测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def test_remove_expired():
    """测试清理过期条目"""
    print("\n" + "=" * 60)
    print("测试清理过期条目")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "cleanup_test.db")
    
    try:
        # 使用短 TTL
        cache = PersistentCache(db_path=db_path, ttl=1)
        
        # 添加一些条目
        for i in range(3):
            cache.set(f"query {i}", "google", 10, [{"title": f"Result {i}"}])
        
        print("✓ 添加了3个条目")
        
        # 等待过期
        print("等待2秒...")
        time.sleep(2)
        
        # 清理过期条目
        removed = cache.remove_expired()
        print(f"✓ 删除了 {removed} 个过期条目")
        
        assert removed == 3, "应该删除3个过期条目"
        
        stats = cache.get_stats()
        assert stats['size'] == 0, "缓存应该为空"
        
        print("\n✅ 清理测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def main():
    """运行所有测试"""
    print("\n🚀 开始测试持久化缓存功能...\n")
    
    try:
        test_basic_operations()
        test_persistence()
        test_expiration()
        test_export_import()
        test_max_size()
        test_memory_cache()
        test_remove_expired()
        
        print("\n" + "=" * 60)
        print("✅ 所有持久化缓存测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
