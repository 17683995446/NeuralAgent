"""Enhanced Memory System Tests - 增强版记忆系统测试

Complete tests for the enhanced memory system including:
- Working Memory
- Enhanced Short-Term Memory
- Episodic Memory
- Semantic Memory
- Memory Retriever
- Memory Consolidation
- Forgetting Mechanism
"""

import pytest
import time
from datetime import datetime, timedelta

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.memory.enhanced_memory_system import (
    MemoryType,
    MemoryImportance,
    ForgettingStrategy,
    MemoryEntry,
    MemoryQuery,
    MemoryRetrievalResult,
    WorkingMemory,
    ShortTermMemoryEnhanced,
    EpisodicMemory,
    SemanticMemory,
    MemoryRetriever,
    MemoryConsolidator,
    ForgettingMechanism,
    EnhancedMemorySystem,
)


class TestMemoryEntry:
    """MemoryEntry 数据类测试"""
    
    def test_create_entry(self):
        """测试创建记忆条目"""
        entry = MemoryEntry(
            id="test1",
            content="Hello, world!",
            memory_type=MemoryType.SHORT_TERM,
            importance=MemoryImportance.HIGH,
            tags={"important", "test"},
            source_agent="test_agent",
        )
        
        assert entry.id == "test1"
        assert entry.content == "Hello, world!"
        assert entry.memory_type == MemoryType.SHORT_TERM
        assert entry.importance == MemoryImportance.HIGH
        assert "important" in entry.tags
    
    def test_serialization(self):
        """测试序列化和反序列化"""
        entry = MemoryEntry(
            id="test1",
            content="Test content",
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.MEDIUM,
        )
        
        data = entry.to_dict()
        reconstructed = MemoryEntry.from_dict(data)
        
        assert reconstructed.id == entry.id
        assert reconstructed.content == entry.content
        assert reconstructed.memory_type == entry.memory_type
    
    def test_relevance_score(self):
        """测试相关性分数计算"""
        entry = MemoryEntry(
            id="test1",
            content="AI agent collaboration",
            memory_type=MemoryType.SHORT_TERM,
            importance=MemoryImportance.HIGH,
        )
        
        score = entry.get_relevance_score("AI agent")
        assert 0 <= score <= 2


class TestWorkingMemory:
    """工作记忆测试"""
    
    def test_add_and_get(self):
        """测试添加和获取记忆"""
        wm = WorkingMemory(capacity=5)
        
        entry = MemoryEntry(
            id="1",
            content="Test content",
            memory_type=MemoryType.WORKING,
        )
        
        wm.add(entry)
        retrieved = wm.get("1")
        
        assert retrieved is not None
        assert retrieved.content == "Test content"
    
    def test_capacity_limit(self):
        """测试容量限制（LRU eviction）"""
        wm = WorkingMemory(capacity=3)
        
        for i in range(5):
            entry = MemoryEntry(
                id=str(i),
                content=f"Content {i}",
                memory_type=MemoryType.WORKING,
            )
            wm.add(entry)
        
        assert wm.count() == 3
        assert wm.get("0") is None
        assert wm.get("1") is None
        assert wm.get("2") is not None
    
    def test_lru_ordering(self):
        """测试LRU排序"""
        wm = WorkingMemory(capacity=3)
        
        entries = [
            MemoryEntry(id="1", content="1", memory_type=MemoryType.WORKING),
            MemoryEntry(id="2", content="2", memory_type=MemoryType.WORKING),
            MemoryEntry(id="3", content="3", memory_type=MemoryType.WORKING),
        ]
        
        for e in entries:
            wm.add(e)
        
        wm.get("1")
        wm.add(MemoryEntry(id="4", content="4", memory_type=MemoryType.WORKING))
        
        assert wm.get("1") is not None
        assert wm.get("2") is None
    
    def test_search(self):
        """测试搜索功能"""
        wm = WorkingMemory(capacity=10)
        
        entries = [
            MemoryEntry(id="1", content="Python programming", memory_type=MemoryType.WORKING),
            MemoryEntry(id="2", content="Machine learning", memory_type=MemoryType.WORKING),
            MemoryEntry(id="3", content="Python AI", memory_type=MemoryType.WORKING),
        ]
        
        for e in entries:
            wm.add(e)
        
        query = MemoryQuery(query="Python", limit=10)
        result = wm.search(query)
        
        assert result.total_found >= 2
    
    def test_stats(self):
        """测试统计信息"""
        wm = WorkingMemory(capacity=10)
        
        wm.add(MemoryEntry(id="1", content="1", memory_type=MemoryType.WORKING))
        wm.get("1")
        wm.get("nonexistent")
        
        stats = wm.get_stats()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1


