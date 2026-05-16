"""
测试 prometheus_metrics 模块

验证我们新的基于 prometheus-client 的指标系统是否正常工作
"""
import pytest
from unittest.mock import patch, MagicMock
from prometheus_client import REGISTRY

from backend.core.infrastructure.observability.prometheus_metrics import (
    Metrics,
    MetricsConfig,
    get_metrics,
    init_metrics
)


class TestMetricsConfig:
    """测试 MetricsConfig 配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = MetricsConfig()
        assert config.http_server_port is None
        assert config.prefix == "neural_agent"
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = MetricsConfig(
            http_server_port=9090,
            prefix="custom_prefix"
        )
        assert config.http_server_port == 9090
        assert config.prefix == "custom_prefix"


class TestMetrics:
    """测试 Metrics 类"""
    
    @pytest.fixture
    def clean_registry(self):
        """测试前清理注册表"""
        # 保存现有状态以便恢复
        collectors = list(REGISTRY._collector_to_names.keys())
        yield
        # 清理我们的指标
        for collector in collectors:
            if collector.__class__.__name__ != "_ValueClass":
                try:
                    REGISTRY.unregister(collector)
                except Exception:
                    pass
    
    @pytest.fixture
    def metrics(self, clean_registry):
        """测试前创建干净的 Metrics 实例"""
        # 重置全局状态
        import backend.core.prometheus_metrics as pm
        pm._metrics_instance = None
        # 返回新实例
        return Metrics()
    
    def test_metrics_initialization(self, metrics):
        """测试 Metrics 初始化"""
        assert metrics is not None
        # 检查我们定义的指标是否存在
        assert hasattr(metrics, 'API_REQUESTS_TOTAL')
        assert hasattr(metrics, 'TASKS_CREATED')
        assert hasattr(metrics, 'LLM_REQUESTS_TOTAL')
        assert hasattr(metrics, 'API_REQUEST_DURATION')
        assert hasattr(metrics, 'SYSTEM_INFO')
    
    def test_record_api_request(self, metrics):
        """测试 API 请求记录"""
        # 初始值应该是0
        initial_value = metrics.API_REQUESTS_TOTAL.labels(
            endpoint="/test", method="GET", status_code="200"
        )._value.get()
        
        # 记录请求
        metrics.record_api_request(
            endpoint="/test", 
            method="GET", 
            status_code="200"
        )
        
        # 验证值增加了
        new_value = metrics.API_REQUESTS_TOTAL.labels(
            endpoint="/test", method="GET", status_code="200"
        )._value.get()
        assert new_value == initial_value + 1
    
    def test_record_api_error(self, metrics):
        """测试 API 错误记录"""
        # 初始值应该是0
        initial_value = metrics.API_ERRORS_TOTAL.labels(
            endpoint="/test", error_type="TestError"
        )._value.get()
        
        # 记录错误
        metrics.record_api_error(
            endpoint="/test", 
            error_type="TestError"
        )
        
        # 验证值增加了
        new_value = metrics.API_ERRORS_TOTAL.labels(
            endpoint="/test", error_type="TestError"
        )._value.get()
        assert new_value == initial_value + 1
    
    def test_task_created_and_completed(self, metrics):
        """测试任务状态记录"""
        # 创建任务
        initial_active = metrics.ACTIVE_TASKS._value.get()
        metrics.task_created("test_task")
        
        # 验证创建
        created_count = metrics.TASKS_CREATED.labels(task_type="test_task")._value.get()
        assert created_count == 1
        assert metrics.ACTIVE_TASKS._value.get() == initial_active + 1
        
        # 完成任务
        metrics.task_completed("test_task", "success")
        
        # 验证完成
        completed_count = metrics.TASKS_COMPLETED.labels(
            task_type="test_task", status="success"
        )._value.get()
        assert completed_count == 1
        assert metrics.ACTIVE_TASKS._value.get() == initial_active
    
    def test_task_decorator(self, metrics):
        """测试任务装饰器"""
        
        @metrics.track_task("test_decorator")
        def test_function():
            return "test result"
        
        # 调用
        result = test_function()
        assert result == "test result"
        
        # 验证指标
        assert metrics.TASKS_CREATED.labels(task_type="test_decorator")._value.get() >= 1
        assert metrics.TASKS_COMPLETED.labels(
            task_type="test_decorator", status="success"
        )._value.get() >= 1
    
    def test_llm_request_tracking(self, metrics):
        """测试 LLM 请求跟踪"""
        metrics.llm_request(model="gpt-4", request_type="chat")
        assert metrics.LLM_REQUESTS_TOTAL.labels(
            model="gpt-4", request_type="chat"
        )._value.get() == 1
        
        metrics.llm_error(model="gpt-4", error_type="APIError")
        assert metrics.LLM_ERRORS_TOTAL.labels(
            model="gpt-4", error_type="APIError"
        )._value.get() == 1
    
    def test_vector_store_ops(self, metrics):
        """测试向量存储操作"""
        metrics.vector_store_op(operation="search", backend="chroma", success=True)
        assert metrics.VECTOR_STORE_OPS_TOTAL.labels(
            operation="search", backend="chroma"
        )._value.get() == 1
        
        metrics.vector_store_op(operation="search", backend="chroma", success=False)
        assert metrics.VECTOR_STORE_ERRORS_TOTAL.labels(
            operation="search", backend="chroma"
        )._value.get() == 1


class TestGlobalMetrics:
    """测试全局 Metrics 实例"""
    
    def test_get_metrics(self):
        """测试获取全局 Metrics 实例"""
        import backend.core.prometheus_metrics as pm
        # 重置
        pm._metrics_instance = None
        
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        
        assert metrics1 is metrics2  # 单例
    
    def test_init_metrics(self):
        """测试初始化 Metrics"""
        import backend.core.prometheus_metrics as pm
        # 重置
        pm._metrics_instance = None
        
        config = MetricsConfig(http_server_port=None)
        metrics = init_metrics(config=config)
        
        assert metrics is not None
        assert metrics.config == config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
