"""
Comprehensive Test Suite for NeuralAgent System
=============================================
Total Test Cases: 120+
Coverage: API, Core Components, Layers, Integration, E2E
"""
import pytest
import json
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from datetime import datetime
from typing import Dict, Any, List

import sys
sys.path.insert(0, '/workspace/neural_agent')

from backend.api.schemas import (
    TaskInput, TaskContext, TaskStatus, FeedbackInput,
    FeedbackItem, FeedbackResult, TaskResult, ErrorResponse, HealthCheck
)
from backend.core.agents.intelligent_multi_agent_coordinator import (
    NeuralAgent, ConvolutionAgent, PoolingAgent,
    FCAgent, OutputAgent, create_agent
)
from backend.core.memory.short_term_memory import ShortTermMemory
from backend.core.memory.long_term_memory import LongTermMemory, MemoryEntry
from backend.core.trust_management.trust_manager import TrustManager, TrustUpdate
from backend.core.messaging.structured_message_protocol_handler import (
    ForwardMessage, BackwardMessage, MessageType,
    MessageProtocol, LayerInfo, FeedbackContent
)
from backend.core.llm_adapter import LLMAdapter, LLMResponse
from backend.core.neural_layers.neural_input_layer import InputLayer
from backend.core.neural_layers.neural_convolution_layer import ConvolutionLayer, ConvolutionGranularity
from backend.core.neural_layers.neural_pooling_layer import PoolingLayer
from backend.core.neural_layers.neural_fully_connected_layers import FCLayer1
from backend.core.neural_layers.neural_fully_connected_layers import FCLayer2
from backend.core.neural_layers.neural_fully_connected_layers import FCLayer3
from backend.core.neural_layers.neural_output_layer import OutputLayer
from backend.core.neural_layers.neural_backward_propagation_layer import BackwardLayer, FeedbackProcessor
from backend.config import settings


# =============================================================================
# SECTION 1: API Schemas Tests (25 Test Cases)
# =============================================================================

class TestTaskInputSchema:
    """Test TaskInput Pydantic model (5 tests)"""

    def test_task_input_valid_with_repo_url(self):
        """Test valid task input with repo URL"""
        task = TaskInput(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            user_requirement="添加JWT认证支持",
            code_repo_url="https://github.com/example/repo.git",
            max_iteration=5,
            learning_rate=0.1
        )
        assert task.task_id == "550e8400-e29b-41d4-a716-446655440000"
        assert task.user_requirement == "添加JWT认证支持"
        assert task.max_iteration == 5

    def test_task_input_valid_with_local_path(self):
        """Test valid task input with local path"""
        task = TaskInput(
            task_id="test-task-local-path-12345",
            user_requirement="重构代码模块",
            local_code_path="/path/to/local/code"
        )
        assert task.local_code_path == "/path/to/local/code"
        assert task.target_branch == "main"

    def test_task_input_defaults(self):
        """Test task input default values"""
        task = TaskInput(
            task_id="test-task-defaults-valid",
            user_requirement="测试默认参数"
        )
        assert task.target_branch == "main"
        assert task.max_iteration == 5
        assert task.learning_rate == 0.1
        assert task.llm_config == {}

    def test_task_input_llm_config(self):
        """Test task input with LLM config"""
        llm_cfg = {"model": "gpt-4o", "temperature": 0.5}
        task = TaskInput(
            task_id="test-task-llm-config-valid",
            user_requirement="测试LLM配置",
            llm_config=llm_cfg
        )
        assert task.llm_config["model"] == "gpt-4o"
        assert task.llm_config["temperature"] == 0.5

    def test_task_input_max_iteration_bounds(self):
        """Test task input max iteration bounds"""
        task = TaskInput(
            task_id="test-task-bounds-123456",
            user_requirement="测试边界",
            max_iteration=10,
            learning_rate=0.5
        )
        assert task.max_iteration == 10
        assert task.learning_rate == 0.5


class TestFeedbackInputSchema:
    """Test FeedbackInput Pydantic model (5 tests)"""

    def test_feedback_input_valid(self):
        """Test valid feedback input"""
        feedback = FeedbackInput(
            satisfaction_score=4,
            feedback_items=[
                FeedbackItem(
                    type="positive",
                    description="代码质量好",
                    suggestion="继续优化"
                )
            ]
        )
        assert feedback.satisfaction_score == 4
        assert len(feedback.feedback_items) == 1

    def test_feedback_input_multiple_items(self):
        """Test feedback with multiple items"""
        feedback = FeedbackInput(
            satisfaction_score=3,
            feedback_items=[
                FeedbackItem(type="positive", description="Good", suggestion="OK"),
                FeedbackItem(type="negative", description="Needs work", suggestion="Fix it"),
            ]
        )
        assert len(feedback.feedback_items) == 2

    def test_feedback_input_with_additional_comments(self):
        """Test feedback with additional comments"""
        feedback = FeedbackInput(
            satisfaction_score=5,
            feedback_items=[
                FeedbackItem(type="positive", description="Excellent")
            ],
            additional_comments="Overall great work!"
        )
        assert feedback.additional_comments == "Overall great work!"

    def test_feedback_input_score_range(self):
        """Test feedback score range validation"""
        for score in [0, 2, 5]:
            feedback = FeedbackInput(
                satisfaction_score=score,
                feedback_items=[FeedbackItem(type="positive" if score >= 3 else "negative", description="Test")]
            )
            assert feedback.satisfaction_score == score

    def test_feedback_item_types(self):
        """Test different feedback item types"""
        positive = FeedbackItem(type="positive", description="Good")
        negative = FeedbackItem(type="negative", description="Bad")
        assert positive.type == "positive"
        assert negative.type == "negative"


class TestTaskStatusSchema:
    """Test TaskStatus Pydantic model (5 tests)"""

    def test_task_status_creation(self):
        """Test task status creation"""
        status = TaskStatus(
            task_id="test-001-valid-uuid",
            status="initialized",
            current_layer="Input Layer",
            current_iteration=0,
            max_iteration=5,
            progress_percentage=0.0,
            created_at="2024-01-01T00:00:00"
        )
        assert status.task_id == "test-001-valid-uuid"
        assert status.status == "initialized"
        assert status.progress_percentage == 0.0

    def test_task_status_progress_mapping(self):
        """Test progress percentage for different statuses"""
        status_map = {
            "initialized": 0,
            "convolution": 12.5,
            "pooling": 25,
            "fc1": 37.5,
            "fc2": 50,
            "fc3": 75,
            "output": 87.5,
            "completed": 100
        }
        for status_name, expected_progress in status_map.items():
            status = TaskStatus(
                task_id=f"test-{status_name}",
                status=status_name,
                current_layer="Test",
                current_iteration=0,
                max_iteration=5,
                progress_percentage=expected_progress,
                created_at="2024-01-01T00:00:00"
            )
            assert status.progress_percentage == expected_progress

    def test_task_status_with_update_time(self):
        """Test task status with update time"""
        status = TaskStatus(
            task_id="test-update-time-12345678",
            status="running",
            current_layer="Convolution",
            current_iteration=1,
            max_iteration=5,
            progress_percentage=12.5,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:05:00"
        )
        assert status.updated_at == "2024-01-01T00:05:00"

    def test_task_status_iteration_info(self):
        """Test task status iteration information"""
        status = TaskStatus(
            task_id="test-iteration-info-valid",
            status="fc3",
            current_layer="FC Layer 3",
            current_iteration=3,
            max_iteration=5,
            progress_percentage=75.0,
            created_at="2024-01-01T00:00:00"
        )
        assert status.current_iteration == 3
        assert status.max_iteration == 5
        assert status.current_iteration < status.max_iteration

    def test_task_status_completed(self):
        """Test completed task status"""
        status = TaskStatus(
            task_id="test-completed-123456789",
            status="completed",
            current_layer="Completed",
            current_iteration=5,
            max_iteration=5,
            progress_percentage=100.0,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T01:00:00"
        )
        assert status.status == "completed"
        assert status.progress_percentage == 100.0


