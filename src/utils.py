"""
工具模块 - 搜索结果处理、重试机制、限流保护

提供以下功能：
1. 搜索结果去重和排序
2. 错误重试装饰器（指数退避）
3. API 限流保护（令牌桶算法）
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Callable, Optional
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================
# 搜索结果去重和排序
# ============================================================

def deduplicate_results(
    results: List[Dict[str, Any]],
    key: str = "url"
) -> List[Dict[str, Any]]:
    """
    对搜索结果去重
    
    Args:
        results: 搜索结果列表
        key: 用于去重的键（默认为 "url"）
        
    Returns:
        去重后的结果列表
    """
    seen = set()
    deduplicated = []
    
    for result in results:
        identifier = result.get(key)
        if identifier and identifier not in seen:
            seen.add(identifier)
            deduplicated.append(result)
    
    logger.debug(
        f"Deduplicated results: {len(results)} -> {len(deduplicated)}"
    )
    return deduplicated


def sort_results(
    results: List[Dict[str, Any]],
    engine_priority: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """
    对搜索结果排序
    
    排序规则：
    1. 首先按引擎优先级排序
    2. 同一引擎内保持原始顺序
    
    Args:
        results: 搜索结果列表
        engine_priority: 引擎优先级字典 {引擎名: 优先级分数}
                        分数越高优先级越高
                        
    Returns:
        排序后的结果列表
    """
    if not engine_priority:
        # 默认优先级：Google > Brave > SearXNG > DuckDuckGo
        engine_priority = {
            "google": 4,
            "brave": 3,
            "searxng": 2,
            "duckduckgo": 1,
        }
    
    def get_priority(result: Dict[str, Any]) -> tuple:
        engine = result.get("engine", "unknown")
        priority = engine_priority.get(engine.lower(), 0)
        # 返回负数使高优先级排在前面
        return (-priority, results.index(result))
    
    sorted_results = sorted(results, key=get_priority)
    logger.debug(f"Sorted {len(results)} results by engine priority")
    return sorted_results


def merge_and_deduplicate(
    all_results: Dict[str, List[Dict[str, Any]]],
    num_results: int = 10,
    engine_priority: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """
    合并多个引擎的结果，去重并排序
    
    Args:
        all_results: 所有引擎的结果 {引擎名: [结果列表]}
        num_results: 最终返回的结果数量
        engine_priority: 引擎优先级字典
        
    Returns:
        合并、去重、排序后的结果列表
    """
    # 合并所有结果
    merged = []
    for engine, results in all_results.items():
        for result in results:
            # 确保每个结果都有 engine 字段
            if "engine" not in result:
                result["engine"] = engine
            merged.append(result)
    
    # 去重
    deduplicated = deduplicate_results(merged)
    
    # 排序
    sorted_results = sort_results(deduplicated, engine_priority)
    
    # 截取指定数量
    final_results = sorted_results[:num_results]
    
    logger.info(
        f"Merged results: {len(merged)} -> "
        f"deduplicated: {len(deduplicated)} -> "
        f"final: {len(final_results)}"
    )
    
    return final_results


# ============================================================
# 错误重试机制
# ============================================================

def async_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    异步函数重试装饰器（指数退避）
    
    Args:
        max_attempts: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数退避基数
        exceptions: 需要重试的异常类型元组
        
    Usage:
        @async_retry(max_attempts=3, initial_delay=1.0)
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试失败，抛出异常
                        logger.error(
                            f"{func.__name__} failed after "
                            f"{max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # 计算延迟时间（指数退避）
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # 理论上不会到达这里
            raise last_exception
        
        return wrapper
    return decorator


# ============================================================
# API 限流保护（令牌桶算法）
# ============================================================

@dataclass
class RateLimitConfig:
    """限流配置"""
    max_requests: int  # 时间窗口内最大请求数
    time_window: float  # 时间窗口（秒）
    
    @property
    def rate(self) -> float:
        """每秒生成的令牌数"""
        return self.max_requests / self.time_window


class RateLimiter:
    """
    API 限流器（令牌桶算法）
    
    实现了令牌桶算法来限制 API 调用频率
    每个时间窗口内允许的最大请求数是固定的
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        初始化限流器
        
        Args:
            config: 限流配置
        """
        self.config = config
        self.tokens = float(config.max_requests)  # 当前令牌数
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        
        logger.info(
            f"RateLimiter initialized: "
            f"{config.max_requests} requests per {config.time_window}s "
            f"(rate: {config.rate:.2f} req/s)"
        )
    
    def _add_tokens(self):
        """添加令牌（基于时间流逝）"""
        now = time.time()
        elapsed = now - self.last_update
        
        # 根据经过的时间添加令牌
        new_tokens = elapsed * self.config.rate
        self.tokens = min(
            self.config.max_requests,
            self.tokens + new_tokens
        )
        self.last_update = now
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        获取令牌（阻塞直到获得令牌）
        
        Args:
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取令牌
        """
        async with self.lock:
            while True:
                self._add_tokens()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    logger.debug(
                        f"Token acquired. Remaining: {self.tokens:.2f}"
                    )
                    return True
                
                # 计算需要等待的时间
                needed_tokens = tokens - self.tokens
                wait_time = needed_tokens / self.config.rate
                
                logger.debug(
                    f"Rate limit reached. Waiting {wait_time:.2f}s..."
                )
                
                await asyncio.sleep(wait_time)
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌（非阻塞）
        
        Args:
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取令牌
        """
        async with self.lock:
            self._add_tokens()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(
                    f"Token acquired. Remaining: {self.tokens:.2f}"
                )
                return True
            
            logger.debug(
                f"Rate limit reached. Tokens available: {self.tokens:.2f}"
            )
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取限流器状态
        
        Returns:
            状态字典
        """
        self._add_tokens()
        return {
            "available_tokens": round(self.tokens, 2),
            "max_tokens": self.config.max_requests,
            "rate": round(self.config.rate, 2),
            "utilization": round(
                (1 - self.tokens / self.config.max_requests) * 100, 2
            ),
        }


