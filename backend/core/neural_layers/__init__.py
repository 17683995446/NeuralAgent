"""Neural Layers Module - 神经网络层模块

包含 NeuralAgent 深度神经网络的所有层实现。

架构版本: v2.0
总层数: 18 层
"""

import logging

logger = logging.getLogger(__name__)

# Layer 1: Embedding Layer
try:
    from .neural_embedding_layer import (
        NeuralEmbeddingLayer,
        EmbeddingConfig,
        EmbeddingResult,
        create_embedding_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_embedding_layer: {e}")

# Layer 2: Input Layer
try:
    from .neural_input_layer import (
        NeuralInputLayer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_input_layer: {e}")

# Layer 3: Normalization Layer
try:
    from .neural_normalization_layer import (
        NeuralNormalizationLayer,
        NormalizationConfig,
        create_normalization_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_normalization_layer: {e}")

# Layer 4: Convolution Layer
try:
    from .neural_convolution_layer import (
        NeuralConvolutionLayer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_convolution_layer: {e}")

# Layer 5: Pooling Layer
try:
    from .neural_pooling_layer import (
        NeuralPoolingLayer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_pooling_layer: {e}")

# Layer 6: Attention Layer
try:
    from .neural_attention_layer import (
        NeuralAttentionLayer,
        AttentionConfig,
        create_attention_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_attention_layer: {e}")

# Layer 7-8: Residual Layer
try:
    from .neural_residual_layer import (
        NeuralResidualLayer,
        ResidualConfig,
        create_residual_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_residual_layer: {e}")

# Layer 9: Dropout Layer
try:
    from .neural_dropout_layer import (
        NeuralDropoutLayer,
        DropoutConfig,
        create_dropout_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_dropout_layer: {e}")

# Layer 10-12: Fully Connected Layers
try:
    from .neural_fully_connected_layers import (
        FCLayer1,
        FCLayer2,
        FCLayer3,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_fully_connected_layers: {e}")

# Layer 13: Memory Layer
try:
    from .neural_memory_layer import (
        NeuralMemoryLayer,
        MemoryConfig,
        create_memory_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_memory_layer: {e}")

# Layer 14: Reasoning Layer
try:
    from .neural_reasoning_layer import (
        NeuralReasoningLayer,
        ReasoningConfig,
        create_reasoning_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_reasoning_layer: {e}")

# Layer 15: Planning Layer
try:
    from .neural_planning_layer import (
        NeuralPlanningLayer,
        PlanningConfig,
        create_planning_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_planning_layer: {e}")

# Layer 16: Output Layer
try:
    from .neural_output_layer import (
        NeuralOutputLayer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_output_layer: {e}")

# Layer 17: Execution Layer
try:
    from .neural_execution_layer import (
        NeuralExecutionLayer,
        ExecutionConfig,
        create_execution_layer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_execution_layer: {e}")

# Layer 18: Backward Propagation Layer
try:
    from .neural_backward_propagation_layer import (
        NeuralBackwardPropagationLayer,
    )
except ImportError as e:
    logger.warning(f"Failed to import neural_backward_propagation_layer: {e}")


__all__ = [
    # Layer 1
    "NeuralEmbeddingLayer",
    "EmbeddingConfig",
    "create_embedding_layer",
    
    # Layer 2
    "NeuralInputLayer",
    
    # Layer 3
    "NeuralNormalizationLayer",
    "NormalizationConfig",
    "create_normalization_layer",
    
    # Layer 4
    "NeuralConvolutionLayer",
    
    # Layer 5
    "NeuralPoolingLayer",
    
    # Layer 6
    "NeuralAttentionLayer",
    "AttentionConfig",
    "create_attention_layer",
    
    # Layer 7-8
    "NeuralResidualLayer",
    "ResidualConfig",
    "create_residual_layer",
    
    # Layer 9
    "NeuralDropoutLayer",
    "DropoutConfig",
    "create_dropout_layer",
    
    # Layer 10-12
    "FCLayer1",
    "FCLayer2",
    "FCLayer3",
    
    # Layer 13
    "NeuralMemoryLayer",
    "MemoryConfig",
    "create_memory_layer",
    
    # Layer 14
    "NeuralReasoningLayer",
    "ReasoningConfig",
    "create_reasoning_layer",
    
    # Layer 15
    "NeuralPlanningLayer",
    "PlanningConfig",
    "create_planning_layer",
    
    # Layer 16
    "NeuralOutputLayer",
    
    # Layer 17
    "NeuralExecutionLayer",
    "ExecutionConfig",
    "create_execution_layer",
    
    # Layer 18
    "NeuralBackwardPropagationLayer",
]

logger.info("Neural Layers Module loaded successfully - 18 layers available")
