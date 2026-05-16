"""
Multi-Level Cache System - 多级缓存系统

支持：
1. L1: 本地内存缓存（快速访问）
2. L2: Redis缓存（分布式共享）
3. 智能缓存策略
4. 缓存预热机制

安全特性：
- 输入验证：空键检查、空值检查、键长度限制
- 线程安全：使用线程锁保护共享状态
- 边界检查：防止资源耗尽攻击
"""

import asyncio
import logging
import threading
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""
    L1 = "l1"  # 本地内存
    L2 = "l2"  # Redis
    BOTH = "both"


class CacheValidationError(Exception):
    """缓存验证错误"""
    pass


class CacheEmptyKeyError(CacheValidationError):
    """空键错误"""
    pass


class CacheNullValueError(CacheValidationError):
    """空值错误"""
    pass


class CacheKeyTooLongError(CacheValidationError):
    """键太长错误"""
    pass


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: datetime = None
    accessed_at: datetime = None
    access_count: int = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.accessed_at:
            self.accessed_at = datetime.now()


class L1Cache:
    """L1 本地内存缓存 - 线程安全版本"""
    
    MAX_KEY_LENGTH = 1024
    MAX_VALUE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        self._lock = threading.RLock()
        logger.info(f"L1Cache initialized (max_size={max_size})")
    
    def _validate_key(self, key: str) -> None:
        """验证缓存键"""
        if not key:
            raise CacheEmptyKeyError("Cache key cannot be empty")
        if len(key) > self.MAX_KEY_LENGTH:
            raise CacheKeyTooLongError(f"Cache key too long (max {self.MAX_KEY_LENGTH} chars)")
        if "\x00" in key:
            raise CacheValidationError("Cache key contains null bytes")
    
    def _validate_value(self, value: Any) -> None:
        """验证缓存值"""
        if value is None:
            raise CacheNullValueError("Cache value cannot be None")
        if isinstance(value, str) and len(value) > self.MAX_VALUE_SIZE:
            raise CacheValidationError(f"Cache value too large (max {self.MAX_VALUE_SIZE} bytes)")
    
    def _cleanup_expired(self):
        """清理过期条目"""
        now = datetime.now()
        keys_to_remove = []
        
        with self._lock:
            for key, entry in self.cache.items():
                if entry.ttl:
                    if now > entry.created_at + timedelta(seconds=entry.ttl):
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        self._validate_key(key)
        self._cleanup_expired()
        
        with self._lock:
            entry = self.cache.get(key)
            if entry:
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                self.hits += 1
                
                self.cache.move_to_end(key)
                return entry.value
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        self._validate_key(key)
        self._validate_value(value)
        
        with self._lock:
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[key] = CacheEntry(
                key=key,
                value=value,
                ttl=ttl if ttl else self.default_ttl
            )
    
    def delete(self, key: str):
        """删除缓存"""
        if not key:
            return
        
        with self._lock:
            if key in self.cache:
                del self.cache[key]
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        self._cleanup_expired()
        
        with self._lock:
            return key in self.cache
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            hit_rate = self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "size": len(self.cache),
                "max_size": self.max_size
            }


