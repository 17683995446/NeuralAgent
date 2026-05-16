"""批量embedding优化和缓存层
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import time
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingCacheConfig:
    """Embedding缓存配置"""
    max_size: int = 10000
    ttl_seconds: float = 3600.0
    batch_size: int = 100


class LRUCache:
    """线程安全的LRU缓存"""
    
    def __init__(self, max_size: int = 10000):
        """初始化LRU缓存
        
        Args:
            max_size: 最大缓存条目数
        """
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在则返回None
        """
        with self._lock:
            if key in self._cache:
                # 移动到末尾（最近使用）
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None
    
    def set(self, key: str, value: Any):
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                self._cache[key] = value
                if len(self._cache) > self.max_size:
                    # 移除最旧的条目
                    self._cache.popitem(last=False)
    
    def delete(self, key: str):
        """删除缓存值
        
        Args:
            key: 缓存键
        """
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计
        
        Returns:
            统计信息
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate
            }


class TTLCache:
    """带过期时间的缓存"""
    
    def __init__(self, max_size: int = 10000, default_ttl: float = 3600.0):
        """初始化TTL缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._expiry: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（自动检查过期）
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在或过期则返回None
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            # 检查是否过期
            if key in self._expiry and time.time() > self._expiry[key]:
                # 已过期，删除
                del self._cache[key]
                del self._expiry[key]
                return None
            
            # 移动到末尾
            self._cache.move_to_end(key)
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None则使用默认值
        """
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                self._cache[key] = value
                if len(self._cache) > self.max_size:
                    # 移除最旧的未过期条目
                    self._evict_oldest()
            
            # 设置过期时间
            self._expiry[key] = time.time() + (ttl if ttl is not None else self.default_ttl)
    
    def _evict_oldest(self):
        """移除最旧的条目"""
        if not self._cache:
            return
        
        oldest_key = next(iter(self._cache))
        del self._cache[oldest_key]
        if oldest_key in self._expiry:
            del self._expiry[oldest_key]
    
    def cleanup_expired(self):
        """清理所有过期条目"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, expiry in self._expiry.items()
                if current_time > expiry
            ]
            for key in expired_keys:
                del self._cache[key]
                del self._expiry[key]
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计
        
        Returns:
            统计信息
        """
        with self._lock:
            current_time = time.time()
            expired_count = sum(1 for e in self._expiry.values() if current_time > e)
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "expired_count": expired_count
            }


class BatchEmbeddingCache:
    """批量embedding缓存"""
    
    def __init__(
        self,
        max_size: int = 10000,
        ttl_seconds: float = 3600.0,
        batch_size: int = 100
    ):
        """初始化批量embedding缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 过期时间（秒）
            batch_size: 批处理大小
        """
        self.cache = TTLCache(max_size=max_size, default_ttl=ttl_seconds)
        self.batch_size = batch_size
        self._pending_batch: List[str] = []
        self._pending_callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._batch_lock = threading.Lock()
    
    def _compute_key(self, text: str) -> str:
        """计算文本的缓存键
        
        Args:
            text: 文本内容
            
        Returns:
            MD5哈希作为键
        """
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """获取缓存的embedding
        
        Args:
            text: 文本内容
            
        Returns:
            embedding向量，不存在则返回None
        """
        key = self._compute_key(text)
        return self.cache.get(key)
    
    def set(self, text: str, embedding: List[float], ttl: Optional[float] = None):
        """设置缓存
        
        Args:
            text: 文本内容
            embedding: embedding向量
            ttl: 过期时间（秒）
        """
        key = self._compute_key(text)
        self.cache.set(key, embedding, ttl)
    
    def get_batch(
        self,
        texts: List[str],
        embedding_fn: Callable[[List[str]], List[List[float]]]
    ) -> List[Optional[List[float]]]:
        """批量获取embedding（智能缓存）
        
        Args:
            texts: 文本列表
            embedding_fn: embedding生成函数
            
        Returns:
            embedding向量列表
        """
        results = []
        cache_hits = []
        cache_misses = []
        miss_indices = []
        
        # 第一步：检查缓存
        for i, text in enumerate(texts):
            cached = self.get(text)
            if cached is not None:
                results.append(cached)
                cache_hits.append(i)
            else:
                results.append(None)
                cache_misses.append(text)
                miss_indices.append(i)
        
        # 第二步：批量处理未命中的
        if cache_misses:
            # 分批处理
            for i in range(0, len(cache_misses), self.batch_size):
                batch = cache_misses[i:i + self.batch_size]
                
                try:
                    batch_embeddings = embedding_fn(batch)
                    
                    # 更新缓存和结果
                    for j, (text, embedding) in enumerate(zip(batch, batch_embeddings)):
                        original_idx = miss_indices[i + j]
                        results[original_idx] = embedding
                        self.set(text, embedding)
                        
                except Exception as e:
                    logger.error(f"Batch embedding failed: {e}")
                    # 失败的处理
                    for j in range(len(batch)):
                        original_idx = miss_indices[i + j]
                        results[original_idx] = [0.0] * 1536  # 默认向量
        
        return results
    
    def invalidate(self, text: str):
        """使缓存失效
        
        Args:
            text: 文本内容
        """
        key = self._compute_key(text)
        self.cache.delete(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        return {
            "cache_stats": self.cache.get_stats(),
            "batch_size": self.batch_size
        }


class AsyncBatchEmbedding:
    """异步批量embedding处理器"""
    
    def __init__(
        self,
        embedding_fn: Callable[[List[str]], List[List[float]]],
        batch_size: int = 100,
        max_workers: int = 4
    ):
        """初始化异步批量embedding
        
        Args:
            embedding_fn: embedding生成函数
            batch_size: 批处理大小
            max_workers: 最大工作线程数
        """
        self.embedding_fn = embedding_fn
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cache = BatchEmbeddingCache(batch_size=batch_size)
        
        # 预热缓存
        self._warmup_cache: Optional[List[str]] = None
        self._warmup_thread: Optional[threading.Thread] = None
    
    def embed(self, text: str) -> List[float]:
        """单个文本embedding
        
        Args:
            text: 文本内容
            
        Returns:
            embedding向量
        """
        results = self.embed_batch([text])
        return results[0] if results else [0.0] * 1536
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量embedding
        
        Args:
            texts: 文本列表
            
        Returns:
            embedding向量列表
        """
        return self.cache.get_batch(texts, self.embedding_fn)
    
    def embed_async(self, text: str):
        """异步单个文本embedding
        
        Args:
            text: 文本内容
            
        Returns:
            Future对象
        """
        def _embed():
            return self.embed(text)
        
        return self.executor.submit(_embed)
    
    def prefetch(self, texts: List[str]):
        """预加载文本到缓存
        
        Args:
            texts: 文本列表
        """
        if self._warmup_cache is None:
            self._warmup_cache = texts
            self._warmup_thread = threading.Thread(
                target=self._do_prefetch,
                daemon=True
            )
            self._warmup_thread.start()
    
    def _do_prefetch(self):
        """执行预加载"""
        if self._warmup_cache:
            self.embed_batch(self._warmup_cache)
    
    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.shutdown()
        return False


def create_async_embedding(
    embedding_fn: Callable[[List[str]], List[List[float]]],
    batch_size: int = 100
) -> AsyncBatchEmbedding:
    """工厂函数：创建异步embedding处理器
    
    Args:
        embedding_fn: embedding生成函数
        batch_size: 批处理大小
        
    Returns:
        AsyncBatchEmbedding实例
    """
    return AsyncBatchEmbedding(
        embedding_fn=embedding_fn,
        batch_size=batch_size
    )

