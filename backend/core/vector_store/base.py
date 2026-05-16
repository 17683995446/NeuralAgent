"""
NeuralAgent - 向量存储统一接口
支持多种向量数据库后端：Milvus、Qdrant、Weaviate、Pinecone
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


class VectorStoreType(Enum):
    """向量数据库类型"""
    MILVUS = "milvus"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    PINECONE = "pinecone"
    CHROMA = "chroma"
    FAISS = "faiss"


class SearchStrategy(Enum):
    """搜索策略"""
    SIMILARITY = "similarity"
    MMR = "mmr"
    HYBRID = "hybrid"


@dataclass
class VectorDocument:
    """向量文档"""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None


@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    type: VectorStoreType
    host: str = "localhost"
    port: int = 19530
    collection_name: str = "neuralagent_docs"
    dimension: int = 1536
    metric_type: str = "COSINE"
    index_params: Dict[str, Any] = field(default_factory=dict)
    batch_size: int = 100


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到向量数据库"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def create_collection(self, collection_name: Optional[str] = None) -> None:
        """创建集合"""
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: Optional[str] = None) -> None:
        """删除集合"""
        pass
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[VectorDocument],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """添加文档"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_expr: Optional[Dict[str, Any]] = None,
        strategy: SearchStrategy = SearchStrategy.SIMILARITY
    ) -> List[VectorDocument]:
        """搜索相似文档"""
        pass
    
    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """获取单个文档"""
        pass
    
    @abstractmethod
    async def delete_documents(self, doc_ids: List[str]) -> None:
        """删除文档"""
        pass
    
    @abstractmethod
    async def count_documents(self) -> int:
        """统计文档数量"""
        pass


class InMemoryVectorStore(VectorStore):
    """内存向量存储（用于测试和开发）"""
    
    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self.documents: Dict[str, VectorDocument] = {}
        self.embeddings: Dict[str, List[float]] = {}
        self._connected = False
    
    async def connect(self) -> None:
        self._connected = True
    
    async def disconnect(self) -> None:
        self._connected = False
    
    async def create_collection(self, collection_name: Optional[str] = None) -> None:
        if collection_name:
            self.config.collection_name = collection_name
    
    async def delete_collection(self, collection_name: Optional[str] = None) -> None:
        self.documents.clear()
        self.embeddings.clear()
    
    async def add_documents(
        self,
        documents: List[VectorDocument],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        doc_ids = []
        for i, doc in enumerate(documents):
            self.documents[doc.id] = doc
            if embeddings and i < len(embeddings):
                self.embeddings[doc.id] = embeddings[i]
            doc_ids.append(doc.id)
        return doc_ids
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_expr: Optional[Dict[str, Any]] = None,
        strategy: SearchStrategy = SearchStrategy.SIMILARITY
    ) -> List[VectorDocument]:
        scores = []
        
        for doc_id, doc in self.documents.items():
            if doc_id in self.embeddings:
                doc_vec = self.embeddings[doc_id]
                similarity = self._cosine_similarity(query_embedding, doc_vec)
                scores.append((similarity, doc))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, doc in scores[:top_k]:
            result_doc = VectorDocument(
                id=doc.id,
                content=doc.content,
                embedding=doc.embedding,
                metadata=doc.metadata,
                score=score
            )
            results.append(result_doc)
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度（不依赖numpy）"""
        if not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        return self.documents.get(doc_id)
    
    async def delete_documents(self, doc_ids: List[str]) -> None:
        for doc_id in doc_ids:
            if doc_id in self.documents:
                del self.documents[doc_id]
            if doc_id in self.embeddings:
                del self.embeddings[doc_id]
    
    async def count_documents(self) -> int:
        return len(self.documents)


def create_vector_store(config: VectorStoreConfig) -> VectorStore:
    """创建向量存储实例"""
    if config.type == VectorStoreType.MILVUS:
        # TODO: 实现 MilvusVectorStore
        return InMemoryVectorStore(config)
    elif config.type == VectorStoreType.QDRANT:
        # TODO: 实现 QdrantVectorStore
        return InMemoryVectorStore(config)
    elif config.type == VectorStoreType.CHROMA:
        # TODO: 实现 ChromaVectorStore
        return InMemoryVectorStore(config)
    else:
        return InMemoryVectorStore(config)
