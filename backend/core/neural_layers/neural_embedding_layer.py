"""Neural Embedding Layer - 神经网络嵌入层

Layer 1 of the NeuralAgent Deep Architecture.

功能：
- 将用户需求、代码、文档等输入转换为向量表示
- 支持多种嵌入模型（BERT, CodeBERT, Sentence-BERT）
- 提供统一的嵌入接口
- 支持mock模式用于测试和离线环境
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """嵌入层配置"""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 768
    max_sequence_length: int = 512
    batch_size: int = 32
    normalize_embeddings: bool = True
    use_cache: bool = True
    cache_size: int = 10000
    use_mock: bool = False  # 新增：是否使用mock模式


@dataclass
class EmbeddingResult:
    """嵌入结果"""
    text: str
    embedding: List[float]
    dimension: int
    model_name: str
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseEmbedder(ABC):
    """嵌入器基类"""
    
    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """嵌入单个文本"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量嵌入文本"""
        pass


class MockEmbedder(BaseEmbedder):
    """模拟嵌入器（用于测试和无依赖环境）"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.model_name = "mock-embedder"
    
    async def embed(self, text: str) -> EmbeddingResult:
        """生成模拟嵌入向量"""
        import time
        import hashlib
        
        start_time = time.time()
        
        text_hash = hashlib.md5(text.encode()).hexdigest()
        embedding = []
        for i in range(self.dimension):
            hash_part = int(text_hash[i % len(text_hash)], 16) / 15.0
            embedding.append(hash_part * 2 - 1)
        
        processing_time = (time.time() - start_time) * 1000
        
        return EmbeddingResult(
            text=text,
            embedding=embedding,
            dimension=self.dimension,
            model_name=self.model_name,
            processing_time_ms=processing_time
        )
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量生成模拟嵌入向量"""
        return [await self.embed(text) for text in texts]


