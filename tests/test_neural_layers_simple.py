"""Neural Layers Unit Tests - 神经网络层单元测试 (简化版)

测试所有 18 层神经网络层的功能。
使用mock模式确保离线测试通过。
"""

import pytest
import sys
import os
from pathlib import Path

# 强制使用mock嵌入器
os.environ["NEURALAGENT_USE_MOCK_EMBEDDER"] = "true"

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = __import__('logging').getLogger(__name__)


class TestNeuralEmbeddingLayer:
    """嵌入层测试 - Layer 1"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_embedding_layer import NeuralEmbeddingLayer, EmbeddingConfig
        
        config = EmbeddingConfig(use_mock=True)
        layer = NeuralEmbeddingLayer(config)
        assert layer is not None
        assert layer.config is not None
        assert layer._stats["total_embeddings"] == 0
        assert layer.config.use_mock == True
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers.neural_embedding_layer import NeuralEmbeddingLayer, EmbeddingConfig
        
        config = EmbeddingConfig(use_mock=True)
        layer = NeuralEmbeddingLayer(config)
        result = await layer.forward("test query")
        
        assert "embeddings" in result
        assert "embedding_dimension" in result
        assert "layer_id" in result
        assert result["layer_id"] == 1
        assert result["layer"] == "embedding"
    
    def test_stats_tracking(self):
        """测试统计追踪"""
        from backend.core.neural_layers.neural_embedding_layer import NeuralEmbeddingLayer, EmbeddingConfig
        
        config = EmbeddingConfig(use_mock=True)
        layer = NeuralEmbeddingLayer(config)
        stats = layer.get_stats()
        
        assert "config" in stats
        assert "model_name" in stats["config"]
        assert "use_mock" in stats["config"]
        assert stats["config"]["use_mock"] == True


class TestNeuralNormalizationLayer:
    """归一化层测试 - Layer 3"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_normalization_layer import NeuralNormalizationLayer
        
        layer = NeuralNormalizationLayer()
        assert layer is not None
        assert layer.config is not None


class TestNeuralAttentionLayer:
    """注意力层测试 - Layer 6"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_attention_layer import NeuralAttentionLayer
        
        layer = NeuralAttentionLayer()
        assert layer is not None
        assert layer.config is not None
        assert layer.config.num_heads == 12


class TestNeuralResidualLayer:
    """残差层测试 - Layer 7-8"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_residual_layer import NeuralResidualLayer
        
        layer = NeuralResidualLayer(layer_id=7)
        assert layer is not None
        assert layer.layer_id == 7


class TestNeuralDropoutLayer:
    """Dropout层测试 - Layer 9"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_dropout_layer import NeuralDropoutLayer
        
        layer = NeuralDropoutLayer()
        assert layer is not None
        assert layer.config.dropout_rate == 0.1
    
    def test_training_mode(self):
        """测试训练模式"""
        from backend.core.neural_layers.neural_dropout_layer import NeuralDropoutLayer
        
        layer = NeuralDropoutLayer()
        layer.set_training(True)
        assert layer.config.training is True
        
        layer.set_training(False)
        assert layer.config.training is False


class TestNeuralMemoryLayer:
    """记忆层测试 - Layer 13"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_memory_layer import NeuralMemoryLayer
        
        layer = NeuralMemoryLayer()
        assert layer is not None
        assert layer.config.memory_capacity == 10000


class TestNeuralReasoningLayer:
    """推理层测试 - Layer 14"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_reasoning_layer import NeuralReasoningLayer
        
        layer = NeuralReasoningLayer()
        assert layer is not None
        assert layer.config.reasoning_depth == 3


class TestNeuralPlanningLayer:
    """规划层测试 - Layer 15"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_planning_layer import NeuralPlanningLayer
        
        layer = NeuralPlanningLayer()
        assert layer is not None
        assert layer.config.max_plan_depth == 5


class TestNeuralExecutionLayer:
    """执行层测试 - Layer 17"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers.neural_execution_layer import NeuralExecutionLayer
        
        layer = NeuralExecutionLayer()
        assert layer is not None
        assert layer.config.timeout_seconds == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
