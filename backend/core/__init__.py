""" NeuralAgent System - Core Package

    遵循架构原则：
    - 站在巨人的肩膀上
    - 不重复造轮子
    - 高度模块化
    - 每个模块都产品化
"""
import logging

logger = logging.getLogger(__name__)

# ==================== 核心业务模块 ====================
# LLM Adapter - 统一 LLM 接口
try:
    from .llm_adapter import (
        LLMProvider,
        LLMConfig,
        LLMAdapter,
        MockLLMAdapter,
        OpenAILLMAdapter,
        AnthropicLLMAdapter,
        OllamaLLMAdapter,
        create_llm_adapter
    )
except Exception as e:
    logger.debug(f"LLM adapter optional: {e}")

# LLM Integration - 完整的 LLM 集成
try:
    from .llm_integration.unified_llm_client_wrapper import (
        LLMClient,
        LLMResponse,
        EmbeddingResponse
    )
except Exception as e:
    logger.debug(f"LLM integration optional: {e}")

# Memory System - 完整的记忆系统
try:
    from .memory.short_term_memory import ShortTermMemory
    from .memory.long_term_memory import LongTermMemory, MemoryEntry
except Exception as e:
    logger.debug(f"Memory system optional: {e}")

# Neural Layers - 18层神经网络
try:
    from .neural_layers import (
        neural_embedding_layer,
        neural_input_layer,
        neural_normalization_layer,
        neural_convolution_layer,
        neural_pooling_layer,
        neural_attention_layer,
        neural_residual_layer,
        neural_dropout_layer,
        neural_fully_connected_layers,
        neural_memory_layer,
        neural_reasoning_layer,
        neural_planning_layer,
        neural_output_layer,
        neural_execution_layer,
        neural_backward_propagation_layer
    )
except Exception as e:
    logger.debug(f"Neural layers optional: {e}")

# Agent Coordination - 多 Agent 协调
try:
    from .agents import (
        intelligent_multi_agent_coordinator,
        distributed_multi_agent_orchestrator
    )
except Exception as e:
    logger.debug(f"Agent system optional: {e}")

# Quality Assurance - 质量保证
try:
    from .quality_assurance import (
        enhanced_product_quality_scorer,
        ultimate_product_quality_scorer
    )
except Exception as e:
    logger.debug(f"Quality system optional: {e}")

# Trust Management - 信任管理
try:
    from .trust_management.trust_manager import TrustManager
except Exception as e:
    logger.debug(f"Trust system optional: {e}")

# Infrastructure - 基础设施
try:
    from .infrastructure import (
        cache,
        error_handling,
        observability,
        security,
        performance,
        vector_db
    )
except Exception as e:
    logger.debug(f"Infrastructure optional: {e}")

# ==================== 配置系统 ====================
try:
    from .configuration import settings
except Exception as e:
    logger.debug(f"Configuration optional: {e}")
