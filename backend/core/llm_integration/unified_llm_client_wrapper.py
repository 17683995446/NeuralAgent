"""LLM集成（直接使用LiteLLM）

不重复造轮子，直接使用成熟的LiteLLM库！
LiteLLM支持100+模型：OpenAI, Anthropic, Azure, Ollama, 等等
https://docs.litellm.ai/
"""
from typing import (
    Dict,
    List,
    Optional,
    Any,
    Union
)
from dataclasses import dataclass
import logging
import asyncio

# 直接使用LiteLLM！
import litellm
from litellm import (
    completion,
    aembedding,
    embedding,
    acompletion,
    supports_function_calling
)

from backend.config import settings
from backend.core.infrastructure.observability.prometheus_metrics import get_metrics
from backend.core.infrastructure.error_handling.error_resilience import (
    retry_llm,
    llm_breaker,
    with_circuit_breaker
)

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM响应封装"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None


@dataclass
class EmbeddingResponse:
    """Embedding响应封装"""
    embedding: List[float]
    model: str
    usage: Optional[Dict[str, int]] = None


class LLMClient:
    """LLM客户端（直接使用LiteLLM）
    
    不重复造轮子，只做轻量级封装！
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """初始化LLM客户端
        
        Args:
            model: 模型名称，默认从配置读取
            temperature: 温度，默认从配置读取
            max_tokens: 最大token数，默认从配置读取
            timeout: 超时时间，默认从配置读取
            api_key: API密钥，默认从配置读取
            base_url: API基础URL，默认从配置读取
        """
        # 使用配置或提供的参数
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.timeout = timeout or settings.llm_timeout
        self.api_key = api_key or settings.llm_api_key
        self.base_url = base_url or settings.llm_base_url
        self.embedding_model = settings.llm_embedding_model
        
        # 配置LiteLLM
        if self.api_key:
            litellm.api_key = self.api_key
        if self.base_url:
            litellm.api_base = self.base_url
        
        # 设置超时
        litellm.request_timeout = self.timeout
        
        # 记录初始化
        logger.info(f"LLMClient initialized with model: {self.model}")
        
        # 获取Metrics
        self.metrics = get_metrics()
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """聊天请求（异步）
        
        Args:
            messages: 消息列表
            model: 模型名称（可选）
            temperature: 温度（可选）
            max_tokens: 最大token数（可选）
            stream: 是否流式响应
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        model_to_use = model or self.model
        
        @retry_llm(max_attempts=2)
        @with_circuit_breaker(breaker=llm_breaker)
        async def _call():
            with self.metrics.LLM_REQUEST_DURATION.labels(model=model_to_use).time():
                response = await acompletion(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature if temperature is not None else self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                    stream=stream,
                    **kwargs
                )
                self.metrics.llm_request(model=model_to_use, request_type="chat")
                return response
        
        try:
            response = await _call()
            
            # 解析响应
            content = response.choices[0].message.content
            usage = response.usage.__dict__ if hasattr(response, "usage") else None
            
            return LLMResponse(
                content=content,
                model=model_to_use,
                usage=usage,
                raw_response=response
            )
        except Exception as e:
            self.metrics.llm_error(model=model_to_use, error_type=type(e).__name__)
            logger.error(f"LLM chat error: {e}")
            raise
    
    def chat_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """聊天请求（同步）
        
        Args:
            messages: 消息列表
            model: 模型名称（可选）
            temperature: 温度（可选）
            max_tokens: 最大token数（可选）
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        model_to_use = model or self.model
        
        @retry_llm(max_attempts=2)
        @with_circuit_breaker(breaker=llm_breaker)
        def _call():
            with self.metrics.LLM_REQUEST_DURATION.labels(model=model_to_use).time():
                response = completion(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature if temperature is not None else self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                    **kwargs
                )
                self.metrics.llm_request(model=model_to_use, request_type="chat")
                return response
        
        try:
            response = _call()
            
            # 解析响应
            content = response.choices[0].message.content
            usage = response.usage.__dict__ if hasattr(response, "usage") else None
            
            return LLMResponse(
                content=content,
                model=model_to_use,
                usage=usage,
                raw_response=response
            )
        except Exception as e:
            self.metrics.llm_error(model=model_to_use, error_type=type(e).__name__)
            logger.error(f"LLM chat error: {e}")
            raise
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """生成embedding（异步）
        
        Args:
            text: 输入文本
            model: 模型名称（可选）
            **kwargs: 其他参数
            
        Returns:
            Embedding响应
        """
        model_to_use = model or self.embedding_model
        
        @retry_llm(max_attempts=2)
        @with_circuit_breaker(breaker=llm_breaker)
        async def _call():
            response = await aembedding(
                model=model_to_use,
                input=[text],
                **kwargs
            )
            self.metrics.llm_request(model=model_to_use, request_type="embedding")
            return response
        
        try:
            response = await _call()
            embedding_list = response.data[0]["embedding"]
            
            usage = response.usage.__dict__ if hasattr(response, "usage") else None
            
            return EmbeddingResponse(
                embedding=embedding_list,
                model=model_to_use,
                usage=usage
            )
        except Exception as e:
            self.metrics.llm_error(model=model_to_use, error_type=type(e).__name__)
            logger.error(f"LLM embedding error: {e}")
            raise
    
    def embed_sync(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """生成embedding（同步）
        
        Args:
            text: 输入文本
            model: 模型名称（可选）
            **kwargs: 其他参数
            
        Returns:
            Embedding响应
        """
        model_to_use = model or self.embedding_model
        
        @retry_llm(max_attempts=2)
        @with_circuit_breaker(breaker=llm_breaker)
        def _call():
            response = embedding(
                model=model_to_use,
                input=[text],
                **kwargs
            )
            self.metrics.llm_request(model=model_to_use, request_type="embedding")
            return response
        
        try:
            response = _call()
            embedding_list = response.data[0]["embedding"]
            
            usage = response.usage.__dict__ if hasattr(response, "usage") else None
            
            return EmbeddingResponse(
                embedding=embedding_list,
                model=model_to_use,
                usage=usage
            )
        except Exception as e:
            self.metrics.llm_error(model=model_to_use, error_type=type(e).__name__)
            logger.error(f"LLM embedding error: {e}")
            raise
    
    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[List[float]]:
        """批量生成embedding（异步）
        
        Args:
            texts: 输入文本列表
            model: 模型名称（可选）
            **kwargs: 其他参数
            
        Returns:
            Embedding列表
        """
        model_to_use = model or self.embedding_model
        
        @retry_llm(max_attempts=2)
        @with_circuit_breaker(breaker=llm_breaker)
        async def _call():
            response = await aembedding(
                model=model_to_use,
                input=texts,
                **kwargs
            )
            self.metrics.llm_request(model=model_to_use, request_type="embedding_batch")
            self.metrics.BATCH_EMBEDDING_SIZE.labels(model=model_to_use).observe(len(texts))
            return response
        
        try:
            response = await _call()
            return [item["embedding"] for item in response.data]
        except Exception as e:
            self.metrics.llm_error(model=model_to_use, error_type=type(e).__name__)
            logger.error(f"LLM batch embedding error: {e}")
            raise
    
    def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """简单的文本补全（兼容旧代码）
        
        Args:
            prompt: 提示词
            model: 模型名称（可选）
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat_sync(messages, model=model, **kwargs)


