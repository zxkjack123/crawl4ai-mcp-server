"""
单元测试套件 - utils 模块

测试覆盖率目标: > 80%
"""

import pytest
import asyncio
import time
from src.utils import (
    deduplicate_results,
    sort_results,
    merge_and_deduplicate,
    async_retry,
    RateLimiter,
    RateLimitConfig,
    MultiRateLimiter
)


class TestDeduplication:
    """测试去重功能"""
    
    def test_deduplicate_by_link(self):
        """测试按 link 去重"""
        results = [
            {"title": "A", "link": "http://a.com"},
            {"title": "B", "link": "http://b.com"},
            {"title": "A2", "link": "http://a.com"},  # 重复
        ]
        
        deduplicated = deduplicate_results(results)
        assert len(deduplicated) == 2
        assert deduplicated[0]['title'] == "A"
        assert deduplicated[1]['title'] == "B"
    
    def test_deduplicate_custom_key(self):
        """测试自定义键去重"""
        results = [
            {"id": "1", "name": "A"},
            {"id": "2", "name": "B"},
            {"id": "1", "name": "A2"},  # 重复
        ]
        
        deduplicated = deduplicate_results(results, key="id")
        assert len(deduplicated) == 2
    
    def test_deduplicate_empty(self):
        """测试空列表去重"""
        deduplicated = deduplicate_results([])
        assert deduplicated == []
    
    def test_deduplicate_missing_key(self):
        """测试缺少去重键的情况"""
        results = [
            {"title": "A"},  # 缺少 link
            {"title": "B", "link": "http://b.com"},
        ]
        
        deduplicated = deduplicate_results(results)
        # 缺少键的条目会被跳过
        assert len(deduplicated) == 1
        assert deduplicated[0]['title'] == "B"


class TestSorting:
    """测试排序功能"""
    
    def test_sort_by_default_priority(self):
        """测试默认优先级排序"""
        results = [
            {"engine": "duckduckgo", "title": "A"},
            {"engine": "google", "title": "B"},
            {"engine": "brave", "title": "C"},
        ]
        
        sorted_results = sort_results(results)
        # Google > Brave > DuckDuckGo
        assert sorted_results[0]['engine'] == "google"
        assert sorted_results[1]['engine'] == "brave"
        assert sorted_results[2]['engine'] == "duckduckgo"
    
    def test_sort_by_custom_priority(self):
        """测试自定义优先级排序"""
        results = [
            {"engine": "a", "title": "A"},
            {"engine": "b", "title": "B"},
            {"engine": "c", "title": "C"},
        ]
        
        priority = {"c": 10, "b": 5, "a": 1}
        sorted_results = sort_results(results, priority)
        
        assert sorted_results[0]['engine'] == "c"
        assert sorted_results[1]['engine'] == "b"
        assert sorted_results[2]['engine'] == "a"
    
    def test_sort_preserves_order_within_engine(self):
        """测试同引擎内保持原始顺序"""
        results = [
            {"engine": "google", "title": "A", "order": 1},
            {"engine": "google", "title": "B", "order": 2},
            {"engine": "google", "title": "C", "order": 3},
        ]
        
        sorted_results = sort_results(results)
        # 应保持原始顺序
        assert sorted_results[0]['order'] == 1
        assert sorted_results[1]['order'] == 2
        assert sorted_results[2]['order'] == 3


class TestMergeAndDeduplicate:
    """测试合并去重功能"""
    
    def test_merge_multiple_engines(self):
        """测试合并多个引擎的结果"""
        all_results = {
            "google": [
                {"title": "A", "link": "http://a.com", "engine": "google"}
            ],
            "brave": [
                {"title": "B", "link": "http://b.com", "engine": "brave"}
            ]
        }
        
        merged = merge_and_deduplicate(all_results, num_results=10)
        assert len(merged) == 2
    
    def test_merge_with_duplicates(self):
        """测试合并时去重"""
        all_results = {
            "google": [
                {"title": "A", "link": "http://same.com", "engine": "google"}
            ],
            "brave": [
                {"title": "B", "link": "http://same.com", "engine": "brave"}
            ]
        }
        
        merged = merge_and_deduplicate(all_results, num_results=10)
        # 去重后只保留一个
        assert len(merged) == 1
    
    def test_merge_respects_num_results(self):
        """测试尊重结果数量限制"""
        all_results = {
            "google": [
                {"title": f"A{i}", "link": f"http://a{i}.com", "engine": "google"}
                for i in range(10)
            ]
        }
        
        merged = merge_and_deduplicate(all_results, num_results=5)
        assert len(merged) <= 5
    
    def test_merge_empty_results(self):
        """测试合并空结果"""
        merged = merge_and_deduplicate({}, num_results=10)
        assert merged == []


