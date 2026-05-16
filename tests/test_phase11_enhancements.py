"""
NeuralAgent - Phase 11 Enhancements Test
阶段11综合测试
"""
import pytest
import asyncio
import time
from typing import Dict, Any
from datetime import datetime


class TestEnhancedWorkflowEngine:
    """测试高级工作流引擎"""
    
    @pytest.mark.asyncio
    async def test_workflow_basic_execution(self):
        """测试基本工作流执行"""
        from backend.core.workflow.enhanced_workflow import (
            EnhancedWorkflowEngine,
            WorkflowStatus,
            StepStatus
        )
        
        engine = EnhancedWorkflowEngine()
        
        async def step1(results: Dict[str, Any], context: Dict[str, Any]):
            return {"step1": "done"}
        
        async def step2(results: Dict[str, Any], context: Dict[str, Any]):
            return {"step2": "done", "prev": results.get("step1")}
        
        engine.add_step("step1", step1)
        engine.add_step("step2", step2, depends_on=["step1"])
        
        result = await engine.execute()
        
        assert engine.status == WorkflowStatus.COMPLETED
        assert "step1" in result
        assert "step2" in result
        assert result["step2"]["prev"] == "done"
    
    @pytest.mark.asyncio
    async def test_workflow_retry_policy(self):
        """测试工作流重试策略"""
        from backend.core.workflow.enhanced_workflow import (
            EnhancedWorkflowEngine,
            RetryPolicy,
            RetryStrategy
        )
        
        engine = EnhancedWorkflowEngine()
        attempts = []
        
        async def flaky_step(results, context):
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("Temporary failure")
            return {"success": True}
        
        retry_policy = RetryPolicy(
            max_attempts=3,
            strategy=RetryStrategy.FIXED_DELAY,
            initial_delay=0.1
        )
        
        engine.add_step("flaky", flaky_step, retry_policy=retry_policy)
        
        result = await engine.execute()
        
        assert len(attempts) == 3
        assert result["flaky"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_workflow_events(self):
        """测试工作流事件"""
        from backend.core.workflow.enhanced_workflow import (
            EnhancedWorkflowEngine,
            WorkflowEventListener,
            WorkflowEvent,
            StepStartedEvent
        )
        
        events = []
        
        class TestListener(WorkflowEventListener):
            async def on_event(self, event: WorkflowEvent):
                events.append(event)
        
        engine = EnhancedWorkflowEngine()
        engine.add_listener(TestListener())
        
        async def simple_step(results, context):
            return {"ok": True}
        
        engine.add_step("test", simple_step)
        
        await engine.execute()
        
        assert len(events) > 0
        event_types = [e.event_type for e in events]
        assert "WorkflowStartedEvent" in event_types or "StepStartedEvent" in event_types
    
    def test_workflow_summary(self):
        """测试工作流摘要"""
        from backend.core.workflow.enhanced_workflow import (
            EnhancedWorkflowEngine
        )
        
        engine = EnhancedWorkflowEngine()
        
        async def step(results, context):
            return {"x": 1}
        
        engine.add_step("test", step)
        
        summary = engine.get_summary()
        
        assert "workflow_id" in summary
        assert "status" in summary
        assert summary["status"] == "pending"


class TestHTTPClient:
    """测试HTTP客户端"""
    
    def test_http_client_config(self):
        """测试HTTP客户端配置"""
        from backend.core.http_client import (
            HTTPClientConfig,
            HTTPMethod
        )
        
        config = HTTPClientConfig(
            timeout=10.0,
            max_connections=50,
            retries=2
        )
        
        assert config.timeout == 10.0
        assert config.max_connections == 50
        assert config.retries == 2
        assert HTTPMethod.GET.value == "GET"
        assert HTTPMethod.POST.value == "POST"
    
    def test_http_client_init(self):
        """测试HTTP客户端初始化"""
        from backend.core.http_client import HTTPClientConfig
        
        try:
            from backend.core.http_client import HTTPClient
            config = HTTPClientConfig(timeout=5.0)
            client = HTTPClient(config)
            assert client is not None
            assert client.config.timeout == 5.0
        except ImportError:
            pytest.skip("httpx not available")


class TestPluginSystem:
    """测试插件系统"""
    
    def test_plugin_info(self):
        """测试插件信息"""
        from backend.core.plugins import PluginInfo
        
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test"
        )
        
        assert info.name == "test_plugin"
        assert info.version == "1.0.0"
        assert info.description == "A test plugin"
    
    def test_plugin_status_enum(self):
        """测试插件状态枚举"""
        from backend.core.plugins import PluginStatus
        
        assert PluginStatus.DISABLED.value == "disabled"
        assert PluginStatus.LOADED.value == "loaded"
        assert PluginStatus.ACTIVE.value == "active"
    
    def test_hook_type_enum(self):
        """测试钩子类型枚举"""
        from backend.core.plugins import HookType
        
        assert HookType.BEFORE_REQUEST.value == "before_request"
        assert HookType.AFTER_REQUEST.value == "after_request"


class TestDataValidation:
    """测试数据验证"""
    
    def test_email_validation(self):
        """测试邮箱验证"""
        from backend.core.models import validate_email
        
        assert validate_email("test@example.com") is True
        assert validate_email("invalid-email") is False
        assert validate_email("test@.com") is False
    
    def test_length_validation(self):
        """测试长度验证"""
        from backend.core.models import validate_length
        
        validate_length("hello", 1, 10)
        with pytest.raises(ValueError):
            validate_length("", 1, 10)
        with pytest.raises(ValueError):
            validate_length("very long string" * 100, 1, 10)
    
    def test_range_validation(self):
        """测试范围验证"""
        from backend.core.models import validate_range
        
        validate_range(5, 1, 10)
        with pytest.raises(ValueError):
            validate_range(0, 1, 10)
        with pytest.raises(ValueError):
            validate_range(15, 1, 10)


class TestRetryPolicy:
    """测试重试策略"""
    
    def test_retry_policy_defaults(self):
        """测试重试策略默认值"""
        from backend.core.workflow.enhanced_workflow import (
            RetryPolicy,
            RetryStrategy
        )
        
        policy = RetryPolicy()
        
        assert policy.max_attempts == 3
        assert policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert policy.initial_delay == 1.0


class TestWorkflowStepDependencies:
    """测试工作流步骤依赖"""
    
    @pytest.mark.asyncio
    async def test_step_dependency_execution(self):
        """测试步骤依赖执行"""
        from backend.core.workflow.enhanced_workflow import EnhancedWorkflowEngine
        
        engine = EnhancedWorkflowEngine()
        execution_order = []
        
        async def step_a(results, context):
            execution_order.append("a")
            return {"a": 1}
        
        async def step_b(results, context):
            execution_order.append("b")
            return {"b": 2}
        
        async def step_c(results, context):
            execution_order.append("c")
            return {"c": results["a"]["a"] + results["b"]["b"]}
        
        engine.add_step("a", step_a)
        engine.add_step("b", step_b)
        engine.add_step("c", step_c, depends_on=["a", "b"])
        
        result = await engine.execute()
        
        assert execution_order.index("a") < execution_order.index("c")
        assert execution_order.index("b") < execution_order.index("c")
        assert result["c"]["c"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
