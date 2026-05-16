#!/usr/bin/env python3
"""Fix Import Paths Script - 批量修复导入路径脚本"""

import os
import re
from pathlib import Path

# 定义导入映射
IMPORT_MAPPINGS = {
    "from backend.core.configuration.configuration_validator": "from backend.core.configuration.configuration_validator",
    "from backend.core.infrastructure.error_handling.error_codes": "from backend.core.infrastructure.error_handling.error_codes",
    "from backend.core.infrastructure.error_handling.error_resilience": "from backend.core.infrastructure.error_handling.error_resilience",
    "from backend.core.infrastructure.observability.health_monitor": "from backend.core.infrastructure.observability.health_monitor",
    "from backend.core.infrastructure.observability.prometheus_metrics": "from backend.core.infrastructure.observability.prometheus_metrics",
    "from backend.core.infrastructure.observability.structured_logger": "from backend.core.infrastructure.observability.structured_logger",
    "from backend.core.infrastructure.performance.performance_optimizer": "from backend.core.infrastructure.performance.performance_optimizer",
    "from backend.core.infrastructure.cache.cache_manager": "from backend.core.infrastructure.cache.cache_manager",
    "from backend.core.infrastructure.security.rate_limiter": "from backend.core.infrastructure.security.rate_limiter",
    "from backend.core.infrastructure.security.authentication_service": "from backend.core.infrastructure.security.authentication_service",
    "from backend.core.infrastructure.security": "from backend.core.infrastructure.security",
    "from backend.core.llm_integration.unified_llm_client_wrapper": "from backend.core.llm_integration.unified_llm_client_wrapper",
    "from backend.core.llm_integration.batch_embedding_processor": "from backend.core.llm_integration.batch_embedding_processor",
    "from backend.core.agents.intelligent_multi_agent_coordinator": "from backend.core.agents.intelligent_multi_agent_coordinator",
    "from backend.core.agents.distributed_multi_agent_orchestrator": "from backend.core.agents.distributed_multi_agent_orchestrator",
    "from backend.core.task_management.intelligent_task_decomposer_service": "from backend.core.task_management.intelligent_task_decomposer_service",
    "from backend.core.messaging.multi_agent_communication_handler": "from backend.core.messaging.multi_agent_communication_handler",
    "from backend.core.messaging.structured_message_protocol_handler": "from backend.core.messaging.structured_message_protocol_handler",
    "from backend.core.memory.enhanced_memory_system": "from backend.core.memory.enhanced_memory_system",
    "from backend.core.memory.short_term_memory": "from backend.core.memory.short_term_memory",
    "from backend.core.memory.long_term_memory": "from backend.core.memory.long_term_memory",
    "from backend.core.trust_management.trust_manager": "from backend.core.trust_management.trust_manager",
    "from backend.core.quality_assurance.product_quality_scorer": "from backend.core.quality_assurance.product_quality_scorer",
    "from backend.core.quality_assurance.enhanced_product_quality_scorer": "from backend.core.quality_assurance.enhanced_product_quality_scorer",
    "from backend.core.quality_assurance.ultimate_product_quality_scorer": "from backend.core.quality_assurance.ultimate_product_quality_scorer",
}

def fix_imports_in_file(file_path):
    """修复单个文件中的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                print(f"  ✅ Fixed: {old_import} -> {new_import} in {file_path.name}")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False

def main():
    """主函数"""
    base_path = Path("/workspace/neural_agent")
    
    # 需要扫描的目录
    scan_dirs = [
        base_path / "backend",
        base_path / "tests",
        base_path / "scripts"
    ]
    
    # 文件扩展名
    extensions = [".py"]
    
    total_fixed = 0
    total_files = 0
    
    for scan_dir in scan_dirs:
        print(f"\n🔍 Scanning {scan_dir}...")
        
        for ext in extensions:
            for file_path in scan_dir.rglob(f"*{ext}"):
                # 跳过 __pycache__ 和 .pyc 文件
                if "__pycache__" in str(file_path) or file_path.name.endswith(".pyc"):
                    continue
                
                if fix_imports_in_file(file_path):
                    total_files += 1
                    total_fixed += 1
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Fixed imports in {total_files} files")
    print(f"  📝 Total fixes: {total_fixed}")

if __name__ == "__main__":
    main()
