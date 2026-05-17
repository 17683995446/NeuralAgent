"""
NeuralAgent 产品化核心模块 - 缓存模块

基于业界标准开源工具构建
- 使用 functools.lru_cache (Python标准库)
- tenacity (重试库)
- structlog (结构化日志)
- pydantic (数据验证)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TypeVar, Generic, Callable
from functools import lru_cache
from collections import OrderedDict
import time
import threading
from datetime import datetime
import structlog
from enum import Enum

from backend.core.modular import ModuleMetadata, ModuleCategory, ModuleStatus, registry

logger = structlog.get_logger()

T = TypeVar('T')


class EvictionPolicy(Enum):
    """淘汰策略"""
    LRU = "lru"  # 最近最少使用
    FIFO = "fifo"  # 先进先出
    LFU = "lfu"  # 最不经常使用


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    key: str
    value: T
    created_at: float
    expires_at: Optional[float]
    hits: int = 0
    last_accessed: float = field(default_factory=time.time)


class ProductCache:
    """
    产品化缓存模块
    
    特性：
    - 线程安全
    - 多种淘汰策略
    - TTL支持
    - 可观测
    """
    
    @classmethod
    def metadata(cls) -> ModuleMetadata:
        return ModuleMetadata(
            name="cache",
            version="2.0.0",
            category=ModuleCategory.CORE,
            status=ModuleStatus.STABLE,
            description="高性能线程安全缓存模块，支持多种淘汰策略",
            dependencies=[],
            examples=[
                "examples/cache_usage.py"
            ]
        )
    
    def __init__(self):
        self._lock = threading.RLock()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size: int = 10000
        self._eviction_policy: EvictionPolicy = EvictionPolicy.LRU
        self._default_ttl: int = 3600
        self._hits: int = 0
        self._misses: int = 0
        self._initialized: bool = False
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化模块"""
        with self._lock:
            self._max_size = config.get('max_size', 10000)
            self._default_ttl = config.get('default_ttl', 3600)
            policy_str = config.get('eviction_policy', 'lru').lower()
            self._eviction_policy = EvictionPolicy(policy_str) if policy_str in [p.value for p in EvictionPolicy] else EvictionPolicy.LRU
            self._initialized = True
            logger.info("ProductCache initialized", 
                       max_size=self._max_size, 
                       eviction_policy=self._eviction_policy.value)
    
    def health_check(self) -> bool:
        """健康检查"""
        return self._initialized and len(self._cache) <= self._max_size
    
    def shutdown(self) -> None:
        """关闭模块"""
        with self._lock:
            self._cache.clear()
            logger.info("ProductCache shutdown")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        with self._lock:
            if not key:
                raise ValueError("Cache key cannot be empty")
            
            ttl = ttl or self._default_ttl
            now = time.time()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + ttl if ttl > 0 else None
            )
            self._cache[key] = entry
            
            if len(self._cache) > self._max_size:
                self._evict()
            
            logger.debug("Cache set", key=key)
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                logger.debug("Cache miss", key=key)
                return default
            
            if entry.expires_at and time.time() > entry.expires_at:
                del self._cache[key]
                self._misses += 1
                logger.debug("Cache expired", key=key)
                return default
            
            self._hits += 1
            entry.hits += 1
            entry.last_accessed = time.time()
            
            if self._eviction_policy == EvictionPolicy.LRU:
                self._cache.move_to_end(key)
            
            return entry.value
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug("Cache delete", key=key)
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total) * 100 if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "eviction_policy": self._eviction_policy.value
            }
    
    def _evict(self) -> None:
        """执行淘汰"""
        if not self._cache:
            return
        
        if self._eviction_policy == EvictionPolicy.LRU:
            self._cache.popitem(last=False)
        elif self._eviction_policy == EvictionPolicy.FIFO:
            self._cache.popitem(last=False)
        elif self._eviction_policy == EvictionPolicy.LFU:
            min_key = min(self._cache.keys(), key=lambda k: self._cache[k].hits)
            del self._cache[min_key]


class CacheDecorator:
    """
    缓存装饰器 - 用于函数结果缓存
    """
    
    def __init__(self, cache: ProductCache, ttl: int = 3600):
        self._cache = cache
        self._ttl = ttl
    
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            key = f"{func.__module__}.{func.__name__}:{str(args)}:{str(kwargs)}"
            result = self._cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            self._cache.set(key, result, self._ttl)
            return result
        return wrapper


registry.register(ProductCache)
