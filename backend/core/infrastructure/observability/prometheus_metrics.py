"""Prometheus metrics集成（业界标准实现）

使用成熟的 prometheus-client库，而不是重复造轮子。
https://github.com/prometheus/client_python
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from functools import wraps
import logging

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    Info,
    start_http_server,
    REGISTRY
)
from prometheus_client.metrics import MetricWrapperBase

logger = logging.getLogger(__name__)


@dataclass
class MetricsConfig:
    """Metrics配置"""
    http_server_port: Optional[int] = None
    prefix: str = "neural_agent"


class Metrics:
    """Metrics管理类
    
    直接使用prometheus-client，避免重复造轮子
    """
    
    def __init__(self, config: Optional[MetricsConfig] = None):
        self.config = config or MetricsConfig()
        # 启动 HTTP 服务器（如果配置了）
        if self.config.http_server_port:
            try:
                start_http_server(self.config.http_server_port)
                logger.info(f"Prometheus metrics server started on port {self.config.http_server_port}")
            except Exception as e:
                logger.warning(f"Could not start Prometheus server: {e}")
    
    # ==================== 计数器 ====================
    # API指标
    API_REQUESTS_TOTAL = Counter(
        "api_requests_total",
        "Total number of API requests",
        ["endpoint", "method", "status_code"]
    )
    
    API_ERRORS_TOTAL = Counter(
        "api_errors_total",
        "Total number of API errors",
        ["endpoint", "error_type"]
    )
    
    # Task指标
    TASKS_CREATED = Counter(
        "tasks_created_total",
        "Total tasks created",
        ["task_type"]
    )
    
    TASKS_COMPLETED = Counter(
        "tasks_completed_total",
        "Total tasks completed",
        ["task_type", "status"]
    )
    
    # LLM指标
    LLM_REQUESTS_TOTAL = Counter(
        "llm_requests_total",
        "Total LLM requests made",
        ["model", "request_type"]
    )
    
    LLM_ERRORS_TOTAL = Counter(
        "llm_errors_total",
        "Total LLM errors",
        ["model", "error_type"]
    )
    
    # 向量存储指标
    VECTOR_STORE_OPS_TOTAL = Counter(
        "vector_store_ops_total",
        "Total vector store operations",
        ["operation", "backend"]
    )
    
    VECTOR_STORE_ERRORS_TOTAL = Counter(
        "vector_store_errors_total",
        "Total vector store errors",
        ["operation", "backend"]
    )
    
    # ==================== 仪表盘 ====================
    ACTIVE_TASKS = Gauge(
        "active_tasks",
        "Number of active tasks"
    )
    
    MEMORY_USAGE_BYTES = Gauge(
        "memory_usage_bytes",
        "Process memory usage in bytes"
    )
    
    CPU_USAGE_PERCENT = Gauge(
        "cpu_usage_percent",
        "Process CPU usage percent"
    )
    
    QUEUE_DEPTH = Gauge(
        "queue_depth",
        "Current queue depth",
        ["queue_name"]
    )
    
    # ==================== 直方图（延迟） ====================
    API_REQUEST_DURATION = Histogram(
        "api_request_duration_seconds",
        "API request duration",
        ["endpoint"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
    )
    
    TASK_PROCESSING_DURATION = Histogram(
        "task_processing_duration_seconds",
        "Task processing duration",
        ["task_type"],
        buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
    )
    
    LLM_REQUEST_DURATION = Histogram(
        "llm_request_duration_seconds",
        "LLM request duration",
        ["model"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
    )
    
    VECTOR_SEARCH_DURATION = Histogram(
        "vector_search_duration_seconds",
        "Vector search duration",
        ["backend"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
    )
    
    # ==================== Summary ====================
    BATCH_EMBEDDING_SIZE = Summary(
        "batch_embedding_size",
        "Size of embedding batches",
        ["model"]
    )
    
    # ==================== 系统信息 ====================
    SYSTEM_INFO = Info(
        "system",
        "System information"
    )
    
    def __init__(self, config: Optional[MetricsConfig] = None):
        self.config = config or MetricsConfig()
        self._started_metrics_server = False
    
    def start_server(self, port: Optional[int] = None) -> None:
        """启动Prometheus metrics HTTP服务器
        
        Args:
            port: Metrics服务器端口，默认使用配置中的端口
        """
        port_to_use = port or self.config.http_server_port
        if not port_to_use:
            logger.info("No port configured for metrics server")
            return
        
        if self._started_metrics_server:
            logger.warning("Metrics server already started")
            return
        
        start_http_server(port_to_use)
        self._started_metrics_server = True
        logger.info(f"Prometheus metrics server started on port {port_to_use}")
        logger.info(f"Metrics available at http://localhost:{port_to_use}/metrics")
    
    def record_api_request(self, endpoint: str, method: str, status_code: int = 200) -> None:
        """记录API请求"""
        self.API_REQUESTS_TOTAL.labels(
            endpoint=endpoint,
            method=method,
            status_code=status_code
        ).inc()
    
    def record_api_error(self, endpoint: str, error_type: str) -> None:
        """记录API错误"""
        self.API_ERRORS_TOTAL.labels(
            endpoint=endpoint,
            error_type=error_type
        ).inc()
    
    def task_created(self, task_type: str) -> None:
        """任务创建"""
        self.TASKS_CREATED.labels(task_type=task_type).inc()
        self.ACTIVE_TASKS.inc()
    
    def task_completed(self, task_type: str, status: str = "success") -> None:
        """任务完成"""
        self.TASKS_COMPLETED.labels(task_type=task_type, status=status).inc()
        self.ACTIVE_TASKS.dec()
    
    def llm_request(self, model: str, request_type: str = "chat") -> None:
        """LLM请求记录"""
        self.LLM_REQUESTS_TOTAL.labels(model=model, request_type=request_type).inc()
    
    def llm_error(self, model: str, error_type: str) -> None:
        """LLM错误记录"""
        self.LLM_ERRORS_TOTAL.labels(model=model, error_type=error_type).inc()
    
    def vector_store_op(self, operation: str, backend: str, success: bool = True) -> None:
        """向量存储操作记录"""
        self.VECTOR_STORE_OPS_TOTAL.labels(
            operation=operation,
            backend=backend
        ).inc()
        
        if not success:
            self.VECTOR_STORE_ERRORS_TOTAL.labels(
                operation=operation,
                backend=backend
            ).inc()
    
    # ==================== 装饰器 ====================
    
    def track_api_request(self, endpoint: str):
        """API请求追踪装饰器"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                status_code = 200
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status_code = 500
                    self.record_api_error(endpoint, type(e).__name__)
                    raise
                finally:
                    duration = time.time() - start_time
                    self.API_REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
                    self.record_api_request(
                        endpoint=endpoint,
                        method=func.__name__.upper(),
                        status_code=status_code
                    )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                status_code = 200
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status_code = 500
                    self.record_api_error(endpoint, type(e).__name__)
                    raise
                finally:
                    duration = time.time() - start_time
                    self.API_REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
                    self.record_api_request(
                        endpoint=endpoint,
                        method=func.__name__.upper(),
                        status_code=status_code
                    )
            
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def track_llm_request(self, model: str = "default"):
        """LLM请求追踪装饰器"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    self.llm_request(model=model, request_type="chat")
                    return result
                except Exception as e:
                    self.llm_error(model=model, error_type=type(e).__name__)
                    raise
                finally:
                    duration = time.time() - start_time
                    self.LLM_REQUEST_DURATION.labels(model=model).observe(duration)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    self.llm_request(model=model, request_type="chat")
                    return result
                except Exception as e:
                    self.llm_error(model=model, error_type=type(e).__name__)
                    raise
                finally:
                    duration = time.time() - start_time
                    self.LLM_REQUEST_DURATION.labels(model=model).observe(duration)
            
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def track_task(self, task_type: str):
        """任务追踪装饰器"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                status = "success"
                
                self.task_created(task_type=task_type)
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception:
                    status = "failed"
                    raise
                finally:
                    duration = time.time() - start_time
                    self.TASK_PROCESSING_DURATION.labels(task_type=task_type).observe(duration)
                    self.task_completed(task_type=task_type, status=status)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                import time
                start_time = time.time()
                status = "success"
                
                self.task_created(task_type=task_type)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    status = "failed"
                    raise
                finally:
                    duration = time.time() - start_time
                    self.TASK_PROCESSING_DURATION.labels(task_type=task_type).observe(duration)
                    self.task_completed(task_type=task_type, status=status)
            
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


# 全局单例
_metrics_instance: Optional[Metrics] = None


def get_metrics() -> Metrics:
    """获取全局Metrics实例
    
    Returns:
        Metrics: 全局Metrics实例
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = Metrics()
    return _metrics_instance


def init_metrics(config: Optional[MetricsConfig] = None) -> Metrics:
    """初始化并返回Metrics实例
    
    Args:
        config: Metrics配置
        
    Returns:
        Metrics: 初始化后的Metrics实例
    """
    global _metrics_instance
    _metrics_instance = Metrics(config=config)
    return _metrics_instance


def track_api_request(endpoint: str):
    """API请求追踪装饰器（便捷函数）
    
    Args:
        endpoint: 端点名称
        
    Returns:
        装饰器函数
    """
    metrics = get_metrics()
    return metrics.track_api_request(endpoint)


def track_llm_call(model: str = "default"):
    """LLM请求追踪装饰器（便捷函数）
    
    Args:
        model: 模型名称
        
    Returns:
        装饰器函数
    """
    metrics = get_metrics()
    return metrics.track_llm_request(model)