class TestShortTermMemoryEnhanced:
    """增强版短期记忆测试"""
    
    def test_fallback_mode(self):
        """测试fallback模式（无Redis）"""
        stm = ShortTermMemoryEnhanced(redis_client=None, use_fallback=True)
        
        entry = MemoryEntry(
            id="test1",
            content="Fallback test",
            memory_type=MemoryType.SHORT_TERM,
        )
        
        stm.add(entry)
        retrieved = stm.get("test1")
        
        assert retrieved is not None
        assert retrieved.content == "Fallback test"
    
    def test_search_with_tags(self):
        """测试带标签的搜索"""
        stm = ShortTermMemoryEnhanced(redis_client=None)
        
        entries = [
            MemoryEntry(id="1", content="Code review", memory_type=MemoryType.SHORT_TERM, tags={"code", "review"}),
            MemoryEntry(id="2", content="Bug fix", memory_type=MemoryType.SHORT_TERM, tags={"bug", "fix"}),
            MemoryEntry(id="3", content="Code fix", memory_type=MemoryType.SHORT_TERM, tags={"code", "fix"}),
        ]
        
        for e in entries:
            stm.add(e)
        
        query = MemoryQuery(query="", tags=["code"], limit=10)
        result = stm.search(query)
        
        assert result.total_found == 2


class TestEpisodicMemory:
    """情节记忆测试"""
    
    def test_add_episode(self):
        """测试添加情节"""
        em = EpisodicMemory()
        
        entry = MemoryEntry(
            id="e1",
            content="Episode event",
            memory_type=MemoryType.EPISODIC,
        )
        
        episode_id = em.add_episode(entry, "episode_1")
        episode = em.get_episode("episode_1")
        
        assert len(episode) == 1
        assert episode[0].id == "e1"
    
    def test_auto_episode_id(self):
        """测试自动生成情节ID"""
        em = EpisodicMemory()
        
        entry = MemoryEntry(
            id="e1",
            content="Auto episode",
            memory_type=MemoryType.EPISODIC,
        )
        
        episode_id = em.add_episode(entry)
        assert episode_id.startswith("episode_")


class TestSemanticMemory:
    """语义记忆测试"""
    
    def test_add_and_search(self):
        """测试添加和搜索"""
        sm = SemanticMemory()
        
        entry = MemoryEntry(
            id="s1",
            content="Machine learning is a subset of AI",
            memory_type=MemoryType.SEMANTIC,
            tags={"AI", "ML"},
        )
        
        sm.add(entry)
        query = MemoryQuery(query="AI", limit=10)
        result = sm.search(query)
        
        assert result.total_found >= 1
    
    def test_relations(self):
        """测试关系"""
        sm = SemanticMemory()
        
        entry1 = MemoryEntry(id="s1", content="AI", memory_type=MemoryType.SEMANTIC)
        entry2 = MemoryEntry(id="s2", content="Machine Learning", memory_type=MemoryType.SEMANTIC)
        
        sm.add(entry1)
        sm.add(entry2)
        sm.add_relation("s1", "s2", "includes")
        
        related = sm.get_related("s1")
        assert len(related) >= 1


