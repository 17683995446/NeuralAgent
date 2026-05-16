"""Unit tests for NeuralAgent core unit."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from backend.core.agents.intelligent_multi_agent_coordinator import (
    NeuralAgent,
    ConvolutionAgent,
    PoolingAgent,
    FCAgent,
    OutputAgent,
    create_agent
)


class TestNeuralAgent:
    """Test cases for NeuralAgent class."""

    def test_default_trust_matrix(self):
        """Test default trust matrix initialization."""
        agent = NeuralAgent(
            agent_id="test_agent",
            layer_name="test_layer",
            role="Tester",
            goal="Test things",
            llm_config={"model": "gpt-4"}
        )

        assert agent.trust_matrix == {
            "global": 1.0,
            "confidence": 1.0,
            "accuracy": 1.0,
            "reliability": 1.0,
        }

    def test_agent_info(self):
        """Test agent info retrieval."""
        agent = NeuralAgent(
            agent_id="info_test",
            layer_name="info_layer",
            role="Info Tester",
            goal="Get info",
            llm_config={"model": "gpt-4"}
        )

        info = agent.get_agent_info()

        assert info["agent_id"] == "info_test"
        assert info["layer_name"] == "info_layer"
        assert info["role"] == "Info Tester"
        assert info["output_count"] == 0

    def test_update_trust_matrix(self):
        """Test trust matrix update."""
        agent = NeuralAgent(
            agent_id="trust_test",
            layer_name="trust_layer",
            role="Trust Tester",
            goal="Test trust",
            llm_config={"model": "gpt-4"}
        )

        new_trust = {"global": 0.8, "confidence": 0.9}
        agent.update_trust_matrix(new_trust)

        assert agent.trust_matrix["global"] == 0.8
        assert agent.trust_matrix["confidence"] == 0.9

    def test_get_trust_score(self):
        """Test getting trust score for source agent."""
        agent = NeuralAgent(
            agent_id="score_test",
            layer_name="score_layer",
            role="Score Tester",
            goal="Test scores",
            llm_config={"model": "gpt-4"}
        )

        agent.trust_matrix = {
            "agent_a": 0.8,
            "agent_b": 0.5,
        }

        assert agent.get_trust_score("agent_a") == 0.8
        assert agent.get_trust_score("agent_b") == 0.5
        assert agent.get_trust_score("unknown") == 1.0

    def test_should_adopt_output(self):
        """Test output adoption decision."""
        agent = NeuralAgent(
            agent_id="adopt_test",
            layer_name="adopt_layer",
            role="Adopt Tester",
            goal="Test adoption",
            llm_config={"model": "gpt-4"}
        )

        assert agent.should_adopt_output(0.7) is True
        assert agent.should_adopt_output(0.5) is False

    def test_should_recheck_output(self):
        """Test output recheck decision."""
        agent = NeuralAgent(
            agent_id="recheck_test",
            layer_name="recheck_layer",
            role="Recheck Tester",
            goal="Test recheck",
            llm_config={"model": "gpt-4"}
        )

        assert agent.should_recheck_output(0.7) is True
        assert agent.should_recheck_output(0.8) is False

    def test_apply_feedback(self):
        """Test feedback application."""
        agent = NeuralAgent(
            agent_id="feedback_test",
            layer_name="feedback_layer",
            role="Feedback Tester",
            goal="Test feedback",
            llm_config={"model": "gpt-4"}
        )

        agent.trust_matrix = {"global": 1.0}

        feedback = {"reward": 0.5, "learning_rate": 0.1}
        updated = agent.apply_feedback(feedback)

        assert updated["global"] == pytest.approx(1.05, rel=0.01)

    def test_output_history(self):
        """Test output history management."""
        agent = NeuralAgent(
            agent_id="history_test",
            layer_name="history_layer",
            role="History Tester",
            goal="Test history",
            llm_config={"model": "gpt-4"}
        )

        agent._output_history.append({"test": "output1"})
        agent._output_history.append({"test": "output2"})

        history = agent.get_output_history()
        assert len(history) == 2

        agent.clear_output_history()
        assert len(agent._output_history) == 0


class TestAgentFactory:
    """Test cases for agent factory function."""

    def test_create_convolution_agent(self):
        """Test creating convolution agent."""
        agent = create_agent(
            agent_type="convolution",
            agent_id="conv_001",
            role="Conv Tester",
            goal="Test convolution",
            llm_config={"model": "gpt-4"}
        )

        assert isinstance(agent, ConvolutionAgent)
        assert agent.layer_name == "convolution"

    def test_create_pooling_agent(self):
        """Test creating pooling agent."""
        agent = create_agent(
            agent_type="pooling",
            agent_id="pool_001",
            role="Pool Tester",
            goal="Test pooling",
            llm_config={"model": "gpt-4"}
        )

        assert isinstance(agent, PoolingAgent)
        assert agent.layer_name == "pooling"

    def test_create_fc_agents(self):
        """Test creating FC layer agents."""
        fc1 = create_agent(
            agent_type="fc1",
            agent_id="fc1_001",
            role="FC1 Tester",
            goal="Test FC1",
            llm_config={"model": "gpt-4"}
        )
        assert isinstance(fc1, FCAgent)
        assert fc1.layer_name == "fc_layer_1"

        fc2 = create_agent(
            agent_type="fc2",
            agent_id="fc2_001",
            role="FC2 Tester",
            goal="Test FC2",
            llm_config={"model": "gpt-4"}
        )
        assert isinstance(fc2, FCAgent)
        assert fc2.layer_name == "fc_layer_2"

        fc3 = create_agent(
            agent_type="fc3",
            agent_id="fc3_001",
            role="FC3 Tester",
            goal="Test FC3",
            llm_config={"model": "gpt-4"}
        )
        assert isinstance(fc3, FCAgent)
        assert fc3.layer_name == "fc_layer_3"

    def test_create_output_agent(self):
        """Test creating output agent."""
        agent = create_agent(
            agent_type="output",
            agent_id="output_001",
            role="Output Tester",
            goal="Test output",
            llm_config={"model": "gpt-4"}
        )

        assert isinstance(agent, OutputAgent)
        assert agent.layer_name == "output"

    def test_create_default_agent(self):
        """Test creating default agent."""
        agent = create_agent(
            agent_type="unknown",
            agent_id="default_001",
            role="Default Tester",
            goal="Test default",
            llm_config={"model": "gpt-4"}
        )

        assert isinstance(agent, NeuralAgent)
