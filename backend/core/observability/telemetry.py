"""
NeuralAgent OpenTelemetry Integration
使用 OpenTelemetry 进行分布式追踪和监控
"""

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.trace import Status, StatusCode
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from contextlib import contextmanager
import time
from typing import Optional, Dict, Any
from functools import wraps


class OpenTelemetryInstrumentor:
    """OpenTelemetry 集成器"""

    def __init__(
        self,
        service_name: str = "neuralagent",
        service_version: str = "1.0.0",
        otlp_endpoint: Optional[str] = None
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint

        self._setup_resource()
        self._setup_tracer_provider()
        self._setup_meter_provider()

    def _setup_resource(self):
        """设置资源信息"""
        self.resource = Resource.create({
            SERVICE_NAME: self.service_name,
            "service.version": self.service_version,
            "deployment.environment": "production"
        })

    def _setup_tracer_provider(self):
        """设置追踪提供者"""
        tracer_provider = TracerProvider(resource=self.resource)

        if self.otlp_endpoint:
            span_exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
            tracer_provider.add_span_processor(
                BatchSpanProcessor(span_exporter)
            )

        trace.set_tracer_provider(tracer_provider)
        self.tracer = trace.get_tracer(self.service_name)

    def _setup_meter_provider(self):
        """设置指标提供者"""
        meter_provider = MeterProvider(resource=self.resource)

        if self.otlp_endpoint:
            metric_exporter = OTLPMetricExporter(endpoint=self.otlp_endpoint)
            meter_provider.add_metric_reader(
                PeriodicExportingMetricReader(metric_exporter)
            )

        metrics.set_meter_provider(meter_provider)
        self.meter = metrics.get_meter(self.service_name)

        self._create_default_metrics()

    def _create_default_metrics(self):
        """创建默认指标"""
        self.request_counter = self.meter.create_counter(
            name="http_requests_total",
            description="Total HTTP requests",
            unit="1"
        )

        self.request_duration = self.meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration",
            unit="s"
        )

        self.agent_execution_counter = self.meter.create_counter(
            name="agent_executions_total",
            description="Total agent executions",
            unit="1"
        )

        self.agent_execution_duration = self.meter.create_histogram(
            name="agent_execution_duration_seconds",
            description="Agent execution duration",
            unit="s"
        )

        self.active_agents_gauge = self.meter.create_up_down_counter(
            name="active_agents",
            description="Number of active agents",
            unit="1"
        )

    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """创建追踪跨度"""
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def trace_function(self, name: Optional[str] = None):
        """追踪函数的装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"

                with self.tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)

                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise

            return wrapper
        return decorator

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """记录 HTTP 请求"""
        self.request_counter.add(
            1,
            {
                "http.method": method,
                "http.endpoint": endpoint,
                "http.status_code": status_code
            }
        )

        self.request_duration.record(
            duration,
            {
                "http.method": method,
                "http.endpoint": endpoint
            }
        )

    def record_agent_execution(
        self,
        agent_name: str,
        task_type: str,
        success: bool,
        duration: float,
        tokens_used: Optional[int] = None
    ):
        """记录 Agent 执行"""
        self.agent_execution_counter.add(
            1,
            {
                "agent.name": agent_name,
                "task.type": task_type,
                "execution.success": success
            }
        )

        self.agent_execution_duration.record(
            duration,
            {
                "agent.name": agent_name,
                "task.type": task_type
            }
        )

    def increment_active_agents(self, agent_name: str):
        """增加活跃 Agent 计数"""
        self.active_agents_gauge.add(1, {"agent.name": agent_name})

    def decrement_active_agents(self, agent_name: str):
        """减少活跃 Agent 计数"""
        self.active_agents_gauge.add(-1, {"agent.name": agent_name})


class BatchSpanProcessor:
    """批量跨度处理器"""

    def __init__(self, exporter, max_queue_size: int = 2048, schedule_delay_millis: int = 5000):
        self.exporter = exporter
        self.max_queue_size = max_queue_size
        self.schedule_delay_millis = schedule_delay_millis
        self.span_queue = []

    def on_end(self, span):
        """处理结束的跨度"""
        if len(self.span_queue) < self.max_queue_size:
            self.span_queue.append(span)

    def on_start(self, span):
        """处理开始的跨度"""
        pass

    def shutdown(self):
        """关闭处理器"""
        self.exporter.export(self.span_queue)


class PeriodicExportingMetricReader:
    """周期性导出指标读取器"""

    def __init__(self, exporter, export_interval_millis: int = 60000):
        self.exporter = exporter
        self.export_interval_millis = export_interval_millis

    def receive(self, metric_data):
        """接收指标数据"""
        self.exporter.export(metric_data)


def create_instrumentor() -> OpenTelemetryInstrumentor:
    """创建默认的仪器化器"""
    return OpenTelemetryInstrumentor(
        service_name="neuralagent",
        service_version="1.0.0",
        otlp_endpoint=None
    )
