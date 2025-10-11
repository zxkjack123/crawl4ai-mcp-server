"""
持久化缓存模块

提供基于 SQLite 的持久化缓存，支持跨会话缓存共享和预热。
"""

import sqlite3
import hashlib
import time
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    query: str
    engine: str
    num_results: int
    results: str  # JSON 字符串
    timestamp: float
    hits: int = 0
    
    def get_results(self) -> List[Dict]:
        """获取结果列表"""
        return json.loads(self.results)
    
    def is_expired(self, ttl: int) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > ttl


class PersistentCache:
    """持久化搜索结果缓存管理器（基于 SQLite）"""

    def __init__(
        self,
        db_path: str = "cache/search_cache.db",
        ttl: int = 3600,
        max_size: int = 10000,
        enable_memory_cache: bool = True
    ):
        """
        初始化持久化缓存管理器

        Args:
            db_path: SQLite 数据库路径
            ttl: 缓存过期时间（秒），默认1小时
            max_size: 最大缓存条目数，默认10000
            enable_memory_cache: 是否启用内存缓存（加速访问）
        """
        self.db_path = Path(db_path)
        self.ttl = ttl
        self.max_size = max_size
        self.enable_memory_cache = enable_memory_cache
        
        # 内存缓存（可选）
        self._memory_cache: Dict[str, CacheEntry] = {}
        
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        logger.info(
            f"Persistent cache initialized: db={db_path}, "
            f"ttl={ttl}s, max_size={max_size}, "
            f"memory_cache={enable_memory_cache}"
        )

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建缓存表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    key TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    engine TEXT NOT NULL,
                    num_results INTEGER NOT NULL,
                    results TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    hits INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON search_cache(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_engine 
                ON search_cache(query, engine)
            """)
            
            logger.debug("Database initialized successfully")

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
        
        # 先检查内存缓存
        if self.enable_memory_cache and key in self._memory_cache:
            entry = self._memory_cache[key]
            if not entry.is_expired(self.ttl):
                logger.debug(f"Memory cache hit: {query[:50]}...")
                return entry.get_results()
            else:
                # 过期，从内存缓存删除
                del self._memory_cache[key]
        
        # 从数据库查询
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM search_cache 
                    WHERE key = ? 
                    LIMIT 1
                    """,
                    (key,)
                )
                row = cursor.fetchone()
                
                if not row:
                    logger.debug(f"Cache miss: {query[:50]}...")
                    return None
                
                # 检查是否过期
                timestamp = row['timestamp']
                if time.time() - timestamp > self.ttl:
                    logger.debug(f"Cache expired: {query[:50]}...")
                    # 删除过期条目
                    cursor.execute(
                        "DELETE FROM search_cache WHERE key = ?",
                        (key,)
                    )
                    return None
                
                # 更新访问计数
                cursor.execute(
                    """
                    UPDATE search_cache 
                    SET hits = hits + 1, updated_at = ? 
                    WHERE key = ?
                    """,
                    (time.time(), key)
                )
                
                results = json.loads(row['results'])
                
                # 更新内存缓存
                if self.enable_memory_cache:
                    entry = CacheEntry(
                        key=key,
                        query=row['query'],
                        engine=row['engine'],
                        num_results=row['num_results'],
                        results=row['results'],
                        timestamp=timestamp,
                        hits=row['hits'] + 1
                    )
                    self._memory_cache[key] = entry
                
                logger.info(
                    f"Cache hit: {query[:50]}... "
                    f"(hits={row['hits'] + 1}, "
                    f"age={int(time.time() - timestamp)}s)"
                )
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None

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
        key = self._generate_key(query, engine, num_results)
        results_json = json.dumps(results, ensure_ascii=False)
        current_time = time.time()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查缓存大小
                cursor.execute(
                    "SELECT COUNT(*) as count FROM search_cache"
                )
                count = cursor.fetchone()['count']
                
                if count >= self.max_size:
                    # 删除最老的条目
                    cursor.execute(
                        """
                        DELETE FROM search_cache 
                        WHERE key IN (
                            SELECT key FROM search_cache 
                            ORDER BY timestamp ASC 
                            LIMIT 100
                        )
                        """
                    )
                    logger.debug("Cache evicted: 100 oldest entries")
                
                # 插入或更新
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO search_cache 
                    (key, query, engine, num_results, results, 
                     timestamp, hits, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                    """,
                    (key, query, engine, num_results, results_json,
                     current_time, current_time, current_time)
                )
                
                # 更新内存缓存
                if self.enable_memory_cache:
                    entry = CacheEntry(
                        key=key,
                        query=query,
                        engine=engine,
                        num_results=num_results,
                        results=results_json,
                        timestamp=current_time,
                        hits=0
                    )
                    self._memory_cache[key] = entry
                
                logger.debug(f"Cache set: {query[:50]}...")
                
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")

    def clear(self) -> int:
        """
        清空所有缓存

        Returns:
            删除的条目数
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM search_cache")
                count = cursor.fetchone()['count']
                cursor.execute("DELETE FROM search_cache")
                
            # 清空内存缓存
            self._memory_cache.clear()
            
            logger.info(f"Cache cleared: {count} entries removed")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    def remove_expired(self) -> int:
        """
        删除所有过期的缓存条目

        Returns:
            删除的条目数
        """
        try:
            expiry_time = time.time() - self.ttl
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM search_cache "
                    "WHERE timestamp < ?",
                    (expiry_time,)
                )
                count = cursor.fetchone()['count']
                
                cursor.execute(
                    "DELETE FROM search_cache WHERE timestamp < ?",
                    (expiry_time,)
                )
            
            # 清理内存缓存中的过期条目
            expired_keys = [
                k for k, v in self._memory_cache.items()
                if v.is_expired(self.ttl)
            ]
            for key in expired_keys:
                del self._memory_cache[key]
            
            if count > 0:
                logger.info(
                    f"Removed {count} expired cache entries "
                    f"(memory: {len(expired_keys)})"
                )
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to remove expired entries: {e}")
            return 0

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 总条目数
                cursor.execute(
                    "SELECT COUNT(*) as count FROM search_cache"
                )
                total_count = cursor.fetchone()['count']
                
                # 总命中数
                cursor.execute(
                    "SELECT SUM(hits) as total_hits FROM search_cache"
                )
                total_hits = cursor.fetchone()['total_hits'] or 0
                
                # 平均年龄
                current_time = time.time()
                cursor.execute(
                    "SELECT AVG(? - timestamp) as avg_age "
                    "FROM search_cache",
                    (current_time,)
                )
                avg_age = cursor.fetchone()['avg_age'] or 0
                
                # 各引擎统计
                cursor.execute(
                    """
                    SELECT engine, COUNT(*) as count 
                    FROM search_cache 
                    GROUP BY engine
                    """
                )
                engine_counts = {
                    row['engine']: row['count'] 
                    for row in cursor.fetchall()
                }
                
                return {
                    "type": "persistent",
                    "db_path": str(self.db_path),
                    "size": total_count,
                    "max_size": self.max_size,
                    "total_hits": total_hits,
                    "ttl": self.ttl,
                    "avg_age_seconds": int(avg_age),
                    "memory_cache_size": len(self._memory_cache),
                    "memory_cache_enabled": self.enable_memory_cache,
                    "engines": engine_counts
                }
                
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def export_to_json(self, filepath: str) -> int:
        """
        导出缓存到 JSON 文件

        Args:
            filepath: 导出文件路径

        Returns:
            导出的条目数
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM search_cache")
                rows = cursor.fetchall()
                
                entries = []
                for row in rows:
                    entries.append({
                        "key": row['key'],
                        "query": row['query'],
                        "engine": row['engine'],
                        "num_results": row['num_results'],
                        "results": json.loads(row['results']),
                        "timestamp": row['timestamp'],
                        "hits": row['hits'],
                        "created_at": row['created_at'],
                        "updated_at": row['updated_at']
                    })
                
                data = {
                    "ttl": self.ttl,
                    "max_size": self.max_size,
                    "export_time": time.time(),
                    "entries": entries
                }
                
                output_path = Path(filepath)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(
                    f"Cache exported to {filepath}: {len(entries)} entries"
                )
                return len(entries)
                
        except Exception as e:
            logger.error(f"Failed to export cache: {e}")
            return 0

    def import_from_json(self, filepath: str) -> int:
        """
        从 JSON 文件导入缓存

        Args:
            filepath: 导入文件路径

        Returns:
            导入的条目数
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for entry_dict in data.get('entries', []):
                    # 检查是否过期
                    if time.time() - entry_dict['timestamp'] > self.ttl:
                        continue
                    
                    results_json = json.dumps(
                        entry_dict['results'],
                        ensure_ascii=False
                    )
                    
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO search_cache 
                        (key, query, engine, num_results, results, 
                         timestamp, hits, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            entry_dict['key'],
                            entry_dict['query'],
                            entry_dict['engine'],
                            entry_dict['num_results'],
                            results_json,
                            entry_dict['timestamp'],
                            entry_dict['hits'],
                            entry_dict.get('created_at', entry_dict['timestamp']),
                            entry_dict.get('updated_at', time.time())
                        )
                    )
                    count += 1
            
            logger.info(
                f"Cache imported from {filepath}: {count} entries"
            )
            return count
            
        except Exception as e:
            logger.error(f"Failed to import cache: {e}")
            return 0

    def warmup(
        self,
        queries: List[Dict[str, any]],
        search_func
    ) -> Dict[str, int]:
        """
        缓存预热

        Args:
            queries: 查询列表，每个查询是包含 query, engine, num_results 的字典
            search_func: 搜索函数，用于执行实际搜索

        Returns:
            预热统计信息
        """
        stats = {
            "total": len(queries),
            "success": 0,
            "failed": 0,
            "cached": 0
        }
        
        logger.info(f"Starting cache warmup with {len(queries)} queries...")
        
        for query_dict in queries:
            query = query_dict.get('query')
            engine = query_dict.get('engine', 'auto')
            num_results = query_dict.get('num_results', 10)
            
            try:
                # 检查是否已缓存
                cached = self.get(query, engine, num_results)
                if cached:
                    stats['cached'] += 1
                    logger.debug(f"Already cached: {query[:50]}...")
                    continue
                
                # 执行搜索
                results = search_func(query, num_results, engine)
                if results:
                    self.set(query, engine, num_results, results)
                    stats['success'] += 1
                    logger.debug(f"Warmed up: {query[:50]}...")
                else:
                    stats['failed'] += 1
                    logger.debug(f"No results: {query[:50]}...")
                    
            except Exception as e:
                stats['failed'] += 1
                logger.error(f"Warmup failed for '{query}': {e}")
        
        logger.info(
            f"Cache warmup completed: "
            f"{stats['success']} success, "
            f"{stats['cached']} cached, "
            f"{stats['failed']} failed"
        )
        
        return stats

    def vacuum(self) -> None:
        """
        优化数据库（VACUUM）

        清理已删除的数据，压缩数据库文件
        """
        try:
            with self._get_connection() as conn:
                conn.execute("VACUUM")
            logger.info("Database vacuumed successfully")
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
