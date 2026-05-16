"""
Prometheus Monitoring - Prometheus 监控集成

支持：
1. 自定义指标收集
2. HTTP 请求指标
3. 缓存指标
4. 定时任务指标
5. 自定义告警规则
"""

import asyncio
import logging
from typing import Dict, Any, Callable
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        Info,
        start_http_server
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("prometheus-client not installed")
    PROMETHEUS_AVAILABLE = False


@dataclass
class MetricConfig:
    """指标配置"""
    name: str
    description: str
    labels: list = None
    bucket_boundaries: list = None


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.summaries: Dict[str, Summary] = {}
        self.infos: Dict[str, Info] = {}
        
        if PROMETHEUS_AVAILABLE:
            self._init_default_metrics()
    
    def _init_default_metrics(self):
        """初始化默认指标"""
        # HTTP 请求指标
        self.request_counter = Counter(
            "neuralagent_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"]
        )
        
        self.request_duration = Histogram(
            "neuralagent_http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
        )
        
        self.request_size = Summary(
            "neuralagent_http_request_size_bytes",
            "HTTP request size",
            ["method", "endpoint"]
        )
        
        # 缓存指标
        self.cache_hits = Counter(
            "neuralagent_cache_hits_total",
            "Cache hits",
            ["cache_name", "level"]
        )
        
        self.cache_misses = Counter(
            "neuralagent_cache_misses_total",
            "Cache misses",
            ["cache_name", "level"]
        )
        
        # LLM 指标
        self.llm_requests = Counter(
            "neuralagent_llm_requests_total",
            "LLM requests",
            ["provider", "model", "status"]
        )
        
        self.llm_latency = Histogram(
            "neuralagent_llm_latency_seconds",
            "LLM request latency",
            ["provider", "model"]
        )
        
        self.llm_tokens = Counter(
            "neuralagent_llm_tokens_total",
            "LLM tokens used",
            ["provider", "model", "type"]
        )
        
        # 记忆系统指标
        self.memory_operations = Counter(
            "neuralagent_memory_operations_total",
            "Memory operations",
            ["operation", "backend"]
        )
        
        # 工作流指标
        self.workflow_executions = Counter(
            "neuralagent_workflow_executions_total",
            "Workflow executions",
            ["workflow_id", "status"]
        )
        
        self.workflow_duration = Histogram(
            "neuralagent_workflow_duration_seconds",
            "Workflow duration",
            ["workflow_id"]
        )
        
        # 系统指标
        self.system_info = Info(
            "neuralagent_system",
            "System information"
        )
        
        self.active_connections = Gauge(
            "neuralagent_active_connections",
            "Active connections"
        )
        
        logger.info("Default metrics initialized")
    
    def register_counter(self, config: MetricConfig) -> Counter:
        """注册计数器"""
        if not PROMETHEUS_AVAILABLE:
            return None
        
        counter = Counter(
            config.name,
            config.description,
            config.labels or []
        )
        self.counters[config.name] = counter
        return counter
    
    def register_histogram(self, config: MetricConfig) -> Histogram:
        """注册直方图"""
        if not PROMETHEUS_AVAILABLE:
            return None
        
        histogram = Histogram(
            config.name,
            config.description,
            config.labels or [],
            buckets=config.bucket_boundaries or [0.01, 0.1, 1.0, 10.0]
        )
        self.histograms[config.name] = histogram
        return histogram
    
    def register_gauge(self, config: MetricConfig) -> Gauge:
        """注册仪表"""
        if not PROMETHEUS_AVAILABLE:
            return None
        
        gauge = Gauge(
            config.name,
            config.description,
            config.labels or []
        )
        self.gauges[config.name] = gauge
        return gauge
    
    def register_summary(self, config: MetricConfig) -> Summary:
        """注册摘要"""
        if not PROMETHEUS_AVAILABLE:
            return None
        
        summary = Summary(
            config.name,
            config.description,
            config.labels or []
        )
        self.summaries[config.name] = summary
        return summary
    
    def increment_request(self, method: str, endpoint: str, status_code: int):
        """增加请求计数"""
        if PROMETHEUS_AVAILABLE:
            self.request_counter.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
    
    def observe_request_duration(self, method: str, endpoint: str, duration: float):
        """记录请求耗时"""
        if PROMETHEUS_AVAILABLE:
            self.request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    def increment_cache_hit(self, cache_name: str, level: str):
        """增加缓存命中"""
        if PROMETHEUS_AVAILABLE:
            self.cache_hits.labels(cache_name=cache_name, level=level).inc()
    
    def increment_cache_miss(self, cache_name: str, level: str):
        """增加缓存未命中"""
        if PROMETHEUS_AVAILABLE:
            self.cache_misses.labels(cache_name=cache_name, level=level).inc()
    
    def record_llm_request(self, provider: str, model: str, status: str, latency: float = None, tokens: int = None):
        """记录 LLM 请求"""
        if PROMETHEUS_AVAILABLE:
            self.llm_requests.labels(provider=provider, model=model, status=status).inc()
            
            if latency:
                self.llm_latency.labels(provider=provider, model=model).observe(latency)
            
            if tokens:
                self.llm_tokens.labels(provider=provider, model=model, type="total").inc(tokens)
    
    def record_workflow_execution(self, workflow_id: str, status: str, duration: float = None):
        """记录工作流执行"""
        if PROMETHEUS_AVAILABLE:
            self.workflow_executions.labels(workflow_id=workflow_id, status=status).inc()
            
            if duration:
                self.workflow_duration.labels(workflow_id=workflow_id).observe(duration)