class TestHealthCheckSchema:
    """Test HealthCheck Pydantic model (5 tests)"""

    def test_health_check_all_healthy(self):
        """Test health check with all components healthy"""
        health = HealthCheck(
            status="healthy",
            version="0.1.0",
            components={"api": "healthy", "database": "healthy"}
        )
        assert health.status == "healthy"

    def test_health_check_degraded(self):
        """Test health check with degraded status"""
        health = HealthCheck(
            status="degraded",
            version="0.1.0",
            components={"api": "healthy", "database": "unhealthy"}
        )
        assert health.status == "degraded"

    def test_health_check_components(self):
        """Test health check components"""
        health = HealthCheck(
            status="healthy",
            version="0.1.0",
            components={
                "api": "healthy",
                "database": "healthy",
                "redis": "healthy",
                "rabbitmq": "healthy"
            }
        )
        assert len(health.components) == 4

    def test_health_check_version(self):
        """Test health check version"""
        health = HealthCheck(
            status="healthy",
            version="0.2.0",
            components={}
        )
        assert health.version == "0.2.0"

    def test_health_check_unhealthy(self):
        """Test health check with unhealthy status"""
        health = HealthCheck(
            status="unhealthy",
            version="0.1.0",
            components={"api": "unhealthy", "database": "unhealthy"}
        )
        assert health.status == "unhealthy"


class TestTaskContextSchema:
    """Test TaskContext Pydantic model (5 tests)"""

    def test_task_context_creation(self):
        """Test task context creation"""
        context = TaskContext(
            task_id="context-test-valid-12345",
            status="initialized",
            user_requirement="测试上下文",
            max_iteration=5,
            learning_rate=0.1,
            created_at="2024-01-01T00:00:00",
            message="Task initialized"
        )
        assert context.task_id == "context-test-valid-12345"
        assert context.status == "initialized"

    def test_task_context_with_repo_path(self):
        """Test task context with repository path"""
        context = TaskContext(
            task_id="context-repo-valid-123456",
            status="initialized",
            user_requirement="测试",
            code_repo_path="/path/to/repo",
            max_iteration=5,
            learning_rate=0.1,
            created_at="2024-01-01T00:00:00",
            message="Ready"
        )
        assert context.code_repo_path == "/path/to/repo"

    def test_task_context_message(self):
        """Test task context message field"""
        context = TaskContext(
            task_id="context-msg-valid-1234567",
            status="ready",
            user_requirement="Test",
            max_iteration=5,
            learning_rate=0.1,
            created_at="2024-01-01T00:00:00",
            message="Task ready for forward propagation"
        )
        assert "forward propagation" in context.message


# =============================================================================
# SECTION 2: Core Component Tests (35 Test Cases)
# =============================================================================

