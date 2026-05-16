"""Unit tests for trust management."""
import pytest
from unittest.mock import MagicMock, patch
from backend.core.trust_management.trust_manager import TrustManager, TrustUpdate


class TestTrustManager:
    """Test cases for TrustManager class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def trust_manager(self, mock_db_session):
        """Create TrustManager instance."""
        return TrustManager(db_session=mock_db_session, use_rllib=False)

    def test_initial_trust_matrix(self, trust_manager):
        """Test initial trust matrix generation."""
        matrix = trust_manager._get_initial_trust_matrix("test_agent")

        assert matrix == {
            "global": 1.0,
            "confidence": 1.0,
            "accuracy": 1.0,
            "reliability": 1.0,
        }

    def test_calculate_reward_high_satisfaction(self, trust_manager):
        """Test reward calculation with high satisfaction."""
        reward = trust_manager.calculate_reward(
            satisfaction_score=5,
            feedback_items=[{"type": "positive", "description": "Good"}]
        )

        assert reward > 0
        assert reward <= 1.0

    def test_calculate_reward_low_satisfaction(self, trust_manager):
        """Test reward calculation with low satisfaction."""
        reward = trust_manager.calculate_reward(
            satisfaction_score=1,
            feedback_items=[{"type": "negative", "description": "Bad"}]
        )

        assert reward < 0
        assert reward >= -1.0

    def test_calculate_reward_neutral(self, trust_manager):
        """Test reward calculation with neutral satisfaction."""
        reward = trust_manager.calculate_reward(
            satisfaction_score=3,
            feedback_items=[]
        )

        assert reward == 0.0

    def test_calculate_reward_clamping(self, trust_manager):
        """Test reward value clamping."""
        reward = trust_manager.calculate_reward(
            satisfaction_score=5,
            feedback_items=[
                {"type": "positive"} for _ in range(20)
            ]
        )

        assert reward <= 1.0
        assert reward >= -1.0

    def test_apply_reward_adjustment(self, trust_manager):
        """Test reward adjustment application."""
        trust_weights = {"global": 1.0, "accuracy": 0.8}
        reward = 0.5
        learning_rate = 0.1

        adjusted = trust_manager._apply_reward_adjustment(
            trust_weights, reward, learning_rate
        )

        assert adjusted["global"] == pytest.approx(1.05, rel=0.01)
        assert adjusted["accuracy"] == pytest.approx(0.85, rel=0.01)

    def test_apply_reward_adjustment_bounds(self, trust_manager):
        """Test reward adjustment respects bounds."""
        trust_weights = {"global": 2.0}
        reward = 0.5
        learning_rate = 0.1

        adjusted = trust_manager._apply_reward_adjustment(
            trust_weights, reward, learning_rate
        )

        assert adjusted["global"] == 2.0

    def test_apply_negative_reward_adjustment(self, trust_manager):
        """Test negative reward adjustment."""
        trust_weights = {"global": 1.0}
        reward = -0.5
        learning_rate = 0.1

        adjusted = trust_manager._apply_reward_adjustment(
            trust_weights, reward, learning_rate
        )

        assert adjusted["global"] == pytest.approx(0.95, rel=0.01)

    def test_filter_by_trust(self, trust_manager):
        """Test filtering items by trust score."""
        items = [
            {"agent_id": "high_trust", "data": "a"},
            {"agent_id": "low_trust", "data": "b"},
            {"agent_id": "medium_trust", "data": "c"},
        ]

        trust_matrix = {
            "high_trust": 0.9,
            "low_trust": 0.4,
            "medium_trust": 0.7,
        }

        filtered = trust_manager.filter_by_trust(items, trust_matrix)

        assert len(filtered) == 2
        assert all(item["trust_score"] >= 0.6 for item in filtered)

    def test_filter_by_trust_empty_items(self, trust_manager):
        """Test filtering empty items list."""
        filtered = trust_manager.filter_by_trust([], {})

        assert len(filtered) == 0

    def test_infer_layer_from_agent_id(self, trust_manager):
        """Test layer inference from agent ID."""
        assert trust_manager._infer_layer_from_agent_id("conv_001") == "convolution"
        assert trust_manager._infer_layer_from_agent_id("pool_001") == "pooling"
        assert trust_manager._infer_layer_from_agent_id("fc1_001") == "fc_layer_1"
        assert trust_manager._infer_layer_from_agent_id("understand_001") == "fc_layer_1"
        assert trust_manager._infer_layer_from_agent_id("generate_001") == "fc_layer_2"
        assert trust_manager._infer_layer_from_agent_id("fc3_001") == "fc_layer_3"
        assert trust_manager._infer_layer_from_agent_id("test_001") == "fc_layer_3"
        assert trust_manager._infer_layer_from_agent_id("unknown_001") == "unknown"


class TestTrustUpdate:
    """Test cases for TrustUpdate dataclass."""

    def test_trust_update_creation(self):
        """Test TrustUpdate instance creation."""
        from datetime import datetime

        update = TrustUpdate(
            agent_id="test_agent",
            previous_trust={"global": 1.0},
            new_trust={"global": 1.1},
            reward=0.5,
            learning_rate=0.1,
            update_time=datetime.utcnow()
        )

        assert update.agent_id == "test_agent"
        assert update.reward == 0.5
        assert update.learning_rate == 0.1
