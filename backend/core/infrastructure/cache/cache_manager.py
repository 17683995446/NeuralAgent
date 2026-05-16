"""Cache Management Module - Product Grade.

Standing on the shoulders of giants: using Redis for distributed caching.
Not reinventing the wheel: using industry-standard patterns.
Highly modular: clear separation of concerns.
Productized: comprehensive caching with TTL, serialization, and error handling.
"""

import json
import logging
import hashlib
from typing import Any, Optional, Callable, TypeVar, Union
from functools import wraps
from datetime import timedelta
import pickle
import importlib

logger = logging.getLogger(__name__)

# Check for redis availability
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache fallback")


T = TypeVar('T')


class CacheManager:
    """Product-grade cache manager with Redis backend and fallback."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 3600,
        max_retries: int = 3,
        key_prefix: str = "neural_agent:cache:"
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_retries = max_retries
        self.key_prefix = key_prefix
        self._redis_client = None
        self._in_memory_cache = {}
        
        if REDIS_AVAILABLE:
            self._init_redis()
    
    def _init_redis(self) -> None:
        """Initialize Redis connection with retry logic."""
        for attempt in range(self.max_retries):
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                self._redis_client.ping()
                logger.info(f"Redis connected: {self.redis_url}")
                break
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logger.error("Redis unavailable, using in-memory cache")
                    self._redis_client = None
    
    def _get_key(self, key: str) -> str:
        """Generate cache key with prefix."""
        return f"{self.key_prefix}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            return pickle.dumps(value)
        except Exception:
            return pickle.dumps(str(value))
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            return pickle.loads(data)
        except Exception:
            return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        cache_key = self._get_key(key)
        
        if self._redis_client:
            try:
                data = self._redis_client.get(cache_key)
                if data:
                    return self._deserialize(data)
                return default
            except Exception as e:
                logger.error(f"Redis GET failed: {e}")
        
        return self._in_memory_cache.get(cache_key, default)
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        cache_key = self._get_key(key)
        ttl = ttl or self.default_ttl
        
        if self._redis_client:
            try:
                serialized = self._serialize(value)
                self._redis_client.setex(cache_key, ttl, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis SET failed: {e}")
        
        self._in_memory_cache[cache_key] = value
        return True
    
    def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        cache_key = self._get_key(key)
        
        if self._redis_client:
            try:
                self._redis_client.delete(cache_key)
                return True
            except Exception as e:
                logger.error(f"Redis DELETE failed: {e}")
        
        if cache_key in self._in_memory_cache:
            del self._in_memory_cache[cache_key]
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists
        """
        cache_key = self._get_key(key)
        
        if self._redis_client:
            try:
                return bool(self._redis_client.exists(cache_key))
            except Exception as e:
                logger.error(f"Redis EXISTS failed: {e}")
        
        return cache_key in self._in_memory_cache
    
    def clear(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if successful
        """
        if self._redis_client:
            try:
                keys = self._redis_client.keys(f"{self.key_prefix}*")
                if keys:
                    self._redis_client.delete(*keys)
                return True
            except Exception as e:
                logger.error(f"Redis CLEAR failed: {e}")
        
        self._in_memory_cache.clear()
        return True
    
    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        result = {}
        
        if self._redis_client:
            try:
                cache_keys = [self._get_key(k) for k in keys]
                values = self._redis_client.mget(cache_keys)
                for key, value in zip(keys, values):
                    if value:
                        result[key] = self._deserialize(value)
            except Exception as e:
                logger.error(f"Redis MGET failed: {e}")
        
        for key in keys:
            if key not in result:
                cache_key = self._get_key(key)
                if cache_key in self._in_memory_cache:
                    result[key] = self._in_memory_cache[cache_key]
        
        return result
    
    def set_many(
        self,
        items: dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache.
        
        Args:
            items: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        ttl = ttl or self.default_ttl
        success = True
        
        if self._redis_client:
            try:
                pipe = self._redis_client.pipeline()
                for key, value in items.items():
                    cache_key = self._get_key(key)
                    pipe.setex(cache_key, ttl, self._serialize(value))
                pipe.execute()
            except Exception as e:
                logger.error(f"Redis MSET failed: {e}")
                success = False
        
        for key, value in items.items():
            cache_key = self._get_key(key)
            self._in_memory_cache[cache_key] = value
        
        return success
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            New value or None if failed
        """
        cache_key = self._get_key(key)
        
        if self._redis_client:
            try:
                return self._redis_client.incrby(cache_key, amount)
            except Exception as e:
                logger.error(f"Redis INCR failed: {e}")
        
        current = self._in_memory_cache.get(cache_key, 0)
        new_value = current + amount
        self._in_memory_cache[cache_key] = new_value
        return new_value
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds or None
        """
        cache_key = self._get_key(key)
        
        if self._redis_client:
            try:
                ttl = self._redis_client.ttl(cache_key)
                return ttl if ttl > 0 else None
            except Exception as e:
                logger.error(f"Redis TTL failed: {e}")
        
        return None
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "backend": "redis" if self._redis_client else "memory",
            "total_keys": 0,
            "memory_usage_bytes": 0
        }
        
        if self._redis_client:
            try:
                info = self._redis_client.info("stats")
                stats.update({
                    "total_keys": self._redis_client.dbsize(),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "memory_used": info.get("used_memory_human", "unknown")
                })
            except Exception as e:
                logger.error(f"Redis INFO failed: {e}")
        
        stats["memory_keys"] = len(self._in_memory_cache)
        return stats


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(
    redis_url: str = None,
    default_ttl: int = 3600
) -> CacheManager:
    """Get or create the global cache manager instance.
    
    Args:
        redis_url: Redis connection URL
        default_ttl: Default TTL in seconds
        
    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        if redis_url is None:
            try:
                from backend.config import settings
                redis_url = settings.redis_url
            except Exception:
                redis_url = "redis://localhost:6379/0"
        
        _cache_manager = CacheManager(
            redis_url=redis_url,
            default_ttl=default_ttl
        )
    return _cache_manager


def cache_result(
    key_prefix: str = "",
    ttl: Optional[int] = None,
    unless: Optional[Callable[..., bool]] = None
):
    """Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        unless: Function that returns True to skip caching
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            if unless and unless(*args, **kwargs):
                return func(*args, **kwargs)
            
            cache = get_cache_manager()
            
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cache miss: {cache_key}")
            
            return result
        
        wrapper.cache_clear = lambda: get_cache_manager().clear()
        return wrapper
    
    return decorator


def invalidate_cache(key_pattern: str) -> int:
    """Invalidate cache entries matching pattern.
    
    Args:
        key_pattern: Pattern to match
        
    Returns:
        Number of keys invalidated
    """
    cache = get_cache_manager()
    
    if cache._redis_client:
        try:
            keys = cache._redis_client.keys(f"{cache.key_prefix}{key_pattern}")
            if keys:
                return cache._redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
    
    return 0