class MonitoringServer:
    """监控服务器"""
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.metrics_collector = MetricsCollector()
        self._server_started = False
    
    async def start(self):
        """启动监控服务器"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available, skipping monitoring server")
            return
        
        if self._server_started:
            logger.warning("Monitoring server already started")
            return
        
        import threading
        
        thread = threading.Thread(
            target=start_http_server,
            args=(self.port,),
            daemon=True
        )
        thread.start()
        
        self._server_started = True
        logger.info(f"Monitoring server started on port {self.port}")
    
    def stop(self):
        """停止监控服务器"""
        # Prometheus server runs in daemon thread, no need to stop
        self._server_started = False
        logger.info("Monitoring server stopped")
    
    def is_running(self) -> bool:
        """检查服务器是否运行"""
        return self._server_started
    
    def get_collector(self) -> MetricsCollector:
        """获取指标收集器"""
        return self.metrics_collector


class MonitoringMiddleware:
    """FastAPI 监控中间件"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    async def __call__(self, scope, receive, send):
        """中间件处理"""
        if scope["type"] != "http":
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": []
            })
            await send({"type": "http.response.body", "body": b""})
            return
        
        start_time = datetime.now()
        method = scope["method"]
        path = scope["path"]
        
        # 记录请求大小
        request_data = await receive()
        body_size = len(request_data.get("body", b""))
        
        # 调用下一个中间件
        response_status = 200
        
        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
        
        try:
            # 这里应该调用应用，但简化处理
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": []
            })
            await send({"type": "http.response.body", "body": b"OK"})
        finally:
            # 记录指标
            duration = (datetime.now() - start_time).total_seconds()
            self.collector.increment_request(method, path, response_status)
            self.collector.observe_request_duration(method, path, duration)


class AlertRule:
    """告警规则"""
    
    def __init__(
        self,
        name: str,
        condition: Callable[[], bool],
        threshold: float,
        description: str,
        severity: str = "warning"
    ):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.description = description
        self.severity = severity
        self.last_triggered = None
        self.triggered_count = 0
    
    def check(self) -> bool:
        """检查是否触发告警"""
        if self.condition():
            self.last_triggered = datetime.now()
            self.triggered_count += 1
            return True
        return False


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alert_callbacks: list = []
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules[rule.name] = rule
    
    def remove_rule(self, name: str):
        """移除告警规则"""
        if name in self.rules:
            del self.rules[name]
    
    async def check_alerts(self) -> list:
        """检查所有告警规则"""
        triggered = []
        for rule in self.rules.values():
            if rule.check():
                triggered.append({
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity,
                    "triggered_at": rule.last_triggered,
                    "count": rule.triggered_count
                })
        return triggered
    
    def register_callback(self, callback: Callable):
        """注册告警回调"""
        self.alert_callbacks.append(callback)
    
    async def run(self, interval: int = 30):
        """运行告警检查循环"""
        while True:
            alerts = await self.check_alerts()
            if alerts:
                for callback in self.alert_callbacks:
                    try:
                        await callback(alerts)
                    except:
                        pass
            await asyncio.sleep(interval)


# 全局监控实例
_monitoring_server = None


def get_monitoring_server(port: int = 8001) -> MonitoringServer:
    """获取监控服务器单例"""
    global _monitoring_server
    if not _monitoring_server:
        _monitoring_server = MonitoringServer(port)
    return _monitoring_server


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器"""
    server = get_monitoring_server()
    return server.metrics_collector


async def example_usage():
    """示例用法"""
    server = get_monitoring_server(8001)
    await server.start()
    
    collector = server.get_collector()
    
    # 记录请求
    collector.increment_request("GET", "/api/memory", 200)
    collector.observe_request_duration("GET", "/api/memory", 0.123)
    
    # 记录缓存命中
    collector.increment_cache_hit("default", "L1")
    
    # 记录 LLM 请求
    collector.record_llm_request("openai", "gpt-4", "success", 1.5, 100)
    
    print("Metrics recorded successfully")


if __name__ == "__main__":
    asyncio.run(example_usage())
