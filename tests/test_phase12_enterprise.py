"""
NeuralAgent - 阶段12综合测试
企业级功能验证
"""

import pytest
from datetime import datetime


class TestVectorStore:
    """向量存储测试"""
    
    def test_vector_document(self):
        """测试向量文档"""
        from backend.core.vector_store import VectorDocument
        
        doc = VectorDocument(
            id="doc1",
            content="这是测试文档",
            metadata={"source": "test"}
        )
        
        assert doc.id == "doc1"
        assert doc.content == "这是测试文档"
        assert doc.metadata["source"] == "test"
    
    def test_in_memory_vector_store(self):
        """测试内存向量存储"""
        import asyncio
        from backend.core.vector_store import (
            VectorStoreConfig,
            VectorStoreType,
            InMemoryVectorStore,
            VectorDocument
        )
        
        config = VectorStoreConfig(
            type=VectorStoreType.MILVUS,
            collection_name="test_collection"
        )
        store = InMemoryVectorStore(config)
        
        async def test_ops():
            await store.connect()
            
            doc1 = VectorDocument(
                id="test1",
                content="文档内容1",
                metadata={"category": "A"}
            )
            doc2 = VectorDocument(
                id="test2",
                content="文档内容2",
                metadata={"category": "B"}
            )
            
            doc_ids = await store.add_documents(
                [doc1, doc2],
                [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            )
            
            assert len(doc_ids) == 2
            assert await store.count_documents() == 2
            
            retrieved = await store.search([0.15, 0.25, 0.35], top_k=2)
            assert len(retrieved) > 0
            
            await store.disconnect()
        
        asyncio.run(test_ops())


class TestRAGSystem:
    """RAG系统测试"""
    
    def test_text_chunker(self):
        """测试文本分块器"""
        from backend.core.rag import TextChunker, ChunkConfig, ChunkingStrategy
        
        config = ChunkConfig(
            strategy=ChunkingStrategy.FIXED_SIZE,
            chunk_size=50,
            chunk_overlap=10
        )
        chunker = TextChunker(config)
        
        text = "这是一段很长的文本内容，需要被分成多个小块。" * 5
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert "content" in chunk
            assert "metadata" in chunk
    
    def test_rag_result(self):
        """测试RAG结果"""
        from backend.core.rag import RAGResult
        
        result = RAGResult(
            answer="这是答案",
            sources=[
                {"content": "来源1", "score": 0.9},
                {"content": "来源2", "score": 0.8}
            ],
            confidence=0.85
        )
        
        assert result.answer == "这是答案"
        assert len(result.sources) == 2
        assert result.confidence == 0.85


class TestMultiAgentSystem:
    """多Agent系统测试"""
    
    def test_agent_config(self):
        """测试Agent配置"""
        from backend.core.agents import AgentConfig, AgentType
        
        config = AgentConfig(
            agent_type=AgentType.RESEARCHER,
            name="研究员",
            role="负责研究和信息收集",
            goals=["收集信息", "分析数据"]
        )
        
        assert config.agent_type == AgentType.RESEARCHER
        assert config.name == "研究员"
        assert len(config.goals) == 2
    
    def test_agent_task(self):
        """测试Agent任务"""
        from backend.core.agents import AgentTask, TaskStatus
        
        task = AgentTask(
            task_id="task1",
            description="分析数据",
            assigned_agent="研究员",
            priority=8
        )
        
        assert task.task_id == "task1"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 8


class TestI18nSystem:
    """i18n系统测试"""
    
    def test_language_enum(self):
        """测试语言枚举"""
        from backend.core.i18n import Language
        
        assert Language.ENGLISH.value == "en"
        assert Language.CHINESE_SIMPLIFIED.value == "zh-CN"
    
    def test_i18n_manager(self):
        """测试i18n管理器"""
        from backend.core.i18n import create_i18n_manager, Language
        
        manager = create_i18n_manager(default_language=Language.ENGLISH)
        
        manager.store.set_translation("welcome", "欢迎使用 NeuralAgent!", Language.CHINESE_SIMPLIFIED)
        
        en_trans = manager.t("welcome", Language.ENGLISH)
        zh_trans = manager.t("welcome", Language.CHINESE_SIMPLIFIED)
        
        assert en_trans == "Welcome to NeuralAgent!"
        assert zh_trans == "欢迎使用 NeuralAgent!"


class TestEnterpriseSecurity:
    """企业安全测试"""
    
    def test_role_and_permission(self):
        """测试角色和权限"""
        from backend.core.security.enterprise import Role, Permission
        
        assert Role.ADMIN.value == "admin"
        assert Permission.READ.value == "read"
        assert Permission.WRITE.value == "write"
    
    def test_user_model(self):
        """测试用户模型"""
        from backend.core.security.enterprise import User, Role
        
        user = User(
            user_id="user1",
            username="admin",
            email="admin@example.com",
            role=Role.ADMIN
        )
        
        assert user.user_id == "user1"
        assert user.role == Role.ADMIN
        assert user.is_active is True
    
    def test_rbac_policy(self):
        """测试RBAC策略"""
        from backend.core.security.enterprise import (
            RBACPolicy,
            User,
            Role,
            Permission
        )
        
        policy = RBACPolicy()
        
        admin = User(
            user_id="admin1",
            username="admin",
            email="admin@example.com",
            role=Role.ADMIN
        )
        
        user = User(
            user_id="user1",
            username="user",
            email="user@example.com",
            role=Role.USER
        )
        
        policy.add_user(admin)
        policy.add_user(user)
        
        assert policy.has_permission(admin, Permission.MANAGE_USERS) is True
        assert policy.has_permission(user, Permission.MANAGE_USERS) is False
        assert policy.has_permission(user, Permission.READ) is True
    
    def test_audit_logger(self):
        """测试审计日志"""
        from backend.core.security.enterprise import AuditLogger, AuditAction
        
        logger = AuditLogger()
        
        log = logger.log(
            user_id="user1",
            action=AuditAction.LOGIN,
            resource="api",
            ip_address="192.168.1.1"
        )
        
        assert log.user_id == "user1"
        assert log.action == AuditAction.LOGIN
        
        logs = logger.get_logs(user_id="user1")
        assert len(logs) == 1


class TestSDK:
    """SDK测试"""
    
    def test_sdk_config(self):
        """测试SDK配置"""
        from sdk.python.neuralagent_sdk import SDKConfig
        
        config = SDKConfig(
            api_key="test_key",
            base_url="http://localhost:8000"
        )
        
        assert config.api_key == "test_key"
        assert config.base_url == "http://localhost:8000"
    
    def test_sdk_creation(self):
        """测试SDK创建"""
        from sdk.python.neuralagent_sdk import create_sdk
        
        sdk = create_sdk(
            api_key="test_key",
            base_url="http://localhost:8000"
        )
        
        assert sdk is not None
        assert sdk.config.api_key == "test_key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
