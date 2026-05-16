
"""向量存储集成 - 增强错误处理和可靠性
"""
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import logging
import json
import time
import threading

logger = logging.getLogger(__name__)

# Milvus导入（可选）
try:
    from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logger.warning("Milvus not available")


class VectorStoreError(Exception):
    """向量存储错误基类"""
    pass


class ConnectionError(VectorStoreError):
    """连接错误"""
    pass


class OperationTimeoutError(VectorStoreError):
    """操作超时"""
    pass


class QuotaExceededError(VectorStoreError):
    """配额超限"""
    pass


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常
    OPEN = "open"  # 熔断中
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    id: str
    score: float
    metadata: Dict[str, Any]
    content: str


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3


class CircuitBreaker:
    """熔断器 - 防止级联故障"""
    
    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """执行带熔断保护的函数"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info("Circuit breaker: OPEN -> HALF_OPEN")
                else:
                    raise VectorStoreError("Circuit breaker is OPEN")
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise VectorStoreError("Circuit breaker half-open max calls exceeded")
                self.half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if not self.last_failure_time:
            return True
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout
    
    def _on_success(self):
        """记录成功"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info("Circuit breaker: HALF_OPEN -> CLOSED")
            self.failure_count = 0
    
    def _on_failure(self):
        """记录失败"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker: HALF_OPEN -> OPEN")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker: CLOSED -> OPEN (failures: {self.failure_count})")
    
    def reset(self):
        """重置熔断器"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
            self.last_failure_time = None


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    initial_delay: float = 0.1
    backoff_factor: float = 2.0
    max_delay: float = 10.0
    retryable_errors: Tuple = (ConnectionError, OperationTimeoutError)


def with_retry(config: RetryConfig = None):
    """重试装饰器"""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retryable_errors as e:
                    last_error = e
                    if attempt < config.max_retries:
                        delay = min(
                            config.initial_delay * (config.backoff_factor ** attempt),
                            config.max_delay
                        )
                        logger.warning(
                            f"Retryable error in {func.__name__} (attempt {attempt + 1}), "
                            f"retrying in {delay:.2f}s: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {attempt + 1} attempts")
            
            raise last_error
        
        return wrapper
    return decorator


