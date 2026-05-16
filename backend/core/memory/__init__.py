"""Memory Module - 记忆系统模块

包含工作记忆、短期记忆、长期记忆等功能。
支持 Redis 和内存两种后端。
"""

import logging

logger = logging.getLogger(__name__)

# 导入旧模块（保持兼容）- 安全导入，避免强制依赖redis
EnhancedMemorySystem = None
ShortTermMemory = None
LongTermMemory = None

try:
    from .enhanced_memory_system import EnhancedMemorySystem
except Exception as e:
    logger.debug(f"EnhancedMemorySystem not available: {e}")

try:
    from .short_term_memory import ShortTermMemory
except Exception as e:
    logger.debug(f"ShortTermMemory not available (requires redis): {e}")

try:
    from .long_term_memory import LongTermMemory
except Exception as e:
    logger.debug(f"LongTermMemory not available: {e}")

# 导入新的统一模块
from .unified_memory import (
    MemoryBackend,
    InMemoryBackend,
    RedisBackend,
    UnifiedMemorySystem,
    create_memory_backend,
    create_memory_backend_safe,
    get_memory_system
)

__all__ = [
    "EnhancedMemorySystem",
    "ShortTermMemory",
    "LongTermMemory",
    "MemoryBackend",
    "InMemoryBackend",
    "RedisBackend",
    "UnifiedMemorySystem",
    "create_memory_backend",
    "create_memory_backend_safe",
    "get_memory_system",
]

logger.info("Memory module loaded successfully")
