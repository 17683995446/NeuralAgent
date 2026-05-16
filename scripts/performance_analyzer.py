"""系统性能分析工具

提供详细的性能分析功能，包括：
- 操作性能分析
- 资源使用分析
- 瓶颈识别
- 优化建议生成
"""
import json
import time
import psutil
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    threads: int
    open_files: int
    network_connections: int


@dataclass
class BottleneckInfo:
    """瓶颈信息"""
    component: str
    severity: str  # critical, warning, info
    metric: str
    value: float
    threshold: float
    description: str
    suggestion: str


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, sample_interval: float = 1.0):
        """初始化分析器
        
        Args:
            sample_interval: 采样间隔（秒）
        """
        self.sample_interval = sample_interval
        self.snapshots: List[PerformanceSnapshot] = []
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # 阈值配置
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "threads": 100,
            "response_time": 1.0,  # 秒
            "error_rate": 0.05,  # 5%
            "queue_length": 50
        }
    
    def start_monitoring(self):
        """启动性能监控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """监控循环"""
        process = psutil.Process()
        
        while self._monitoring:
            try:
                snapshot = PerformanceSnapshot(
                    timestamp=datetime.now().isoformat(),
                    cpu_percent=process.cpu_percent(interval=0.1),
                    memory_percent=process.memory_percent(),
                    memory_used_mb=process.memory_info().rss / 1024 / 1024,
                    threads=process.num_threads(),
                    open_files=len(process.open_files()),
                    network_connections=len(process.connections())
                )
                
                with self._lock:
                    self.snapshots.append(snapshot)
                    # 保留最近1000个快照
                    if len(self.snapshots) > 1000:
                        self.snapshots = self.snapshots[-1000:]
                
                time.sleep(self.sample_interval)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.sample_interval)
    
    def record_operation(self, operation: str, duration: float):
        """记录操作耗时
        
        Args:
            operation: 操作名称
            duration: 耗时（秒）
        """
        with self._lock:
            self.operation_times[operation].append(duration)
            # 保留最近10000条记录
            if len(self.operation_times[operation]) > 10000:
                self.operation_times[operation] = self.operation_times[operation][-10000:]
    
    def analyze_bottlenecks(self) -> List[BottleneckInfo]:
        """分析系统瓶颈
        
        Returns:
            瓶颈信息列表
        """
        bottlenecks = []
        
        # 分析CPU
        cpu_avg = self._get_average_cpu()
        if cpu_avg > self.thresholds["cpu_percent"]:
            bottlenecks.append(BottleneckInfo(
                component="CPU",
                severity="critical" if cpu_avg > 90 else "warning",
                metric="cpu_percent",
                value=cpu_avg,
                threshold=self.thresholds["cpu_percent"],
                description=f"CPU使用率平均 {cpu_avg:.1f}%",
                suggestion="考虑增加工作进程或优化计算密集型操作"
            ))
        
        # 分析内存
        memory_avg = self._get_average_memory()
        if memory_avg > self.thresholds["memory_percent"]:
            bottlenecks.append(BottleneckInfo(
                component="Memory",
                severity="critical" if memory_avg > 95 else "warning",
                metric="memory_percent",
                value=memory_avg,
                threshold=self.thresholds["memory_percent"],
                description=f"内存使用率平均 {memory_avg:.1f}%",
                suggestion="检查内存泄漏或增加内存限制"
            ))
        
        # 分析线程数
        threads_avg = self._get_average_threads()
        if threads_avg > self.thresholds["threads"]:
            bottlenecks.append(BottleneckInfo(
                component="Threading",
                severity="warning",
                metric="threads",
                value=threads_avg,
                threshold=self.thresholds["threads"],
                description=f"平均线程数 {threads_avg:.0f}",
                suggestion="考虑使用线程池或异步处理减少线程创建"
            ))
        
        # 分析慢操作
        slow_ops = self._find_slow_operations()
        for op, avg_time, p95_time in slow_ops:
            bottlenecks.append(BottleneckInfo(
                component="Operation",
                severity="warning",
                metric=op,
                value=avg_time,
                threshold=self.thresholds["response_time"],
                description=f"操作 {op} 平均耗时 {avg_time*1000:.1f}ms, P95: {p95_time*1000:.1f}ms",
                suggestion=f"优化 {op} 实现或添加缓存"
            ))
        
        return bottlenecks
    
    def _get_average_cpu(self) -> float:
        """获取平均CPU使用率"""
        if not self.snapshots:
            return 0.0
        return sum(s.cpu_percent for s in self.snapshots) / len(self.snapshots)
    
    def _get_average_memory(self) -> float:
        """获取平均内存使用率"""
        if not self.snapshots:
            return 0.0
        return sum(s.memory_percent for s in self.snapshots) / len(self.snapshots)
    
    def _get_average_threads(self) -> float:
        """获取平均线程数"""
        if not self.snapshots:
            return 0.0
        return sum(s.threads for s in self.snapshots) / len(self.snapshots)
    
    def _find_slow_operations(self) -> List[tuple]:
        """查找慢操作"""
        slow_ops = []
        
        for op, times in self.operation_times.items():
            if not times:
                continue
            
            times_sorted = sorted(times)
            avg_time = sum(times) / len(times)
            p95_time = times_sorted[int(len(times) * 0.95)] if len(times) > 20 else avg_time
            
            if p95_time > self.thresholds["response_time"]:
                slow_ops.append((op, avg_time, p95_time))
        
        return sorted(slow_ops, key=lambda x: x[1], reverse=True)[:10]
    
    def generate_report(self, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """生成性能分析报告
        
        Args:
            duration_seconds: 分析时间窗口
            
        Returns:
            报告字典
        """
        with self._lock:
            # 过滤时间窗口内的快照
            if duration_seconds:
                cutoff = datetime.now() - timedelta(seconds=duration_seconds)
                recent_snapshots = [
                    s for s in self.snapshots
                    if datetime.fromisoformat(s.timestamp) >= cutoff
                ]
            else:
                recent_snapshots = self.snapshots.copy()
            
            # 计算统计数据
            stats = {
                "analysis_time": datetime.now().isoformat(),
                "duration_seconds": duration_seconds or len(recent_snapshots) * self.sample_interval,
                "snapshot_count": len(recent_snapshots),
                "cpu": {
                    "avg": sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots) if recent_snapshots else 0,
                    "max": max((s.cpu_percent for s in recent_snapshots), default=0),
                    "min": min((s.cpu_percent for s in recent_snapshots), default=0)
                },
                "memory": {
                    "avg_percent": sum(s.memory_percent for s in recent_snapshots) / len(recent_snapshots) if recent_snapshots else 0,
                    "avg_mb": sum(s.memory_used_mb for s in recent_snapshots) / len(recent_snapshots) if recent_snapshots else 0,
                    "max_mb": max((s.memory_used_mb for s in recent_snapshots), default=0)
                },
                "threads": {
                    "avg": sum(s.threads for s in recent_snapshots) / len(recent_snapshots) if recent_snapshots else 0,
                    "max": max((s.threads for s in recent_snapshots), default=0)
                }
            }
            
            # 操作统计
            operation_stats = {}
            for op, times in self.operation_times.items():
                if not times:
                    continue
                times_sorted = sorted(times)
                operation_stats[op] = {
                    "count": len(times),
                    "avg_ms": (sum(times) / len(times)) * 1000,
                    "min_ms": min(times) * 1000,
                    "max_ms": max(times) * 1000,
                    "p50_ms": times_sorted[int(len(times) * 0.5)] * 1000,
                    "p95_ms": times_sorted[int(len(times) * 0.95)] * 1000,
                    "p99_ms": times_sorted[int(len(times) * 0.99)] * 1000
                }
            
            stats["operations"] = operation_stats
            
            # 瓶颈分析
            bottlenecks = self.analyze_bottlenecks()
            stats["bottlenecks"] = [asdict(b) for b in bottlenecks]
            
            # 优化建议
            stats["recommendations"] = self._generate_recommendations(bottlenecks, operation_stats)
            
            return stats
    
    def _generate_recommendations(
        self,
        bottlenecks: List[BottleneckInfo],
        operation_stats: Dict
    ) -> List[Dict[str, str]]:
        """生成优化建议"""
        recommendations = []
        
        # 基于瓶颈的建议
        for bottleneck in bottlenecks:
            if bottleneck.severity in ("critical", "warning"):
                recommendations.append({
                    "priority": bottleneck.severity,
                    "area": bottleneck.component,
                    "issue": bottleneck.description,
                    "suggestion": bottleneck.suggestion
                })
        
        # 基于操作统计的建议
        for op, stats in operation_stats.items():
            if stats["p95_ms"] > 1000:  # > 1秒
                recommendations.append({
                    "priority": "warning",
                    "area": "Operation",
                    "issue": f"操作 {op} P95延迟超过1秒",
                    "suggestion": f"考虑添加缓存或优化算法"
                })
        
        return recommendations
    
    def export_to_json(self, filename: str, duration_seconds: Optional[int] = None):
        """导出报告到JSON文件
        
        Args:
            filename: 文件名
            duration_seconds: 分析时间窗口
        """
        report = self.generate_report(duration_seconds)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report exported to {filename}")
    
    def get_live_stats(self) -> Dict[str, Any]:
        """获取实时统计"""
        if not self.snapshots:
            return {}
        
        latest = self.snapshots[-1]
        return {
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "memory_mb": latest.memory_used_mb,
            "threads": latest.threads,
            "snapshots_collected": len(self.snapshots)
        }


class ProfilerContext:
    """性能分析上下文管理器"""
    
    def __init__(self, analyzer: PerformanceAnalyzer, operation: str):
        self.analyzer = analyzer
        self.operation = operation
        self.start_time: float = 0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.analyzer.record_operation(self.operation, duration)


# 全局实例
_global_analyzer: Optional[PerformanceAnalyzer] = None


def get_performance_analyzer() -> PerformanceAnalyzer:
    """获取全局性能分析器"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = PerformanceAnalyzer()
    return _global_analyzer


def profile(operation: str):
    """快速性能分析装饰器"""
    analyzer = get_performance_analyzer()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ProfilerContext(analyzer, operation):
                return func(*args, **kwargs)
        return wrapper
    return decorator
