#!/usr/bin/env python3
"""NeuralAgent 项目结构重构脚本
"""

import os
import shutil
from pathlib import Path
import logging
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"

# 源文件 -> 目标文件映射表
MOVE_MAP: Dict[Path, Path] = {
    # ==================== 核心模块 ====================
    # 配置模块
    BACKEND_DIR / "core" / "config_validator.py": 
        BACKEND_DIR / "core" / "configuration" / "configuration_validator.py",
    
    # 记忆模块
    BACKEND_DIR / "core" / "short_term_memory.py":
        BACKEND_DIR / "core" / "memory" / "short_term_memory.py",
    BACKEND_DIR / "core" / "long_term_memory.py":
        BACKEND_DIR / "core" / "memory" / "long_term_memory.py",
    BACKEND_DIR / "core" / "memory_enhanced.py":
        BACKEND_DIR / "core" / "memory" / "enhanced_memory_system.py",
    
    # Agent 模块
    BACKEND_DIR / "core" / "neural_agent.py":
        BACKEND_DIR / "core" / "agents" / "neural_agent.py",
    BACKEND_DIR / "core" / "agent_orchestration.py":
        BACKEND_DIR / "core" / "agents" / "agent_orchestration.py",
    BACKEND_DIR / "core" / "agent_communication.py":
        BACKEND_DIR / "core" / "messaging" / "agent_communication.py",
    
    # 任务管理模块
    BACKEND_DIR / "core" / "task_decomposer.py":
        BACKEND_DIR / "core" / "task_management" / "task_decomposer.py",
    
    # 信任管理模块
    BACKEND_DIR / "core" / "trust_manager.py":
        BACKEND_DIR / "core" / "trust_management" / "trust_manager.py",
    
    # 消息协议模块
    BACKEND_DIR / "core" / "message_protocol.py":
        BACKEND_DIR / "core" / "messaging" / "message_protocol.py",
    
    # LLM 集成模块
    BACKEND_DIR / "core" / "llm_client.py":
        BACKEND_DIR / "core" / "llm_integration" / "llm_client.py",
    BACKEND_DIR / "core" / "batch_embedding.py":
        BACKEND_DIR / "core" / "llm_integration" / "batch_embedding_processor.py",
    
    # 质量保证模块
    BACKEND_DIR / "core" / "product_quality_scoring.py":
        BACKEND_DIR / "core" / "quality_assurance" / "quality_scorer.py",
    BACKEND_DIR / "core" / "enhanced_product_scoring.py":
        BACKEND_DIR / "core" / "quality_assurance" / "quality_enhanced_scorer.py",
    BACKEND_DIR / "core" / "ultimate_quality_scoring.py":
        BACKEND_DIR / "core" / "quality_assurance" / "quality_ultimate_scorer.py",
    
    # 基础设施 - 错误处理
    BACKEND_DIR / "core" / "error_codes.py":
        BACKEND_DIR / "core" / "infrastructure" / "error_handling" / "error_codes.py",
    BACKEND_DIR / "core" / "error_resilience.py":
        BACKEND_DIR / "core" / "infrastructure" / "error_handling" / "error_resilience.py",
    
    # 基础设施 - 可观测性
    BACKEND_DIR / "core" / "health_monitor.py":
        BACKEND_DIR / "core" / "infrastructure" / "observability" / "health_monitor.py",
    BACKEND_DIR / "core" / "structured_logging.py":
        BACKEND_DIR / "core" / "infrastructure" / "observability" / "structured_logger.py",
    BACKEND_DIR / "core" / "prometheus_metrics.py":
        BACKEND_DIR / "core" / "infrastructure" / "observability" / "prometheus_metrics.py",
    
    # 基础设施 - 性能
    BACKEND_DIR / "core" / "performance_optimizer.py":
        BACKEND_DIR / "core" / "infrastructure" / "performance" / "performance_optimizer.py",
    
    # 基础设施 - 安全
    BACKEND_DIR / "core" / "security.py":
        BACKEND_DIR / "core" / "infrastructure" / "security" / "authentication_service.py",
    BACKEND_DIR / "core" / "rate_limiter.py":
        BACKEND_DIR / "core" / "infrastructure" / "security" / "rate_limiter.py",
    
    # 基础设施 - 缓存
    BACKEND_DIR / "core" / "cache_manager.py":
        BACKEND_DIR / "core" / "infrastructure" / "cache" / "cache_manager.py",
    
    # 代码处理模块
    BACKEND_DIR / "core" / "code_chunker.py":
        BACKEND_DIR / "processing" / "code_processing" / "code_chunker.py",
    
    # 向量存储模块
    BACKEND_DIR / "core" / "vector_store.py":
        BACKEND_DIR / "processing" / "vector_storing" / "vector_store_manager.py",
    
    # 大规模处理模块
    BACKEND_DIR / "core" / "parallel_processor.py":
        BACKEND_DIR / "processing" / "large_scale" / "parallel_processor.py",
    BACKEND_DIR / "core" / "incremental_processor.py":
        BACKEND_DIR / "processing" / "large_scale" / "incremental_processor.py",
    
    # 神经网络层模块
    BACKEND_DIR / "layers" / "input_layer.py":
        BACKEND_DIR / "core" / "neural_layers" / "neural_input_layer.py",
    BACKEND_DIR / "layers" / "convolution_layer.py":
        BACKEND_DIR / "core" / "neural_layers" / "neural_convolution_layer.py",
    BACKEND_DIR / "layers" / "pooling_layer.py":
        BACKEND_DIR / "core" / "neural_layers" / "neural_pooling_layer.py",
    BACKEND_DIR / "layers" / "output_layer.py":
        BACKEND_DIR / "core" / "neural_layers" / "neural_output_layer.py",
    BACKEND_DIR / "layers" / "backward_layer.py":
        BACKEND_DIR / "core" / "neural_layers" / "neural_backward_propagation_layer.py",
    
    # 配置模型
    BACKEND_DIR / "config.py":
        BACKEND_DIR / "core" / "configuration" / "settings_model.py",
}


