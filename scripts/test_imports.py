#!/usr/bin/env python3
"""Test Imports - 测试导入脚本"""

import sys
sys.path.insert(0, '/workspace/neural_agent')

try:
    print("Testing imports...")
    
    # 测试error_handling
    print("\n1. Testing error_handling...")
    from backend.core.infrastructure.error_handling import (
        ErrorCode,
        NeuralAgentException,
        SystemError,
        ValidationError,
        with_retry,
        with_circuit_breaker,
        CircuitBreakerError
    )
    print("✅ error_handling imports OK")
    
    # 测试observability
    print("\n2. Testing observability...")
    from backend.core.infrastructure.observability import (
        HealthMonitor,
        PrometheusMetrics,
        StructuredLogger
    )
    print("✅ observability imports OK")
    
    # 测试cache
    print("\n3. Testing cache...")
    from backend.core.infrastructure.cache import CacheManager
    print("✅ cache imports OK")
    
    # 测试security
    print("\n4. Testing security...")
    from backend.core.infrastructure.security import (
        AuthenticationService,
        RateLimiter
    )
    print("✅ security imports OK")
    
    # 测试agents
    print("\n5. Testing agents...")
    from backend.core.agents import (
        IntelligentMultiAgentCoordinator,
        DistributedMultiAgentOrchestrator
    )
    print("✅ agents imports OK")
    
    # 测试llm_integration
    print("\n6. Testing llm_integration...")
    from backend.core.llm_integration import (
        UnifiedLLMClientWrapper,
        BatchEmbeddingProcessor
    )
    print("✅ llm_integration imports OK")
    
    # 测试task_management
    print("\n7. Testing task_management...")
    from backend.core.task_management import IntelligentTaskDecomposerService
    print("✅ task_management imports OK")
    
    # 测试messaging
    print("\n8. Testing messaging...")
    from backend.core.messaging import (
        MultiAgentCommunicationHandler,
        StructuredMessageProtocolHandler
    )
    print("✅ messaging imports OK")
    
    # 测试memory
    print("\n9. Testing memory...")
    from backend.core.memory import (
        EnhancedMemorySystem,
        ShortTermMemory,
        LongTermMemory
    )
    print("✅ memory imports OK")
    
    # 测试quality_assurance
    print("\n10. Testing quality_assurance...")
    from backend.core.quality_assurance import (
        ProductQualityScorer,
        EnhancedProductQualityScorer,
        UltimateProductQualityScorer
    )
    print("✅ quality_assurance imports OK")
    
    print("\n" + "="*60)
    print("🎉 All imports successful!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
