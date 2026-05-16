"""
Enhanced Memory System - 增强记忆系统

创新性功能：
1. 自适应记忆压缩
2. 跨会话学习
3. 情感记忆
4. 意图预测
"""

import json
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import hashlib
import re

logger = logging.getLogger(__name__)


class SentimentType(Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class MemoryImportance(Enum):
    """记忆重要性"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TRIVIAL = 1


@dataclass
class MemoryEntry:
    """记忆条目"""
    key: str
    value: Any
    created_at: datetime = None
    updated_at: datetime = None
    ttl: Optional[int] = None
    importance: MemoryImportance = MemoryImportance.MEDIUM
    access_count: int = 0
    last_accessed: datetime = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()
        if not self.last_accessed:
            self.last_accessed = self.created_at


@dataclass
class EmotionalRecord:
    """情感记录"""
    user_id: str
    sentiment: SentimentType
    context: str
    timestamp: datetime
    confidence: float = 0.8
    keywords: List[str] = field(default_factory=list)


@dataclass
class IntentPattern:
    """意图模式"""
    pattern: str
    intent_type: str
    frequency: int = 0
    last_matched: datetime = None
    success_rate: float = 0.0


class AdaptiveMemoryCompressor:
    """自适应记忆压缩器"""
    
    def __init__(self, compression_threshold: int = 1000):
        self.compression_threshold = compression_threshold
        self.compression_history = []
    
    def should_compress(self, memory_size: int, memory_importance: MemoryImportance) -> bool:
        """判断是否需要压缩"""
        if memory_importance.value >= MemoryImportance.HIGH.value:
            return False
        
        if memory_size < self.compression_threshold:
            return False
        
        return True
    
    def compress(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """压缩记忆"""
        compressed = {
            "summary": self._generate_summary(memory),
            "key_points": self._extract_key_points(memory),
            "metadata": {
                "original_size": len(str(memory)),
                "compressed_at": datetime.now().isoformat()
            }
        }
        
        self.compression_history.append({
            "original_size": len(str(memory)),
            "compressed_size": len(str(compressed)),
            "timestamp": datetime.now()
        })
        
        return compressed
    
    def _generate_summary(self, memory: Any) -> str:
        """生成记忆摘要"""
        if isinstance(memory, str):
            return memory[:200] + "..." if len(memory) > 200 else memory
        elif isinstance(memory, dict):
            return f"Dict with {len(memory)} keys"
        elif isinstance(memory, list):
            return f"List with {len(memory)} items"
        return str(memory)[:200]
    
    def _extract_key_points(self, memory: Any) -> List[str]:
        """提取关键点"""
        key_points = []
        
        if isinstance(memory, str):
            sentences = re.split(r'[.!?]+', memory)
            key_points = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
        elif isinstance(memory, dict):
            key_points = [f"{k}: {v}" for k, v in list(memory.items())[:5]]
        
        return key_points


class EmotionalMemory:
    """情感记忆 - 记录用户情感偏好和反馈"""
    
    def __init__(self):
        self.sentiments: Dict[str, List[EmotionalRecord]] = defaultdict(list)
        self.preferences: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.feedback_history: List[Dict[str, Any]] = []
        logger.info("EmotionalMemory 初始化完成")
    
    def record_sentiment(
        self,
        user_id: str,
        sentiment: SentimentType,
        context: str,
        confidence: float = 0.8
    ):
        """记录用户情感"""
        keywords = self._extract_keywords(context)
        
        record = EmotionalRecord(
            user_id=user_id,
            sentiment=sentiment,
            context=context,
            timestamp=datetime.now(),
            confidence=confidence,
            keywords=keywords
        )
        
        self.sentiments[user_id].append(record)
        
        if len(self.sentiments[user_id]) > 100:
            self.sentiments[user_id] = self.sentiments[user_id][-100:]
        
        logger.debug(f"记录情感: {user_id} - {sentiment.value}")
    
    def record_feedback(self, user_id: str, feedback_type: str, content: Any, rating: int = None):
        """记录用户反馈"""
        feedback = {
            "user_id": user_id,
            "type": feedback_type,
            "content": content,
            "rating": rating,
            "timestamp": datetime.now()
        }
        
        self.feedback_history.append(feedback)
        self._update_preferences(user_id, feedback)
    
    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏好"""
        return self.preferences.get(user_id, {})
    
    def get_sentiment_trend(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """获取情感趋势"""
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            r for r in self.sentiments.get(user_id, [])
            if r.timestamp > cutoff
        ]
        
        if not recent:
            return {"trend": "neutral", "count": 0}
        
        sentiment_counts = defaultdict(int)
        for record in recent:
            sentiment_counts[record.sentiment.value] += 1
        
        most_common = max(sentiment_counts.items(), key=lambda x: x[1])
        
        return {
            "trend": most_common[0],
            "count": len(recent),
            "sentiment_distribution": dict(sentiment_counts)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = re.findall(r'\b\w{4,}\b', text.lower())
        stopwords = {'this', 'that', 'with', 'have', 'from', 'they', 'been', 'were', 'will', 'would'}
        return [w for w in words if w not in stopwords][:10]
    
    def _update_preferences(self, user_id: str, feedback: Dict[str, Any]):
        """更新用户偏好"""
        if feedback.get("rating") is not None:
            current = self.preferences[user_id].get("avg_rating", 0)
            count = self.preferences[user_id].get("rating_count", 0)
            
            new_avg = (current * count + feedback["rating"]) / (count + 1)
            self.preferences[user_id]["avg_rating"] = new_avg
            self.preferences[user_id]["rating_count"] = count + 1


class IntentPredictor:
    """意图预测器 - 基于历史数据预测用户意图"""
    
    def __init__(self):
        self.patterns: Dict[str, List[IntentPattern]] = defaultdict(list)
        self.session_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        logger.info("IntentPredictor 初始化完成")
    
    def learn_pattern(self, user_id: str, query: str, intent: str, success: bool = True):
        """学习用户意图模式"""
        pattern_hash = self._hash_pattern(query)
        
        existing = next(
            (p for p in self.patterns[user_id] if p.pattern == pattern_hash),
            None
        )
        
        if existing:
            existing.frequency += 1
            existing.last_matched = datetime.now()
            if success:
                existing.success_rate = (
                    existing.success_rate * (existing.frequency - 1) + 1.0
                ) / existing.frequency
            else:
                existing.success_rate = (
                    existing.success_rate * (existing.frequency - 1)
                ) / existing.frequency
        else:
            self.patterns[user_id].append(
                IntentPattern(
                    pattern=pattern_hash,
                    intent_type=intent,
                    frequency=1,
                    last_matched=datetime.now(),
                    success_rate=1.0 if success else 0.0
                )
            )
    
    def predict_intent(self, user_id: str, query: str) -> Optional[str]:
        """预测用户意图"""
        pattern_hash = self._hash_pattern(query)
        
        candidates = [
            p for p in self.patterns.get(user_id, [])
            if self._is_similar(pattern_hash, p.pattern)
        ]
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda p: (p.frequency * p.success_rate), reverse=True)
        
        return candidates[0].intent_type
    
    def get_next_suggestion(self, user_id: str) -> Optional[str]:
        """获取下一个建议"""
        history = self.session_history.get(user_id, [])
        if not history:
            return None
        
        last_intent = history[-1].get("intent")
        if not last_intent:
            return None
        
        next_intents = self._get_sequential_pattern(last_intent)
        if next_intents:
            return next_intents[0]
        
        return None
    
    def _hash_pattern(self, text: str) -> str:
        """生成模式哈希"""
        normalized = text.lower().strip()
        words = re.findall(r'\b\w+\b', normalized)
        return hashlib.md5(' '.join(sorted(words)).encode()).hexdigest()
    
    def _is_similar(self, hash1: str, hash2: str) -> bool:
        """检查两个哈希是否相似"""
        if hash1 == hash2:
            return True
        
        distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        return distance <= 3
    
    def _get_sequential_pattern(self, current_intent: str) -> List[str]:
        """获取顺序模式"""
        patterns = []
        for session in self.session_history.values():
            for i, item in enumerate(session[:-1]):
                if item.get("intent") == current_intent and i + 1 < len(session):
                    next_intent = session[i + 1].get("intent")
                    if next_intent:
                        patterns.append(next_intent)
        
        return patterns[:3]


class CrossSessionLearner:
    """跨会话学习器"""
    
    def __init__(self):
        self.global_patterns: Dict[str, int] = defaultdict(int)
        self.session_summaries: Dict[str, Dict[str, Any]] = {}
        self.learned_insights: List[Dict[str, Any]] = []
        logger.info("CrossSessionLearner 初始化完成")
    
    def add_session_summary(self, session_id: str, summary: Dict[str, Any]):
        """添加会话摘要"""
        self.session_summaries[session_id] = {
            **summary,
            "created_at": datetime.now()
        }
        
        self._extract_global_patterns(summary)
        self._generate_insights()
    
    def get_learned_insights(self) -> List[Dict[str, Any]]:
        """获取学到的洞察"""
        return self.learned_insights[-10:]
    
    def get_common_patterns(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """获取常见模式"""
        sorted_patterns = sorted(
            self.global_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {"pattern": pattern, "frequency": freq}
            for pattern, freq in sorted_patterns
        ]
    
    def _extract_global_patterns(self, summary: Dict[str, Any]):
        """提取全局模式"""
        if "topics" in summary:
            for topic in summary["topics"]:
                self.global_patterns[topic] += 1
        
        if "goals" in summary:
            for goal in summary["goals"]:
                self.global_patterns[f"goal:{goal}"] += 1
    
    def _generate_insights(self):
        """生成洞察"""
        if len(self.session_summaries) < 5:
            return
        
        self.learned_insights.append({
            "type": "pattern_discovered",
            "description": f"发现 {len(self.global_patterns)} 个全局模式",
            "timestamp": datetime.now()
        })


class EnhancedMemorySystem:
    """增强记忆系统 - 整合所有创新功能"""
    
    def __init__(
        self,
        compression_threshold: int = 1000,
        max_memories: int = 10000
    ):
        self.compressor = AdaptiveMemoryCompressor(compression_threshold)
        self.emotional_memory = EmotionalMemory()
        self.intent_predictor = IntentPredictor()
        self.cross_session_learner = CrossSessionLearner()
        self.max_memories = max_memories
        
        self.memories: Dict[str, MemoryEntry] = {}
        self.access_patterns: Dict[str, int] = defaultdict(int)
        
        logger.info("EnhancedMemorySystem 初始化完成")
    
    async def store(
        self,
        key: str,
        value: Any,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        ttl: Optional[int] = None
    ):
        """存储记忆"""
        if len(self.memories) >= self.max_memories:
            await self._auto_cleanup()
        
        entry = MemoryEntry(
            key=key,
            value=value,
            importance=importance,
            ttl=ttl
        )
        
        self.memories[key] = entry
        logger.debug(f"存储记忆: {key} (重要性: {importance.name})")
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆"""
        entry = self.memories.get(key)
        if not entry:
            return None
        
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        self.access_patterns[key] += 1
        
        if self.compressor.should_compress(
            entry.access_count,
            entry.importance
        ):
            entry.value = self.compressor.compress(entry.value)
            logger.debug(f"已压缩记忆: {key}")
        
        return entry.value
    
    async def record_emotion(
        self,
        user_id: str,
        sentiment: SentimentType,
        context: str,
        confidence: float = 0.8
    ):
        """记录情感"""
        self.emotional_memory.record_sentiment(user_id, sentiment, context, confidence)
    
    async def predict_intent(self, user_id: str, query: str) -> Optional[str]:
        """预测意图"""
        return self.intent_predictor.predict_intent(user_id, query)
    
    async def learn_from_session(self, session_id: str, summary: Dict[str, Any]):
        """从会话中学习"""
        self.cross_session_learner.add_session_summary(session_id, summary)
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        return {
            "preferences": self.emotional_memory.get_preferences(user_id),
            "sentiment_trend": self.emotional_memory.get_sentiment_trend(user_id),
            "common_patterns": self.cross_session_learner.get_common_patterns(),
            "learned_insights": self.cross_session_learner.get_learned_insights()
        }
    
    async def _auto_cleanup(self):
        """自动清理低价值记忆"""
        low_priority = [
            (key, entry) for key, entry in self.memories.items()
            if entry.importance.value <= MemoryImportance.LOW.value
        ]
        
        low_priority.sort(key=lambda x: (x[1].access_count, x[1].created_at))
        
        to_remove = len(self.memories) - self.max_memories + 100
        for key, _ in low_priority[:to_remove]:
            del self.memories[key]
            logger.debug(f"自动清理记忆: {key}")


def get_enhanced_memory_system() -> EnhancedMemorySystem:
    """获取增强记忆系统单例"""
    if not hasattr(get_enhanced_memory_system, '_instance'):
        get_enhanced_memory_system._instance = EnhancedMemorySystem()
    return get_enhanced_memory_system._instance