class TestMemoryRetriever:
    """记忆检索器测试"""
    
    def test_retrieve_across_systems(self):
        """测试跨系统检索"""
        wm = WorkingMemory()
        stm = ShortTermMemoryEnhanced(redis_client=None)
        em = EpisodicMemory()
        sm = SemanticMemory()
        
        retriever = MemoryRetriever(wm, stm, em, sm)
        
        wm.add(MemoryEntry(id="w1", content="Working AI", memory_type=MemoryType.WORKING))
        stm.add(MemoryEntry(id="s1", content="Short-term AI", memory_type=MemoryType.SHORT_TERM))
        
        query = MemoryQuery(query="AI", limit=10)
        result = retriever.retrieve(query)
        
        assert result.total_found >= 2
    
    def test_retrieve_context(self):
        """测试上下文检索"""
        wm = WorkingMemory()
        stm = ShortTermMemoryEnhanced(redis_client=None)
        em = EpisodicMemory()
        sm = SemanticMemory()
        
        retriever = MemoryRetriever(wm, stm, em, sm)
        
        wm.add(MemoryEntry(id="1", content="Agent collaboration", memory_type=MemoryType.WORKING))
        stm.add(MemoryEntry(id="2", content="Multi-agent systems", memory_type=MemoryType.SHORT_TERM))
        
        context, entries = retriever.retrieve_context("agent systems", max_tokens=1000)
        
        assert isinstance(context, str)
        assert len(entries) >= 1


class TestMemoryConsolidator:
    """记忆巩固测试"""
    
    def test_consolidation(self):
        """测试记忆巩固"""
        wm = WorkingMemory()
        stm = ShortTermMemoryEnhanced(redis_client=None)
        em = EpisodicMemory()
        sm = SemanticMemory()
        
        consolidator = MemoryConsolidator(wm, stm, em, sm)
        
        wm.add(MemoryEntry(
            id="1", 
            content="Consolidate me", 
            memory_type=MemoryType.WORKING,
            importance=MemoryImportance.HIGH
        ))
        
        consolidated = consolidator.consolidate()
        assert consolidated >= 0


class TestForgettingMechanism:
    """遗忘机制测试"""
    
    def test_forgetting_strategies(self):
        """测试不同遗忘策略"""
        forgetter = ForgettingMechanism(strategy=ForgettingStrategy.LRU)
        memory = ShortTermMemoryEnhanced(redis_client=None)
        
        for i in range(10):
            entry = MemoryEntry(
                id=str(i),
                content=f"Content {i}",
                memory_type=MemoryType.SHORT_TERM,
            )
            memory.add(entry)
        
        initial_count = memory.count()
        removed = forgetter.apply(memory, target_size=5)
        
        assert memory.count() <= 5
        assert removed >= initial_count - 5
    
    def test_cleanup_expired(self):
        """测试清理过期记忆"""
        forgetter = ForgettingMechanism()
        memory = ShortTermMemoryEnhanced(redis_client=None)
        
        expired = MemoryEntry(
            id="expired",
            content="Expired",
            memory_type=MemoryType.SHORT_TERM,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        fresh = MemoryEntry(
            id="fresh",
            content="Fresh",
            memory_type=MemoryType.SHORT_TERM,
        )
        
        memory.add(expired)
        memory.add(fresh)
        
        removed = forgetter.cleanup_expired(memory)
        assert removed >= 1
        assert memory.get("fresh") is not None


class TestEnhancedMemorySystem:
    """综合增强记忆系统测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        system = EnhancedMemorySystem()
        
        # Add memory
        mem_id = system.add(
            content="Neural agents work together",
            memory_type=MemoryType.WORKING,
            importance=MemoryImportance.HIGH,
            tags={"neural", "agent"},
            source_agent="test_agent",
        )
        
        # Retrieve
        result = system.retrieve("neural agents")
        assert result.total_found >= 1
        
        # Consolidate
        consolidated = system.consolidate()
        assert consolidated >= 0
        
        # Get stats
        stats = system.get_stats()
        assert "retriever_stats" in stats
        assert "consolidator_stats" in stats
    
    def test_retrieve_context_for_llm(self):
        """测试为LLM检索上下文"""
        system = EnhancedMemorySystem()
        
        system.add("Agent communication protocol", tags={"protocol"}, memory_type=MemoryType.WORKING)
        system.add("Trust-based filtering", tags={"trust"}, memory_type=MemoryType.SHORT_TERM)
        system.add("Collaboration patterns", tags={"pattern"}, memory_type=MemoryType.SEMANTIC)
        
        context, entries = system.retrieve_context("agent trust", max_tokens=2000)
        
        assert isinstance(context, str)
        assert len(entries) >= 1
        print(f"Retrieved {len(entries)} entries for LLM context")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

