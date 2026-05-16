"""Vector Database Tests - 向量数据库测试"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestInMemoryVectorDB:
    """内存向量数据库测试"""
    
    @pytest.mark.asyncio
    async def test_add_vectors(self):
        """测试添加向量"""
        from backend.core.infrastructure.vector_db import InMemoryVectorDB, VectorDBConfig
        
        config = VectorDBConfig()
        db = InMemoryVectorDB(config)
        
        texts = ["Hello world", "Python programming"]
        embeddings = [
            [0.1] * 768,
            [0.2] * 768
        ]
        
        ids = await db.add(texts, embeddings)
        
        assert len(ids) == 2
        assert await db.count() == 2
    
    @pytest.mark.asyncio
    async def test_search_vectors(self):
        """测试搜索向量"""
        from backend.core.infrastructure.vector_db import InMemoryVectorDB, VectorDBConfig
        
        config = VectorDBConfig()
        db = InMemoryVectorDB(config)
        
        texts = ["Hello world", "Python programming", "Machine learning"]
        embeddings = [
            [1.0] * 768,
            [0.5] * 768,
            [0.3] * 768
        ]
        
        await db.add(texts, embeddings)
        
        # 搜索与[1.0]*768最相似的向量
        query_embedding = [1.0] * 768
        results = await db.search(query_embedding, top_k=2)
        
        assert len(results) == 2
        assert results[0].text == "Hello world"  # 应该最相似
    
    @pytest.mark.asyncio
    async def test_delete_vectors(self):
        """测试删除向量"""
        from backend.core.infrastructure.vector_db import InMemoryVectorDB, VectorDBConfig
        
        config = VectorDBConfig()
        db = InMemoryVectorDB(config)
        
        texts = ["Hello world", "Python programming"]
        embeddings = [[0.1] * 768, [0.2] * 768]
        
        ids = await db.add(texts, embeddings)
        assert await db.count() == 2
        
        await db.delete([ids[0]])
        assert await db.count() == 1


class TestVectorDBConfig:
    """向量数据库配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        from backend.core.infrastructure.vector_db import VectorDBConfig
        
        config = VectorDBConfig()
        
        assert config.provider == "chroma"
        assert config.collection_name == "neural_agent"
        assert config.embedding_dimension == 768
    
    def test_custom_config(self):
        """测试自定义配置"""
        from backend.core.infrastructure.vector_db import VectorDBConfig
        
        config = VectorDBConfig(
            provider="pinecone",
            collection_name="test_collection",
            embedding_dimension=1536
        )
        
        assert config.provider == "pinecone"
        assert config.collection_name == "test_collection"
        assert config.embedding_dimension == 1536


class TestVectorSearchResult:
    """向量搜索结果测试"""
    
    def test_create_result(self):
        """测试创建搜索结果"""
        from backend.core.infrastructure.vector_db import VectorSearchResult
        
        result = VectorSearchResult(
            id="test_1",
            text="Hello world",
            embedding=[0.1] * 10,
            score=0.95,
            metadata={"source": "test"}
        )
        
        assert result.id == "test_1"
        assert result.text == "Hello world"
        assert len(result.embedding) == 10
        assert result.score == 0.95
        assert result.metadata["source"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