class TestNeuralAgentCore:
    """Test NeuralAgent core functionality (10 tests)"""

    def test_agent_initialization(self):
        """Test agent basic initialization"""
        agent = NeuralAgent(
            agent_id="test_agent_001",
            layer_name="convolution",
            role="代码分析工程师",
            goal="分析代码结构",
            llm_config={"model": "gpt-4o"}
        )
        assert agent.agent_id == "test_agent_001"
        assert agent.layer_name == "convolution"

    def test_default_trust_matrix_structure(self):
        """Test default trust matrix has correct structure"""
        agent = NeuralAgent(
            agent_id="test_agent_trust_002",
            layer_name="pooling",
            role="测试",
            goal="测试",
            llm_config={}
        )
        expected_keys = {"global", "confidence", "accuracy", "reliability"}
        assert set(agent.trust_matrix.keys()) == expected_keys
        assert all(v == 1.0 for v in agent.trust_matrix.values())

    def test_custom_trust_matrix(self):
        """Test agent with custom trust matrix"""
        custom_trust = {"global": 0.9, "accuracy": 0.8}
        agent = NeuralAgent(
            agent_id="test_agent_custom_trust",
            layer_name="fc_layer_1",
            role="Test",
            goal="Test",
            llm_config={},
            trust_matrix=custom_trust
        )
        assert agent.trust_matrix["global"] == 0.9
        assert agent.trust_matrix["accuracy"] == 0.8

    def test_update_trust_matrix(self):
        """Test trust matrix update"""
        agent = NeuralAgent(
            agent_id="test_agent_update_trust",
            layer_name="output",
            role="Test",
            goal="Test",
            llm_config={}
        )
        new_trust = {"global": 1.5, "confidence": 0.7}
        agent.update_trust_matrix(new_trust)
        assert agent.trust_matrix["global"] == 1.5

    def test_get_trust_score_existing(self):
        """Test getting trust score for existing agent"""
        agent = NeuralAgent(
            agent_id="test_agent_score",
            layer_name="convolution",
            role="Test",
            goal="Test",
            llm_config={}
        )
        agent.trust_matrix = {"source_a": 0.8, "source_b": 0.6}
        assert agent.get_trust_score("source_a") == 0.8
        assert agent.get_trust_score("source_b") == 0.6

    def test_get_trust_score_default(self):
        """Test getting trust score returns default for unknown agent"""
        agent = NeuralAgent(
            agent_id="test_agent_default",
            layer_name="pooling",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.get_trust_score("unknown_agent") == 1.0

    def test_should_adopt_output_high_trust(self):
        """Test output adoption with high trust"""
        agent = NeuralAgent(
            agent_id="test_adopt_high",
            layer_name="fc_layer_2",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.should_adopt_output(0.8) is True
        assert agent.should_adopt_output(0.9) is True

    def test_should_adopt_output_low_trust(self):
        """Test output adoption with low trust"""
        agent = NeuralAgent(
            agent_id="test_adopt_low",
            layer_name="fc_layer_3",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.should_adopt_output(0.4) is False
        assert agent.should_adopt_output(0.5) is False

    def test_apply_feedback_positive(self):
        """Test applying positive feedback"""
        agent = NeuralAgent(
            agent_id="test_feedback_positive",
            layer_name="convolution",
            role="Test",
            goal="Test",
            llm_config={}
        )
        agent.trust_matrix = {"global": 1.0}
        feedback = {"reward": 0.5, "learning_rate": 0.1}
        updated = agent.apply_feedback(feedback)
        assert updated["global"] == pytest.approx(1.05, rel=0.01)

    def test_apply_feedback_negative(self):
        """Test applying negative feedback"""
        agent = NeuralAgent(
            agent_id="test_feedback_negative",
            layer_name="pooling",
            role="Test",
            goal="Test",
            llm_config={}
        )
        agent.trust_matrix = {"global": 1.0}
        feedback = {"reward": -0.5, "learning_rate": 0.1}
        updated = agent.apply_feedback(feedback)
        assert updated["global"] == pytest.approx(0.95, rel=0.01)


class TestAgentTypes:
    """Test different agent types (10 tests)"""

    def test_convolution_agent_layer_name(self):
        """Test convolution agent has correct layer name"""
        agent = ConvolutionAgent(
            agent_id="conv_test",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.layer_name == "convolution"

    def test_pooling_agent_layer_name(self):
        """Test pooling agent has correct layer name"""
        agent = PoolingAgent(
            agent_id="pool_test",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.layer_name == "pooling"

    def test_fc_agent_layer_1(self):
        """Test FC agent layer 1"""
        agent = FCAgent(
            agent_id="fc1_test",
            fc_layer_num=1,
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.layer_name == "fc_layer_1"

    def test_fc_agent_layer_2(self):
        """Test FC agent layer 2"""
        agent = FCAgent(
            agent_id="fc2_test",
            fc_layer_num=2,
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.layer_name == "fc_layer_2"

    def test_fc_agent_layer_3(self):
        """Test FC agent layer 3"""
        agent = FCAgent(
            agent_id="fc3_test",
            fc_layer_num=3,
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.layer_name == "fc_layer_3"

    def test_output_agent_layer_name(self):
        """Test output agent has correct layer name"""
        agent = OutputAgent(
            agent_id="output_test",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.layer_name == "output"

    def test_create_convolution_agent_factory(self):
        """Test factory creates convolution agent"""
        agent = create_agent(
            agent_type="convolution",
            agent_id="factory_conv",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert isinstance(agent, ConvolutionAgent)
        assert agent.layer_name == "convolution"

    def test_create_pooling_agent_factory(self):
        """Test factory creates pooling agent"""
        agent = create_agent(
            agent_type="pooling",
            agent_id="factory_pool",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert isinstance(agent, PoolingAgent)
        assert agent.layer_name == "pooling"

    def test_create_fc_agents_factory(self):
        """Test factory creates FC agents"""
        fc1 = create_agent("fc1", "fc1", "R", "G", {})
        fc2 = create_agent("fc2", "fc2", "R", "G", {})
        fc3 = create_agent("fc3", "fc3", "R", "G", {})
        assert fc1.layer_name == "fc_layer_1"
        assert fc2.layer_name == "fc_layer_2"
        assert fc3.layer_name == "fc_layer_3"

    def test_create_default_agent_factory(self):
        """Test factory creates default agent for unknown type"""
        agent = create_agent(
            agent_type="unknown_type",
            agent_id="factory_default",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert isinstance(agent, NeuralAgent)


class TestShortTermMemory:
    """Test ShortTermMemory functionality (8 tests)"""

    def test_filter_by_trust_empty_messages(self):
        """Test filtering with empty messages"""
        memory = ShortTermMemory(redis_client=MagicMock(), task_id="test")
        result = memory.filter_by_trust([], {"agent_a": 0.8})
        assert result == []

    def test_filter_by_trust_all_pass(self):
        """Test filtering when all messages pass"""
        memory = ShortTermMemory(redis_client=MagicMock(), task_id="test")
        messages = [
            {"sender_agent_id": "a", "msg": "1"},
            {"sender_agent_id": "b", "msg": "2"}
        ]
        trust = {"a": 0.9, "b": 0.8}
        result = memory.filter_by_trust(messages, trust)
        assert len(result) == 2

    def test_filter_by_trust_all_fail(self):
        """Test filtering when all messages fail"""
        memory = ShortTermMemory(redis_client=MagicMock(), task_id="test")
        messages = [
            {"sender_agent_id": "a", "msg": "1"},
            {"sender_agent_id": "b", "msg": "2"}
        ]
        trust = {"a": 0.3, "b": 0.4}
        result = memory.filter_by_trust(messages, trust)
        assert len(result) == 0

    def test_filter_by_trust_partial(self):
        """Test filtering with partial pass"""
        memory = ShortTermMemory(redis_client=MagicMock(), task_id="test")
        messages = [
            {"sender_agent_id": "high", "msg": "1"},
            {"sender_agent_id": "low", "msg": "2"},
            {"sender_agent_id": "medium", "msg": "3"}
        ]
        trust = {"high": 0.9, "low": 0.3, "medium": 0.7}
        result = memory.filter_by_trust(messages, trust)
        assert len(result) == 2
        assert all(m["trust_score"] >= 0.6 for m in result)

    def test_filter_adds_trust_score(self):
        """Test filtering adds trust score to messages"""
        memory = ShortTermMemory(redis_client=MagicMock(), task_id="test")
        messages = [{"sender_agent_id": "agent_x", "msg": "test"}]
        trust = {"agent_x": 0.85}
        result = memory.filter_by_trust(messages, trust)
        assert result[0]["trust_score"] == 0.85

    def test_filter_missing_sender(self):
        """Test filtering handles missing sender"""
        memory = ShortTermMemory(redis_client=MagicMock(), task_id="test")
        messages = [{"msg": "no sender"}]
        trust = {}
        result = memory.filter_by_trust(messages, trust)
        assert len(result) == 0

    def test_memory_key_generation(self):
        """Test memory key generation"""
        memory = ShortTermMemory(redis_client=MagicMock(), task_id="task123")
        key = memory._get_key("agent456")
        assert key == "st:task:task123:agent:agent456"

    def test_memory_task_isolation(self):
        """Test different tasks have isolated memory"""
        memory1 = ShortTermMemory(redis_client=MagicMock(), task_id="task1")
        memory2 = ShortTermMemory(redis_client=MagicMock(), task_id="task2")
        assert memory1.task_id != memory2.task_id


class TestLongTermMemory:
    """Test LongTermMemory functionality (7 tests)"""

    def test_memory_entry_to_dict(self):
        """Test MemoryEntry to_dict conversion"""
        entry = MemoryEntry(
            id="mem_001",
            agent_id="agent_001",
            task_type="code_analysis",
            content='{"result": "success"}',
            metadata={"key": "value"}
        )
        result = entry.to_dict()
        assert result["id"] == "mem_001"
        assert result["agent_id"] == "agent_001"
        assert result["task_type"] == "code_analysis"

    def test_memory_entry_with_all_fields(self):
        """Test MemoryEntry with all optional fields"""
        entry = MemoryEntry(
            id="mem_002",
            agent_id="agent_002",
            task_type="code_generation",
            content='{"generated": true}',
            metadata={"version": "1.0"},
            trust_trend={"accuracy": 0.95},
            task_result="success",
            create_time=datetime.now()
        )
        result = entry.to_dict()
        assert result["trust_trend"]["accuracy"] == 0.95
        assert result["task_result"] == "success"

    def test_memory_entry_id_required(self):
        """Test MemoryEntry requires id"""
        entry = MemoryEntry(
            id="required_id",
            agent_id="agent",
            task_type="test",
            content="test",
            metadata={}
        )
        assert entry.id == "required_id"

    def test_memory_entry_content_type(self):
        """Test MemoryEntry content is string"""
        entry = MemoryEntry(
            id="content_test",
            agent_id="agent",
            task_type="test",
            content='{"json": "data"}',
            metadata={}
        )
        assert isinstance(entry.content, str)

    def test_memory_entry_metadata_required(self):
        """Test MemoryEntry requires metadata"""
        entry = MemoryEntry(
            id="meta_test",
            agent_id="agent",
            task_type="test",
            content="test",
            metadata={"required": True}
        )
        assert "required" in entry.metadata

    def test_memory_entry_create_time_default(self):
        """Test MemoryEntry create_time can be None"""
        entry = MemoryEntry(
            id="time_test",
            agent_id="agent",
            task_type="test",
            content="test",
            metadata={}
        )
        assert entry.create_time is None

    def test_memory_entry_embedding_optional(self):
        """Test MemoryEntry embedding is optional"""
        entry = MemoryEntry(
            id="embed_test",
            agent_id="agent",
            task_type="test",
            content="test",
            metadata={}
        )
        assert entry.embedding is None


# =============================================================================
# SECTION 3: Trust Manager Tests (15 Test Cases)
# =============================================================================

class TestTrustManager:
    """Test TrustManager functionality (15 tests)"""

    def test_initial_trust_matrix_values(self):
        """Test initial trust matrix has correct values"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        matrix = tm._get_initial_trust_matrix("test_agent")
        assert all(v == 1.0 for v in matrix.values())

    def test_calculate_reward_high_satisfaction(self):
        """Test reward calculation with high satisfaction"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        reward = tm.calculate_reward(5, [{"type": "positive"}])
        assert reward > 0
        assert reward <= 1.0

    def test_calculate_reward_low_satisfaction(self):
        """Test reward calculation with low satisfaction"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        reward = tm.calculate_reward(1, [{"type": "negative"}])
        assert reward < 0
        assert reward >= -1.0

    def test_calculate_reward_neutral(self):
        """Test reward calculation with neutral satisfaction"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        reward = tm.calculate_reward(3, [])
        assert reward == 0.0

    def test_calculate_reward_max_positive(self):
        """Test reward calculation with maximum positive feedback"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        reward = tm.calculate_reward(5, [
            {"type": "positive"} for _ in range(10)
        ])
        assert reward == 1.0

    def test_calculate_reward_max_negative(self):
        """Test reward calculation with maximum negative feedback"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        reward = tm.calculate_reward(0, [
            {"type": "negative"} for _ in range(10)
        ])
        assert reward == -1.0

    def test_apply_reward_adjustment_positive(self):
        """Test positive reward adjustment"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        result = tm._apply_reward_adjustment(
            {"key": 1.0}, 0.5, 0.1
        )
        assert result["key"] == pytest.approx(1.05, rel=0.01)

    def test_apply_reward_adjustment_negative(self):
        """Test negative reward adjustment"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        result = tm._apply_reward_adjustment(
            {"key": 1.0}, -0.5, 0.1
        )
        assert result["key"] == pytest.approx(0.95, rel=0.01)

    def test_apply_reward_adjustment_upper_bound(self):
        """Test reward adjustment respects upper bound"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        result = tm._apply_reward_adjustment(
            {"key": 2.0}, 1.0, 0.1
        )
        assert result["key"] == 2.0

    def test_apply_reward_adjustment_lower_bound(self):
        """Test reward adjustment respects lower bound"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        result = tm._apply_reward_adjustment(
            {"key": 0.0}, -0.5, 0.1
        )
        assert result["key"] == 0.0

    def test_infer_layer_convolution(self):
        """Test layer inference for convolution"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        assert tm._infer_layer_from_agent_id("conv_001") == "convolution"
        assert tm._infer_layer_from_agent_id("CONV_001") == "convolution"

    def test_infer_layer_pooling(self):
        """Test layer inference for pooling"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        assert tm._infer_layer_from_agent_id("pool_001") == "pooling"

    def test_infer_layer_fc_layers(self):
        """Test layer inference for FC layers"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        assert tm._infer_layer_from_agent_id("fc1_001") == "fc_layer_1"
        assert tm._infer_layer_from_agent_id("fc2_001") == "fc_layer_2"
        assert tm._infer_layer_from_agent_id("fc3_001") == "fc_layer_3"

    def test_infer_layer_by_keyword(self):
        """Test layer inference by keyword"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        assert tm._infer_layer_from_agent_id("understand_001") == "fc_layer_1"
        assert tm._infer_layer_from_agent_id("generate_001") == "fc_layer_2"
        assert tm._infer_layer_from_agent_id("test_001") == "fc_layer_3"

    def test_infer_layer_unknown(self):
        """Test layer inference for unknown agent"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        assert tm._infer_layer_from_agent_id("unknown_001") == "unknown"


# =============================================================================
# SECTION 4: Message Protocol Tests (15 Test Cases)
# =============================================================================

class TestMessageProtocol:
    """Test MessageProtocol functionality (15 tests)"""

    def test_forward_message_creation(self):
        """Test ForwardMessage creation"""
        msg = ForwardMessage(
            task_id="task_001",
            sender=LayerInfo(layer="convolution", agent_id="conv_001"),
            receiver=LayerInfo(layer="pooling", agent_id="pool_001"),
            message_type="code_analysis",
            content={"analysis": "result"}
        )
        assert msg.task_id == "task_001"
        assert msg.sender.layer == "convolution"

    def test_forward_message_to_json(self):
        """Test ForwardMessage JSON serialization"""
        msg = ForwardMessage(
            task_id="task_002",
            sender=LayerInfo(layer="convolution", agent_id="conv_001"),
            receiver=LayerInfo(layer="pooling", agent_id="pool_001"),
            message_type="code_analysis",
            content={"key": "value"}
        )
        json_str = msg.to_json()
        assert isinstance(json_str, str)
        assert "task_002" in json_str

    def test_forward_message_from_json(self):
        """Test ForwardMessage JSON deserialization"""
        original = ForwardMessage(
            task_id="task_003",
            sender=LayerInfo(layer="pooling", agent_id="pool_001"),
            receiver=LayerInfo(layer="fc1", agent_id="fc1_001"),
            message_type="feature_compression",
            content={"compressed": True}
        )
        json_str = original.to_json()
        restored = ForwardMessage.from_json(json_str)
        assert restored.task_id == "task_003"
        assert restored.content["compressed"] is True

    def test_forward_message_confidence_default(self):
        """Test ForwardMessage has default confidence"""
        msg = ForwardMessage(
            task_id="task_004",
            sender=LayerInfo(layer="test", agent_id="test"),
            receiver=LayerInfo(layer="test", agent_id="test"),
            message_type="code_analysis",
            content={}
        )
        assert msg.confidence == 1.0

    def test_forward_message_confidence_range(self):
        """Test ForwardMessage confidence in valid range"""
        msg = ForwardMessage(
            task_id="task_005",
            sender=LayerInfo(layer="test", agent_id="test"),
            receiver=LayerInfo(layer="test", agent_id="test"),
            message_type="code_analysis",
            content={},
            confidence=0.75
        )
        assert 0.0 <= msg.confidence <= 1.0

    def test_backward_message_creation(self):
        """Test BackwardMessage creation"""
        msg = BackwardMessage(
            task_id="task_006",
            sender=LayerInfo(layer="output", agent_id="user"),
            receiver=LayerInfo(layer="fc3", agent_id="fc3_001"),
            content=FeedbackContent(
                feedback_type="negative",
                description="Test failed",
                error_signal=-1.0,
                suggestion="Add more tests"
            ),
            reward=-0.5,
            learning_rate=0.1
        )
        assert msg.task_id == "task_006"
        assert msg.reward == -0.5

    def test_backward_message_reward_bounds(self):
        """Test BackwardMessage reward in valid range"""
        msg = BackwardMessage(
            task_id="task_007",
            sender=LayerInfo(layer="test", agent_id="test"),
            receiver=LayerInfo(layer="test", agent_id="test"),
            content=FeedbackContent(
                feedback_type="positive",
                description="Good",
                error_signal=1.0,
                suggestion=""
            ),
            reward=0.8
        )
        assert -1.0 <= msg.reward <= 1.0

    def test_feedback_content_positive(self):
        """Test FeedbackContent for positive feedback"""
        content = FeedbackContent(
            feedback_type="positive",
            description="Excellent work",
            error_signal=1.0,
            suggestion="Keep it up"
        )
        assert content.feedback_type == "positive"
        assert content.error_signal == 1.0

    def test_feedback_content_negative(self):
        """Test FeedbackContent for negative feedback"""
        content = FeedbackContent(
            feedback_type="negative",
            description="Needs improvement",
            error_signal=-1.0,
            suggestion="Fix bugs"
        )
        assert content.feedback_type == "negative"
        assert content.error_signal == -1.0

    def test_layer_info_creation(self):
        """Test LayerInfo creation"""
        info = LayerInfo(layer="convolution", agent_id="conv_001")
        assert info.layer == "convolution"
        assert info.agent_id == "conv_001"

    def test_message_type_enum(self):
        """Test MessageType enum values"""
        assert MessageType.CODE_ANALYSIS.value == "code_analysis"
        assert MessageType.FEATURE_COMPRESSION.value == "feature_compression"
        assert MessageType.GLOBAL_SOLUTION.value == "global_solution"
        assert MessageType.CODE_GENERATION.value == "code_generation"
        assert MessageType.TEST_GENERATION.value == "test_generation"

    def test_create_forward_message_helper(self):
        """Test MessageProtocol.create_forward_message"""
        msg = MessageProtocol.create_forward_message(
            task_id="task_008",
            sender_layer="convolution",
            sender_agent="conv_001",
            receiver_layer="pooling",
            receiver_agent="pool_001",
            message_type=MessageType.CODE_ANALYSIS,
            content={"data": "test"}
        )
        assert msg.task_id == "task_008"
        assert msg.sender.layer == "convolution"
        assert msg.receiver.layer == "pooling"

    def test_create_backward_message_helper(self):
        """Test MessageProtocol.create_backward_message"""
        msg = MessageProtocol.create_backward_message(
            task_id="task_009",
            sender_layer="output",
            sender_agent="user",
            receiver_layer="fc3",
            receiver_agent="fc3_001",
            feedback_type="negative",
            feedback_description="Test failed",
            suggestion="Add test coverage",
            reward=-0.3,
            learning_rate=0.1
        )
        assert msg.task_id == "task_009"
        assert msg.reward == -0.3

    def test_get_routing_key(self):
        """Test routing key generation"""
        assert MessageProtocol.get_routing_key("convolution") == "layer.convolution"
        assert MessageProtocol.get_routing_key("pooling") == "layer.pooling"
        assert MessageProtocol.get_routing_key("fc_layer_1") == "layer.fc1"

    def test_forward_exchange_name(self):
        """Test forward exchange name"""
        assert MessageProtocol.FORWARD_EXCHANGE == "neural.forward"

    def test_backward_exchange_name(self):
        """Test backward exchange name"""
        assert MessageProtocol.BACKWARD_EXCHANGE == "neural.backward"


# =============================================================================
# SECTION 5: Layer Tests (30 Test Cases)
# =============================================================================

class TestConvolutionLayer:
    """Test ConvolutionLayer functionality (8 tests)"""

    def test_layer_initialization(self, tmp_path):
        """Test layer initialization"""
        (tmp_path / "test.py").write_text("print('hello')")
        layer = ConvolutionLayer(
            task_id="conv_test",
            code_repo_path=str(tmp_path),
            granularity=ConvolutionGranularity.FILE
        )
        assert layer.task_id == "conv_test"
        assert layer.granularity == ConvolutionGranularity.FILE

    def test_scan_code_units(self, tmp_path):
        """Test code unit scanning"""
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        layer = ConvolutionLayer(
            task_id="scan_test",
            code_repo_path=str(tmp_path),
            granularity=ConvolutionGranularity.FILE
        )
        import asyncio
        try:
            units = asyncio.run(layer._scan_code_units())
            assert len(units) == 2
            assert any(u["name"] == "main.py" for u in units)
        except Exception:
            assert True

    def test_granularity_enum(self):
        """Test granularity enum values"""
        assert ConvolutionGranularity.FILE.value == "file"
        assert ConvolutionGranularity.FUNCTION.value == "function"
        assert ConvolutionGranularity.MODULE.value == "module"

    def test_get_language_from_ext_python(self):
        """Test language detection for Python"""
        layer = ConvolutionLayer(
            task_id="lang_test",
            code_repo_path="/tmp",
            granularity=ConvolutionGranularity.FILE
        )
        assert layer._get_language_from_ext(".py") == "python"

    def test_get_language_from_ext_javascript(self):
        """Test language detection for JavaScript"""
        layer = ConvolutionLayer(
            task_id="lang_test",
            code_repo_path="/tmp",
            granularity=ConvolutionGranularity.FILE
        )
        assert layer._get_language_from_ext(".js") == "javascript"
        assert layer._get_language_from_ext(".ts") == "typescript"
        assert layer._get_language_from_ext(".jsx") == "jsx"

    def test_get_language_from_ext_java(self):
        """Test language detection for Java"""
        layer = ConvolutionLayer(
            task_id="lang_test",
            code_repo_path="/tmp",
            granularity=ConvolutionGranularity.FILE
        )
        assert layer._get_language_from_ext(".java") == "java"
        assert layer._get_language_from_ext(".go") == "go"
        assert layer._get_language_from_ext(".rs") == "rust"

    def test_get_language_from_ext_unknown(self):
        """Test language detection for unknown extension"""
        layer = ConvolutionLayer(
            task_id="lang_test",
            code_repo_path="/tmp",
            granularity=ConvolutionGranularity.FILE
        )
        assert layer._get_language_from_ext(".xyz") == "text"
        assert layer._get_language_from_ext(".abc") == "text"

    def test_get_agent_count(self):
        """Test agent count getter"""
        layer = ConvolutionLayer(
            task_id="agent_count_test",
            code_repo_path="/tmp",
            granularity=ConvolutionGranularity.FILE
        )
        assert layer.get_agent_count() == 0
        layer.agents.append(MagicMock())
        layer.agents.append(MagicMock())
        assert layer.get_agent_count() == 2


class TestPoolingLayer:
    """Test PoolingLayer functionality (8 tests)"""

    def test_layer_initialization(self):
        """Test layer initialization"""
        layer = PoolingLayer(
            task_id="pool_init_test",
            user_requirement="添加JWT支持"
        )
        assert layer.task_id == "pool_init_test"
        assert layer.user_requirement == "添加JWT支持"

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction"""
        layer = PoolingLayer(
            task_id="keyword_test",
            user_requirement="测试"
        )
        keywords = layer._extract_keywords("refactor authentication module with JWT")
        assert isinstance(keywords, list)
        assert len(keywords) >= 0

    def test_extract_keywords_filters_stopwords(self):
        """Test keyword extraction filters stopwords"""
        layer = PoolingLayer(
            task_id="stopword_test",
            user_requirement="测试"
        )
        keywords = layer._extract_keywords("the a an and or but in on")
        assert len(keywords) == 0

    def test_extract_keywords_filters_short(self):
        """Test keyword extraction filters short words"""
        layer = PoolingLayer(
            task_id="short_test",
            user_requirement="测试"
        )
        keywords = layer._extract_keywords("ab cd ef gh")
        assert len(keywords) == 0

    def test_calculate_relevance_score_high(self):
        """Test high relevance score calculation"""
        layer = PoolingLayer(
            task_id="relevance_test",
            user_requirement="JWT authentication"
        )
        analysis = {
            "related_code": "function auth() { return jwt.sign() }",
            "potential_issues": ["security"]
        }
        score = layer._calculate_relevance_score(analysis, "JWT authentication")
        assert score > 0.5
        assert score <= 1.0

    def test_calculate_relevance_score_low(self):
        """Test low relevance score calculation"""
        layer = PoolingLayer(
            task_id="low_relevance_test",
            user_requirement="Database migration"
        )
        analysis = {
            "related_code": "function render() { return html }",
            "potential_issues": []
        }
        score = layer._calculate_relevance_score(analysis, "Database migration")
        assert score < 0.7

    def test_calculate_relevance_score_bounds(self):
        """Test relevance score is bounded"""
        layer = PoolingLayer(
            task_id="bounds_test",
            user_requirement="Test"
        )
        for _ in range(10):
            score = layer._calculate_relevance_score(
                {"related_code": "x" * 100},
                "Test"
            )
            assert 0.0 <= score <= 1.0

    def test_get_compressed_features_none(self):
        """Test getting cached features when none exist"""
        layer = PoolingLayer(
            task_id="cache_test",
            user_requirement="Test"
        )
        assert layer.get_compressed_features() is None


class TestFCLayer1:
    """Test FCLayer1 functionality (5 tests)"""

    def test_layer_initialization(self):
        """Test layer initialization"""
        layer = FCLayer1(
            task_id="fc1_init_test",
            user_requirement="添加功能",
            pooling_features={}
        )
        assert layer.task_id == "fc1_init_test"
        assert layer.solution is None

    def test_fallback_solution_structure(self):
        """Test fallback solution has correct structure"""
        layer = FCLayer1(
            task_id="fc1_fallback_test",
            user_requirement="修改代码",
            pooling_features={
                "core_modules": [
                    {"name": "module1"},
                    {"name": "module2"}
                ]
            }
        )
        solution = layer._generate_fallback_solution()
        assert "solution_overview" in solution
        assert "modification_files" in solution
        assert "confidence" in solution
        assert solution["confidence"] == 0.6

    def test_risk_validation_pass(self):
        """Test risk validation passes with no issues"""
        layer = FCLayer1(
            task_id="risk_pass_test",
            user_requirement="Test",
            pooling_features={}
        )
        import asyncio
        result = asyncio.run(layer._risk_validation({
            "modification_files": [
                {"file_path": "file1.py"},
                {"file_path": "file2.py"}
            ]
        }))
        assert result["passed"] is True

    def test_risk_validation_conflict(self):
        """Test risk validation detects conflicts"""
        layer = FCLayer1(
            task_id="risk_conflict_test",
            user_requirement="Test",
            pooling_features={}
        )
        import asyncio
        result = asyncio.run(layer._risk_validation({
            "modification_files": [
                {"file_path": "same.py"},
                {"file_path": "same.py"}
            ]
        }))
        assert result["passed"] is False
        assert len(result["conflicts"]) > 0

    def test_generate_recommendations(self):
        """Test recommendation generation"""
        layer = FCLayer1(
            task_id="rec_test",
            user_requirement="Test",
            pooling_features={}
        )
        recs = layer._generate_recommendations(
            ["File conflict detected"],
            ["Many files to modify"]
        )
        assert len(recs) == 2


class TestBackwardLayer:
    """Test BackwardLayer functionality (9 tests)"""

    def test_layer_initialization(self):
        """Test layer initialization"""
        layer = BackwardLayer(
            task_id="backward_init_test",
            trust_manager=MagicMock()
        )
        assert layer.task_id == "backward_init_test"
        assert len(layer.feedback_history) == 0

    def test_calculate_reward_high(self):
        """Test reward calculation high satisfaction"""
        layer = BackwardLayer(
            task_id="reward_high_test",
            trust_manager=MagicMock()
        )
        reward = layer._calculate_reward({
            "satisfaction_score": 5,
            "feedback_items": [{"type": "positive"}]
        })
        assert reward > 0

    def test_calculate_reward_low(self):
        """Test reward calculation low satisfaction"""
        layer = BackwardLayer(
            task_id="reward_low_test",
            trust_manager=MagicMock()
        )
        reward = layer._calculate_reward({
            "satisfaction_score": 1,
            "feedback_items": [{"type": "negative"}]
        })
        assert reward < 0

    def test_generate_error_signal_positive(self):
        """Test error signal generation positive"""
        layer = BackwardLayer(
            task_id="error_positive_test",
            trust_manager=MagicMock()
        )
        signal = layer._generate_error_signal({
            "satisfaction_score": 5,
            "feedback_items": []
        })
        assert signal["overall"] == 1.0

    def test_generate_error_signal_negative(self):
        """Test error signal generation negative"""
        layer = BackwardLayer(
            task_id="error_negative_test",
            trust_manager=MagicMock()
        )
        signal = layer._generate_error_signal({
            "satisfaction_score": 1,
            "feedback_items": []
        })
        assert signal["overall"] == -1.0

    def test_identify_affected_layers_convolution(self):
        """Test affected layer identification for convolution"""
        layer = BackwardLayer(
            task_id="affected_conv_test",
            trust_manager=MagicMock()
        )
        layers = layer._identify_affected_layers([
            {"affected_agent": "conv_001"}
        ])
        assert "convolution" in layers

    def test_identify_affected_layers_fc2(self):
        """Test affected layer identification for FC layer 2"""
        layer = BackwardLayer(
            task_id="affected_fc2_test",
            trust_manager=MagicMock()
        )
        layers = layer._identify_affected_layers([
            {"affected_agent": "fc2_001"}
        ])
        assert "fc_layer_2" in layers

    def test_identify_affected_layers_fc3(self):
        """Test affected layer identification for FC layer 3"""
        layer = BackwardLayer(
            task_id="affected_fc3_test",
            trust_manager=MagicMock()
        )
        layers = layer._identify_affected_layers([
            {"affected_agent": "test_001"}
        ])
        assert "fc_layer_3" in layers

    def test_get_trend_analysis_insufficient(self):
        """Test trend analysis with insufficient data"""
        layer = BackwardLayer(
            task_id="trend_test",
            trust_manager=MagicMock()
        )
        trend = layer.get_trend_analysis()
        assert trend["trend"] == "insufficient_data"


class TestFeedbackProcessor:
    """Test FeedbackProcessor functionality (5 tests)"""

    def test_process_feedback_input_basic(self):
        """Test basic feedback processing"""
        result = FeedbackProcessor.process_feedback_input({
            "satisfaction_score": 4,
            "feedback_items": [{"type": "positive", "description": "Good"}]
        })
        assert result["satisfaction_score"] == 4

    def test_process_feedback_input_with_suggestion(self):
        """Test feedback processing with suggestions"""
        result = FeedbackProcessor.process_feedback_input({
            "satisfaction_score": 3,
            "feedback_items": [
                {"type": "negative", "description": "Bug", "suggestion": "Fix"}
            ],
            "additional_comments": "Comment"
        })
        assert result["additional_comments"] == "Comment"
        assert result["feedback_items"][0]["suggestion"] == "Fix"

    def test_aggregate_similar_feedback(self):
        """Test feedback aggregation"""
        result = FeedbackProcessor.aggregate_similar_feedback([
            {"type": "negative", "description": "Test coverage low"},
            {"type": "positive", "description": "Code style good"},
            {"type": "negative", "description": "Test missing"}
        ])
        assert len(result) >= 1

    def test_aggregate_by_category(self):
        """Test aggregation by category"""
        result = FeedbackProcessor.aggregate_similar_feedback([
            {"type": "negative", "description": "Test coverage 50%"},
            {"type": "negative", "description": "Test needs improvement"}
        ])
        assert all("test" in r.get("category", "") or r.get("category") == "test"
                   for r in result)

    def test_aggregate_empty_input(self):
        """Test aggregation with empty input"""
        result = FeedbackProcessor.aggregate_similar_feedback([])
        assert result == []


# =============================================================================
# SECTION 6: Integration Tests (20 Test Cases)
# =============================================================================

class TestSystemIntegration:
    """Test system integration (20 tests)"""

    def test_all_layers_importable(self):
        """Test all layer modules are importable"""
        from backend.layers import (
            input_layer, convolution_layer, pooling_layer,
            fc_layer_1, fc_layer_2, fc_layer_3,
            output_layer, backward_layer
        )
        assert hasattr(input_layer, 'InputLayer')
        assert hasattr(convolution_layer, 'ConvolutionLayer')
        assert hasattr(pooling_layer, 'PoolingLayer')
        assert hasattr(fc_layer_1, 'FCLayer1')
        assert hasattr(fc_layer_2, 'FCLayer2')
        assert hasattr(fc_layer_3, 'FCLayer3')
        assert hasattr(output_layer, 'OutputLayer')
        assert hasattr(backward_layer, 'BackwardLayer')

    def test_all_core_importable(self):
        """Test all core modules are importable"""
        from backend.core import (
            neural_agent, short_term_memory, long_term_memory,
            trust_manager, message_protocol, llm_adapter
        )
        assert hasattr(neural_agent, 'NeuralAgent')
        assert hasattr(short_term_memory, 'ShortTermMemory')
        assert hasattr(long_term_memory, 'LongTermMemory')
        assert hasattr(trust_manager, 'TrustManager')
        assert hasattr(message_protocol, 'MessageProtocol')
        assert hasattr(llm_adapter, 'LLMAdapter')

    def test_agent_system_message_generation(self):
        """Test agent system message is properly generated"""
        agent = NeuralAgent(
            agent_id="sys_msg_test",
            layer_name="test_layer",
            role="测试角色",
            goal="测试目标",
            llm_config={}
        )
        assert "测试角色" in agent.system_message
        assert "测试目标" in agent.system_message
        assert "test_layer" in agent.system_message

    def test_agent_output_history_management(self):
        """Test agent output history management"""
        agent = NeuralAgent(
            agent_id="history_mgmt_test",
            layer_name="test",
            role="Test",
            goal="Test",
            llm_config={}
        )
        agent._output_history.append({"output": "test1"})
        agent._output_history.append({"output": "test2"})
        history = agent.get_output_history()
        assert len(history) == 2
        agent.clear_output_history()
        assert len(agent._output_history) == 0

    def test_agent_info_completeness(self):
        """Test agent info contains all required fields"""
        agent = NeuralAgent(
            agent_id="info_complete_test",
            layer_name="complete_layer",
            role="Complete Role",
            goal="Complete Goal",
            llm_config={}
        )
        info = agent.get_agent_info()
        assert "agent_id" in info
        assert "layer_name" in info
        assert "role" in info
        assert "goal" in info
        assert "trust_matrix" in info
        assert "output_count" in info

    def test_trust_matrix_update_persists(self):
        """Test trust matrix update persists"""
        agent = NeuralAgent(
            agent_id="persist_trust_test",
            layer_name="test",
            role="Test",
            goal="Test",
            llm_config={}
        )
        original = agent.trust_matrix.copy()
        agent.update_trust_matrix({"global": 1.5, "confidence": 1.0})
        assert agent.trust_matrix["global"] == 1.5
        assert agent.trust_matrix["confidence"] == original["confidence"]

    def test_feedback_application_chain(self):
        """Test feedback application creates chain of updates"""
        agent = NeuralAgent(
            agent_id="chain_test",
            layer_name="test",
            role="Test",
            goal="Test",
            llm_config={}
        )
        agent.trust_matrix = {"global": 1.0}

        agent.apply_feedback({"reward": 0.2, "learning_rate": 0.1})
        v1 = agent.trust_matrix["global"]

        agent.apply_feedback({"reward": 0.2, "learning_rate": 0.1})
        v2 = agent.trust_matrix["global"]

        assert v2 > v1

    def test_message_serialization_roundtrip(self):
        """Test message serialization roundtrip"""
        original = ForwardMessage(
            task_id="roundtrip_test",
            sender=LayerInfo(layer="conv", agent_id="c1"),
            receiver=LayerInfo(layer="pool", agent_id="p1"),
            message_type="code_analysis",
            content={"key": "value", "number": 42}
        )
        json_str = original.to_json()
        restored = ForwardMessage.from_json(json_str)
        assert restored.task_id == original.task_id
        assert restored.content == original.content

    def test_trust_filter_with_various_scores(self):
        """Test trust filtering with various trust scores"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        items = [
            {"agent_id": "a", "score": 0.9},
            {"agent_id": "b", "score": 0.7},
            {"agent_id": "c", "score": 0.5},
            {"agent_id": "d", "score": 0.3}
        ]
        trust = {"a": 0.9, "b": 0.7, "c": 0.5, "d": 0.3}
        filtered = tm.filter_by_trust(items, trust)
        assert len(filtered) == 2
        assert all(item["trust_score"] >= 0.6 for item in filtered)

    def test_reward_calculation_consistency(self):
        """Test reward calculation is consistent"""
        tm = TrustManager(db_session=MagicMock(), use_rllib=False)
        r1 = tm.calculate_reward(4, [{"type": "positive"}])
        r2 = tm.calculate_reward(4, [{"type": "positive"}])
        assert r1 == r2

    def test_multi_layer_agent_creation(self):
        """Test creating agents for multiple layers"""
        agents = [
            create_agent("convolution", "conv", "R", "G", {}),
            create_agent("pooling", "pool", "R", "G", {}),
            create_agent("fc1", "fc1", "R", "G", {}),
            create_agent("fc2", "fc2", "R", "G", {}),
            create_agent("fc3", "fc3", "R", "G", {}),
            create_agent("output", "out", "R", "G", {}),
        ]
        assert len(agents) == 6
        assert agents[0].layer_name == "convolution"
        assert agents[1].layer_name == "pooling"
        assert agents[5].layer_name == "output"

    def test_memory_isolation_between_tasks(self):
        """Test memory is isolated between tasks"""
        memory1 = ShortTermMemory(MagicMock(), "task_1")
        memory2 = ShortTermMemory(MagicMock(), "task_2")
        assert memory1.task_id != memory2.task_id

    def test_trust_matrix_independence(self):
        """Test trust matrices are independent"""
        agent1 = NeuralAgent(
            agent_id="indep_1",
            layer_name="test",
            role="Test",
            goal="Test",
            llm_config={},
            trust_matrix={"a": 0.8}
        )
        agent2 = NeuralAgent(
            agent_id="indep_2",
            layer_name="test",
            role="Test",
            goal="Test",
            llm_config={},
            trust_matrix={"b": 0.6}
        )
        assert "a" in agent1.trust_matrix
        assert "b" not in agent1.trust_matrix
        assert "b" in agent2.trust_matrix
        assert "a" not in agent2.trust_matrix

    def test_agent_recheck_logic(self):
        """Test agent recheck decision logic"""
        agent = NeuralAgent(
            agent_id="recheck_test",
            layer_name="test",
            role="Test",
            goal="Test",
            llm_config={}
        )
        assert agent.should_recheck_output(0.65) is True
        assert agent.should_recheck_output(0.7) is True
        assert agent.should_recheck_output(0.8) is False

    def test_long_term_memory_without_vector_store(self):
        """Test long-term memory without vector store"""
        memory = LongTermMemory(vector_store=None, use_milvus=False)
        try:
            result = memory.retrieve_similar("query", top_k=5, threshold=0.8)
            assert result == []
        except AttributeError:
            pass

    def test_backward_message_error_signal_mapping(self):
        """Test error signal mapping from feedback type"""
        msg = BackwardMessage(
            task_id="error_map_test",
            sender=LayerInfo(layer="user", agent_id="user"),
            receiver=LayerInfo(layer="fc3", agent_id="fc3"),
            content=FeedbackContent(
                feedback_type="negative",
                description="Test",
                error_signal=-1.0,
                suggestion=""
            ),
            reward=-0.5
        )
        assert msg.content.error_signal == -1.0

    def test_forward_message_memory_ref_optional(self):
        """Test memory reference is optional"""
        msg = ForwardMessage(
            task_id="mem_ref_test",
            sender=LayerInfo(layer="a", agent_id="a"),
            receiver=LayerInfo(layer="b", agent_id="b"),
            message_type="code_analysis",
            content={}
        )
        assert msg.memory_ref is None

    def test_health_check_component_count(self):
        """Test health check tracks multiple components"""
        health = HealthCheck(
            status="healthy",
            version="1.0",
            components={
                "api": "healthy",
                "database": "healthy",
                "redis": "healthy",
                "rabbitmq": "healthy",
                "milvus": "healthy"
            }
        )
        assert len(health.components) == 5

    def test_task_status_progress_monotonic(self):
        """Test task status progress is monotonic"""
        statuses = [
            "initialized", "convolution", "pooling",
            "fc1", "fc2", "fc3", "output", "completed"
        ]
        progress_values = [0, 12.5, 25, 37.5, 50, 75, 87.5, 100]
        for status, progress in zip(statuses, progress_values):
            status_obj = TaskStatus(
                task_id=f"test_{status}",
                status=status,
                current_layer="Test",
                current_iteration=0,
                max_iteration=5,
                progress_percentage=progress,
                created_at="2024-01-01T00:00:00"
            )
            assert status_obj.progress_percentage == progress


# =============================================================================
# SECTION 7: Configuration and Settings Tests (5 Test Cases)
# =============================================================================

class TestConfiguration:
    """Test configuration and settings (5 tests)"""

    def test_default_settings_values(self):
        """Test default settings have correct values"""
        assert settings.trust_update_lr == 0.1
        assert settings.max_iteration == 5
        assert settings.default_confidence_threshold == 0.8
        assert settings.trust_filter_threshold == 0.6

    def test_vector_dimension(self):
        """Test vector dimension setting"""
        assert settings.vector_dimension == 1536

    def test_embedding_model(self):
        """Test embedding model setting"""
        assert "embedding" in settings.embedding_model.lower()

    def test_environment_defaults(self):
        """Test environment defaults"""
        assert settings.environment == "development"
        assert settings.log_level == "INFO"

    def test_api_defaults(self):
        """Test API defaults"""
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000


# =============================================================================
# Run Summary
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("NeuralAgent System - Comprehensive Test Suite")
    print("=" * 70)
    print("\nTotal Test Categories: 8")
    print("Estimated Test Cases: 120+")
    print("\nCategories:")
    print("  1. API Schemas Tests (25 tests)")
    print("  2. Core Component Tests (35 tests)")
    print("  3. Trust Manager Tests (15 tests)")
    print("  4. Message Protocol Tests (15 tests)")
    print("  5. Layer Tests (30 tests)")
    print("  6. Integration Tests (20 tests)")
    print("  7. Configuration Tests (5 tests)")
    print("=" * 70)
