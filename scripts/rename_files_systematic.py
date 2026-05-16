#!/usr/bin/env python3
"""系统化文件重命名脚本 - 将短文件名重命名为更语义化的长文件名"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path("/workspace/neural_agent")

RENAME_MAPPINGS = {
    # backend/layers/ 目录重命名
    "backend/layers/input_layer.py": "backend/layers/neural_input_processing_layer.py",
    "backend/layers/output_layer.py": "backend/layers/neural_output_generation_layer.py",
    "backend/layers/convolution_layer.py": "backend/layers/neural_convolution_analysis_layer.py",
    "backend/layers/pooling_layer.py": "backend/layers/neural_pooling_compression_layer.py",
    "backend/layers/fc_layer_1.py": "backend/layers/neural_fc_global_understanding_layer.py",
    "backend/layers/fc_layer_2.py": "backend/layers/neural_fc_code_generation_layer.py",
    "backend/layers/fc_layer_3.py": "backend/layers/neural_fc_test_generation_layer.py",
    "backend/layers/backward_layer.py": "backend/layers/neural_backward_propagation_layer.py",

    # backend/utils/ 目录重命名
    "backend/utils/helpers.py": "backend/utils/common_helper_functions.py",

    # backend/models/ 目录重命名
    "backend/models/database.py": "backend/models/persistent_data_models.py",

    # backend/services/ 目录重命名
    "backend/services/database_service.py": "backend/services/code_processing_database_service.py",
}

IMPORT_UPDATES = {
    # input_layer imports
    ("backend/layers/neural_input_processing_layer.py", "backend.layers.input_layer"): "backend.layers.neural_input_processing_layer",
    ("backend/layers/neural_input_processing_layer.py", "from backend.core.neural_layers.neural_input_layer"): "from backend.core.neural_layers.neural_input_layer",

    # output_layer imports
    ("backend/layers/neural_output_generation_layer.py", "backend.layers.output_layer"): "backend.layers.neural_output_generation_layer",
    ("backend/layers/neural_output_generation_layer.py", "from backend.core.neural_layers.neural_output_layer"): "from backend.core.neural_layers.neural_output_layer",

    # convolution_layer imports
    ("backend/layers/neural_convolution_analysis_layer.py", "backend.layers.convolution_layer"): "backend.layers.neural_convolution_analysis_layer",
    ("backend/layers/neural_convolution_analysis_layer.py", "from backend.core.neural_layers.neural_convolution_layer"): "from backend.core.neural_layers.neural_convolution_layer",

    # pooling_layer imports
    ("backend/layers/neural_pooling_compression_layer.py", "backend.layers.pooling_layer"): "backend.layers.neural_pooling_compression_layer",
    ("backend/layers/neural_pooling_compression_layer.py", "from backend.core.neural_layers.neural_pooling_layer"): "from backend.core.neural_layers.neural_pooling_layer",

    # fc_layer imports
    ("backend/layers/neural_fc_global_understanding_layer.py", "backend.layers.fc_layer_1"): "backend.layers.neural_fc_global_understanding_layer",
    ("backend/layers/neural_fc_global_understanding_layer.py", "from backend.core.neural_layers.neural_fully_connected_layers"): "from backend.core.neural_layers.neural_fully_connected_layers",

    ("backend/layers/neural_fc_code_generation_layer.py", "backend.layers.fc_layer_2"): "backend.layers.neural_fc_code_generation_layer",
    ("backend/layers/neural_fc_code_generation_layer.py", "from backend.core.neural_layers.neural_fully_connected_layers"): "from backend.core.neural_layers.neural_fully_connected_layers",

    ("backend/layers/neural_fc_test_generation_layer.py", "backend.layers.fc_layer_3"): "backend.layers.neural_fc_test_generation_layer",
    ("backend/layers/neural_fc_test_generation_layer.py", "from backend.core.neural_layers.neural_fully_connected_layers"): "from backend.core.neural_layers.neural_fully_connected_layers",

    # backward_layer imports
    ("backend/layers/neural_backward_propagation_layer.py", "backend.layers.backward_layer"): "backend.layers.neural_backward_propagation_layer",
    ("backend/layers/neural_backward_propagation_layer.py", "from backend.core.neural_layers.neural_backward_propagation_layer"): "from backend.core.neural_layers.neural_backward_propagation_layer",

    # helpers imports
    ("backend/utils/common_helper_functions.py", "backend.utils.helpers"): "backend.utils.common_helper_functions",
    ("backend/utils/common_helper_functions.py", "from backend.utils.helpers"): "from backend.utils.common_helper_functions",

    # database model imports
    ("backend/models/persistent_data_models.py", "backend.models.database"): "backend.models.persistent_data_models",
    ("backend/models/persistent_data_models.py", "from backend.models.database"): "from backend.models.persistent_data_models",

    # database service imports
    ("backend/services/code_processing_database_service.py", "backend.services.database_service"): "backend.services.code_processing_database_service",
    ("backend/services/code_processing_database_service.py", "from backend.services.database_service"): "from backend.services.code_processing_database_service",
}


def rename_files() -> List[Tuple[str, str]]:
    """重命名文件"""
    renamed = []

    for old_path, new_path in RENAME_MAPPINGS.items():
        old_full = PROJECT_ROOT / old_path
        new_full = PROJECT_ROOT / new_path

        if old_full.exists():
            new_full.parent.mkdir(parents=True, exist_ok=True)
            old_full.rename(new_full)
            renamed.append((old_path, new_path))
            print(f"✓ 重命名: {old_path} → {new_path}")
        else:
            print(f"⚠ 跳过（文件不存在）: {old_path}")

    return renamed


def update_imports_in_file(file_path: Path) -> bool:
    """更新单个文件中的导入语句"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        for (target_file, old_import), new_import in IMPORT_UPDATES.items():
            if target_file in str(file_path):
                if old_import in content:
                    content = content.replace(old_import, new_import)

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"✓ 更新导入: {file_path.name}")
            return True

        return False
    except Exception as e:
        print(f"✗ 更新失败 {file_path.name}: {e}")
        return False


