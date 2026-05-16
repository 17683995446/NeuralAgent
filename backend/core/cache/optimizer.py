"""
NeuralAgent Cache Optimizer
多层缓存优化系统
"""

import time
import hashlib
import json
from typing import Any, Optional, Callable, Dict
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import asyncio


class CacheLevel(str, Enum):
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DATABASE = "l3_database"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    level: CacheLevel
    hits: int = 0


class L1MemoryCache:
    """L1 内存缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        if entry.expires_at and time.time() > entry.expires_at:
            del self.cache[key]
            self.misses += 1
            return None

        entry.hits += 1
        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        ttl = ttl or self.ttl
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            expires_at=time.time() + ttl if ttl else None,
            level=CacheLevel.L1_MEMORY
        )

        self.cache[key] = entry

    def _evict_lru(self) -> None:
        """LRU 驱逐策略"""
        if not self.cache:
            return

        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].created_at
        )
        del self.cache[lru_key]

    def delete(self, key: str) -> None:
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "ttl": self.ttl
        }


class CacheOptimizer:
    """多层缓存优化器"""

    def __init__(self, redis_url: Optional[str] = None):
        self.l1_cache = L1MemoryCache(max_size=1000, ttl=300)
        self.redis_url = redis_url
        self.redis_client = None

        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
            except Exception:
                pass

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]

        for arg in args:
            key_parts.append(str(arg))

        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get_or_set(
        self,
        key: str,
        func: Callable,
        ttl: int = 300,
        use_redis: bool = True
    ) -> Any:
        """获取或设置缓存"""
        cached = self.l1_cache.get(key)
        if cached is not None:
            return cached

        if self.redis_client and use_redis:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    value = json.loads(cached)
                    self.l1_cache.set(key, value, ttl)
                    return value
            except Exception:
                pass

        value = await func() if asyncio.iscoroutinefunction(func) else func()

        self.l1_cache.set(key, value, ttl)

        if self.redis_client and use_redis:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception:
                pass

        return value

    def invalidate(self, key: str) -> None:
        """使缓存失效"""
        self.l1_cache.delete(key)

        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass

    def warm_up(self, queries: list) -> None:
        """缓存预热"""
        for query in queries:
            if callable(query):
                try:
                    result = query()
                    key = self.generate_key("warmup", str(query))
                    self.l1_cache.set(key, result)
                except Exception:
                    pass


def cached(
    prefix: str = "default",
    ttl: int = 300,
    use_redis: bool = True
):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            key_parts = [prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            from backend.core.cache.optimizer import CacheOptimizer
            optimizer = CacheOptimizer()

            cached_value = optimizer.l1_cache.get(key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)

            optimizer.l1_cache.set(key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_parts = [prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            from backend.core.cache.optimizer import CacheOptimizer
            optimizer = CacheOptimizer()

            cached_value = optimizer.l1_cache.get(key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)

            optimizer.l1_cache.set(key, result, ttl)

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
