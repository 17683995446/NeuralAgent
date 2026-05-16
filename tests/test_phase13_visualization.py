"""
NeuralAgent - 阶段13综合测试
可视化、监控、提示工程、向量数据库测试
"""

import pytest
from datetime import datetime, timedelta


class TestAlertManager:
    """测试告警管理器"""
    
    def test_alert_creation(self):
        """测试告警创建"""
        from backend.core.monitoring.advanced import Alert, AlertStatus, AlertSeverity
        
        alert = Alert(
            id="test1",
            name="Test Alert",
            severity=AlertSeverity.WARNING,
            message="This is a test",
            status=AlertStatus.PENDING
        )
        
        assert alert.id == "test1"
        assert alert.name == "Test Alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.PENDING
    
    def test_alert_manager_initialization(self):
        """测试告警管理器初始化"""
        from backend.core.monitoring.advanced import create_alert_manager
        
        manager = create_alert_manager()
        assert manager is not None
        assert len(manager.rules) >= 2  # 默认规则
    
    def test_metric_recording(self):
        """测试指标记录"""
        from backend.core.monitoring.advanced import create_alert_manager
        
        manager = create_alert_manager()
        manager.record_metric("cpu_usage", 50.0, {"host": "test"})
        
        # 检查指标被记录
        metrics = manager.metrics_store.query("cpu_usage")
        assert len(metrics) > 0


class TestPromptWorkbench:
    """测试提示工程工作台"""
    
    def test_prompt_creation(self):
        """测试提示创建"""
        from tools.prompt_workbench import (
            create_prompt_workbench,
            PromptVariable
        )
        
        workbench = create_prompt_workbench()
        
        variables = [
            PromptVariable(name="input", description="User input"),
            PromptVariable(name="context", description="Context information", required=False)
        ]
        
        template = workbench.create_prompt(
            name="Test Prompt",
            description="A test prompt template",
            content="User input: {input}\nContext: {context}",
            variables=variables,
            tags=["test", "example"]
        )
        
        assert template.id is not None
        assert template.name == "Test Prompt"
        assert len(template.variables) == 2
    
    def test_prompt_rendering(self):
        """测试提示渲染"""
        from tools.prompt_workbench import (
            create_prompt_workbench,
            PromptVariable
        )
        
        workbench = create_prompt_workbench()
        
        variables = [
            PromptVariable(name="name", description="User name"),
            PromptVariable(name="question", description="User question")
        ]
        
        template = workbench.create_prompt(
            name="Greeting",
            description="Greeting prompt",
            content="Hello, {name}! Your question: {question}",
            variables=variables
        )
        
        rendered = workbench.render_prompt(
            template.id,
            {"name": "Alice", "question": "What is AI?"}
        )
        
        assert rendered == "Hello, Alice! Your question: What is AI?"
    
    def test_prompt_evaluation(self):
        """测试提示评估"""
        from tools.prompt_workbench import (
            create_prompt_workbench,
            PromptVariable,
            EvaluationMetric
        )
        
        workbench = create_prompt_workbench()
        
        variables = [PromptVariable(name="input", description="Input")]
        template = workbench.create_prompt(
            name="Evaluation Test",
            description="Test evaluation",
            content="Input: {input}",
            variables=variables
        )
        
        evaluation = workbench.evaluate_prompt(
            template_id=template.id,
            test_case="Hello",
            output="Hi there!",
            metrics={
                EvaluationMetric.RELEVANCE: 0.9,
                EvaluationMetric.COHERENCE: 0.8
            },
            evaluated_by="tester"
        )
        
        assert evaluation.id is not None
        assert abs(evaluation.overall_score - 0.85) < 0.0001


class TestMilvusVectorStore:
    """测试Milvus向量存储"""
    
    def test_vector_store_config(self):
        """测试向量存储配置"""
        from backend.core.vector_store import VectorStoreConfig, VectorStoreType
        from backend.core.vector_store.milvus import MilvusConfig, MetricType
        
        config = VectorStoreConfig(
            type=VectorStoreType.MILVUS,
            collection_name="test_collection",
            dimension=128
        )
        
        milvus_config = MilvusConfig(
            host="localhost",
            port=19530,
            metric_type=MetricType.COSINE
        )
        
        assert config.type == VectorStoreType.MILVUS
        assert milvus_config.metric_type == MetricType.COSINE
    
    def test_in_memory_vector_store(self):
        """测试内存向量存储（Milvus回退）"""
        from backend.core.vector_store import (
            create_vector_store,
            VectorStoreConfig,
            VectorStoreType,
            VectorDocument
        )
        
        config = VectorStoreConfig(
            type=VectorStoreType.MILVUS,
            collection_name="test"
        )
        
        store = create_vector_store(config)
        
        docs = [
            VectorDocument(id="doc1", content="Hello world", metadata={"type": "test"}),
            VectorDocument(id="doc2", content="Machine learning", metadata={"type": "test"})
        ]
        
        # 即使没有Milvus也应该能工作
        doc_ids = store.add_documents(docs, [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        assert len(doc_ids) == 2


class TestDashboardAPI:
    """测试仪表板API"""
    
    def test_dashboard_stats_model(self):
        """测试仪表板统计模型"""
        from backend.api.dashboard import DashboardStats
        
        stats = DashboardStats(
            total_agents=5,
            active_agents=3,
            total_memories=100,
            total_queries=1000,
            avg_response_time_ms=120.5,
            uptime_seconds=3600.0,
            cpu_usage=30.0,
            memory_usage=45.0
        )
        
        assert stats.total_agents == 5
        assert stats.uptime_seconds == 3600.0
    
    def test_log_entry_model(self):
        """测试日志条目模型"""
        from backend.api.dashboard import LogEntry
        
        log = LogEntry(
            id="log1",
            timestamp="2026-05-16T10:00:00",
            level="INFO",
            message="Test message",
            component="dashboard",
            metadata={"key": "value"}
        )
        
        assert log.id == "log1"
        assert log.level == "INFO"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
