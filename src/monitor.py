"""
监控和日志系统

提供以下功能：
1. 结构化日志配置
2. 性能指标收集
3. 统计报告生成
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import threading


# ============================================================
# 结构化日志配置
# ============================================================

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    配置结构化日志
    
    Args:
        level: 日志级别
        log_file: 日志文件路径（可选）
        log_format: 日志格式（可选）
        
    Returns:
        配置好的 logger
    """
    if log_format is None:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        )
    
    # 配置根 logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    logger = logging.getLogger("crawl4ai_mcp_server")
    logger.setLevel(level)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_file}")
    
    return logger


class StructuredLogger:
    """
    结构化日志记录器
    
    记录带有结构化数据的日志，便于后续分析
    """
    
    def __init__(self, logger: logging.Logger):
        """
        初始化结构化日志记录器
        
        Args:
            logger: 基础 logger
        """
        self.logger = logger
    
    def log_search(
        self,
        query: str,
        engine: str,
        num_results: int,
        duration: float,
        success: bool,
        cached: bool = False,
        error: Optional[str] = None
    ):
        """
        记录搜索操作
        
        Args:
            query: 搜索查询
            engine: 搜索引擎
            num_results: 结果数量
            duration: 耗时（秒）
            success: 是否成功
            cached: 是否使用缓存
            error: 错误信息（如果失败）
        """
        log_data = {
            "event": "search",
            "query": query,
            "engine": engine,
            "num_results": num_results,
            "duration": round(duration, 3),
            "success": success,
            "cached": cached,
        }
        
        if error:
            log_data["error"] = str(error)
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"Search {engine}: {query} - "
            f"{'success' if success else 'failed'} "
            f"({duration:.3f}s, cached={cached})",
            extra={"structured": log_data}
        )
    
    def log_cache_operation(
        self,
        operation: str,
        details: Dict[str, Any]
    ):
        """
        记录缓存操作
        
        Args:
            operation: 操作类型（hit/miss/set/clear/export/import）
            details: 操作详情
        """
        log_data = {
            "event": "cache",
            "operation": operation,
            **details
        }
        
        self.logger.debug(
            f"Cache {operation}: {details}",
            extra={"structured": log_data}
        )
    
    def log_rate_limit(
        self,
        engine: str,
        wait_time: float,
        tokens_available: float
    ):
        """
        记录限流事件
        
        Args:
            engine: 搜索引擎
            wait_time: 等待时间（秒）
            tokens_available: 可用令牌数
        """
        log_data = {
            "event": "rate_limit",
            "engine": engine,
            "wait_time": round(wait_time, 3),
            "tokens_available": round(tokens_available, 2),
        }
        
        self.logger.warning(
            f"Rate limit reached for {engine}, "
            f"waiting {wait_time:.3f}s",
            extra={"structured": log_data}
        )


# ============================================================
# 性能指标收集
# ============================================================

@dataclass
class SearchMetrics:
    """单次搜索的指标"""
    query: str
    engine: str
    start_time: float
    end_time: float = 0.0
    success: bool = False
    cached: bool = False
    num_results: int = 0
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """搜索耗时（秒）"""
        return self.end_time - self.start_time if self.end_time else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "engine": self.engine,
            "duration": round(self.duration, 3),
            "success": self.success,
            "cached": self.cached,
            "num_results": self.num_results,
            "error": self.error,
            "timestamp": datetime.fromtimestamp(
                self.start_time
            ).isoformat(),
        }


@dataclass
class EngineStats:
    """引擎统计信息"""
    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    total_duration: float = 0.0
    total_results: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.cached_requests / self.total_requests
    
    @property
    def avg_duration(self) -> float:
        """平均耗时"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_duration / self.successful_requests
    
    @property
    def avg_results(self) -> float:
        """平均结果数"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_results / self.successful_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "cached_requests": self.cached_requests,
            "success_rate": round(self.success_rate * 100, 2),
            "cache_hit_rate": round(self.cache_hit_rate * 100, 2),
            "avg_duration": round(self.avg_duration, 3),
            "avg_results": round(self.avg_results, 1),
            "total_duration": round(self.total_duration, 3),
            "error_count": len(self.errors),
        }


