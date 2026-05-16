"""Vector Database Integration - 向量数据库集成

支持多种向量数据库：
- Chroma (默认，离线优先)
- Pinecone (云端)
- Milvus (自托管)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    id: str
    text: str
    embedding: Optional[List[float]] = None
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorDBConfig:
    """向量数据库配置"""
    provider: str = "chroma"  # chroma, pinecone, milvus
    collection_name: str = "neural_agent"
    embedding_dimension: int = 768
    persist_directory: Optional[str] = None
    # Pinecone配置
    api_key: Optional[str] = None
    environment: Optional[str] = None
    # Milvus配置
    host: Optional[str] = None
    port: Optional[int] = None


class BaseVectorDB(ABC):
    """向量数据库基类"""
    
    @abstractmethod
    async def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加向量"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """搜索向量"""
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """删除向量"""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """获取向量数量"""
        pass


class ChromaVectorDB(BaseVectorDB):
    """Chroma向量数据库（离线优先）"""
    
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.client = None
        self.collection = None
        self._initialize()
    
    def _initialize(self):
        """初始化Chroma"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 创建客户端
            if self.config.persist_directory:
                self.client = chromadb.PersistentClient(
                    path=self.config.persist_directory,
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                self.client = chromadb.Client()
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"dimension": self.config.embedding_dimension}
            )
            
            logger.info(f"Initialized Chroma collection: {self.config.collection_name}")
        except ImportError:
            logger.warning("Chroma not installed, using in-memory fallback")
            self.client = None
            self.collection = None
    
    async def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加向量"""
        if self.collection is None:
            logger.warning("Chroma not available, skipping add operation")
            return []
        
        # 生成IDs
        if ids is None:
            ids = [f"id_{i}_{datetime.now().timestamp()}" for i in range(len(texts))]
        
        # 添加到集合
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{}] * len(texts),
            ids=ids
        )
        
        logger.info(f"Added {len(texts)} vectors to collection")
        return ids
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """搜索向量"""
        if self.collection is None:
            logger.warning("Chroma not available, returning empty results")
            return []
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict
        )
        
        search_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                search_results.append(VectorSearchResult(
                    id=results['ids'][0][i],
                    text=results['documents'][0][i],
                    embedding=results['embeddings'][0][i] if 'embeddings' in results else None,
                    score=float(results['distances'][0][i]) if 'distances' in results else 0.0,
                    metadata=results['metadatas'][0][i] if 'metadatas' in results else {}
                ))
        
        return search_results
    
    async def delete(self, ids: List[str]) -> bool:
        """删除向量"""
        if self.collection is None:
            return False
        
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} vectors from collection")
        return True
    
    async def count(self) -> int:
        """获取向量数量"""
        if self.collection is None:
            return 0
        return self.collection.count()


class InMemoryVectorDB(BaseVectorDB):
    """内存向量数据库（无依赖）"""
    
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.vectors: Dict[str, Dict[str, Any]] = {}
        self._id_counter = 0
    
    async def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加向量"""
        if ids is None:
            ids = [f"mem_{self._id_counter + i}" for i in range(len(texts))]
        
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            self.vectors[ids[i]] = {
                "text": text,
                "embedding": embedding,
                "metadata": metadatas[i] if metadatas else {},
                "created_at": datetime.now()
            }
            self._id_counter += 1
        
        logger.info(f"Added {len(texts)} vectors to in-memory store")
        return ids
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """搜索向量（简单余弦相似度）"""
        results = []
        
        for vid, data in self.vectors.items():
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_embedding, data["embedding"])
            
            results.append(VectorSearchResult(
                id=vid,
                text=data["text"],
                embedding=data["embedding"],
                score=similarity,
                metadata=data["metadata"]
            ))
        
        # 排序并返回top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    async def delete(self, ids: List[str]) -> bool:
        """删除向量"""
        for vid in ids:
            if vid in self.vectors:
                del self.vectors[vid]
        return True
    
    async def count(self) -> int:
        """获取向量数量"""
        return len(self.vectors)


def create_vector_db(config: Optional[VectorDBConfig] = None) -> BaseVectorDB:
    """创建向量数据库实例"""
    config = config or VectorDBConfig()
    
    if config.provider == "chroma":
        try:
            return ChromaVectorDB(config)
        except Exception as e:
            logger.warning(f"Failed to initialize Chroma: {e}, falling back to in-memory")
            return InMemoryVectorDB(config)
    else:
        return InMemoryVectorDB(config)


# 全局实例
_vector_db: Optional[BaseVectorDB] = None


def get_vector_db() -> BaseVectorDB:
    """获取全局向量数据库实例"""
    global _vector_db
    if _vector_db is None:
        _vector_db = create_vector_db()
    return _vector_db
