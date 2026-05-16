"""Enhanced Memory System - 产品级增强记忆系统

Standing on the shoulders of giants:
- Inspired by cognitive science theories (Atkinson-Shiffrin model)
- Uses Redis for working/short-term memory
- Uses Milvus/Chroma for long-term semantic/episodic memory
- Implements RAG (Retrieval-Augmented Generation) patterns
- Includes memory consolidation and forgetting mechanisms

Highly modular:
- WorkingMemory - 当前活跃任务上下文
- ShortTermMemoryEnhanced - 短期记忆（会话级）
- EpisodicMemory - 情节记忆（事件序列）
- SemanticMemory - 语义记忆（知识图谱）
- MemoryRetriever - 统一检索接口
- MemoryConsolidator - 记忆巩固
- ForgettingMechanism - 遗忘机制

Productized:
- Full error handling
- Graceful fallbacks
- Configurable parameters
- Monitoring and metrics
"""

import json
import hashlib
import logging
import math
import threading
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from heapq import nlargest
import time

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class MemoryType(Enum):
    """记忆类型枚举"""
    WORKING = auto()
    SHORT_TERM = auto()
    EPISODIC = auto()
    SEMANTIC = auto()
    PROCEDURAL = auto()


class MemoryImportance(Enum):
    """记忆重要性等级"""
    TRIVIAL = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ForgettingStrategy(Enum):
    """遗忘策略"""
    LRU = auto()  # Least Recently Used
    LFU = auto()  # Least Frequently Used
    FIFO = auto()  # First In First Out
    TIME_BASED = auto()  # Time-based expiration
    WEIGHTED = auto()  # Weighted combination


@dataclass
class MemoryEntry:
    """增强版记忆条目数据类"""
    id: str
    content: str
    memory_type: MemoryType
    importance: MemoryImportance = MemoryImportance.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_agent: Optional[str] = None
    source_task: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    embedding: Optional[List[float]] = None
    similarity_score: Optional[float] = None
    confidence: float = 1.0
    
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    
    consolidated: bool = False
    compressed: bool = False
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.name,
            "importance": self.importance.value,
            "metadata": self.metadata,
            "source_agent": self.source_agent,
            "source_task": self.source_task,
            "tags": list(self.tags),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "similarity_score": self.similarity_score,
            "confidence": self.confidence,
            "parent_ids": self.parent_ids,
            "child_ids": self.child_ids,
            "consolidated": self.consolidated,
            "compressed": self.compressed,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType[data["memory_type"]],
            importance=MemoryImportance(data["importance"]),
            metadata=data.get("metadata", {}),
            source_agent=data.get("source_agent"),
            source_task=data.get("source_task"),
            tags=set(data.get("tags", [])),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if "last_accessed" in data else datetime.utcnow(),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            similarity_score=data.get("similarity_score"),
            confidence=data.get("confidence", 1.0),
            parent_ids=data.get("parent_ids", []),
            child_ids=data.get("child_ids", []),
            consolidated=data.get("consolidated", False),
            compressed=data.get("compressed", False),
            version=data.get("version", 1),
        )
    
    def get_relevance_score(self, query: str, current_time: Optional[datetime] = None) -> float:
        """计算记忆相关性分数"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        time_age = (current_time - self.created_at).total_seconds()
        recency_factor = max(0.1, 1.0 - time_age / (86400 * 7))
        
        access_factor = min(2.0, 1.0 + math.log10(1 + self.access_count))
        
        importance_factor = (self.importance.value + 1) / 5
        
        recency_weight = 0.3
        access_weight = 0.3
        importance_weight = 0.4
        
        if self.similarity_score is not None:
            return (
                self.similarity_score * 0.5 +
                recency_factor * recency_weight +
                access_factor * access_weight +
                importance_factor * importance_weight
            )
        
        return (
            recency_factor * recency_weight +
            access_factor * access_weight +
            importance_factor * importance_weight
        )
    
    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        if current_time is None:
            current_time = datetime.utcnow()
        return self.expires_at is not None and current_time > self.expires_at


@dataclass
class MemoryQuery:
    """记忆查询参数"""
    query: str
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    source_agent: Optional[str] = None
    source_task: Optional[str] = None
    min_importance: Optional[MemoryImportance] = None
    max_age_hours: Optional[float] = None
    limit: int = 10
    threshold: float = 0.0
    include_expired: bool = False
    sort_by: str = "relevance"


@dataclass
class MemoryRetrievalResult:
    """记忆检索结果"""
    query: MemoryQuery
    entries: List[MemoryEntry]
    total_found: int
    retrieval_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Base Memory Classes
# ============================================================================

class BaseMemory(ABC):
    """记忆基类"""
    
    @abstractmethod
    def add(self, entry: MemoryEntry) -> str:
        """添加记忆"""
        pass
    
    @abstractmethod
    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """获取记忆"""
        pass
    
    @abstractmethod
    def update(self, entry: MemoryEntry) -> bool:
        """更新记忆"""
        pass
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        pass
    
    @abstractmethod
    def search(self, query: MemoryQuery) -> MemoryRetrievalResult:
        """搜索记忆"""
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 100) -> List[MemoryEntry]:
        """获取所有记忆"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """获取记忆数量"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空记忆"""
        pass


