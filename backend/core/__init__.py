""" NeuralAgent System - Core Package

    遵循架构原则：
    - 站在巨人的肩膀上
    - 不重复造轮子
    - 高度模块化
    - 每个模块都产品化
"""
import logging

logger = logging.getLogger(__name__)

# ==================== 核心基础设施模块（使用业界标准开源库） ====================
# Prometheus Metrics - 监控与可观测性
try:
    from .prometheus_metrics import (
        Metrics,
        MetricsConfig,
        init_metrics,
        get_metrics,
        track_llm_call,
        track_api_request
    )
except Exception as e:
    logger.warning(f"Failed to import prometheus_metrics: {e}")

# Error Resilience - 错误处理与重试（tenacity + pybreaker）
try:
    from .error_resilience import (
        retry_llm,
        retry_db,
        retry_api,
        with_circuit_breaker,
        llm_circuit_breaker,
        db_circuit_breaker,
        api_circuit_breaker
    )
except Exception as e:
    logger.warning(f"Failed to import error_resilience: {e}")

# LLM Client - 统一 LLM 接口（LiteLLM）
try:
    from .llm_client import (
        LLMClient,
        get_llm_client,
        chat,
        chat_sync,
        embed,
        embed_sync
    )
except Exception as e:
    logger.warning(f"Failed to import llm_client: {e}")

# Security - 认证与安全
try:
    from .security import (
        SecurityConfig,
        hash_password,
        verify_password,
        create_access_token,
        decode_access_token,
        Role,
        Permission,
        RolePermissionManager
    )
except Exception as e:
    logger.warning(f"Failed to import security: {e}")

# Structured Logging - 结构化日志系统
try:
    from .structured_logging import (
        setup_structured_logging,
        get_logger,
        bind_context,
        unbind_context,
        clear_context
    )
except Exception as e:
    logger.warning(f"Failed to import structured_logging: {e}")

# Cache Manager - 缓存管理系统
try:
    from .cache_manager import (
        CacheManager,
        get_cache_manager,
        cache_result,
        invalidate_cache
    )
except Exception as e:
    logger.warning(f"Failed to import cache_manager: {e}")

# Error Codes - 错误码系统
try:
    from .error_codes import (
        ErrorCode,
        NeuralAgentException,
        AuthenticationError,
        AuthorizationError,
        TaskError,
        LLMError,
        CodeProcessingError,
        VectorStoreError,
        ValidationError,
        RateLimitError,
        SystemError,
        get_error_message,
        is_retryable_error,
        get_retry_after
    )
except Exception as e:
    logger.warning(f"Failed to import error_codes: {e}")

# Config Validator - 配置验证系统
try:
    from .config_validator import (
        ConfigValidator,
        ConfigValidationResult,
        ValidationLevel,
        create_neuralagent_validator,
        validate_config_and_raise,
        with_config_validation,
        validate_url,
        validate_port,
        validate_positive_number,
        validate_enum_value,
        validate_log_level,
        validate_llm_temperature
    )
except Exception as e:
    logger.warning(f"Failed to import config_validator: {e}")

# Agent Orchestration - Agent 编排框架
try:
    from .agent_orchestration import (
        OrchestrationFramework,
        AgentConfig,
        TaskConfig,
        BaseOrchestrator,
        AutoGenOrchestrator,
        CrewAIOrchestrator,
        LangChainOrchestrator,
        OrchestratorFactory
    )
except Exception as e:
    logger.warning(f"Failed to import agent_orchestration: {e}")

# Health Monitor - 健康检查和系统监控
try:
    from .health_monitor import (
        HealthStatus,
        CheckResult,
        SystemMetrics,
        ApplicationHealth,
        HealthCheck,
        HealthMonitor,
        get_health_monitor,
        check_health
    )
except Exception as e:
    logger.warning(f"Failed to import health_monitor: {e}")

# Product Quality Scoring - 产品质量评分系统
try:
    from .product_quality_scoring import (
        MetricCategory,
        ScoringLevel,
        MetricResult,
        CategoryScore,
        QualityReport,
        QualityScoringSystem,
        generate_quality_report
    )
