"""
测试 llm_client 模块

验证我们基于 LiteLLM 的 LLM 客户端是否正常工作
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List, Dict, Any

from backend.core.llm_integration.unified_llm_client_wrapper import (
    LLMClient,
    LLMResponse,
    EmbeddingResponse,
    get_llm_client,
    complete,
    embed_single
)


class MockLLMResponse:
    """模拟 LiteLLM 响应"""
    
    def __init__(self, content: str):
        self.choices = [MagicMock(message=MagicMock(content=content))]
        self.usage = MagicMock()


class MockEmbeddingResponse:
    """模拟嵌入响应"""
    
    def __init__(self, embeddings: List[List[float]]):
        self.data = [{"embedding": emb} for emb in embeddings]
        self.usage = MagicMock()


class TestLLMResponse:
    """测试 LLMResponse 数据类"""
    
    def test_create_response(self):
        """测试创建 LLM 响应"""
        response = LLMResponse(
            content="Hello, world!",
            model="gpt-4"
        )
        assert response.content == "Hello, world!"
        assert response.model == "gpt-4"


class TestEmbeddingResponse:
    """测试 EmbeddingResponse 数据类"""
    
    def test_create_embedding_response(self):
        """测试创建嵌入响应"""
        response = EmbeddingResponse(
            embedding=[0.1, 0.2, 0.3],
            model="text-embedding-ada-002"
        )
        assert response.embedding == [0.1, 0.2, 0.3]
        assert response.model == "text-embedding-ada-002"


class TestLLMClient:
    """测试 LLMClient 类"""
    
    @pytest.fixture
    def llm_client(self):
        """创建测试用的 LLMClient 实例"""
        with patch('backend.core.llm_client.get_metrics') as mock_metrics:
            mock_metrics.return_value = MagicMock()
            client = LLMClient(
                model="gpt-4",
                temperature=0.7,
                max_tokens=100
            )
            yield client
    
    @patch('backend.core.llm_client.completion')
    def test_chat_sync(self, mock_completion, llm_client):
        """测试同步聊天"""
        mock_completion.return_value = MockLLMResponse("Test response")
        
        messages = [{"role": "user", "content": "Hello"}]
        response = llm_client.chat_sync(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        mock_completion.assert_called_once()
    
    @patch('backend.core.llm_client.completion')
    def test_complete(self, mock_completion, llm_client):
        """测试 complete 方法（兼容旧接口）"""
        mock_completion.return_value = MockLLMResponse("Complete response")
        
        response = llm_client.complete("Tell me a story")
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Complete response"
        mock_completion.assert_called_once()
    
    @patch('backend.core.llm_client.embedding')
    def test_embed_sync(self, mock_embedding, llm_client):
        """测试同步嵌入"""
        mock_embedding.return_value = MockEmbeddingResponse([[0.1, 0.2, 0.3]])
        
        response = llm_client.embed_sync("Test text")
        
        assert isinstance(response, EmbeddingResponse)
        assert response.embedding == [0.1, 0.2, 0.3]
        mock_embedding.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.core.llm_client.acompletion')
    async def test_chat(self, mock_acompletion, llm_client):
        """测试异步聊天"""
        mock_acompletion.return_value = MockLLMResponse("Async response")
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await llm_client.chat(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Async response"
    
    @pytest.mark.asyncio
    @patch('backend.core.llm_client.aembedding')
    async def test_embed(self, mock_aembedding, llm_client):
        """测试异步嵌入"""
        mock_aembedding.return_value = MockEmbeddingResponse([[0.4, 0.5, 0.6]])
        
        response = await llm_client.embed("Async text")
        
        assert isinstance(response, EmbeddingResponse)
        assert response.embedding == [0.4, 0.5, 0.6]
    
    @pytest.mark.asyncio
    @patch('backend.core.llm_client.aembedding')
    async def test_embed_batch(self, mock_aembedding, llm_client):
        """测试批量嵌入"""
        mock_aembedding.return_value = MockEmbeddingResponse([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ])
        
        embeddings = await llm_client.embed_batch(["text1", "text2"])
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]


class TestGlobalFunctions:
    """测试全局便捷函数"""
    
    @patch('backend.core.llm_client.get_llm_client')
    def test_complete(self, mock_get_client):
        """测试 complete 函数"""
        mock_client = MagicMock()
        mock_client.complete.return_value = LLMResponse("Global response", "gpt-4")
        mock_get_client.return_value = mock_client
        
        result = complete("Global test")
        
        assert result == "Global response"
        mock_client.complete.assert_called_once_with("Global test")
    
    @patch('backend.core.llm_client.get_llm_client')
    def test_embed_single(self, mock_get_client):
        """测试 embed_single 函数"""
        mock_client = MagicMock()
        mock_client.embed_sync.return_value = EmbeddingResponse([0.1, 0.2], "model")
        mock_get_client.return_value = mock_client
        
        result = embed_single("Test text")
        
        assert result == [0.1, 0.2]
        mock_client.embed_sync.assert_called_once_with("Test text")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
