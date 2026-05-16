"""Neural Layers Unit Tests - 神经网络层单元测试

测试所有 18 层神经网络层的功能。
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = __import__('logging').getLogger(__name__)


class TestNeuralEmbeddingLayer:
    """嵌入层测试 - Layer 1"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralEmbeddingLayer
        
        layer = NeuralEmbeddingLayer()
        assert layer is not None
        assert layer.config is not None
        assert layer._stats["total_embeddings"] == 0
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralEmbeddingLayer
        
        layer = NeuralEmbeddingLayer()
        result = await layer.forward("test query")
        
        assert "embedding_dimension" in result
        assert "layer_id" in result
        assert result["layer_id"] == 1
        assert result["layer"] == "embedding"
    
    def test_stats_tracking(self):
        """测试统计追踪"""
        from backend.core.neural_layers import NeuralEmbeddingLayer
        
        layer = NeuralEmbeddingLayer()
        stats = layer.get_stats()
        
        assert "config" in stats
        assert "model_name" in stats["config"]


class TestNeuralNormalizationLayer:
    """归一化层测试 - Layer 3"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralNormalizationLayer
        
        layer = NeuralNormalizationLayer()
        assert layer is not None
        assert layer.config is not None
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralNormalizationLayer
        
        layer = NeuralNormalizationLayer()
        test_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = await layer.forward(test_data)
        
        assert "normalized_data" in result
        assert "layer_id" in result
        assert result["layer_id"] == 3


class TestNeuralAttentionLayer:
    """注意力层测试 - Layer 6"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralAttentionLayer
        
        layer = NeuralAttentionLayer()
        assert layer is not None
        assert layer.config is not None
        assert layer.config.num_heads == 12
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralAttentionLayer
        
        layer = NeuralAttentionLayer()
        test_data = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        result = await layer.forward(test_data)
        
        assert "attention_output" in result
        assert "num_heads" in result
        assert result["layer_id"] == 6


class TestNeuralResidualLayer:
    """残差层测试 - Layer 7-8"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralResidualLayer
        
        layer = NeuralResidualLayer(layer_id=7)
        assert layer is not None
        assert layer.layer_id == 7
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralResidualLayer
        
        layer = NeuralResidualLayer(layer_id=7)
        test_data = [[1.0, 0.0], [0.0, 1.0]]
        result = await layer.forward(test_data)
        
        assert "residual_output" in result
        assert "residual_connections" in result
        assert result["layer_id"] == 7


class TestNeuralDropoutLayer:
    """Dropout层测试 - Layer 9"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralDropoutLayer
        
        layer = NeuralDropoutLayer()
        assert layer is not None
        assert layer.config.dropout_rate == 0.1
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralDropoutLayer
        
        layer = NeuralDropoutLayer()
        test_data = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        
        layer.set_training(False)
        result = await layer.forward(test_data)
        
        assert "dropout_output" in result
        assert result["training"] is False
        assert result["layer_id"] == 9
    
    def test_training_mode(self):
        """测试训练模式"""
        from backend.core.neural_layers import NeuralDropoutLayer
        
        layer = NeuralDropoutLayer()
        layer.set_training(True)
        assert layer.config.training is True
        
        layer.set_training(False)
        assert layer.config.training is False


class TestNeuralMemoryLayer:
    """记忆层测试 - Layer 13"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralMemoryLayer
        
        layer = NeuralMemoryLayer()
        assert layer is not None
        assert layer.config.memory_capacity == 10000
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralMemoryLayer
        
        layer = NeuralMemoryLayer()
        result = await layer.forward("test query")
        
        assert "memory_output" in result
        assert "retrieved_memories" in result
        assert result["layer_id"] == 13
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        """测试存储和检索"""
        from backend.core.neural_layers import NeuralMemoryLayer
        
        layer = NeuralMemoryLayer()
        
        # 存储
        memory_id = await layer.store_memory(
            content="test content",
            embedding=[1.0, 0.0, 0.0],
            importance=0.8
        )
        
        assert memory_id is not None
        assert memory_id in layer.memories
        
        # 检索
        result = await layer.forward("test query")
        assert "retrieved_memories" in result


class TestNeuralReasoningLayer:
    """推理层测试 - Layer 14"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralReasoningLayer
        
        layer = NeuralReasoningLayer()
        assert layer is not None
        assert layer.config.reasoning_depth == 3
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralReasoningLayer
        
        layer = NeuralReasoningLayer()
        result = await layer.forward("test problem")
        
        assert "reasoning_output" in result
        assert "reasoning_steps" in result
        assert "reasoning_confidence" in result
        assert result["layer_id"] == 14


class TestNeuralPlanningLayer:
    """规划层测试 - Layer 15"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralPlanningLayer
        
        layer = NeuralPlanningLayer()
        assert layer is not None
        assert layer.config.max_plan_depth == 5
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralPlanningLayer
        
        layer = NeuralPlanningLayer()
        result = await layer.forward("plan a task")
        
        assert "planning_output" in result
        assert "plan_steps" in result
        assert "total_estimated_time" in result
        assert result["layer_id"] == 15


class TestNeuralExecutionLayer:
    """执行层测试 - Layer 17"""
    
    def test_initialization(self):
        """测试初始化"""
        from backend.core.neural_layers import NeuralExecutionLayer
        
        layer = NeuralExecutionLayer()
        assert layer is not None
        assert layer.config.timeout_seconds == 60
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """测试前向传播"""
        from backend.core.neural_layers import NeuralExecutionLayer
        
        layer = NeuralExecutionLayer()
        
        simple_plan = [
            {"action": "analyze", "description": "step 1", "priority": 1}
        ]
        
        result = await layer.forward({
            "plan_steps": simple_plan,
            "planning_output": "test"
        })
        
        assert "execution_status" in result
        assert "execution_id" in result
        assert result["layer_id"] == 17


class TestFCLayers:
    """全连接层测试 - Layer 10-12"""
    
    def test_fc1_initialization(self):
        """测试FC1层初始化"""
        from backend.core.neural_layers import FCLayer1
        
        # FC1需要更多参数，先测试导入
        from backend.core.neural_layers import FCLayer1, FCLayer2, FCLayer3
        
        # 这些类在neural_fully_connected_layers中定义
        assert FCLayer1 is not None
        assert FCLayer2 is not None
        assert FCLayer3 is not None


class TestExistingLayers:
    """测试已存在的层"""
    
    def test_input_layer(self):
        """测试输入层 - Layer 2"""
        from backend.core.neural_layers import NeuralInputLayer
        
        layer = NeuralInputLayer()
        assert layer is not None
    
    def test_convolution_layer(self):
        """测试卷积层 - Layer 4"""
        from backend.core.neural_layers import NeuralConvolutionLayer
        
        layer = NeuralConvolutionLayer()
        assert layer is not None
    
    def test_pooling_layer(self):
        """测试池化层 - Layer 5"""
        from backend.core.neural_layers import NeuralPoolingLayer
        
        layer = NeuralPoolingLayer()
        assert layer is not None
    
    def test_output_layer(self):
        """测试输出层 - Layer 16"""
        from backend.core.neural_layers import NeuralOutputLayer
        
        layer = NeuralOutputLayer()
        assert layer is not None
    
    def test_backward_layer(self):
        """测试反向传播层 - Layer 18"""
        from backend.core.neural_layers import NeuralBackwardPropagationLayer
        
        layer = NeuralBackwardPropagationLayer()
        assert layer is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