class PerformanceMonitor:
    """
    性能监控器
    
    收集和分析搜索性能指标
    """
    
    def __init__(self):
        """初始化性能监控器"""
        self.engine_stats: Dict[str, EngineStats] = defaultdict(
            lambda: EngineStats(name="")
        )
        self.recent_searches: List[SearchMetrics] = []
        self.max_recent_searches = 1000  # 最多保留最近 1000 次搜索
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def record_search(self, metrics: SearchMetrics):
        """
        记录搜索指标
        
        Args:
            metrics: 搜索指标
        """
        with self.lock:
            # 更新引擎统计
            stats = self.engine_stats[metrics.engine]
            stats.name = metrics.engine
            stats.total_requests += 1
            
            if metrics.success:
                stats.successful_requests += 1
                stats.total_duration += metrics.duration
                stats.total_results += metrics.num_results
            else:
                stats.failed_requests += 1
                if metrics.error:
                    stats.errors.append(metrics.error)
            
            if metrics.cached:
                stats.cached_requests += 1
            
            # 记录最近搜索
            self.recent_searches.append(metrics)
            if len(self.recent_searches) > self.max_recent_searches:
                self.recent_searches.pop(0)
    
    def get_engine_stats(
        self,
        engine: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取引擎统计信息
        
        Args:
            engine: 引擎名（可选，None 表示所有引擎）
            
        Returns:
            统计信息字典
        """
        with self.lock:
            if engine:
                stats = self.engine_stats.get(engine)
                return stats.to_dict() if stats else {}
            else:
                return {
                    name: stats.to_dict()
                    for name, stats in self.engine_stats.items()
                }
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """
        获取总体统计信息
        
        Returns:
            总体统计字典
        """
        with self.lock:
            total_requests = sum(
                s.total_requests for s in self.engine_stats.values()
            )
            successful_requests = sum(
                s.successful_requests for s in self.engine_stats.values()
            )
            cached_requests = sum(
                s.cached_requests for s in self.engine_stats.values()
            )
            
            uptime = time.time() - self.start_time
            
            return {
                "uptime_seconds": round(uptime, 1),
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": total_requests - successful_requests,
                "cached_requests": cached_requests,
                "success_rate": round(
                    (successful_requests / total_requests * 100)
                    if total_requests > 0 else 0.0,
                    2
                ),
                "cache_hit_rate": round(
                    (cached_requests / total_requests * 100)
                    if total_requests > 0 else 0.0,
                    2
                ),
                "engines": len(self.engine_stats),
                "recent_searches_count": len(self.recent_searches),
            }
    
    def get_recent_searches(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取最近的搜索记录
        
        Args:
            limit: 返回的记录数量
            
        Returns:
            最近搜索列表
        """
        with self.lock:
            recent = self.recent_searches[-limit:]
            return [m.to_dict() for m in reversed(recent)]
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成完整的性能报告
        
        Returns:
            性能报告字典
        """
        with self.lock:
            return {
                "generated_at": datetime.now().isoformat(),
                "overall": self.get_overall_stats(),
                "engines": self.get_engine_stats(),
                "recent_searches": self.get_recent_searches(20),
            }
    
    def export_report(self, filepath: str):
        """
        导出性能报告到文件
        
        Args:
            filepath: 输出文件路径
        """
        report = self.generate_report()
        
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Performance report exported to: {filepath}")
    
    def reset(self):
        """重置所有统计信息"""
        with self.lock:
            self.engine_stats.clear()
            self.recent_searches.clear()
            self.start_time = time.time()
        
        logging.info("Performance monitor reset")


# ============================================================
# 全局监控实例
# ============================================================

# 全局性能监控器实例
global_monitor = PerformanceMonitor()

# 全局结构化日志记录器
global_structured_logger: Optional[StructuredLogger] = None


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return global_monitor


def get_structured_logger() -> Optional[StructuredLogger]:
    """获取全局结构化日志记录器"""
    return global_structured_logger


def initialize_monitoring(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None
):
    """
    初始化监控系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径（可选）
    """
    global global_structured_logger
    
    logger = setup_logging(log_level, log_file)
    global_structured_logger = StructuredLogger(logger)
    
    logging.info("Monitoring system initialized")
