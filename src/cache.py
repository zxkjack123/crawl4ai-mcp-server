"""
搜索结果缓存模块

提供基于内存的搜索结果缓存，减少API调用次数，节省配额。
"""

import hashlib
import time
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    query: str
    engine: str
    num_results: int
    results: List[Dict]
    timestamp: float
    hits: int = 0

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    def is_expired(self, ttl: int) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > ttl


class SearchCache:
    """搜索结果缓存管理器"""

    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """
        初始化缓存管理器

        Args:
            ttl: 缓存过期时间（秒），默认1小时
            max_size: 最大缓存条目数，默认1000
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # LRU 访问顺序
        logger.info(
            f"Search cache initialized: ttl={ttl}s, "
            f"max_size={max_size}"
        )

    def _generate_key(
        self, query: str, engine: str, num_results: int
    ) -> str:
        """
        生成缓存键

        Args:
            query: 搜索查询
            engine: 搜索引擎
            num_results: 结果数量

        Returns:
            缓存键（MD5哈希）
        """
        key_str = f"{query}|{engine}|{num_results}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(
        self, query: str, engine: str, num_results: int
    ) -> Optional[List[Dict]]:
        """
        从缓存获取结果

        Args:
            query: 搜索查询
            engine: 搜索引擎
            num_results: 结果数量

        Returns:
            缓存的结果，如果不存在或已过期则返回None
        """
        key = self._generate_key(query, engine, num_results)

        if key not in self._cache:
            logger.debug(f"Cache miss: {query[:50]}...")
            return None

        entry = self._cache[key]

        # 检查是否过期
        if entry.is_expired(self.ttl):
            logger.debug(f"Cache expired: {query[:50]}...")
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None

        # 更新访问信息
        entry.hits += 1
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.info(
            f"Cache hit: {query[:50]}... "
            f"(hits={entry.hits}, age={int(time.time() - entry.timestamp)}s)"
        )
        return entry.results

    def set(
        self,
        query: str,
        engine: str,
        num_results: int,
        results: List[Dict]
    ) -> None:
        """
        存储结果到缓存

        Args:
            query: 搜索查询
            engine: 搜索引擎
            num_results: 结果数量
            results: 搜索结果
        """
        # 检查缓存大小，如果满了则删除最老的条目（LRU）
        if len(self._cache) >= self.max_size:
            if self._access_order:
                oldest_key = self._access_order.pop(0)
                if oldest_key in self._cache:
                    del self._cache[oldest_key]
                    logger.debug(f"Cache evicted (LRU): {oldest_key}")

        key = self._generate_key(query, engine, num_results)
        entry = CacheEntry(
            query=query,
            engine=engine,
            num_results=num_results,
            results=results,
            timestamp=time.time(),
            hits=0
        )

        self._cache[key] = entry
        self._access_order.append(key)

        logger.debug(
            f"Cache set: {query[:50]}... "
            f"(size={len(self._cache)}/{self.max_size})"
        )

    def clear(self) -> None:
        """清空所有缓存"""
        size = len(self._cache)
        self._cache.clear()
        self._access_order.clear()
        logger.info(f"Cache cleared: {size} entries removed")

    def remove_expired(self) -> int:
        """
        删除所有过期的缓存条目

        Returns:
            删除的条目数
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired(self.ttl)
        ]

        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)

        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        total_hits = sum(entry.hits for entry in self._cache.values())
        avg_age = 0
        if self._cache:
            current_time = time.time()
            avg_age = sum(
                current_time - entry.timestamp
                for entry in self._cache.values()
            ) / len(self._cache)

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_hits": total_hits,
            "ttl": self.ttl,
            "avg_age_seconds": int(avg_age)
        }

    def export_to_file(self, filepath: str) -> None:
        """
        导出缓存到文件

        Args:
            filepath: 导出文件路径
        """
        data = {
            "ttl": self.ttl,
            "max_size": self.max_size,
            "entries": [
                entry.to_dict()
                for entry in self._cache.values()
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Cache exported to {filepath}")

    def import_from_file(self, filepath: str) -> int:
        """
        从文件导入缓存

        Args:
            filepath: 导入文件路径

        Returns:
            导入的条目数
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0
            for entry_dict in data.get('entries', []):
                entry = CacheEntry(**entry_dict)
                if not entry.is_expired(self.ttl):
                    key = self._generate_key(
                        entry.query,
                        entry.engine,
                        entry.num_results
                    )
                    self._cache[key] = entry
                    self._access_order.append(key)
                    count += 1

            logger.info(f"Cache imported from {filepath}: {count} entries")
            return count

        except Exception as e:
            logger.error(f"Failed to import cache: {e}")
            return 0
