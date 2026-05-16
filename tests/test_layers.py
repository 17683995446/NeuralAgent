"""Unit tests for layer implementations."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.core.neural_layers.neural_convolution_layer import ConvolutionLayer, ConvolutionGranularity
from backend.core.neural_layers.neural_pooling_layer import PoolingLayer
from backend.core.neural_layers.neural_fully_connected_layers import FCLayer1
from backend.core.neural_layers.neural_fully_connected_layers import FCLayer2
from backend.core.neural_layers.neural_fully_connected_layers import FCLayer3
from backend.core.neural_layers.neural_output_layer import OutputLayer
from backend.core.neural_layers.neural_backward_propagation_layer import BackwardLayer, FeedbackProcessor


class TestConvolutionLayer:
    """Test cases for ConvolutionLayer class."""

    @pytest.fixture
    def convolution_layer(self, tmp_path):
        """Create ConvolutionLayer instance."""
        (tmp_path / "test.py").write_text("print('hello')")

        return ConvolutionLayer(
            task_id="test_task",
            code_repo_path=str(tmp_path),
            granularity=ConvolutionGranularity.FILE
        )

    def test_layer_initialization(self, convolution_layer):
        """Test layer initialization."""
        assert convolution_layer.task_id == "test_task"
        assert convolution_layer.granularity == ConvolutionGranularity.FILE
        assert len(convolution_layer.agents) == 0

    def test_scan_code_units(self, convolution_layer):
        """Test code unit scanning."""
        import asyncio
        units = asyncio.run(convolution_layer._scan_code_units())

        assert len(units) > 0
        assert any(u["type"] == "file" for u in units)
        assert any(u["name"] == "test.py" for u in units)

    def test_get_language_from_ext(self, convolution_layer):
        """Test language detection from extension."""
        assert convolution_layer._get_language_from_ext(".py") == "python"
        assert convolution_layer._get_language_from_ext(".js") == "javascript"
        assert convolution_layer._get_language_from_ext(".java") == "java"
        assert convolution_layer._get_language_from_ext(".unknown") == "text"


class TestPoolingLayer:
    """Test cases for PoolingLayer class."""

    @pytest.fixture
    def pooling_layer(self):
        """Create PoolingLayer instance."""
        return PoolingLayer(
            task_id="test_task",
            user_requirement="重构用户认证模块"
        )

    def test_layer_initialization(self, pooling_layer):
        """Test layer initialization."""
        assert pooling_layer.task_id == "test_task"
        assert pooling_layer.user_requirement == "重构用户认证模块"

    def test_extract_keywords(self, pooling_layer):
        """Test keyword extraction."""
        text = "重构用户认证模块，添加JWT支持，优化性能"
        keywords = pooling_layer._extract_keywords(text)

        assert len(keywords) > 0
        assert any("jwt" in k for k in keywords)

    def test_calculate_relevance_score(self, pooling_layer):
        """Test relevance score calculation."""
        analysis = {
            "related_code": "function authenticate(user) { return jwt.sign() }",
            "potential_issues": ["security risk"]
        }
        user_requirement = "添加JWT支持"

        score = pooling_layer._calculate_relevance_score(
            analysis, user_requirement
        )

        assert 0 <= score <= 1


class TestFCLayer1:
    """Test cases for FC Layer 1 class."""

    @pytest.fixture
    def fc_layer_1(self):
        """Create FCLayer1 instance."""
        return FCLayer1(
            task_id="test_task",
            user_requirement="添加JWT认证",
            pooling_features={
                "architecture_overview": "微服务架构",
                "core_modules": [{"name": "auth"}],
            }
        )

    def test_layer_initialization(self, fc_layer_1):
        """Test layer initialization."""
        assert fc_layer_1.task_id == "test_task"
        assert fc_layer_1.solution is None

    def test_generate_fallback_solution(self, fc_layer_1):
        """Test fallback solution generation."""
        solution = fc_layer_1._generate_fallback_solution()

        assert "solution_overview" in solution
        assert "modification_files" in solution
        assert solution["confidence"] == 0.6


class TestFCLayer2:
    """Test cases for FC Layer 2 class."""

    @pytest.fixture
    def fc_layer_2(self, tmp_path):
        """Create FCLayer2 instance."""
        (tmp_path / "test.py").write_text("def hello(): pass")

        return FCLayer2(
            task_id="test_task",
            solution={
                "modification_files": [
                    {
                        "file_path": "test.py",
                        "modification_type": "modify",
                        "description": "Add JWT",
                    }
                ]
            },
            code_repo_path=str(tmp_path),
            output_dir=str(tmp_path / "output")
        )

    def test_layer_initialization(self, fc_layer_2):
        """Test layer initialization."""
        assert fc_layer_2.task_id == "test_task"
        assert len(fc_layer_2.code_changes) == 0
        assert len(fc_layer_2.failed_changes) == 0

    def test_get_language_from_path(self, fc_layer_2):
        """Test language detection from path."""
        from pathlib import Path

        assert fc_layer_2._get_language_from_path(
            Path("test.py")
        ) == "python"
        assert fc_layer_2._get_language_from_path(
            Path("test.js")
        ) == "javascript"


class TestOutputLayer:
    """Test cases for OutputLayer class."""

    @pytest.fixture
    def output_layer(self, tmp_path):
        """Create OutputLayer instance."""
        return OutputLayer(
            task_id="test_task",
            output_dir=str(tmp_path)
        )

    def test_layer_initialization(self, output_layer):
        """Test layer initialization."""
        assert output_layer.task_id == "test_task"
        assert output_layer.output_dir.exists()

    def test_get_language_from_path(self, output_layer):
        """Test language detection from path."""
        from pathlib import Path

        assert output_layer._get_language_from_path(
            Path("test.py")
        ) == "python"
        assert output_layer._get_language_from_path(
            Path("test.js")
        ) == "javascript"


class TestBackwardLayer:
    """Test cases for BackwardLayer class."""

    @pytest.fixture
    def backward_layer(self):
        """Create BackwardLayer instance."""
        return BackwardLayer(
            task_id="test_task",
            trust_manager=MagicMock()
        )

    def test_layer_initialization(self, backward_layer):
        """Test layer initialization."""
        assert backward_layer.task_id == "test_task"
        assert len(backward_layer.feedback_history) == 0

    def test_calculate_reward_high(self, backward_layer):
        """Test reward calculation with high satisfaction."""
        feedback = {
            "satisfaction_score": 5,
            "feedback_items": [
                {"type": "positive", "description": "Great work"}
            ]
        }

        reward = backward_layer._calculate_reward(feedback)

        assert reward > 0

    def test_calculate_reward_low(self, backward_layer):
        """Test reward calculation with low satisfaction."""
        feedback = {
            "satisfaction_score": 1,
            "feedback_items": [
                {"type": "negative", "description": "Poor quality"}
            ]
        }

        reward = backward_layer._calculate_reward(feedback)

        assert reward < 0

    def test_identify_affected_layers(self, backward_layer):
        """Test affected layer identification."""
        feedback_items = [
            {"affected_agent": "conv_001"},
            {"affected_agent": "fc2_001"},
        ]

        layers = backward_layer._identify_affected_layers(feedback_items)

        assert "convolution" in layers
        assert "fc_layer_2" in layers

    def test_get_trend_analysis_insufficient_data(self, backward_layer):
        """Test trend analysis with insufficient data."""
        trend = backward_layer.get_trend_analysis()

        assert trend["trend"] == "insufficient_data"


class TestFeedbackProcessor:
    """Test cases for FeedbackProcessor class."""

    def test_process_feedback_input(self):
        """Test feedback input processing."""
        input_data = {
            "satisfaction_score": 4,
            "feedback_items": [
                {"type": "positive", "description": "Good", "suggestion": "OK"}
            ],
            "additional_comments": "Great job"
        }

        processed = FeedbackProcessor.process_feedback_input(input_data)

        assert processed["satisfaction_score"] == 4
        assert len(processed["feedback_items"]) == 1
        assert processed["additional_comments"] == "Great job"

    def test_aggregate_similar_feedback(self):
        """Test feedback aggregation."""
        feedback_items = [
            {"type": "negative", "description": "Test coverage is low"},
            {"type": "positive", "description": "Code is clean"},
            {"type": "negative", "description": "Test missing for edge cases"},
        ]

        aggregated = FeedbackProcessor.aggregate_similar_feedback(feedback_items)

        assert len(aggregated) > 0
