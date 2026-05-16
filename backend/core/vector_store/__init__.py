"""
NeuralAgent - 向量存储包
支持多种向量数据库后端
"""
from .base import (
    VectorStore,
    VectorStoreType,
    VectorStoreConfig,
    VectorDocument,
    SearchStrategy,
    InMemoryVectorStore,
    create_vector_store
)

__all__ = [
    "VectorStore",
    "VectorStoreType",
    "VectorStoreConfig",
    "VectorDocument",
    "SearchStrategy",
    "InMemoryVectorStore",
    "create_vector_store"
]