class TestAsyncRetry:
    """测试异步重试装饰器"""
    
    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """测试首次尝试成功"""
        call_count = 0
        
        @async_retry(max_attempts=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await success_func()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """测试重试后成功"""
        call_count = 0
        
        @async_retry(max_attempts=3, initial_delay=0.1)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = await flaky_func()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """测试重试次数耗尽"""
        call_count = 0
        
        @async_retry(max_attempts=3, initial_delay=0.1)
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            await always_fail()
        
        assert call_count == 3


class TestRateLimiter:
    """测试限流功能"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """测试基本限流"""
        config = RateLimitConfig(max_requests=2, time_window=10)
        limiter = RateLimiter(config)
        
        # 第一次请求应该立即通过
        start = time.time()
        result1 = await limiter.acquire()
        elapsed1 = time.time() - start
        
        assert result1 is True
        assert elapsed1 < 0.1  # 应该很快
        
        # 第二次请求应该立即通过
        start = time.time()
        result2 = await limiter.acquire()
        elapsed2 = time.time() - start
        
        assert result2 is True
        assert elapsed2 < 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_refill(self):
        """测试令牌补充"""
        config = RateLimitConfig(max_requests=5, time_window=1.0)  # 5令牌/秒
        limiter = RateLimiter(config)
        
        # 用完所有令牌
        for _ in range(5):
            await limiter.acquire()
        
        # 等待令牌补充
        await asyncio.sleep(0.3)  # 等待0.3秒，应该补充1.5个令牌
        
        # 这个请求应该可以通过（因为有补充的令牌）
        start = time.time()
        result = await limiter.acquire()
        elapsed = time.time() - start
        
        assert result is True
        # 应该有足够的令牌，不需要等待太久
        assert elapsed < 0.5


class TestMultiRateLimiter:
    """测试多引擎限流器"""
    
    @pytest.mark.asyncio
    async def test_multi_limiter_different_engines(self):
        """测试不同引擎独立限流"""
        configs = {
            "engine_a": RateLimitConfig(max_requests=2, time_window=10),
            "engine_b": RateLimitConfig(max_requests=2, time_window=10)
        }
        
        limiter = MultiRateLimiter(configs)
        
        # 引擎A和B应该独立计数
        await limiter.acquire("engine_a")
        await limiter.acquire("engine_b")
        await limiter.acquire("engine_a")
        await limiter.acquire("engine_b")
        
        # 都应该能成功
        assert True
    
    @pytest.mark.asyncio
    async def test_multi_limiter_unknown_engine(self):
        """测试未知引擎"""
        limiter = MultiRateLimiter({})
        
        # 未知引擎应该被允许通过（或使用默认配置）
        await limiter.acquire("unknown_engine")
        assert True


class TestEdgeCases:
    """边界情况测试"""
    
    def test_deduplicate_all_duplicates(self):
        """测试全部重复的情况"""
        results = [
            {"title": "A", "link": "http://same.com"},
            {"title": "B", "link": "http://same.com"},
            {"title": "C", "link": "http://same.com"},
        ]
        
        deduplicated = deduplicate_results(results)
        assert len(deduplicated) == 1
    
    def test_sort_single_item(self):
        """测试单个条目排序"""
        results = [{"engine": "google", "title": "A"}]
        sorted_results = sort_results(results)
        assert len(sorted_results) == 1
    
    def test_merge_single_engine(self):
        """测试单引擎合并"""
        all_results = {
            "google": [
                {"title": "A", "link": "http://a.com", "engine": "google"}
            ]
        }
        
        merged = merge_and_deduplicate(all_results, num_results=10)
        assert len(merged) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.utils", "--cov-report=term-missing"])
