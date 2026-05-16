"""
LLM Adapter - A unified interface for various LLM providers
using LiteLLM for multi-provider support
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

# 尝试导入 LiteLLM，如果失败则使用 Mock
try:
    import litellm
    from litellm import completion, embedding
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("LiteLLM not available, will use mock mode only")


class LLMProvider(str, Enum):
    """LLM provider types"""
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    SILICONFLOW = "siliconflow"


@dataclass
class LLMConfig:
    """Configuration for LLM adapter"""
    provider: LLMProvider = LLMProvider.MOCK
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1024
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3


class LLMAdapter:
    """Base class for all LLM adapters"""
    
    async def generate(self, prompt: str) -> str:
        """Generate text from prompt"""
        raise NotImplementedError()
    
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with the model"""
        raise NotImplementedError()
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        raise NotImplementedError()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        raise NotImplementedError()


class MockLLMAdapter(LLMAdapter):
    """Mock LLM adapter for testing and development"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        logger.info("MockLLMAdapter initialized")
    
    async def generate(self, prompt: str) -> str:
        """Generate mock text"""
        await asyncio.sleep(0.1)  # Simulate delay
        return f"Mock response to: {prompt}"
    
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Mock chat"""
        await asyncio.sleep(0.1)
        last_content = messages[-1].get('content', '') if messages else ''
        return f"Mock chat response to: {last_content}"
    
    async def embed(self, text: str) -> List[float]:
        """Mock embedding - simple 1536d vector"""
        await asyncio.sleep(0.05)
        return [0.1] * 1536
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Mock batch embeddings"""
        await asyncio.sleep(0.05 * len(texts))
        return [[0.1] * 1536 for _ in texts]


class LiteLLMAdapter(LLMAdapter):
    """LiteLLM adapter supporting multiple providers"""
    
    PROVIDER_MODEL_MAP = {
        LLMProvider.OPENAI: "gpt-4o-mini",
        LLMProvider.ANTHROPIC: "claude-3-haiku-20240307",
        LLMProvider.OLLAMA: "llama2",
        LLMProvider.SILICONFLOW: "deepseek-ai/DeepSeek-Coder-V2",
    }
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._setup_provider_config()
        logger.info(f"LiteLLMAdapter initialized for {config.provider} with model: {config.model}")
    
    def _setup_provider_config(self):
        """Setup provider-specific configuration"""
        # Set API key if provided
        if self.config.api_key:
            if self.config.provider == LLMProvider.OPENAI:
                os.environ["OPENAI_API_KEY"] = self.config.api_key
                if self.config.base_url:
                    os.environ["OPENAI_API_BASE"] = self.config.base_url
            elif self.config.provider == LLMProvider.ANTHROPIC:
                os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
            elif self.config.provider == LLMProvider.SILICONFLOW:
                os.environ["SILICONFLOW_API_KEY"] = self.config.api_key
                if self.config.base_url:
                    os.environ["SILICONFLOW_API_BASE"] = self.config.base_url
    
    def _get_litellm_model(self) -> str:
        """Get the LiteLLM model name"""
        if self.config.provider == LLMProvider.SILICONFLOW:
            # 硅基流动模型格式
            return f"siliconflow/{self.config.model}"
        elif self.config.provider == LLMProvider.OLLAMA:
            return f"ollama/{self.config.model}"
        elif self.config.provider == LLMProvider.OPENAI:
            return self.config.model
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return self.config.model
        return self.config.model
    
    async def _retry_on_failure(self, func, *args, **kwargs):
        """Retry function on failure"""
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        raise last_error
    
    async def generate(self, prompt: str) -> str:
        """Generate text using LiteLLM"""
        if not LITELLM_AVAILABLE or not self.config.api_key:
            logger.warning("LiteLLM not available or no API key, falling back to mock")
            mock = MockLLMAdapter(self.config)
            return await mock.generate(prompt)
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self._retry_on_failure(
                litellm.acompletion,
                model=self._get_litellm_model(),
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LiteLLM generation failed: {e}")
            mock = MockLLMAdapter(self.config)
            return await mock.generate(prompt)
    
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat using LiteLLM"""
        if not LITELLM_AVAILABLE or not self.config.api_key:
            logger.warning("LiteLLM not available or no API key, falling back to mock")
            mock = MockLLMAdapter(self.config)
            return await mock.chat(messages)
        
        try:
            response = await self._retry_on_failure(
                litellm.acompletion,
                model=self._get_litellm_model(),
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LiteLLM chat failed: {e}")
            mock = MockLLMAdapter(self.config)
            return await mock.chat(messages)
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using LiteLLM"""
        if not LITELLM_AVAILABLE or not self.config.api_key:
            logger.warning("LiteLLM not available or no API key, falling back to mock")
            mock = MockLLMAdapter(self.config)
            return await mock.embed(text)
        
        try:
            # For embedding, use a default embedding model
            embed_model = "text-embedding-3-small" if self.config.provider == LLMProvider.OPENAI else self._get_litellm_model()
            
            response = await self._retry_on_failure(
                litellm.aembedding,
                model=embed_model,
                input=[text]
            )
            return response.data[0]['embedding']
        except Exception as e:
            logger.error(f"LiteLLM embedding failed: {e}")
            mock = MockLLMAdapter(self.config)
            return await mock.embed(text)
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using LiteLLM"""
        if not LITELLM_AVAILABLE or not self.config.api_key:
            logger.warning("LiteLLM not available or no API key, falling back to mock")
            mock = MockLLMAdapter(self.config)
            return await mock.embed_batch(texts)
        
        try:
            embed_model = "text-embedding-3-small" if self.config.provider == LLMProvider.OPENAI else self._get_litellm_model()
            
            response = await self._retry_on_failure(
                litellm.aembedding,
                model=embed_model,
                input=texts
            )
            return [item['embedding'] for item in response.data]
        except Exception as e:
            logger.error(f"LiteLLM batch embedding failed: {e}")
            mock = MockLLMAdapter(self.config)
            return await mock.embed_batch(texts)


# 兼容性适配器别名
class OpenAILLMAdapter(LiteLLMAdapter):
    """OpenAI LLM adapter (using LiteLLM)"""
    def __init__(self, config: LLMConfig):
        config.provider = LLMProvider.OPENAI
        super().__init__(config)


class AnthropicLLMAdapter(LiteLLMAdapter):
    """Anthropic Claude adapter (using LiteLLM)"""
    def __init__(self, config: LLMConfig):
        config.provider = LLMProvider.ANTHROPIC
        super().__init__(config)


class OllamaLLMAdapter(LiteLLMAdapter):
    """Ollama local model adapter (using LiteLLM)"""
    def __init__(self, config: LLMConfig):
        config.provider = LLMProvider.OLLAMA
        super().__init__(config)


def create_llm_adapter(
    provider: LLMProvider = LLMProvider.MOCK,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> LLMAdapter:
    """Factory function to create LLM adapter"""
    # 确定默认模型
    if model is None:
        model = LiteLLMAdapter.PROVIDER_MODEL_MAP.get(provider, "gpt-4o-mini")
    
    config = LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
    
    if provider == LLMProvider.MOCK:
        return MockLLMAdapter(config)
    else:
        # 对于真实提供商，使用 LiteLLM 适配器
        return LiteLLMAdapter(config)


# Quick access aliases
@dataclass
class LLMResponse:
    """Simple response wrapper for compatibility."""
    content: str
    model: str = "mock"
    usage: Dict = None
    raw_response: Any = None


# 兼容层 - 创建全局实例，支持旧API风格
_default_adapter = create_llm_adapter(provider=LLMProvider.MOCK)


class _CompatibleLLM:
    """兼容旧API的包装器，支持 complete() 方法。"""
    
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter
    
    async def complete(self, messages: List[Dict[str, str]], temperature: float = 0.7, **kwargs) -> LLMResponse:
        """兼容旧API的 complete 方法。"""
        content = await self.adapter.chat(messages)
        return LLMResponse(
            content=content,
            model="mock",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )
    
    async def embed(self, text: str) -> List[float]:
        """兼容旧API的 embed 方法。"""
        return await self.adapter.embed(text)


# 全局兼容实例
llm_adapter = _CompatibleLLM(_default_adapter)


def set_global_llm_adapter(adapter: LLMAdapter):
    """设置全局 LLM 适配器"""
    global llm_adapter
    llm_adapter = _CompatibleLLM(adapter)
    logger.info("Global LLM adapter updated")
