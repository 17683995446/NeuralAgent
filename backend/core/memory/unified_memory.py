"""
Memory System - 完整的记忆系统实现

包含优雅降级机制：
- 如果 Redis 可用，使用 Redis
- 否则使用内存存储
"""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ==================== 基类和接口 ====================
class MemoryBackend(ABC):
    """记忆系统的抽象基类"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass


class InMemoryBackend(MemoryBackend):
    """内存存储后端（不依赖 Redis）- 优化版"""
    
    def __init__(self, max_size: int = 100000, auto_cleanup_interval: int = 100):
        self._storage: Dict[str, Any] = {}
        self._ttls: Dict[str, datetime] = {}
        self._max_size = max_size
        self._auto_cleanup_interval = auto_cleanup_interval
        self._operation_count = 0
        logger.info(f"InMemoryBackend 初始化完成 (max_size={max_size})")
    
    def _cleanup_ttl(self, force: bool = False):
        """清理过期条目 - 优化：避免频繁清理"""
        self._operation_count += 1
        
        if not force and self._operation_count % self._auto_cleanup_interval != 0:
            return
        
        now = datetime.now()
        expired = [k for k, v in list(self._ttls.items()) if v < now]
        for k in expired:
            if k in self._storage:
                del self._storage[k]
            if k in self._ttls:
                del self._ttls[k]
    
    def _enforce_size_limit(self):
        """强制大小限制 - 移除最老的条目"""
        if len(self._storage) >= self._max_size:
            excess = len(self._storage) - self._max_size // 2
            keys_to_remove = list(self._storage.keys())[:excess]
            for k in keys_to_remove:
                if k in self._storage:
                    del self._storage[k]
                if k in self._ttls:
                    del self._ttls[k]
            logger.warning(f"Storage limit reached, removed {excess} oldest entries")
    
    async def get(self, key: str) -> Optional[Any]:
        self._cleanup_ttl()
        return self._storage.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self._enforce_size_limit()
        self._storage[key] = value
        if ttl:
            self._ttls[key] = datetime.now() + timedelta(seconds=ttl)
    
    async def delete(self, key: str):
        if key in self._storage:
            del self._storage[key]
        if key in self._ttls:
            del self._ttls[key]
    
    async def exists(self, key: str) -> bool:
        self._cleanup_ttl()
        return key in self._storage
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "size": len(self._storage),
            "max_size": self._max_size,
            "ttl_count": len(self._ttls),
            "utilization": len(self._storage) / self._max_size if self._max_size > 0 else 0
        }
    
    def clear(self):
        """清空所有存储"""
        self._storage.clear()
        self._ttls.clear()
        self._operation_count = 0
        logger.info("Storage cleared")


class RedisBackend(MemoryBackend):
    """Redis 存储后端"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            logger.info("RedisBackend 初始化完成")
        except ImportError:
            raise
        except Exception as e:
            logger.warning(f"Redis 连接失败: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        data = await self._redis.get(key)
        if data:
            try:
                return json.loads(data)
            except Exception:
                return data
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        if ttl:
            await self._redis.setex(key, ttl, value)
        else:
            await self._redis.set(key, value)
    
    async def delete(self, key: str):
        await self._redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        result = await self._redis.exists(key)
        return bool(result)


# ==================== 工厂函数 ====================
def create_memory_backend(prefer_redis: bool = True) -> MemoryBackend:
    """创建记忆系统后端（优先使用 Redis，否则使用内存）"""
    
    if prefer_redis:
        try:
            return RedisBackend()
        except Exception as e:
            logger.info(f"Redis 不可用，降级到内存存储: {e}")
            return InMemoryBackend()
    
    return InMemoryBackend()


def create_memory_backend_safe() -> MemoryBackend:
    """安全的创建记忆系统后端（总是成功）"""
    try:
        return create_memory_backend(prefer_redis=True)
    except Exception as e:
        logger.warning(f"创建 Redis 后端失败，使用纯内存: {e}")
        return InMemoryBackend()


# ==================== 高级记忆系统 ====================
@dataclass
class MemoryEntry:
    """记忆条目"""
    key: str
    value: Any
    created_at: datetime = None
    updated_at: datetime = None
    ttl: Optional[int] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()


class UnifiedMemorySystem:
    """统一的记忆系统 - 支持多种后端"""
    
    def __init__(self, backend: MemoryBackend = None):
        self.backend = backend or create_memory_backend()
        logger.info(f"UnifiedMemorySystem 初始化完成，后端: {type(self.backend).__name__}")
    
    async def store(self, key: str, value: Any, ttl: Optional[int] = None):
        """存储记忆"""
        if not key:
            raise ValueError("键不能为空")
        
        entry = MemoryEntry(
            key=key,
            value=value,
            ttl=ttl
        )
        await self.backend.set(key, entry, ttl)
        logger.debug(f"已存储记忆: {key}")
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆（直接返回值）"""
        if not key:
            return None
        
        entry = await self.backend.get(key)
        if entry and isinstance(entry, MemoryEntry):
            return entry.value
        return entry
    
    async def remove(self, key: str):
        """移除记忆"""
        if key:
            await self.backend.delete(key)
            logger.debug(f"已移除记忆: {key}")
    
    async def has(self, key: str) -> bool:
        """检查记忆是否存在"""
        if not key:
            return False
        return await self.backend.exists(key)


# ==================== 快捷访问 ====================
_global_memory = None


def get_memory_system() -> UnifiedMemorySystem:
    """获取全局记忆系统实例 - 安全版本"""
    global _global_memory
    if not _global_memory:
        try:
            _global_memory = UnifiedMemorySystem(create_memory_backend_safe())
        except Exception as e:
            logger.warning(f"记忆系统初始化问题: {e}")
            _global_memory = UnifiedMemorySystem(InMemoryBackend())
    return _global_memory