class MultiRateLimiter:
    """
    多引擎限流管理器
    
    为不同的搜索引擎维护独立的限流器
    """
    
    def __init__(self, configs: Optional[Dict[str, RateLimitConfig]] = None):
        """
        初始化多引擎限流器
        
        Args:
            configs: 引擎限流配置字典 {引擎名: RateLimitConfig}
                    如果为 None，使用默认配置
        """
        if configs is None:
            # 默认配置（基于各引擎的实际限制）
            # 注意：DuckDuckGo 和 SearXNG 如果是自托管，
            # 可以设置很大的限额或完全不限制
            configs = {
                "google": RateLimitConfig(
                    max_requests=100, time_window=86400
                ),  # 100/天 (Google API 限制)
                "brave": RateLimitConfig(
                    max_requests=2000, time_window=2592000
                ),  # 2000/月 (Brave API 限制)
                # DuckDuckGo: 开源免费，无官方限制
                # 设置宽松限制只是为了防止过度请求
                "duckduckgo": RateLimitConfig(
                    max_requests=1000, time_window=60
                ),  # 1000/分钟（非常宽松）
                # SearXNG: 自托管实例，无限制
                # 设置宽松限制只是为了保护服务器
                "searxng": RateLimitConfig(
                    max_requests=1000, time_window=60
                ),  # 1000/分钟（非常宽松）
            }
        
        self.limiters: Dict[str, RateLimiter] = {
            engine: RateLimiter(config)
            for engine, config in configs.items()
        }
        
        logger.info(
            f"MultiRateLimiter initialized with "
            f"{len(self.limiters)} engines"
        )
    
    async def acquire(self, engine: str, tokens: int = 1) -> bool:
        """
        为指定引擎获取令牌
        
        Args:
            engine: 引擎名
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取令牌
        """
        limiter = self.limiters.get(engine.lower())
        if limiter is None:
            logger.warning(f"No rate limiter for engine: {engine}")
            return True  # 没有配置限流器，直接通过
        
        return await limiter.acquire(tokens)
    
    async def try_acquire(self, engine: str, tokens: int = 1) -> bool:
        """
        为指定引擎尝试获取令牌（非阻塞）
        
        Args:
            engine: 引擎名
            tokens: 需要的令牌数
            
        Returns:
            是否成功获取令牌
        """
        limiter = self.limiters.get(engine.lower())
        if limiter is None:
            logger.warning(f"No rate limiter for engine: {engine}")
            return True
        
        return await limiter.try_acquire(tokens)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有引擎的限流状态
        
        Returns:
            所有引擎的状态字典
        """
        return {
            engine: limiter.get_status()
            for engine, limiter in self.limiters.items()
        }