except Exception as e:
    logger.warning(f"Failed to import product_quality_scoring: {e}")

# Enhanced Product Quality Scoring - 增强型多维度产品质量评分系统
try:
    from .enhanced_product_scoring import (
        EnhancedMetricCategory,
        EnhancedQualityReport,
        EnhancedQualityScoringSystem,
        generate_enhanced_report
    )
except Exception as e:
    logger.warning(f"Failed to import enhanced_product_scoring: {e}")

# Ultimate Product Quality Scoring - 终极16维度产品质量评分系统
try:
    from .ultimate_quality_scoring import (
        UltimateMetricCategory,
        UltimateQualityReport,
        UltimateQualityScoringSystem,
        generate_ultimate_report
    )
except Exception as e:
    logger.warning(f"Failed to import ultimate_quality_scoring: {e}")

# Rate Limiter - 速率限制系统
try:
    from .rate_limiter import (
        RateLimiter,
        RateLimitConfig,
        RateLimitResult,
        RateLimitStrategy,
        RateLimitBackend,
        RateLimitException,
        MemoryRateLimiter,
        RedisRateLimiter,
        MultiTierRateLimiter,
        get_rate_limiter,
        rate_limit,
        rate_limit_by_ip,
        rate_limit_by_user,
        RateLimitMiddleware
    )
except Exception as e:
    logger.warning(f"Failed to import rate_limiter: {e}")

# ==================== 核心业务模块 ====================
try:
    from .neural_agent import NeuralAgent
except Exception as e:
    logger.warning(f"Failed to import NeuralAgent: {e}")

try:
    from .short_term_memory import ShortTermMemory
except Exception as e:
    logger.warning(f"Failed to import ShortTermMemory: {e}")

try:
    from .long_term_memory import LongTermMemory
except Exception as e:
    logger.warning(f"Failed to import LongTermMemory: {e}")

try:
    from .trust_manager import TrustManager
except Exception as e:
    logger.warning(f"Failed to import TrustManager: {e}")

try:
    from .message_protocol import ForwardMessage, BackwardMessage
except Exception as e:
    logger.warning(f"Failed to import message protocols: {e}")

# ==================== 大规模处理模块 ====================
try:
    from .code_chunker import CodeChunk, TreeSitterChunker
except Exception as e:
    logger.warning(f"Failed to import code_chunker: {e}")

try:
    from .parallel_processor import (
        ParallelProcessor,
        AsyncParallelProcessor,
        PipelineProcessor,
        ProcessingStats,
        ProcessingBatch,
        CodeAnalysisActor
    )
except Exception as e:
    logger.warning(f"Failed to import parallel_processor: {e}")

try:
    from .vector_store import (
        VectorStoreBase,
        MilvusVectorStore,
        ChromaVectorStore,
        VectorSearchResult,
        create_vector_store
    )
except Exception as e:
    logger.warning(f"Failed to import vector_store: {e}")

try:
    from .incremental_processor import (
        FileChange,
        IncrementalStats,
        GitChangeDetector,
        IncrementalProcessor
    )
except Exception as e:
    logger.warning(f"Failed to import incremental_processor: {e}")

# Performance Optimizer - 性能优化模块
try:
    from .performance_optimizer import (
        OptimizationLevel,
        PerformanceMetrics,
        PerformanceOptimizer,
        PerformanceTester,
        optimizer,
        optimize
    )
except Exception as e:
    logger.warning(f"Failed to import performance_optimizer: {e}")

# Enhanced Memory System - 产品级增强版记忆系统
try:
    from .memory_enhanced import (
        MemoryType,
        MemoryImportance,
        ForgettingStrategy,
        MemoryEntry,
        MemoryQuery,
        MemoryRetrievalResult,
        WorkingMemory,
        ShortTermMemoryEnhanced,
        EpisodicMemory,
        SemanticMemory,
        MemoryRetriever,
        MemoryConsolidator,
        ForgettingMechanism,
        EnhancedMemorySystem,
        create_memory_system,
    )
except Exception as e:
    logger.warning(f"Failed to import memory_enhanced: {e}")