class SentenceTransformerEmbedder(BaseEmbedder):
    """Sentence-Transformer 嵌入器"""
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.model = None
        self.model_name = config.model_name
        
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(config.model_name)
            logger.info(f"Loaded SentenceTransformer model: {config.model_name}")
        except (ImportError, Exception) as e:
            logger.warning(f"Failed to load SentenceTransformer: {e}, using mock embedder")
            self.model = None
    
    async def embed(self, text: str) -> EmbeddingResult:
        """嵌入单个文本"""
        import time
        
        start_time = time.time()
        
        if self.model is None:
            mock = MockEmbedder(self.config.embedding_dimension)
            return await mock.embed(text)
        
        embedding = self.model.encode(
            text,
            normalize_embeddings=self.config.normalize_embeddings
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return EmbeddingResult(
            text=text,
            embedding=embedding.tolist(),
            dimension=len(embedding),
            model_name=self.model_name,
            processing_time_ms=processing_time
        )
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量嵌入文本"""
        import time
        
        start_time = time.time()
        
        if self.model is None:
            mock = MockEmbedder(self.config.embedding_dimension)
            return await mock.embed_batch(texts)
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            normalize_embeddings=self.config.normalize_embeddings
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        results = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            results.append(EmbeddingResult(
                text=text,
                embedding=embedding.tolist(),
                dimension=len(embedding),
                model_name=self.model_name,
                processing_time_ms=processing_time / len(texts)
            ))
        
        return results


class NeuralEmbeddingLayer:
    """神经网络嵌入层 - Layer 1
    
    将输入文本转换为向量表示，支持多种嵌入模型。
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        
        # 检查环境变量是否强制使用mock
        if os.environ.get("NEURALAGENT_USE_MOCK_EMBEDDER", "false").lower() in ("true", "1", "yes"):
            self.config.use_mock = True
            logger.info("Forcing mock embedder due to NEURALAGENT_USE_MOCK_EMBEDDER environment variable")
        
        self.embedder: BaseEmbedder = self._create_embedder()
        
        self._cache: Dict[str, EmbeddingResult] = {}
        self._stats = {
            "total_embeddings": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time_ms": 0.0,
        }
    
    def _create_embedder(self) -> BaseEmbedder:
        """创建嵌入器"""
        # 优先使用mock模式
        if self.config.use_mock:
            logger.info("Using mock embedder (config.use_mock=True)")
            return MockEmbedder(self.config.embedding_dimension)
        
        # 尝试使用SentenceTransformer
        if "sentence-transformers" in self.config.model_name or "all-MiniLM" in self.config.model_name:
            try:
                embedder = SentenceTransformerEmbedder(self.config)
                if embedder.model is not None:
                    return embedder
                else:
                    logger.info("Falling back to mock embedder (SentenceTransformer failed)")
                    return MockEmbedder(self.config.embedding_dimension)
            except Exception as e:
                logger.warning(f"Failed to create SentenceTransformerEmbedder: {e}, using mock")
                return MockEmbedder(self.config.embedding_dimension)
        else:
            return MockEmbedder(self.config.embedding_dimension)
    
    async def forward(
        self,
        input_data: Union[str, Dict[str, Any], List[str]]
    ) -> Dict[str, Any]:
        """前向传播
        
        Args:
            input_data: 输入数据，可以是文本、字典或列表
            
        Returns:
            包含嵌入向量的字典
        """
        import time
        start_time = time.time()
        
        if isinstance(input_data, str):
            texts = [input_data]
            input_type = "single_text"
        elif isinstance(input_data, list):
            texts = input_data
            input_type = "text_list"
        elif isinstance(input_data, dict):
            texts = self._extract_texts_from_dict(input_data)
            input_type = "dict"
        else:
            texts = [str(input_data)]
            input_type = "other"
        
        embeddings = []
        for text in texts:
            if self.config.use_cache and text in self._cache:
                result = self._cache[text]
                self._stats["cache_hits"] += 1
            else:
                result = await self.embedder.embed(text)
                self._stats["cache_misses"] += 1
                
                if self.config.use_cache and len(self._cache) < self.config.cache_size:
                    self._cache[text] = result
            
            embeddings.append(result)
            self._stats["total_embeddings"] += 1
            self._stats["total_processing_time_ms"] += result.processing_time_ms
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "embeddings": embeddings,
            "embedding_dimension": self.config.embedding_dimension,
            "model_name": self.config.model_name,
            "input_type": input_type,
            "num_texts": len(texts),
            "processing_time_ms": processing_time,
            "layer": "embedding",
            "layer_id": 1,
        }
    
    def _extract_texts_from_dict(self, data: Dict[str, Any]) -> List[str]:
        """从字典中提取文本"""
        texts = []
        
        text_fields = ["query", "text", "content", "description", "requirement", "code"]
        
        for field in text_fields:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    texts.append(value)
                elif isinstance(value, list):
                    texts.extend([str(v) for v in value])
        
        if not texts:
            texts.append(str(data))
        
        return texts
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self._stats["cache_hits"] + self._stats["cache_misses"]
        cache_hit_rate = self._stats["cache_hits"] / total if total > 0 else 0.0
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_embeddings"]
            if self._stats["total_embeddings"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "cache_hit_rate": cache_hit_rate,
            "avg_processing_time_ms": avg_processing_time,
            "cache_size": len(self._cache),
            "config": {
                "model_name": self.config.model_name,
                "embedding_dimension": self.config.embedding_dimension,
                "use_mock": self.config.use_mock,
            }
        }
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("Embedding cache cleared")


def create_embedding_layer(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    dimension: int = 768,
    use_mock: bool = False
) -> NeuralEmbeddingLayer:
    """创建嵌入层实例"""
    config = EmbeddingConfig(
        model_name=model_name,
        embedding_dimension=dimension,
        use_mock=use_mock
    )
    return NeuralEmbeddingLayer(config)