class L2Cache:
    """L2 Redis 缓存"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis = None
        self._connect()
    
    def _connect(self):
        """连接 Redis"""
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
            logger.info("L2Cache (Redis) initialized")
        except ImportError:
            logger.warning("redis library not installed")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._redis:
            return None
        
        try:
            data = await self._redis.get(key)
            if data:
                try:
                    import json
                    return json.loads(data)
                except:
                    return data
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        if not self._redis:
            return
        
        try:
            if isinstance(value, (dict, list)):
                import json
                value = json.dumps(value, ensure_ascii=False)
            
            if ttl:
                await self._redis.setex(key, ttl, value)
            else:
                await self._redis.set(key, value)
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
    
    async def delete(self, key: str):
        """删除缓存"""
        if not self._redis:
            return
        
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self._redis:
            return False
        
        try:
            result = await self._redis.exists(key)
            return bool(result)
        except Exception as e:
            logger.warning(f"Redis exists failed: {e}")
            return False


class MultiLevelCache:
    """多级缓存系统"""
    
    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_default_ttl: int = 3600,
        l2_redis_url: str = "redis://localhost:6379/0",
        enable_l2: bool = True
    ):
        self.l1 = L1Cache(max_size=l1_max_size, default_ttl=l1_default_ttl)
        self.l2 = L2Cache(redis_url=l2_redis_url) if enable_l2 else None
        self._cache_warming = False
        logger.info("MultiLevelCache initialized")
    
    async def get(self, key: str, level: CacheLevel = CacheLevel.BOTH) -> Optional[Any]:
        """获取缓存"""
        # 先查 L1
        if level in (CacheLevel.L1, CacheLevel.BOTH):
            value = self.l1.get(key)
            if value is not None:
                logger.debug(f"L1 cache hit: {key}")
                return value
        
        # 再查 L2
        if self.l2 and level in (CacheLevel.L2, CacheLevel.BOTH):
            value = await self.l2.get(key)
            if value is not None:
                logger.debug(f"L2 cache hit: {key}")
                # 写入 L1
                self.l1.set(key, value)
                return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, level: CacheLevel = CacheLevel.BOTH):
        """设置缓存"""
        if level in (CacheLevel.L1, CacheLevel.BOTH):
            self.l1.set(key, value, ttl)
        
        if self.l2 and level in (CacheLevel.L2, CacheLevel.BOTH):
            await self.l2.set(key, value, ttl)
    
    async def delete(self, key: str, level: CacheLevel = CacheLevel.BOTH):
        """删除缓存"""
        if level in (CacheLevel.L1, CacheLevel.BOTH):
            self.l1.delete(key)
        
        if self.l2 and level in (CacheLevel.L2, CacheLevel.BOTH):
            await self.l2.delete(key)
    
    async def exists(self, key: str, level: CacheLevel = CacheLevel.BOTH) -> bool:
        """检查缓存是否存在"""
        if level in (CacheLevel.L1, CacheLevel.BOTH):
            if self.l1.exists(key):
                return True
        
        if self.l2 and level in (CacheLevel.L2, CacheLevel.BOTH):
            return await self.l2.exists(key)
        
        return False
    
    def get_l1_stats(self) -> Dict[str, Any]:
        """获取 L1 统计"""
        return self.l1.get_stats()
    
    async def warmup(self, warmup_data: Dict[str, Any]):
        """缓存预热"""
        self._cache_warming = True
        logger.info(f"Starting cache warmup with {len(warmup_data)} items")
        
        for key, value in warmup_data.items():
            await self.set(key, value, level=CacheLevel.BOTH)
        
        self._cache_warming = False
        logger.info("Cache warmup completed")


class CacheManager:
    """缓存管理器"""
    
    _instance = None
    
    def __init__(self):
        self.caches: Dict[str, MultiLevelCache] = {}
    
    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """获取单例"""
        if cls._instance is None:
            cls._instance = CacheManager()
        return cls._instance
    
    def get_cache(self, name: str = "default") -> MultiLevelCache:
        """获取缓存实例"""
        if name not in self.caches:
            self.caches[name] = MultiLevelCache()
        
        return self.caches[name]
    
    def create_cache(
        self,
        name: str,
        l1_max_size: int = 1000,
        l1_default_ttl: int = 3600,
        enable_l2: bool = True
    ) -> MultiLevelCache:
        """创建自定义缓存"""
        self.caches[name] = MultiLevelCache(
            l1_max_size=l1_max_size,
            l1_default_ttl=l1_default_ttl,
            enable_l2=enable_l2
        )
        return self.caches[name]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有缓存统计"""
        stats = {}
        for name, cache in self.caches.items():
            stats[name] = cache.get_l1_stats()
        return stats


# 全局缓存实例
cache_manager = CacheManager.get_instance()


def get_cache(name: str = "default") -> MultiLevelCache:
    """获取缓存的便捷函数"""
    return cache_manager.get_cache(name)


async def example_usage():
    """示例用法"""
    cache = get_cache()
    
    # 设置缓存
    await cache.set("user:123", {"name": "张三", "age": 30})
    
    # 获取缓存
    user = await cache.get("user:123")
    print(f"User: {user}")
    
    # 检查存在
    exists = await cache.exists("user:123")
    print(f"Exists: {exists}")
    
    # 获取统计
    stats = cache.get_l1_stats()
    print(f"Stats: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())
