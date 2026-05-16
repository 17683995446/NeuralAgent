"""Unit tests for memory systems."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from backend.core.memory.short_term_memory import ShortTermMemory
from backend.core.memory.long_term_memory import LongTermMemory, MemoryEntry


class TestShortTermMemory:
    """Test cases for ShortTermMemory class."""

    def test_filter_by_trust(self):
        """Test message filtering by trust score."""
        memory = ShortTermMemory(
            redis_client=MagicMock(),
            task_id="test_task"
        )

        messages = [
            {"sender_agent_id": "agent_a", "content": "msg1"},
            {"sender_agent_id": "agent_b", "content": "msg2"},
            {"sender_agent_id": "agent_c", "content": "msg3"},
        ]

        trust_matrix = {
            "agent_a": 0.8,
            "agent_b": 0.5,
            "agent_c": 0.7,
        }

        filtered = memory.filter_by_trust(messages, trust_matrix)

        assert len(filtered) == 2
        assert filtered[0]["sender_agent_id"] == "agent_a"
        assert filtered[1]["sender_agent_id"] == "agent_c"

    def test_filter_by_trust_threshold(self):
        """Test trust filtering with different thresholds."""
        memory = ShortTermMemory(
            redis_client=MagicMock(),
            task_id="test_task"
        )

        messages = [
            {"sender_agent_id": "high", "content": "high trust"},
            {"sender_agent_id": "medium", "content": "medium trust"},
            {"sender_agent_id": "low", "content": "low trust"},
        ]

        trust_matrix = {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.4,
        }

        filtered = memory.filter_by_trust(messages, trust_matrix)

        assert len(filtered) == 2
        trust_scores = [msg["trust_score"] for msg in filtered]
        assert all(score >= 0.6 for score in trust_scores)


class TestLongTermMemory:
    """Test cases for LongTermMemory class."""

    def test_memory_entry_to_dict(self):
        """Test MemoryEntry to_dict method."""
        entry = MemoryEntry(
            id="test_id",
            agent_id="agent_001",
            task_type="code_analysis",
            content='{"result": "success"}',
            metadata={"key": "value"},
        )

        result = entry.to_dict()

        assert result["id"] == "test_id"
        assert result["agent_id"] == "agent_001"
        assert result["task_type"] == "code_analysis"

    def test_memory_entry_with_optional_fields(self):
        """Test MemoryEntry with optional fields."""
        entry = MemoryEntry(
            id="test_id_2",
            agent_id="agent_002",
            task_type="code_generation",
            content='{"generated": true}',
            metadata={"version": "1.0"},
            trust_trend={"accuracy": 0.9},
            task_result="success",
        )

        result = entry.to_dict()

        assert result["trust_trend"] == {"accuracy": 0.9}
        assert result["task_result"] == "success"
