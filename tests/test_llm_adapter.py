"""
Unit tests for LLM Adapter system
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from backend.core.llm_adapter import (
    LLMProvider,
    LLMConfig,
    LLMAdapter,
    MockLLMAdapter,
    OpenAILLMAdapter,
    AnthropicLLMAdapter,
    OllamaLLMAdapter,
    create_llm_adapter
)


class TestLLMConfig:
    """Test cases for LLMConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = LLMConfig()
        assert config.provider == LLMProvider.MOCK
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 1024

    def test_custom_config(self):
        """Test custom configuration."""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=512,
            api_key="test-key"
        )
        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5
        assert config.max_tokens == 512


class TestMockLLMAdapter:
    """Test cases for MockLLMAdapter."""

    @pytest.mark.asyncio
    async def test_generate(self):
        """Test text generation."""
        config = LLMConfig(provider=LLMProvider.MOCK)
        adapter = MockLLMAdapter(config)
        
        result = await adapter.generate("Test prompt")
        assert isinstance(result, str)
        assert "Mock" in result

    @pytest.mark.asyncio
    async def test_chat(self):
        """Test chat functionality."""
        config = LLMConfig(provider=LLMProvider.MOCK)
        adapter = MockLLMAdapter(config)
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await adapter.chat(messages)
        assert isinstance(result, str)
        assert "Mock" in result

    @pytest.mark.asyncio
    async def test_embed(self):
        """Test embedding generation."""
        config = LLMConfig(provider=LLMProvider.MOCK)
        adapter = MockLLMAdapter(config)
        
        embedding = await adapter.embed("Test text")
        assert isinstance(embedding, list)
        assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """Test batch embedding generation."""
        config = LLMConfig(provider=LLMProvider.MOCK)
        adapter = MockLLMAdapter(config)
        
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = await adapter.embed_batch(texts)
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)


class TestAdapterFactory:
    """Test cases for create_llm_adapter factory."""

    def test_create_mock_adapter(self):
        """Test creating mock adapter."""
        adapter = create_llm_adapter(provider=LLMProvider.MOCK)
        assert isinstance(adapter, MockLLMAdapter)

    def test_create_openai_adapter(self):
        """Test creating OpenAI adapter."""
        adapter = create_llm_adapter(
            provider=LLMProvider.OPENAI,
            api_key="test-key"
        )
        assert isinstance(adapter, OpenAILLMAdapter)

    def test_create_anthropic_adapter(self):
        """Test creating Anthropic adapter."""
        adapter = create_llm_adapter(
            provider=LLMProvider.ANTHROPIC,
            api_key="test-key"
        )
        assert isinstance(adapter, AnthropicLLMAdapter)

    def test_create_ollama_adapter(self):
        """Test creating Ollama adapter."""
        adapter = create_llm_adapter(
            provider=LLMProvider.OLLAMA,
            base_url="http://localhost:11434"
        )
        assert isinstance(adapter, OllamaLLMAdapter)

    def test_create_with_config(self):
        """Test creating adapter with config object."""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        adapter = create_llm_adapter(config=config)
        assert isinstance(adapter, OpenAILLMAdapter)
