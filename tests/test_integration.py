"""
NeuralAgent 集成测试
端到端完整流程验证
"""

import pytest
import asyncio
from datetime import datetime
import tempfile
import os

# 导入我们的模块
from app_config import get_config, NeuralAgentConfig


class TestConfigSystem:
    """配置系统测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = get_config()
        assert config is not None
        assert config.app_name == "NeuralAgent"
        assert config.environment == "development"
    
    def test_config_validation(self):
        """测试配置验证"""
        config = NeuralAgentConfig()
        assert config.validate()
    
    def test_dict_conversion(self):
        """测试字典转换"""
        config = NeuralAgentConfig()
        config_dict = config.to_dict()
        assert "app_name" in config_dict
        assert "llm" in config_dict
        assert "api" in config_dict
    
    def test_config_from_dict(self):
        """测试从字典创建"""
        original = NeuralAgentConfig(app_name="TestApp", debug=True)
        config_dict = original.to_dict()
        loaded = NeuralAgentConfig.from_dict(config_dict)
        assert loaded.app_name == original.app_name
        assert loaded.debug == original.debug


class TestMultiLevelCache:
    """多级缓存集成测试"""
    
    @pytest.mark.asyncio
    async def test_basic_cache_operations(self):
        """测试基本缓存操作"""
        from backend.core.cache.multi_level_cache import MultiLevelCache
        
        cache = MultiLevelCache(enable_l2=False)
        
        # 设置值
        await cache.set("test:key", "test value")
        
        # 获取值
        value = await cache.get("test:key")
        assert value == "test value"
        
        # 检查存在
        exists = await cache.exists("test:key")
        assert exists
        
        # 删除
        await cache.delete("test:key")
        exists = await cache.exists("test:key")
        assert not exists
    
    @pytest.mark.asyncio
    async def test_cache_warmup(self):
        """测试缓存预热"""
        from backend.core.cache.multi_level_cache import MultiLevelCache
        
        cache = MultiLevelCache(enable_l2=False)
        
        warmup_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        await cache.warmup(warmup_data)
        
        for key, expected in warmup_data.items():
            value = await cache.get(key)
            assert value == expected


class TestMonitoringIntegration:
    """监控系统集成测试"""
    
    def test_collector_creation(self):
        """测试指标收集器创建"""
        from backend.core.monitoring.prometheus_metrics import get_metrics_collector
        
        collector = get_metrics_collector()
        assert collector is not None
    
    def test_record_metrics(self):
        """测试记录指标"""
        from backend.core.monitoring.prometheus_metrics import get_metrics_collector
        
        collector = get_metrics_collector()
        
        collector.increment_request("GET", "/api/test", 200)
        collector.observe_request_duration("GET", "/api/test", 0.1)
        collector.record_llm_request("mock", "test-model", "success", 1.0, 100)
        
        # 不抛出异常就算成功
        assert True


class TestWorkflowIntegration:
    """工作流引擎集成测试"""
    
    def test_workflow_engine_creation(self):
        """测试工作流引擎创建"""
        from backend.core.workflow_engine import get_workflow_engine
        
        engine = get_workflow_engine()
        assert engine is not None
    
    def test_workflow_templates(self):
        """测试工作流模板"""
        from workflows import list_workflow_templates
        
        templates = list_workflow_templates()
        assert len(templates) >= 3


class TestMemoryIntegration:
    """记忆系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_unified_memory(self):
        """测试统一记忆系统（内存后端）"""
        from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
        
        # 直接创建一个使用内存后端的实例
        memory = UnifiedMemorySystem(InMemoryBackend())
        assert memory is not None
        
        await memory.store("integration:test", "test value")
        entry = await memory.retrieve("integration:test")
        
        assert entry is not None
        assert entry.value == "test value"


class TestAPIResponseModels:
    """API 响应模型测试"""
    
    def test_api_response(self):
        """测试 API 响应"""
        from backend.api.api_module import APIResponse
        
        response = APIResponse(
            success=True,
            data={"result": "test"},
            message="操作成功"
        )
        
        assert response.success is True
        assert response.data["result"] == "test"
        assert response.message == "操作成功"
    
    def test_pagination_response(self):
        """测试分页响应"""
        from backend.api.api_module import PaginationResponse
        
        response = PaginationResponse(
            items=[1, 2, 3],
            total=10,
            page=1,
            page_size=5,
            total_pages=2
        )
        
        assert len(response.items) == 3
        assert response.total == 10


class TestEndToEnd:
    """端到端完整流程测试"""
    
    @pytest.mark.asyncio
    async def test_complete_flow(self):
        """测试完整流程"""
        # 1. 初始化配置
        config = NeuralAgentConfig()
        
        # 2. 初始化缓存
        from backend.core.cache.multi_level_cache import get_cache
        cache = get_cache()
        
        # 3. 初始化监控
        from backend.core.monitoring.prometheus_metrics import get_metrics_collector
        collector = get_metrics_collector()
        
        # 4. 测试流程
        await cache.set("e2e:test", "e2e value")
        value = await cache.get("e2e:test")
        assert value == "e2e value"
        
        # 5. 记录指标
        collector.increment_request("GET", "/api/test", 200)
        collector.observe_request_duration("GET", "/api/test", 0.05)
        
        print("✅ 完整流程测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
