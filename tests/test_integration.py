"""Integration tests for NeuralAgent System."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.api.schemas import TaskInput, FeedbackInput
from backend.core.neural_layers.neural_input_layer import InputLayer
from backend.core.trust_management.trust_manager import TrustManager


class TestAPIIntegration:
    """Integration tests for API layer."""

    def test_task_input_validation(self):
        """Test task input schema validation."""
        valid_input = TaskInput(
            task_id="test-task-001-valid",
            user_requirement="添加JWT支持",
            code_repo_url="https://github.com/example/repo.git",
            max_iteration=5,
            learning_rate=0.1
        )

        assert valid_input.task_id == "test-task-001-valid"
        assert valid_input.user_requirement == "添加JWT支持"
        assert valid_input.max_iteration == 5

    def test_task_input_defaults(self):
        """Test task input default values."""
        input_data = TaskInput(
            task_id="test-task-002-valid",
            user_requirement="修改代码"
        )

        assert input_data.target_branch == "main"
        assert input_data.max_iteration == 5
        assert input_data.learning_rate == 0.1

    def test_feedback_input_validation(self):
        """Test feedback input schema validation."""
        feedback = FeedbackInput(
            satisfaction_score=4,
            feedback_items=[
                {
                    "type": "positive",
                    "description": "代码质量好",
                    "suggestion": "继续优化"
                }
            ]
        )

        assert feedback.satisfaction_score == 4
        assert len(feedback.feedback_items) == 1


class TestLayerIntegration:
    """Integration tests for layer interactions."""

    def test_input_to_convolution_flow(self, tmp_path):
        """Test input layer to convolution layer flow."""
        (tmp_path / "main.py").write_text("print('hello')")

        input_layer = InputLayer(db_session=MagicMock())

        with patch.object(input_layer, '_prepare_code_repository', return_value=str(tmp_path)):
            import asyncio
            context = asyncio.run(input_layer.process_task_input(
                TaskInput(
                    task_id="integration-test",
                    user_requirement="测试流程",
                    local_code_path=str(tmp_path)
                )
            ))

        assert context.task_id == "integration-test"
        assert context.status == "initialized"

    def test_trust_update_flow(self):
        """Test trust update flow."""
        trust_manager = TrustManager(db_session=MagicMock(), use_rllib=False)

        reward = trust_manager.calculate_reward(
            satisfaction_score=4,
            feedback_items=[{"type": "positive", "description": "Good"}]
        )

        updated = trust_manager._apply_reward_adjustment(
            {"global": 1.0}, reward, 0.1
        )

        assert "global" in updated


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_flow_structure(self):
        """Test that all components are properly structured."""
        from backend.layers import (
            input_layer,
            convolution_layer,
            pooling_layer,
            fc_layer_1,
            fc_layer_2,
            fc_layer_3,
            output_layer,
            backward_layer
        )

        assert hasattr(input_layer, 'InputLayer')
        assert hasattr(convolution_layer, 'ConvolutionLayer')
        assert hasattr(pooling_layer, 'PoolingLayer')
        assert hasattr(fc_layer_1, 'FCLayer1')
        assert hasattr(fc_layer_2, 'FCLayer2')
        assert hasattr(fc_layer_3, 'FCLayer3')
        assert hasattr(output_layer, 'OutputLayer')
        assert hasattr(backward_layer, 'BackwardLayer')

    def test_core_components_structure(self):
        """Test that all core components are properly structured."""
        from backend.core import (
            neural_agent,
            short_term_memory,
            long_term_memory,
            trust_manager,
            message_protocol,
            llm_adapter
        )

        assert hasattr(neural_agent, 'NeuralAgent')
        assert hasattr(short_term_memory, 'ShortTermMemory')
        assert hasattr(long_term_memory, 'LongTermMemory')
        assert hasattr(trust_manager, 'TrustManager')
        assert hasattr(message_protocol, 'MessageProtocol')
        assert hasattr(llm_adapter, 'LLMAdapter')