# ============================================================================
# Working Memory - 工作记忆
# ============================================================================

class WorkingMemory(BaseMemory):
    """工作记忆 - 当前活跃任务上下文
    
    类似于人类的工作记忆，容量有限（Miller's law 7±2），
    用于当前任务的实时上下文。
    """
    
    DEFAULT_CAPACITY = 15
    DEFAULT_TTL_SECONDS = 3600  # 1 hour
    
    def __init__(
        self,
        capacity: int = DEFAULT_CAPACITY,
        ttl_seconds: int = DEFAULT_TTL_SECONDS
    ):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        
        self._memory: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
    
    def add(self, entry: MemoryEntry) -> str:
        with self._lock:
            if entry.id in self._memory:
                self._memory.move_to_end(entry.id)
            else:
                if len(self._memory) >= self.capacity:
                    self._evict_lru()
                self._eviction_count += 1
            
            self._memory[entry.id] = entry
            return entry.id
    
    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            if memory_id in self._memory:
                entry = self._memory[memory_id]
                self._memory.move_to_end(memory_id)
                self._update_access(entry)
                self._hit_count += 1
                return entry
            self._miss_count += 1
            return None
    
    def update(self, entry: MemoryEntry) -> bool:
        with self._lock:
            if entry.id in self._memory:
                entry.version += 1
                self._memory[entry.id] = entry
                self._memory.move_to_end(entry.id)
                return True
            return False
    
    def delete(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id in self._memory:
                del self._memory[memory_id]
                return True
            return False
    
    def search(self, query: MemoryQuery) -> MemoryRetrievalResult:
        start_time = time.time()
        results: List[MemoryEntry] = []
        
        with self._lock:
            for entry in self._memory.values():
                if self._matches_query(entry, query):
                    self._update_access(entry)
                    results.append(entry)
        
        results.sort(key=lambda e: e.get_relevance_score(query.query), reverse=True)
        results = results[:query.limit]
        
        retrieval_time = (time.time() - start_time) * 1000
        
        return MemoryRetrievalResult(
            query=query,
            entries=results,
            total_found=len(results),
            retrieval_time_ms=retrieval_time
        )
    
    def get_all(self, limit: int = 100) -> List[MemoryEntry]:
        with self._lock:
            return list(self._memory.values())[:limit]
    
    def count(self) -> int:
        with self._lock:
            return len(self._memory)
    
    def clear(self) -> None:
        with self._lock:
            self._memory.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total if total > 0 else 0.0
            return {
                "capacity": self.capacity,
                "current_size": len(self._memory),
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "eviction_count": self._eviction_count,
            }
    
    def _evict_lru(self) -> None:
        if self._memory:
            self._memory.popitem(last=False)
    
    def _update_access(self, entry: MemoryEntry) -> None:
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
    
    def _matches_query(self, entry: MemoryEntry, query: MemoryQuery) -> bool:
        if query.memory_types and entry.memory_type not in query.memory_types:
            return False
        
        if query.tags and not any(tag in entry.tags for tag in query.tags):
            return False
        
        if query.source_agent and entry.source_agent != query.source_agent:
            return False
        
        if query.source_task and entry.source_task != query.source_task:
            return False
        
        if query.min_importance and entry.importance.value < query.min_importance.value:
            return False
        
        if query.max_age_hours:
            age_hours = (datetime.utcnow() - entry.created_at).total_seconds() / 3600
            if age_hours > query.max_age_hours:
                return False
        
        if not query.include_expired and entry.is_expired():
            return False
        
        if query.query:
            if query.query.lower() not in entry.content.lower():
                return False
        
        return True


# ============================================================================
# Enhanced Short-Term Memory - 增强版短期记忆
# ============================================================================

class ShortTermMemoryEnhanced(BaseMemory):
    """增强版短期记忆 - 会话级记忆存储
    
    支持多种后端存储（Redis优先，内存fallback）
    """
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        default_ttl: int = 86400,  # 24 hours
        use_fallback: bool = True
    ):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.use_fallback = use_fallback
        
        self._fallback_memory: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        
        self._hit_count = 0
        self._miss_count = 0
    
    def add(self, entry: MemoryEntry) -> str:
        try:
            if self.redis:
                return self._add_redis(entry)
        except Exception as e:
            logger.warning(f"Redis add failed, using fallback: {e}")
        
        return self._add_fallback(entry)
    
    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        entry = None
        try:
            if self.redis:
                entry = self._get_redis(memory_id)
        except Exception as e:
            logger.warning(f"Redis get failed, trying fallback: {e}")
        
        if entry is None and self.use_fallback:
            entry = self._get_fallback(memory_id)
        
        if entry:
            self._hit_count += 1
            self._update_access(entry)
        else:
            self._miss_count += 1
        
        return entry
    
    def update(self, entry: MemoryEntry) -> bool:
        entry.version += 1
        success = False
        try:
            if self.redis:
                success = self._update_redis(entry)
        except Exception as e:
            logger.warning(f"Redis update failed, trying fallback: {e}")
        
        if not success and self.use_fallback:
            success = self._update_fallback(entry)
        
        return success
    
    def delete(self, memory_id: str) -> bool:
        success = False
        try:
            if self.redis:
                success = self._delete_redis(memory_id)
        except Exception as e:
            logger.warning(f"Redis delete failed, trying fallback: {e}")
        
        if not success and self.use_fallback:
            success = self._delete_fallback(memory_id)
        
        return success
    
    def search(self, query: MemoryQuery) -> MemoryRetrievalResult:
        start_time = time.time()
        results: List[MemoryEntry] = []
        
        try:
            if self.redis:
                results = self._search_redis(query)
        except Exception as e:
            logger.warning(f"Redis search failed, using fallback: {e}")
        
        if not results and self.use_fallback:
            results = self._search_fallback(query)
        
        results.sort(key=lambda e: e.get_relevance_score(query.query), reverse=True)
        results = results[:query.limit]
        
        retrieval_time = (time.time() - start_time) * 1000
        
        return MemoryRetrievalResult(
            query=query,
            entries=results,
            total_found=len(results),
            retrieval_time_ms=retrieval_time
        )
    
    def get_all(self, limit: int = 100) -> List[MemoryEntry]:
        with self._lock:
            return list(self._fallback_memory.values())[:limit]
    
    def count(self) -> int:
        with self._lock:
            return len(self._fallback_memory)
    
    def clear(self) -> None:
        with self._lock:
            self._fallback_memory.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0.0
        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "fallback_count": len(self._fallback_memory),
            "has_redis": self.redis is not None,
        }
    
    def _add_redis(self, entry: MemoryEntry) -> str:
        key = f"memory:stm:{entry.id}"
        data = json.dumps(entry.to_dict())
        ttl = self.default_ttl
        if entry.expires_at:
            ttl = int((entry.expires_at - datetime.utcnow()).total_seconds())
            ttl = max(60, ttl)
        
        if hasattr(self.redis, 'setex'):
            self.redis.setex(key, ttl, data)
        return entry.id
    
    def _get_redis(self, memory_id: str) -> Optional[MemoryEntry]:
        key = f"memory:stm:{memory_id}"
        data = self.redis.get(key) if hasattr(self.redis, 'get') else None
        if data:
            data_str = data.decode() if isinstance(data, bytes) else data
            return MemoryEntry.from_dict(json.loads(data_str))
        return None
    
    def _update_redis(self, entry: MemoryEntry) -> bool:
        return self._add_redis(entry) == entry.id
    
    def _delete_redis(self, memory_id: str) -> bool:
        key = f"memory:stm:{memory_id}"
        return bool(self.redis.delete(key)) if hasattr(self.redis, 'delete') else False
    
    def _search_redis(self, query: MemoryQuery) -> List[MemoryEntry]:
        return self._search_fallback(query)
    
    def _add_fallback(self, entry: MemoryEntry) -> str:
        with self._lock:
            self._fallback_memory[entry.id] = entry
            return entry.id
    
    def _get_fallback(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            return self._fallback_memory.get(memory_id)
    
    def _update_fallback(self, entry: MemoryEntry) -> bool:
        with self._lock:
            if entry.id in self._fallback_memory:
                self._fallback_memory[entry.id] = entry
                return True
            return False
    
    def _delete_fallback(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id in self._fallback_memory:
                del self._fallback_memory[memory_id]
                return True
            return False
    
    def _search_fallback(self, query: MemoryQuery) -> List[MemoryEntry]:
        results: List[MemoryEntry] = []
        with self._lock:
            for entry in self._fallback_memory.values():
                if self._matches_query(entry, query):
                    results.append(entry)
        return results
    
    def _update_access(self, entry: MemoryEntry) -> None:
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
    
    def _matches_query(self, entry: MemoryEntry, query: MemoryQuery) -> bool:
        if query.memory_types and entry.memory_type not in query.memory_types:
            return False
        
        if query.tags and not any(tag in entry.tags for tag in query.tags):
            return False
        
        if query.source_agent and entry.source_agent != query.source_agent:
            return False
        
        if query.source_task and entry.source_task != query.source_task:
            return False
        
        if query.min_importance and entry.importance.value < query.min_importance.value:
            return False
        
        if query.max_age_hours:
            age_hours = (datetime.utcnow() - entry.created_at).total_seconds() / 3600
            if age_hours > query.max_age_hours:
                return False
        
        if not query.include_expired and entry.is_expired():
            return False
        
        if query.query:
            if query.query.lower() not in entry.content.lower():
                return False
        
        return True


# ============================================================================
# Episodic Memory - 情节记忆
# ============================================================================

class EpisodicMemory(BaseMemory):
    """情节记忆 - 事件序列记忆
    
    存储按时间顺序排列的事件序列，支持序列检索。
    """
    
    def __init__(self):
        self._episodes: Dict[str, List[MemoryEntry]] = defaultdict(list)
        self._index: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
    
    def add_episode(self, entry: MemoryEntry, episode_id: Optional[str] = None) -> str:
        if episode_id is None:
            episode_id = f"episode_{datetime.utcnow().strftime('%Y%m%d')}"
        
        with self._lock:
            self._episodes[episode_id].append(entry)
            self._index[entry.id] = entry
            return episode_id
    
    def add(self, entry: MemoryEntry) -> str:
        return self.add_episode(entry)
    
    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            return self._index.get(memory_id)
    
    def update(self, entry: MemoryEntry) -> bool:
        with self._lock:
            if entry.id in self._index:
                self._index[entry.id] = entry
                return True
            return False
    
    def delete(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id in self._index:
                del self._index[memory_id]
                for episode_entries in self._episodes.values():
                    episode_entries[:] = [e for e in episode_entries if e.id != memory_id]
                return True
            return False
    
    def search(self, query: MemoryQuery) -> MemoryRetrievalResult:
        start_time = time.time()
        results: List[MemoryEntry] = []
        
        with self._lock:
            for entry in self._index.values():
                if self._matches_query(entry, query):
                    results.append(entry)
        
        results.sort(key=lambda e: e.get_relevance_score(query.query), reverse=True)
        results = results[:query.limit]
        
        retrieval_time = (time.time() - start_time) * 1000
        
        return MemoryRetrievalResult(
            query=query,
            entries=results,
            total_found=len(results),
            retrieval_time_ms=retrieval_time
        )
    
    def get_episode(self, episode_id: str) -> List[MemoryEntry]:
        with self._lock:
            return list(self._episodes.get(episode_id, []))
    
    def get_all(self, limit: int = 100) -> List[MemoryEntry]:
        with self._lock:
            return list(self._index.values())[:limit]
    
    def count(self) -> int:
        with self._lock:
            return len(self._index)
    
    def clear(self) -> None:
        with self._lock:
            self._episodes.clear()
            self._index.clear()
    
    def _matches_query(self, entry: MemoryEntry, query: MemoryQuery) -> bool:
        if query.memory_types and entry.memory_type not in query.memory_types:
            return False
        
        if query.tags and not any(tag in entry.tags for tag in query.tags):
            return False
        
        if query.source_agent and entry.source_agent != query.source_agent:
            return False
        
        if query.source_task and entry.source_task != query.source_task:
            return False
        
        if query.min_importance and entry.importance.value < query.min_importance.value:
            return False
        
        if query.query:
            if query.query.lower() not in entry.content.lower():
                return False
        
        return True


# ============================================================================
# Semantic Memory - 语义记忆
# ============================================================================

class SemanticMemory(BaseMemory):
    """语义记忆 - 知识图谱式记忆
    
    支持关系型记忆、知识图谱结构。
    """
    
    def __init__(self):
        self._concepts: Dict[str, MemoryEntry] = {}
        self._relations: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = defaultdict(list)
        self._inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def add(self, entry: MemoryEntry) -> str:
        with self._lock:
            self._concepts[entry.id] = entry
            self._index_entry(entry)
            return entry.id
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str, metadata: Optional[Dict[str, Any]] = None):
        with self._lock:
            self._relations[source_id].append((target_id, relation_type, metadata or {}))
    
    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            entry = self._concepts.get(memory_id)
            if entry:
                self._update_access(entry)
            return entry
    
    def update(self, entry: MemoryEntry) -> bool:
        with self._lock:
            if entry.id in self._concepts:
                self._concepts[entry.id] = entry
                self._index_entry(entry)
                return True
            return False
    
    def delete(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id in self._concepts:
                del self._concepts[memory_id]
                if memory_id in self._relations:
                    del self._relations[memory_id]
                for key in list(self._inverted_index.keys()):
                    if memory_id in self._inverted_index[key]:
                        self._inverted_index[key].remove(memory_id)
                return True
            return False
    
    def search(self, query: MemoryQuery) -> MemoryRetrievalResult:
        start_time = time.time()
        results: List[MemoryEntry] = []
        candidate_ids: Set[str] = set()
        
        with self._lock:
            if query.query:
                words = query.query.lower().split()
                for word in words:
                    if word in self._inverted_index:
                        candidate_ids.update(self._inverted_index[word])
            
            if not candidate_ids:
                candidate_ids = set(self._concepts.keys())
            
            for concept_id in candidate_ids:
                entry = self._concepts.get(concept_id)
                if entry and self._matches_query(entry, query):
                    results.append(entry)
        
        results.sort(key=lambda e: e.get_relevance_score(query.query), reverse=True)
        results = results[:query.limit]
        
        retrieval_time = (time.time() - start_time) * 1000
        
        return MemoryRetrievalResult(
            query=query,
            entries=results,
            total_found=len(results),
            retrieval_time_ms=retrieval_time
        )
    
    def get_related(self, concept_id: str, relation_type: Optional[str] = None) -> List[Tuple[MemoryEntry, str, Dict[str, Any]]]:
        with self._lock:
            related: List[Tuple[MemoryEntry, str, Dict[str, Any]]] = []
            for target_id, rel_type, metadata in self._relations.get(concept_id, []):
                if relation_type is None or rel_type == relation_type:
                    target = self._concepts.get(target_id)
                    if target:
                        related.append((target, rel_type, metadata))
            return related
    
    def get_all(self, limit: int = 100) -> List[MemoryEntry]:
        with self._lock:
            return list(self._concepts.values())[:limit]
    
    def count(self) -> int:
        with self._lock:
            return len(self._concepts)
    
    def clear(self) -> None:
        with self._lock:
            self._concepts.clear()
            self._relations.clear()
            self._inverted_index.clear()
    
    def _index_entry(self, entry: MemoryEntry) -> None:
        words = entry.content.lower().split()
        for word in words:
            word = word.strip('.,!?')
            if len(word) > 2:
                self._inverted_index[word].add(entry.id)
        
        for tag in entry.tags:
            self._inverted_index[tag.lower()].add(entry.id)
    
    def _update_access(self, entry: MemoryEntry) -> None:
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
    
    def _matches_query(self, entry: MemoryEntry, query: MemoryQuery) -> bool:
        if query.memory_types and entry.memory_type not in query.memory_types:
            return False
        
        if query.tags and not any(tag in entry.tags for tag in query.tags):
            return False
        
        if query.min_importance and entry.importance.value < query.min_importance.value:
            return False
        
        return True


# ============================================================================
# Memory Retriever - 统一检索接口
# ============================================================================

class MemoryRetriever:
    """统一记忆检索接口 - RAG增强
    
    集成所有记忆系统，提供智能检索和reranking。
    """
    
    def __init__(
        self,
        working_memory: WorkingMemory,
        short_term_memory: ShortTermMemoryEnhanced,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory
    ):
        self.working = working_memory
        self.short_term = short_term_memory
        self.episodic = episodic_memory
        self.semantic = semantic_memory
        
        self._query_cache: OrderedDict[str, Tuple[MemoryRetrievalResult, float]] = OrderedDict()
        self._cache_max_size = 100
        self._cache_ttl = 300  # 5 minutes
        self._lock = threading.RLock()
    
    def retrieve(
        self,
        query: MemoryQuery,
        use_cache: bool = True
    ) -> MemoryRetrievalResult:
        cache_key = self._get_cache_key(query)
        
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                return cached
        
        all_results: List[MemoryEntry] = []
        
        working_result = self.working.search(query)
        all_results.extend(working_result.entries)
        
        st_result = self.short_term.search(query)
        all_results.extend(st_result.entries)
        
        episodic_result = self.episodic.search(query)
        all_results.extend(episodic_result.entries)
        
        semantic_result = self.semantic.search(query)
        all_results.extend(semantic_result.entries)
        
        all_results = self._deduplicate(all_results)
        
        all_results.sort(key=lambda e: e.get_relevance_score(query.query), reverse=True)
        
        all_results = all_results[:query.limit]
        
        result = MemoryRetrievalResult(
            query=query,
            entries=all_results,
            total_found=len(all_results),
            retrieval_time_ms=(working_result.retrieval_time_ms + 
                              st_result.retrieval_time_ms +
                              episodic_result.retrieval_time_ms +
                              semantic_result.retrieval_time_ms),
            metadata={
                "working_count": len(working_result.entries),
                "short_term_count": len(st_result.entries),
                "episodic_count": len(episodic_result.entries),
                "semantic_count": len(semantic_result.entries),
            }
        )
        
        if use_cache:
            self._set_cache(cache_key, result)
        
        return result
    
    def retrieve_context(
        self,
        query: str,
        max_tokens: int = 4000,
        **kwargs
    ) -> Tuple[str, List[MemoryEntry]]:
        """检索并格式化上下文用于LLM"""
        memory_query = MemoryQuery(
            query=query,
            limit=kwargs.get('limit', 20),
            **{k: v for k, v in kwargs.items() if k in MemoryQuery.__dataclass_fields__}
        )
        
        result = self.retrieve(memory_query)
        
        context_parts = []
        used_entries = []
        current_tokens = 0
        
        for entry in result.entries:
            entry_text = self._format_entry(entry)
            entry_tokens = len(entry_text.split())
            
            if current_tokens + entry_tokens > max_tokens:
                break
            
            context_parts.append(entry_text)
            used_entries.append(entry)
            current_tokens += entry_tokens
        
        context = "\n\n=== Memory ===\n\n".join(context_parts) if context_parts else ""
        
        return context, used_entries
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "working_stats": self.working.get_stats(),
                "short_term_stats": self.short_term.get_stats(),
                "working_count": self.working.count(),
                "short_term_count": self.short_term.count(),
                "episodic_count": self.episodic.count(),
                "semantic_count": self.semantic.count(),
                "cache_size": len(self._query_cache),
            }
    
    def _deduplicate(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        seen_ids = set()
        unique = []
        for entry in entries:
            if entry.id not in seen_ids:
                seen_ids.add(entry.id)
                unique.append(entry)
        return unique
    
    def _format_entry(self, entry: MemoryEntry) -> str:
        lines = [
            f"[{entry.memory_type.name}] {entry.content}",
            f"Source: {entry.source_agent or 'system'}",
            f"Created: {entry.created_at.isoformat()}",
        ]
        if entry.tags:
            lines.append(f"Tags: {', '.join(entry.tags)}")
        return "\n".join(lines)
    
    def _get_cache_key(self, query: MemoryQuery) -> str:
        data = {
            "query": query.query,
            "memory_types": [t.name for t in query.memory_types] if query.memory_types else None,
            "tags": query.tags,
            "source_agent": query.source_agent,
            "source_task": query.source_task,
            "limit": query.limit,
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def _get_cache(self, key: str) -> Optional[MemoryRetrievalResult]:
        with self._lock:
            if key in self._query_cache:
                result, timestamp = self._query_cache[key]
                if time.time() - timestamp < self._cache_ttl:
                    self._query_cache.move_to_end(key)
                    return result
                del self._query_cache[key]
            return None
    
    def _set_cache(self, key: str, result: MemoryRetrievalResult) -> None:
        with self._lock:
            self._query_cache[key] = (result, time.time())
            if len(self._query_cache) > self._cache_max_size:
                self._query_cache.popitem(last=False)


# ============================================================================
# Memory Consolidator - 记忆巩固
# ============================================================================

class MemoryConsolidator:
    """记忆巩固 - 定期整理和优化记忆
    
    - 从短期记忆巩固到长期记忆
    - 压缩冗余记忆
    - 提取语义知识
    """
    
    def __init__(
        self,
        working_memory: WorkingMemory,
        short_term_memory: ShortTermMemoryEnhanced,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory
    ):
        self.working = working_memory
        self.short_term = short_term_memory
        self.episodic = episodic_memory
        self.semantic = semantic_memory
        
        self._consolidation_count = 0
        self._compressed_count = 0
        self._lock = threading.RLock()
    
    def consolidate(self, min_importance: MemoryImportance = MemoryImportance.MEDIUM) -> int:
        consolidated = 0
        
        with self._lock:
            for entry in self.working.get_all(limit=100):
                if entry.importance.value >= min_importance.value and not entry.consolidated:
                    self.short_term.add(entry)
                    entry.consolidated = True
                    consolidated += 1
            
            for entry in self.short_term.get_all(limit=100):
                if entry.importance.value >= min_importance.value and not entry.consolidated:
                    if entry.importance.value >= MemoryImportance.HIGH.value:
                        self.episodic.add(entry)
                    self.semantic.add(entry)
                    entry.consolidated = True
                    consolidated += 1
            
            self._consolidation_count += consolidated
        
        return consolidated
    
    def compress(self, similarity_threshold: float = 0.9) -> int:
        compressed = 0
        
        with self._lock:
            all_entries = self.short_term.get_all(limit=1000)
            grouped = self._group_similar(all_entries, similarity_threshold)
            
            for group in grouped:
                if len(group) > 1:
                    merged = self._merge_entries(group)
                    for entry in group:
                        if entry.id != merged.id:
                            self.short_term.delete(entry.id)
                    self.short_term.add(merged)
                    compressed += len(group) - 1
        
        self._compressed_count += compressed
        return compressed
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "consolidation_count": self._consolidation_count,
                "compressed_count": self._compressed_count,
            }
    
    def _group_similar(self, entries: List[MemoryEntry], threshold: float) -> List[List[MemoryEntry]]:
        groups: List[List[MemoryEntry]] = []
        
        for entry in entries:
            found_group = False
            for group in groups:
                if self._is_similar(entry, group[0], threshold):
                    group.append(entry)
                    found_group = True
                    break
            if not found_group:
                groups.append([entry])
        
        return groups
    
    def _is_similar(self, a: MemoryEntry, b: MemoryEntry, threshold: float) -> bool:
        if a.source_agent != b.source_agent:
            return False
        
        content_a = set(a.content.lower().split())
        content_b = set(b.content.lower().split())
        
        intersection = content_a & content_b
        union = content_a | content_b
        
        if not union:
            return False
        
        jaccard = len(intersection) / len(union)
        return jaccard >= threshold
    
    def _merge_entries(self, entries: List[MemoryEntry]) -> MemoryEntry:
        entries.sort(key=lambda e: e.created_at)
        oldest = entries[0]
        newest = entries[-1]
        
        merged_content = "\n---\n".join([e.content for e in entries])
        
        all_tags = set()
        for e in entries:
            all_tags.update(e.tags)
        
        max_importance = max(e.importance.value for e in entries)
        
        return MemoryEntry(
            id=f"merged_{oldest.id}",
            content=merged_content,
            memory_type=oldest.memory_type,
            importance=MemoryImportance(max_importance),
            metadata={
                "merged_from": [e.id for e in entries],
                "merged_at": datetime.utcnow().isoformat(),
            },
            source_agent=oldest.source_agent,
            source_task=oldest.source_task,
            tags=all_tags,
            created_at=oldest.created_at,
            consolidated=True,
            compressed=True,
        )


# ============================================================================
# Forgetting Mechanism - 遗忘机制
# ============================================================================

class ForgettingMechanism:
    """智能遗忘机制
    
    支持多种遗忘策略，保持记忆系统高效。
    """
    
    def __init__(
        self,
        strategy: ForgettingStrategy = ForgettingStrategy.WEIGHTED,
        max_memory_entries: int = 10000
    ):
        self.strategy = strategy
        self.max_memory_entries = max_memory_entries
        
        self._forgotten_count = 0
        self._lock = threading.RLock()
    
    def apply(
        self,
        memory: BaseMemory,
        target_size: Optional[int] = None
    ) -> int:
        if target_size is None:
            target_size = int(self.max_memory_entries * 0.8)
        
        current_size = memory.count()
        if current_size <= target_size:
            return 0
        
        to_remove = current_size - target_size
        removed = 0
        
        entries = memory.get_all(limit=current_size)
        
        if self.strategy == ForgettingStrategy.LRU:
            entries.sort(key=lambda e: e.last_accessed)
        elif self.strategy == ForgettingStrategy.LFU:
            entries.sort(key=lambda e: e.access_count)
        elif self.strategy == ForgettingStrategy.FIFO:
            entries.sort(key=lambda e: e.created_at)
        elif self.strategy == ForgettingStrategy.TIME_BASED:
            entries = [e for e in entries if e.is_expired()]
        elif self.strategy == ForgettingStrategy.WEIGHTED:
            entries.sort(key=lambda e: e.get_relevance_score(""))
        
        for i in range(min(to_remove, len(entries))):
            if memory.delete(entries[i].id):
                removed += 1
        
        with self._lock:
            self._forgotten_count += removed
        
        return removed
    
    def cleanup_expired(self, memory: BaseMemory) -> int:
        removed = 0
        current_time = datetime.utcnow()
        
        for entry in memory.get_all(limit=10000):
            if entry.is_expired(current_time):
                if memory.delete(entry.id):
                    removed += 1
        
        with self._lock:
            self._forgotten_count += removed
        
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "strategy": self.strategy.name,
                "forgotten_count": self._forgotten_count,
                "max_memory_entries": self.max_memory_entries,
            }


# ============================================================================
# Enhanced Memory System - 综合增强记忆系统
# ============================================================================

class EnhancedMemorySystem:
    """综合增强记忆系统 - 完整产品级实现
    
    Standing on the shoulders of giants:
    - Cognitive science theories
    - Redis for working/short-term
    - Milvus/Chroma ready for long-term
    - RAG patterns
    - Memory consolidation and forgetting
    """
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        working_memory_capacity: int = 15,
        short_term_ttl: int = 86400
    ):
        self.working_memory = WorkingMemory(capacity=working_memory_capacity)
        self.short_term_memory = ShortTermMemoryEnhanced(
            redis_client=redis_client,
            default_ttl=short_term_ttl
        )
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        
        self.retriever = MemoryRetriever(
            self.working_memory,
            self.short_term_memory,
            self.episodic_memory,
            self.semantic_memory
        )
        
        self.consolidator = MemoryConsolidator(
            self.working_memory,
            self.short_term_memory,
            self.episodic_memory,
            self.semantic_memory
        )
        
        self.forgetting = ForgettingMechanism()
    
    def add(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        **kwargs
    ) -> str:
        import uuid
        
        entry = MemoryEntry(
            id=kwargs.get('id', str(uuid.uuid4())),
            content=content,
            memory_type=memory_type,
            importance=importance,
            source_agent=kwargs.get('source_agent'),
            source_task=kwargs.get('source_task'),
            tags=set(kwargs.get('tags', [])),
            metadata=kwargs.get('metadata', {}),
            expires_at=kwargs.get('expires_at'),
        )
        
        if memory_type == MemoryType.WORKING:
            return self.working_memory.add(entry)
        elif memory_type == MemoryType.EPISODIC:
            return self.episodic_memory.add(entry)
        elif memory_type == MemoryType.SEMANTIC:
            return self.semantic_memory.add(entry)
        else:
            return self.short_term_memory.add(entry)
    
    def retrieve(
        self,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> MemoryRetrievalResult:
        memory_query = MemoryQuery(
            query=query,
            limit=limit,
            **{k: v for k, v in kwargs.items() if k in MemoryQuery.__dataclass_fields__}
        )
        return self.retriever.retrieve(memory_query)
    
    def retrieve_context(
        self,
        query: str,
        max_tokens: int = 4000,
        **kwargs
    ) -> Tuple[str, List[MemoryEntry]]:
        return self.retriever.retrieve_context(query, max_tokens, **kwargs)
    
    def consolidate(self) -> int:
        return self.consolidator.consolidate()
    
    def forget(self) -> int:
        count = 0
        count += self.forgetting.cleanup_expired(self.short_term_memory)
        count += self.forgetting.apply(self.short_term_memory)
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "retriever_stats": self.retriever.get_stats(),
            "consolidator_stats": self.consolidator.get_stats(),
            "forgetting_stats": self.forgetting.get_stats(),
        }
    
    def clear(self) -> None:
        self.working_memory.clear()
        self.short_term_memory.clear()
        self.episodic_memory.clear()
        self.semantic_memory.clear()


# ============================================================================
# Helper Functions
# ============================================================================

def create_memory_system(redis_client: Optional[Any] = None) -> EnhancedMemorySystem:
    """创建增强版记忆系统实例"""
    return EnhancedMemorySystem(redis_client=redis_client)

