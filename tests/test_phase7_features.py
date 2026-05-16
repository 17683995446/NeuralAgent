"""
综合测试文件 - 验证阶段7的新功能
"""
import pytest
import asyncio
from datetime import datetime

# 测试多级缓存系统
from backend.core.cache.multi_level_cache import (
    MultiLevelCache,
    L1Cache,
    CacheLevel,
    get_cache
)

# 测试监控系统
from backend.core.monitoring.prometheus_metrics import (
    MetricsCollector,
    MonitoringServer,
    get_monitoring_server
)

# 测试 API
from backend.api.api_module import (
    NeuralAgentAPI,
    APIResponse,
    MemoryItem,
    PaginationResponse
)


class TestMultiLevelCache:
    """测试多级缓存系统"""
    
    def test_l1_cache_basic(self):
        """测试 L1 缓存基本操作"""
        cache = L1Cache(max_size=10)
        
        # 设置缓存
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # 获取缓存
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # 检查存在
        assert cache.exists("key1") is True
        assert cache.exists("key3") is False
        
        # 删除缓存
        cache.delete("key1")
        assert cache.exists("key1") is False
    
    def test_l1_cache_lru(self):
        """测试 L1 缓存 LRU 策略"""
        cache = L1Cache(max_size=3)
        
        cache.set("key1", "v1")
        cache.set("key2", "v2")
        cache.set("key3", "v3")
        
        # 访问 key1，使其成为最新
        cache.get("key1")
        
        # 添加第4个，应该删除最久未访问的 key2
        cache.set("key4", "v4")
        
        assert cache.get("key2") is None  # key2 被淘汰
        assert cache.get("key1") == "v1"  # key1 因为被访问过而保留
    
    def test_l1_cache_stats(self):
        """测试 L1 缓存统计"""
        cache = L1Cache(max_size=10)
        
        cache.set("key1", "v1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
    
    @pytest.mark.asyncio
    async def test_multi_level_cache_basic(self):
        """测试多级缓存基本操作"""
        cache = MultiLevelCache(enable_l2=False)
        
        await cache.set("user:1", {"name": "张三"})
        result = await cache.get("user:1")
        
        assert result is not None
        assert result["name"] == "张三"
    
    @pytest.mark.asyncio
    async def test_multi_level_cache_levels(self):
        """测试多级缓存级别"""
        cache = MultiLevelCache(enable_l2=False)
        
        await cache.set("key1", "value1", level=CacheLevel.L1)
        result = await cache.get("key1", level=CacheLevel.L1)
        
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_multi_level_cache_warmup(self):
        """测试缓存预热"""
        cache = MultiLevelCache(enable_l2=False)
        
        warmup_data = {
            "config:default": {"timeout": 30},
            "user:admin": {"role": "admin"}
        }
        
        await cache.warmup(warmup_data)
        
        result1 = await cache.get("config:default")
        result2 = await cache.get("user:admin")
        
        assert result1 == {"timeout": 30}
        assert result2 == {"role": "admin"}


class TestPrometheusMetrics:
    """测试 Prometheus 监控"""
    
    def test_metrics_collector_initialization(self):
        """测试指标收集器初始化"""
        # 使用全局单例避免重复注册问题
        server = get_monitoring_server()
        collector = server.get_collector()
        
        # 检查默认指标是否存在
        assert hasattr(collector, 'request_counter')
        assert hasattr(collector, 'request_duration')
        assert hasattr(collector, 'cache_hits')
        assert hasattr(collector, 'llm_requests')
    
    def test_record_http_request(self):
        """测试记录 HTTP 请求"""
        # 使用全局单例
        server = get_monitoring_server()
        collector = server.get_collector()
        
        collector.increment_request("GET", "/api/test", 200)
        collector.observe_request_duration("GET", "/api/test", 0.123)
        
        # 验证操作完成（不抛出异常）
        assert True
    
    def test_record_cache_metrics(self):
        """测试记录缓存指标"""
        # 使用全局单例
        server = get_monitoring_server()
        collector = server.get_collector()
        
        collector.increment_cache_hit("default", "L1")
        collector.increment_cache_miss("default", "L2")
        
        assert True
    
    def test_record_llm_metrics(self):
        """测试记录 LLM 指标"""
        # 使用全局单例
        server = get_monitoring_server()
        collector = server.get_collector()
        
        collector.record_llm_request("mock", "test-model", "success", 1.5, 100)
        
        assert True
    
    @pytest.mark.asyncio
    async def test_monitoring_server(self):
        """测试监控服务器"""
        server = get_monitoring_server(port=8002)
        await server.start()
        
        assert server.is_running() is True
        
        collector = server.get_collector()
        assert collector is not None


class TestAPIResponseModels:
    """测试 API 响应模型"""
    
    def test_api_response_default(self):
        """测试 API 响应默认值"""
        response = APIResponse()
        
        assert response.success is True
        assert response.data is None
        assert response.message == ""
        assert response.error is None
        assert isinstance(response.timestamp, datetime)
    
    def test_api_response_with_data(self):
        """测试带数据的 API 响应"""
        data = {"key": "value"}
        response = APIResponse(success=True, data=data, message="Success")
        
        assert response.data == data
        assert response.message == "Success"
    
    def test_pagination_response(self):
        """测试分页响应"""
        items = [1, 2, 3, 4, 5]
        response = PaginationResponse(
            items=items,
            total=100,
            page=1,
            page_size=10,
            total_pages=10
        )
        
        assert len(response.items) == 5
        assert response.total == 100
        assert response.total_pages == 10


class TestAPIIntegration:
    """测试 API 集成"""
    
    def test_api_response_model(self):
        """测试 API 响应模型"""
        item = MemoryItem(key="test", value="test value", ttl=3600)
        
        assert item.key == "test"
        assert item.value == "test value"
        assert item.ttl == 3600


@pytest.mark.asyncio
async def test_full_workflow():
    """测试完整工作流程"""
    # 获取缓存
    cache = get_cache()
    
    # 设置缓存
    await cache.set("workflow:test", {"status": "running"})
    
    # 获取缓存
    result = await cache.get("workflow:test")
    assert result is not None
    
    # 获取指标收集器
    server = get_monitoring_server()
    collector = server.get_collector()
    
    # 记录指标
    collector.increment_request("POST", "/api/workflow", 200)
    collector.observe_request_duration("POST", "/api/workflow", 0.5)
    
    print("✅ 完整工作流程测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])