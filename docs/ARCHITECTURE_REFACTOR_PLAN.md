# NeuralAgent 工程化重构计划
=====================================

## 现状问题分析

### 现有问题
1. `backend/core/ 目录下文件过多（30+个文件，没有分组
2. 模块重复（memory_enhanced 与 short_term_memory/long_term_memory 同时存在
3. 命名不够语义化（fc_layer_1.py 这种命名
4. 缺少清晰的功能域划分
5. 模块之间的依赖关系不清晰

### 重构目标
1. 功能域清晰分组
2. 文件命名更加语义化
3. 工程层级更加明确
4. 符合企业级项目结构

## 新架构设计

```
neural_agent/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI 主入口
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── agent_routes.py
│   │   │   ├── task_routes.py
│   │   │   └── health_routes.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── agent_request_schemas.py
│   │   │   └── task_response_schemas.py
│   │   ├── dependencies/
│   │   │   ├── __init__.py
│   │   │   └── authentication_dependencies.py
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── security_middleware.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── configuration/
│   │   │   ├── __init__.py
│   │   │   ├── configuration_manager.py
│   │   │   ├── settings_model.py
│   │   │   └── configuration_validator.py
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── working_memory.py
│   │   │   ├── short_term_memory.py
│   │   │   ├── long_term_memory.py
│   │   │   ├── memory_retriever.py
│   │   │   └── memory_consolidator.py
│   │   │   ├── forgetting_mechanism.py
│   │   │   └── enhanced_memory_system.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── neural_agent.py
│   │   │   ├── agent_composer.py
│   │   │   └── agent_orchestration.py
│   │   │   └── agent_communication.py
│   │   ├── llm_integration/
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py
│   │   │   ├── llm_adapter.py
│   │   │   └── batch_embedding_processor.py
│   │   ├── task_management/
│   │   │   ├── __init__.py
│   │   │   ├── task_decomposer.py
│   │   │   ├── task_executor.py
│   │   │   └── progress_tracker.py
│   │   ├── neural_layers/
│   │   │   ├── __init__.py
│   │   │   ├── neural_input_layer.py
│   │   │   ├── neural_convolution_layer.py
│   │   │   ├── neural_pooling_layer.py
│   │   │   ├── neural_fully_connected_layer.py
│   │   │   ├── neural_output_layer.py
│   │   │   └── neural_backward_propagation_layer.py
│   │   ├── trust_management/
│   │   │   ├── __init__.py
│   │   │   └── trust_manager.py
│   │   │   └── trust_updater.py
│   │   ├── messaging/
│   │   │   ├── __init__.py
│   │   │   ├── message_protocol.py
│   │   │   ├── message_broker.py
│   │   ├── message_router.py
│   │   ├── quality_assurance/
│   │   │   ├── __init__.py
│   │   │   ├── quality_scorer.py
│   │   │   ├── quality_enhanced_scorer.py
│   │   │   └── quality_ultimate_scorer.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── error_handling/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── error_codes.py
│   │   │   │   └── error_resilience.py
│   │   │   ├── observability/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health_monitor.py
│   │   │   │   ├── structured_logger.py
│   │   │   │   └── prometheus_metrics.py
│   │   │   ├── performance/
│   │   │   │   ├── __init__.py
│   │   │   │   └── performance_optimizer.py
│   │   │   ├── security/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── authentication_service.py
│   │   │   │   └── rate_limiter.py
│   │   │   └── cache/
│   │   │       ├── __init__.py
│   │   │       └── cache_manager.py
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── code_processing/
│   │   │   ├── __init__.py
│   │   │   ├── code_chunker.py
│   │   │   └── code_parser.py
│   │   ├── vector_storing/
│   │   │   ├── __init__.py
│   │   │   └── vector_store_manager.py
│   │   └── large_scale/
│   │       ├── __init__.py
│   │       ├── parallel_processor.py
│   │       └── incremental_processor.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── database.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── database_service.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_memory/
│   │   │   ├── __init__.py
│   │   │   ├── test_working_memory.py
│   │   │   ├── test_short_term_memory.py
│   │   │   └── test_enhanced_memory.py
│   │   ├── test_agents/
│   │   │   ├── __init__.py
│   │   │   └── test_neural_agent.py
│   │   ├── test_infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── test_error_handling/
│   │   │   └── test_observability/
│   │   ├── test_quality/
│   │   │   ├── __init__.py
│   │   │   └── test_quality_scoring.py
│   │   └── test_processing/
│   │       ├── __init__.py
│   │       ├── test_code_processing/
│   │       └── test_large_scale/
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_integration.py
│   │   └── test_agent_orchestration_integration.py
│   └── e2e/
│       ├── __init__.py
│       └── e2e_github_project_tests.py
├── scripts/
│   ├── __init__.py
│   ├── health_check.py
│   ├── project_health_analyzer.py
│   └── performance_benchmark.py
├── docs/
│   ├── architecture/
│   ├── development/
│   ├── user_guide/
│   └── api/
└── ...
```

## 重命名映射表
```
backend/core/__init__.py -> backend/core/__init__.py (保持)
backend/core/neural_agent.py -> backend/core/agents/neural_agent.py
backend/core/short_term_memory.py -> backend/core/memory/short_term_memory.py
backend/core/long_term_memory.py -> backend/core/memory/long_term_memory.py
backend/core/memory_enhanced.py -> backend/core/memory/enhanced_memory_system.py
backend/core/attention.py -> backend/core/memory/working_memory.py
backend/core/agent_orchestration.py -> backend/core/agents/agent_orchestration.py
backend/core/agent_communication.py -> backend/core/messaging/message_router.py
backend/core/task_decomposer.py -> backend/core/task_management/task_decomposer.py
backend/core/trust_manager.py -> backend/core/trust_management/trust_manager.py
backend/core/message_protocol.py -> backend/core/messaging/message_protocol.py
backend/core/llm_client.py -> backend/core/llm_integration/llm_client.py
backend/core/batch_embedding.py -> backend/core/llm_integration/batch_embedding_processor.py
backend/core/product_quality_scoring.py -> backend/core/quality_assurance/quality_scorer.py
backend/core/enhanced_product_scoring.py -> backend/core/quality_assurance/quality_enhanced_scorer.py
backend/core/ultimate_quality_scoring.py -> backend/core/quality_assurance/quality_ultimate_scorer.py
backend/core/error_codes.py -> backend/core/infrastructure/error_handling/error_codes.py
backend/core/error_resilience.py -> backend/core/infrastructure/error_handling/error_resilience.py
backend/core/health_monitor.py -> backend/core/infrastructure/observability/health_monitor.py
backend/core/structured_logging.py -> backend/core/infrastructure/observability/structured_logger.py
backend/core/prometheus_metrics.py -> backend/core/infrastructure/observability/prometheus_metrics.py
backend/core/performance_optimizer.py -> backend/core/infrastructure/performance/performance_optimizer.py
backend/core/security.py -> backend/core/infrastructure/security/authentication_service.py
backend/core/rate_limiter.py -> backend/core/infrastructure/security/rate_limiter.py
backend/core/cache_manager.py -> backend/core/infrastructure/cache/cache_manager.py
backend/core/code_chunker.py -> backend/processing/code_processing/code_chunker.py
backend/core/vector_store.py -> backend/processing/vector_storing/vector_store_manager.py
backend/core/parallel_processor.py -> backend/processing/large_scale/parallel_processor.py
backend/core/incremental_processor.py -> backend/processing/large_scale/incremental_processor.py
backend/core/config_validator.py -> backend/core/configuration/configuration_validator.py
backend/layers/input_layer.py -> backend/core/neural_layers/neural_input_layer.py
backend/layers/convolution_layer.py -> backend/core/neural_layers/neural_convolution_layer.py
backend/layers/pooling_layer.py -> backend/core/neural_layers/neural_pooling_layer.py
backend/layers/fc_layer_1.py -> backend/core/neural_layers/neural_fully_connected_layer.py (单一文件，移除数字
backend/layers/fc_layer_2.py -> 合并到 neural_fully_connected_layer.py
backend/layers/fc_layer_3.py -> 合并到 neural_fully_connected_layer.py
backend/layers/output_layer.py -> backend/core/neural_layers/neural_output_layer.py
backend/layers/backward_layer.py -> backend/core/neural_layers/neural_backward_propagation_layer.py
```
