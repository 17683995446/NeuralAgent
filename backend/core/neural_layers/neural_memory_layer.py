"""Neural Memory Layer - 神经网络记忆层

Layer 13 of the NeuralAgent Deep Architecture.

功能：
- 存储和检索长期记忆
- 记忆增强的上下文生成
- 支持向量检索和语义搜索
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """记忆层配置"""
    memory_capacity: int = 10000
    embedding_dimension: int = 768
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.7
    use_external_memory: bool = False


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    embedding: List[float]
    timestamp: datetime
    importance: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryRetrievalResult:
    """记忆检索结果"""
    query: str
    retrieved_memories: List[MemoryEntry]
    similarity_scores: List[float]
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class NeuralMemoryLayer:
    """神经网络记忆层 - Layer 13
    
    存储和检索长期记忆，提供记忆增强的上下文。
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.memories: Dict[str, MemoryEntry] = {}
        self.memory_index: List[str] = []
        
        self._stats = {
            "total_memories": 0,
            "total_retrievals": 0,
            "total_stores": 0,
            "total_processing_time_ms": 0.0,
        }
    
    async def forward(
        self,
        input_data: Union[Dict[str, Any], str]
    ) -> Dict[str, Any]:
        """前向传播
        
        Args:
            input_data: 输入数据
            
        Returns:
            包含记忆增强结果的字典
        """
        import time
        start_time = time.time()
        
        if isinstance(input_data, dict):
            if "dropout_output" in input_data:
                query_embedding = input_data["dropout_output"]
                query_text = input_data.get("query", "")
            elif "data" in input_data:
                query_embedding = input_data["data"]
                query_text = input_data.get("query", "")
            else:
                query_embedding = [[0.0] * self.config.embedding_dimension]
                query_text = ""
        else:
            query_embedding = [[0.0] * self.config.embedding_dimension]
            query_text = str(input_data)
        
        if query_embedding and isinstance(query_embedding[0], list):
            query_embedding = query_embedding[0]
        
        retrieval_result = await self._retrieve_memories(query_embedding, query_text)
        
        memory_context = self._generate_memory_context(retrieval_result)
        
        self._stats["total_retrievals"] += 1
        
        processing_time = (time.time() - start_time) * 1000
        self._stats["total_processing_time_ms"] += processing_time
        
        return {
            "memory_output": query_embedding if query_embedding else [0.0] * self.config.embedding_dimension,
            "retrieved_memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "importance": m.importance,
                    "tags": m.tags,
                }
                for m in retrieval_result.retrieved_memories
            ],
            "similarity_scores": retrieval_result.similarity_scores,
            "memory_context": memory_context,
            "num_memories_retrieved": len(retrieval_result.retrieved_memories),
            "total_memories_stored": len(self.memories),
            "layer": "memory",
            "layer_id": 13,
            "processing_time_ms": processing_time,
        }
    
    async def store_memory(
        self,
        content: str,
        embedding: List[float],
        importance: float = 1.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """存储记忆
        
        Args:
            content: 记忆内容
            embedding: 嵌入向量
            importance: 重要性分数
            tags: 标签列表
            metadata: 元数据
            
        Returns:
            记忆ID
        """
        import uuid
        
        memory_id = str(uuid.uuid4())
        
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            embedding=embedding,
            timestamp=datetime.utcnow(),
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.memories[memory_id] = memory
        self.memory_index.append(memory_id)
        
        if len(self.memories) > self.config.memory_capacity:
            self._evict_memories()
        
        self._stats["total_stores"] += 1
        self._stats["total_memories"] = len(self.memories)
        
        logger.info(f"Stored memory {memory_id}: {content[:50]}...")
        
        return memory_id
    
    async def _retrieve_memories(
        self,
        query_embedding: List[float],
        query_text: str
    ) -> MemoryRetrievalResult:
        """检索记忆"""
        import time
        start_time = time.time()
        
        if not self.memories:
            return MemoryRetrievalResult(
                query=query_text,
                retrieved_memories=[],
                similarity_scores=[],
                processing_time_ms=0.0
            )
        
        similarities = []
        memory_list = list(self.memories.values())
        
        for memory in memory_list:
            similarity = self._cosine_similarity(query_embedding, memory.embedding)
            similarities.append((memory, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        top_memories = []
        top_scores = []
        
        for memory, score in similarities[:self.config.retrieval_top_k]:
            if score >= self.config.similarity_threshold:
                top_memories.append(memory)
                top_scores.append(score)
        
        processing_time = (time.time() - start_time) * 1000
        
        return MemoryRetrievalResult(
            query=query_text,
            retrieved_memories=top_memories,
            similarity_scores=top_scores,
            processing_time_ms=processing_time
        )
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        import math
        
        if not a or not b or len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(x ** 2 for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _generate_memory_context(self, retrieval_result: MemoryRetrievalResult) -> str:
        """生成记忆上下文"""
        if not retrieval_result.retrieved_memories:
            return "No relevant memories found."
        
        context_parts = ["Relevant memories:"]
        
        for i, memory in enumerate(retrieval_result.retrieved_memories):
            score = retrieval_result.similarity_scores[i] if i < len(retrieval_result.similarity_scores) else 0.0
            context_parts.append(f"{i + 1}. [{score:.2f}] {memory.content}")
        
        return "\n".join(context_parts)
    
    def _evict_memories(self) -> None:
        """淘汰记忆"""
        if not self.memories:
            return
        
        sorted_memories = sorted(
            self.memories.items(),
            key=lambda x: x[1].importance * (1.0 / (1 + (datetime.utcnow() - x[1].timestamp).total_seconds() / 86400))
        )
        
        num_to_evict = len(self.memories) - self.config.memory_capacity + 100
        
        for memory_id, _ in sorted_memories[:num_to_evict]:
            del self.memories[memory_id]
            if memory_id in self.memory_index:
                self.memory_index.remove(memory_id)
        
        logger.info(f"Evicted {num_to_evict} memories")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_retrievals"]
            if self._stats["total_retrievals"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "avg_processing_time_ms": avg_processing_time,
            "config": {
                "memory_capacity": self.config.memory_capacity,
                "retrieval_top_k": self.config.retrieval_top_k,
            }
        }


def create_memory_layer(
    capacity: int = 10000,
    dimension: int = 768
) -> NeuralMemoryLayer:
    """创建记忆层实例"""
    config = MemoryConfig(
        memory_capacity=capacity,
        embedding_dimension=dimension
    )
    return NeuralMemoryLayer(config)