def search_and_replace_imports(search_dir: Path) -> int:
    """搜索并替换所有文件中的导入语句"""
    updated_count = 0

    for py_file in search_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding='utf-8')
            original_content = content

            for (target_file, old_import), new_import in IMPORT_UPDATES.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)

            if content != original_content:
                py_file.write_text(content, encoding='utf-8')
                updated_count += 1
                print(f"✓ 更新: {py_file.relative_to(PROJECT_ROOT)}")

        except Exception as e:
            print(f"✗ 处理失败 {py_file}: {e}")

    return updated_count


def update_init_files(search_dir: Path) -> None:
    """更新 __init__.py 文件中的导入"""
    for init_file in search_dir.rglob("__init__.py"):
        if "__pycache__" in str(init_file):
            continue

        try:
            content = init_file.read_text(encoding='utf-8')
            original_content = content

            for old, new in RENAME_MAPPINGS.items():
                old_module = old.replace("/", ".").replace(".py", "")
                new_module = new.replace("/", ".").replace(".py", "")

                if old_module in content:
                    content = content.replace(old_module, new_module)

            if content != original_content:
                init_file.write_text(content, encoding='utf-8')
                print(f"✓ 更新__init__: {init_file.relative_to(PROJECT_ROOT)}")

        except Exception as e:
            print(f"✗ 更新__init__失败 {init_file}: {e}")


def main():
    print("=" * 70)
    print("🚀 开始系统化文件重命名")
    print("=" * 70)
    print()

    print("📁 步骤1: 重命名文件...")
    renamed = rename_files()
    print(f"   完成: {len(renamed)} 个文件重命名\n")

    print("📝 步骤2: 更新导入语句...")
    updated = search_and_replace_imports(PROJECT_ROOT / "backend")
    print(f"   完成: {updated} 个文件更新导入\n")

    print("📦 步骤3: 更新 __init__.py 文件...")
    update_init_files(PROJECT_ROOT / "backend")

    print()
    print("=" * 70)
    print("✅ 重命名完成!")
    print("=" * 70)

    print("\n📋 重命名映射表:")
    for old, new in RENAME_MAPPINGS.items():
        print(f"  {old}")
        print(f"    → {new}\n")


if __name__ == "__main__":
    main()