def create_directories():
    """创建新的目录结构
    """
    directories = [
        # Core 模块目录
        BACKEND_DIR / "core" / "configuration",
        BACKEND_DIR / "core" / "memory",
        BACKEND_DIR / "core" / "agents",
        BACKEND_DIR / "core" / "llm_integration",
        BACKEND_DIR / "core" / "task_management",
        BACKEND_DIR / "core" / "neural_layers",
        BACKEND_DIR / "core" / "trust_management",
        BACKEND_DIR / "core" / "messaging",
        BACKEND_DIR / "core" / "quality_assurance",
        BACKEND_DIR / "core" / "infrastructure",
        BACKEND_DIR / "core" / "infrastructure" / "error_handling",
        BACKEND_DIR / "core" / "infrastructure" / "observability",
        BACKEND_DIR / "core" / "infrastructure" / "performance",
        BACKEND_DIR / "core" / "infrastructure" / "security",
        BACKEND_DIR / "core" / "infrastructure" / "cache",
        
        # Processing 模块目录
        BACKEND_DIR / "processing",
        BACKEND_DIR / "processing" / "code_processing",
        BACKEND_DIR / "processing" / "vector_storing",
        BACKEND_DIR / "processing" / "large_scale",
        
        # Tests 模块目录
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "integration",
        PROJECT_ROOT / "tests" / "e2e",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ 创建目录: {directory}")
        
        # 创建 __init__.py
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""NeuralAgent 模块入口文件\n"""\n')
            logger.info(f"  ✓ 创建 __init__.py")


def move_files():
    """移动文件到新位置
    """
    moved_count = 0
    for src, dest in MOVE_MAP.items():
        if src.exists():
            logger.info(f"移动文件: {src.name} -> {dest.name}")
            shutil.copy2(src, dest)
            moved_count += 1
    logger.info(f"✓ 共移动 {moved_count} 个文件")


def main():
    """主函数
    """
    logger.info("=" * 80)
    logger.info("NeuralAgent 项目结构重构")
    logger.info("=" * 80)
    
    # 检查当前目录
    logger.info(f"项目根目录: {PROJECT_ROOT}")
    
    # 创建目录
    logger.info("\n步骤 1: 创建新的目录结构")
    logger.info("-" * 80)
    create_directories()
    
    # 移动文件
    logger.info("\n步骤 2: 移动和复制文件")
    logger.info("-" * 80)
    move_files()
    
    logger.info("\n" + "=" * 80)
    logger.info("重构完成！")
    logger.info("\n下一步操作:")
    logger.info("1. 手动检查文件内容，合并 fc_layer_1/2/3 到单一文件")
    logger.info("2. 更新所有模块的导入路径")
    logger.info("3. 运行测试验证系统完整性")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