class HealthStatus:
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class VectorStoreBase:
    """向量存储基类"""
    
    def add(
        self,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> bool:
        """添加向量"""
        raise NotImplementedError
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """搜索相似向量"""
        raise NotImplementedError
    
    def delete(self, ids: List[str]) -> bool:
        """删除向量"""
        raise NotImplementedError
    
    def count(self) -> int:
        """获取向量数量"""
        raise NotImplementedError
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        raise NotImplementedError


class MilvusVectorStore(VectorStoreBase):
    """Milvus向量存储实现 - 增强错误处理"""
    
    COLLECTION_NAME = "code_chunks"
    DIMENSION = 1536
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = COLLECTION_NAME,
        timeout: float = 30.0,
        retry_config: RetryConfig = None,
        circuit_breaker_config: CircuitBreakerConfig = None
    ):
        """初始化Milvus向量存储
        
        Args:
            host: Milvus主机地址
            port: Milvus端口
            collection_name: 集合名称
            timeout: 操作超时时间
            retry_config: 重试配置
            circuit_breaker_config: 熔断器配置
        """
        if not MILVUS_AVAILABLE:
            raise RuntimeError("Milvus not available. Install pymilvus: pip install pymilvus")
        
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)
        self.collection = None
        self._connection_time: Optional[datetime] = None
        self._last_error: Optional[Exception] = None
        self._stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "total_latency": 0.0
        }
        
        self._connect()
        self._ensure_collection()
    
    def _connect(self):
        """连接到Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            self._connection_time = datetime.now()
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            self._last_error = e
            raise ConnectionError(f"Failed to connect to Milvus: {e}") from e
    
    def _ensure_collection(self):
        """确保集合存在"""
        try:
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"Loaded existing collection: {self.collection_name}")
            else:
                self._create_collection()
        except Exception as e:
            self._last_error = e
            raise VectorStoreError(f"Failed to ensure collection: {e}") from e
    
    def _create_collection(self):
        """创建集合"""
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="chunk_name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.DIMENSION),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=4096),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Code chunks vector storage for large-scale code analysis"
        )
        
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )
        
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"efConstruction": 128, "M": 16}
        }
        
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        self.collection.flush()
        logger.info(f"Created new collection: {self.collection_name}")
    
    def _record_operation(self, success: bool, latency: float):
        """记录操作统计"""
        self._stats["total_operations"] += 1
        self._stats["total_latency"] += latency
        if success:
            self._stats["successful_operations"] += 1
        else:
            self._stats["failed_operations"] += 1
    
    @with_retry()
    def add(
        self,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> bool:
        """添加向量到存储"""
        start_time = time.time()
        try:
            def _do_add():
                entities = [
                    ids,
                    [m.get("file_path", "") for m in metadata],
                    [m.get("chunk_type", "") for m in metadata],
                    [m.get("chunk_name", "") for m in metadata],
                    [text[:50000] for text in texts],
                    embeddings,
                    [json.dumps(m, ensure_ascii=False) for m in metadata],
                ]
                
                self.collection.insert(entities)
                self.collection.flush()
            
            self.circuit_breaker.call(_do_add)
            
            latency = time.time() - start_time
            self._record_operation(True, latency)
            logger.info(f"Added {len(ids)} vectors to Milvus in {latency:.2f}s")
            return True
            
        except Exception as e:
            latency = time.time() - start_time
            self._record_operation(False, latency)
            self._last_error = e
            logger.error(f"Failed to add vectors: {e}")
            return False
    
    @with_retry()
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """搜索相似向量"""
        start_time = time.time()
        
        def _do_search():
            search_params = {
                "metric_type": "COSINE",
                "params": {"ef": 64}
            }
            
            expr = filter_expr if filter_expr else None
            
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["id", "file_path", "chunk_type", "chunk_name", "content", "metadata"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    meta = {}
                    try:
                        meta = json.loads(hit.entity.get("metadata", "{}"))
                    except Exception:
                        pass
                    search_results.append(VectorSearchResult(
                        id=hit.entity.get("id"),
                        score=hit.score,
                        metadata={
                            "file_path": hit.entity.get("file_path"),
                            "chunk_type": hit.entity.get("chunk_type"),
                            "chunk_name": hit.entity.get("chunk_name"),
                            **meta
                        },
                        content=hit.entity.get("content", "")
                    ))
            
            return search_results
        
        try:
            search_results = self.circuit_breaker.call(_do_search)
            latency = time.time() - start_time
            self._record_operation(True, latency)
            return search_results
            
        except Exception as e:
            latency = time.time() - start_time
            self._record_operation(False, latency)
            self._last_error = e
            logger.error(f"Search failed: {e}")
            return []
    
    @with_retry()
    def search_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """通过文本搜索"""
        try:
            from backend.core.llm_adapter import llm_adapter
            embedding = llm_adapter.embed_single_sync(query_text)
            return self.search(embedding, top_k, filter_expr)
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []
    
    @with_retry()
    def delete(self, ids: List[str]) -> bool:
        """删除向量"""
        try:
            expr = f'id in {ids}'
            self.collection.delete(expr)
            self.collection.flush()
            logger.info(f"Deleted {len(ids)} vectors from Milvus")
            return True
        except Exception as e:
            self._last_error = e
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    @with_retry()
    def count(self) -> int:
        """获取向量数量"""
        try:
            return self.collection.num_entities
        except Exception as e:
            self._last_error = e
            logger.error(f"Failed to count entities: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = HealthStatus.HEALTHY
        issues = []
        
        # 检查连接
        if not self._connection_time:
            status = HealthStatus.UNHEALTHY
            issues.append("Not connected")
        
        # 检查最后错误
        if self._last_error:
            time_since_error = (datetime.now() - getattr(self._last_error, 'timestamp', self._connection_time or datetime.now())).total_seconds()
            if time_since_error < 300:
                status = HealthStatus.DEGRADED
                issues.append(f"Recent error: {self.last_error}")
        
        # 检查熔断器状态
        if self.circuit_breaker.state == CircuitState.OPEN:
            status = HealthStatus.UNHEALTHY
            issues.append("Circuit breaker is OPEN")
        elif self.circuit_breaker.state == CircuitState.HALF_OPEN:
            status = HealthStatus.DEGRADED
            issues.append("Circuit breaker is HALF_OPEN")
        
        # 计算平均延迟
        avg_latency = 0.0
        if self._stats["total_operations"] > 0:
            avg_latency = self._stats["total_latency"] / self._stats["total_operations"]
            if avg_latency > 5.0:
                status = HealthStatus.DEGRADED
                issues.append(f"High latency: {avg_latency:.2f}s")
        
        return {
            "status": status,
            "circuit_breaker": self.circuit_breaker.state.value,
            "avg_latency": avg_latency,
            "total_operations": self._stats["total_operations"],
            "failed_operations": self._stats["failed_operations"],
            "last_error": str(self._last_error) if self._last_error else None,
            "issues": issues
        }
    
    def reset_circuit_breaker(self):
        """重置熔断器"""
        self.circuit_breaker.reset()
        logger.info("Circuit breaker reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "success_rate": (
                self._stats["successful_operations"] / self._stats["total_operations"]
                if self._stats["total_operations"] > 0 else 0.0
            ),
            "avg_latency": (
                self._stats["total_latency"] / self._stats["total_operations"]
                if self._stats["total_operations"] > 0 else 0.0
            )
        }


class ChromaVectorStore(VectorStoreBase):
    """Chroma轻量级向量存储 - 增强错误处理"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        timeout: float = 30.0,
        retry_config: RetryConfig = None,
        circuit_breaker_config: CircuitBreakerConfig = None
    ):
        """初始化Chroma向量存储"""
        self.persist_directory = persist_directory
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)
        self.client = None
        self.collection = None
        self._last_error: Optional[Exception] = None
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.Client(Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            ))
            
            # 检查集合是否已存在
            try:
                self.collection = self.client.get_collection(name="code_chunks")
                logger.info("Loaded existing Chroma collection")
            except Exception:
                self.collection = self.client.create_collection(
                    name="code_chunks",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new Chroma collection")
            
            logger.info(f"Chroma initialized at {persist_directory}")
            
        except ImportError:
            raise RuntimeError("Chroma not available. Install chromadb: pip install chromadb")
    
    @with_retry()
    def add(
        self,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> bool:
        """添加向量"""
        try:
            def _do_add():
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=[{**m, "chunk_id": idx} for idx, m in enumerate(metadata)]
                )
            
            self.circuit_breaker.call(_do_add)
            return True
        except Exception as e:
            self._last_error = e
            logger.error(f"Failed to add to Chroma: {e}")
            return False
    
    @with_retry()
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """搜索相似向量"""
        try:
            def _do_search():
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                
                search_results = []
                for i in range(len(results["ids"][0])):
                    search_results.append(VectorSearchResult(
                        id=results["ids"][0][i],
                        score=1.0 - results["distances"][0][i],
                        metadata=results["metadatas"][0][i],
                        content=results["documents"][0][i]
                    ))
                
                return search_results
            
            return self.circuit_breaker.call(_do_search)
            
        except Exception as e:
            self._last_error = e
            logger.error(f"Chroma search failed: {e}")
            return []
    
    @with_retry()
    def delete(self, ids: List[str]) -> bool:
        """删除向量"""
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            self._last_error = e
            logger.error(f"Failed to delete from Chroma: {e}")
            return False
    
    @with_retry()
    def count(self) -> int:
        """获取向量数量"""
        try:
            return len(self.collection.get()["ids"])
        except Exception:
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = HealthStatus.HEALTHY
        issues = []
        
        if self._last_error:
            status = HealthStatus.DEGRADED
            issues.append(f"Recent error: {self._last_error}")
        
        if self.circuit_breaker.state == CircuitState.OPEN:
            status = HealthStatus.UNHEALTHY
            issues.append("Circuit breaker is OPEN")
        
        return {
            "status": status,
            "circuit_breaker": self.circuit_breaker.state.value,
            "last_error": str(self._last_error) if self._last_error else None,
            "issues": issues
        }
    
    def reset_circuit_breaker(self):
        """重置熔断器"""
        self.circuit_breaker.reset()


def create_vector_store(
    backend: str = "chroma",
    timeout: float = 30.0,
    retry_config: RetryConfig = None,
    circuit_breaker_config: CircuitBreakerConfig = None,
    **kwargs
) -> VectorStoreBase:
    """工厂函数：创建向量存储
    
    Args:
        backend: 存储后端 ("milvus" | "chroma")
        timeout: 操作超时时间
        retry_config: 重试配置
        circuit_breaker_config: 熔断器配置
        **kwargs: 额外参数
        
    Returns:
        向量存储实例
    """
    common_kwargs = {
        "timeout": timeout,
        "retry_config": retry_config,
        "circuit_breaker_config": circuit_breaker_config
    }
    
    if backend == "milvus":
        return MilvusVectorStore(**kwargs, **common_kwargs)
    elif backend == "chroma":
        return ChromaVectorStore(**kwargs, **common_kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")
