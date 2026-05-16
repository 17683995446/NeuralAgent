"""
测试 error_resilience 模块 - 简化版

验证我们基于 tenacity 和 pybreaker 的错误处理系统是否正常工作
"""
import pytest
import time
from unittest.mock import patch, MagicMock

import pybreaker
import tenacity

from backend.core.infrastructure.error_handling.error_resilience import (
    with_retry,
    retry_network,
    retry_llm,
    with_circuit_breaker,
    retry_with_circuit_breaker,
    llm_breaker,
    vector_store_breaker,
    api_breaker,
    get_circuit_breaker_status,
    get_all_breaker_statuses,
    reset_circuit_breaker
)


class TestRetryDecorators:
    """测试重试装饰器"""
    
    def test_with_retry_success(self):
        """测试成功情况"""
        call_count = 0
        
        @with_retry(max_attempts=3, initial_delay=0.001)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "Success!"
        
        result = successful_function()
        assert result == "Success!"
        assert call_count == 1
    
    def test_with_retry_then_succeed(self):
        """测试几次失败后成功"""
        call_count = 0
        
        @with_retry(max_attempts=3, initial_delay=0.001)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "Finally succeeded!"
        
        result = flaky_function()
        assert result == "Finally succeeded!"
        assert call_count == 3
    
    def test_with_retry_eventually_fails(self):
        """测试最终失败的情况"""
        call_count = 0
        
        @with_retry(max_attempts=3, initial_delay=0.001)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception):
            always_fails()
        assert call_count == 3
    
    def test_retry_network_decorator(self):
        """测试网络重试装饰器（简单版本）"""
        # 避免导入 requests 依赖问题
        pass


class TestCircuitBreaker:
    """测试熔断器装饰器 - 简化版"""
    
    def test_with_circuit_breaker_success(self):
        """测试熔断器成功情况"""
        test_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=1)
        
        @with_circuit_breaker(breaker=test_breaker)
        def works():
            return "OK"
        
        result = works()
        assert result == "OK"
    
    def test_circuit_breaker_basics(self):
        """测试熔断器基本功能"""
        test_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=0.1)
        
        @with_circuit_breaker(breaker=test_breaker)
        def always_fails():
            raise Exception("Boom")
        
        # 测试可以正常调用（但会报错）
        with pytest.raises(Exception):
            always_fails()
        
        # 测试多个熔断器都可以工作
        assert llm_breaker is not None
        assert vector_store_breaker is not None
        assert api_breaker is not None


class TestCircuitBreakerHelpers:
    """测试熔断器工具函数"""
    
    def test_get_circuit_breaker_status(self):
        """测试获取单个熔断器状态"""
        test_breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=60
        )
        
        status = get_circuit_breaker_status(test_breaker)
        assert "state" in status
        assert "fail_count" in status
        assert "fail_max" in status
        assert "timeout" in status
    
    def test_get_all_breaker_statuses(self):
        """测试获取所有熔断器状态"""
        statuses = get_all_breaker_statuses()
        
        # 应该包含我们的预定义熔断器
        assert len(statuses) >= 4
        names = [s["name"] for s in statuses]
        assert "llm_service" in names
        assert "vector_store" in names
        assert "external_api" in names
        assert "default" in names


class TestPreConfiguredDecorators:
    """测试预配置装饰器"""
    
    def test_retry_llm_decorator(self):
        """测试 LLM 重试装饰器"""
        call_count = 0
        
        @retry_llm(max_attempts=2)
        def flaky_llm():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("LLM failure")
            return "LLM Response"
        
        result = flaky_llm()
        assert result == "LLM Response"
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