# ==================== 全局实例 ====================

_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取全局LLM客户端
    
    Returns:
        LLM客户端单例
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# ==================== 便捷函数（兼容旧代码） ====================

def complete(prompt: str, model: Optional[str] = None, **kwargs) -> str:
    """便捷的文本补全函数
    
    Args:
        prompt: 提示词
        model: 模型名称（可选）
        **kwargs: 其他参数
        
    Returns:
        生成的文本
    """
    client = get_llm_client()
    response = client.complete(prompt, model=model, **kwargs)
    return response.content


async def acompletion(prompt: str, model: Optional[str] = None, **kwargs) -> str:
    """便捷的异步文本补全函数
    
    Args:
        prompt: 提示词
        model: 模型名称（可选）
        **kwargs: 其他参数
        
    Returns:
        生成的文本
    """
    client = get_llm_client()
    messages = [{"role": "user", "content": prompt}]
    response = await client.chat(messages, model=model, **kwargs)
    return response.content


def embed_single(text: str, model: Optional[str] = None, **kwargs) -> List[float]:
    """便捷的embedding函数
    
    Args:
        text: 输入文本
        model: 模型名称（可选）
        **kwargs: 其他参数
        
    Returns:
        Embedding向量
    """
    client = get_llm_client()
    response = client.embed_sync(text, model=model, **kwargs)
    return response.embedding
