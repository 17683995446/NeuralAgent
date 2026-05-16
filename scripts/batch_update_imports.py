#!/usr/bin/env python3
"""
批量更新废弃导入路径脚本
自动将所有 backend.layers 导入更新为 backend.core.neural_layers
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def get_import_mappings():
    """获取所有导入映射关系"""
    return [
        # 旧导入 -> 新导入
        ("from backend.core.neural_layers.neural_input_layer", "from backend.core.neural_layers.neural_input_layer"),
        ("from backend.core.neural_layers.neural_output_layer", "from backend.core.neural_layers.neural_output_layer"),
        ("from backend.core.neural_layers.neural_convolution_layer", "from backend.core.neural_layers.neural_convolution_layer"),
        ("from backend.core.neural_layers.neural_pooling_layer", "from backend.core.neural_layers.neural_pooling_layer"),
        ("from backend.core.neural_layers.neural_fully_connected_layers", "from backend.core.neural_layers.neural_fully_connected_layers"),
        ("from backend.core.neural_layers.neural_fully_connected_layers", "from backend.core.neural_layers.neural_fully_connected_layers"),
        ("from backend.core.neural_layers.neural_fully_connected_layers", "from backend.core.neural_layers.neural_fully_connected_layers"),
        ("from backend.core.neural_layers.neural_backward_propagation_layer", "from backend.core.neural_layers.neural_backward_propagation_layer"),

        # 新名称的层
        ("from backend.core.neural_layers.neural_input_layer", "from backend.core.neural_layers.neural_input_layer"),
        ("from backend.core.neural_layers.neural_output_layer", "from backend.core.neural_layers.neural_output_layer"),
        ("from backend.core.neural_layers.neural_convolution_layer", "from backend.core.neural_layers.neural_convolution_layer"),
        ("from backend.core.neural_layers.neural_pooling_layer", "from backend.core.neural_layers.neural_pooling_layer"),
        ("from backend.core.neural_layers.neural_fully_connected_layers", "from backend.core.neural_layers.neural_fully_connected_layers"),
        ("from backend.core.neural_layers.neural_fully_connected_layers", "from backend.core.neural_layers.neural_fully_connected_layers"),
        ("from backend.core.neural_layers.neural_fully_connected_layers", "from backend.core.neural_layers.neural_fully_connected_layers"),
        ("from backend.core.neural_layers.neural_backward_propagation_layer", "from backend.core.neural_layers.neural_backward_propagation_layer"),
    ]


def get_class_mappings():
    """获取类名映射"""
    return [
        # Input Layer
        ("InputLayer", "InputLayer"),  # 保持不变
        # Output Layer
        ("OutputLayer", "OutputLayer"),  # 保持不变
        # Convolution Layer
        ("ConvolutionLayer", "ConvolutionLayer"),
        ("ConvolutionGranularity", "ConvolutionGranularity"),
        # Pooling Layer
        ("PoolingLayer", "PoolingLayer"),
        # FC Layers
        ("FCLayer1", "FCLayer"),
        ("FCLayer2", "FCLayer"),
        ("FCLayer3", "FCLayer"),
        # Backward Layer
        ("BackwardLayer", "BackwardLayer"),
        ("FeedbackProcessor", "FeedbackProcessor"),
    ]


def update_file(file_path: Path) -> Tuple[int, List[str]]:
    """更新单个文件的导入路径"""
    if not file_path.exists():
        return 0, []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = []

        # 更新导入路径
        for old_import, new_import in get_import_mappings():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes.append(f"{old_import} -> {new_import}")

        # 如果有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return len(changes), changes

        return 0, []

    except Exception as e:
        return 0, [f"Error: {e}"]


def find_files_needing_update(root_dir: Path) -> List[Path]:
    """查找需要更新的文件"""
    files = []

    for root, dirs, filenames in os.walk(root_dir):
        # 跳过不必要的目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'layers_backup']]

        for filename in filenames:
            if filename.endswith('.py'):
                file_path = Path(root) / filename
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'backend.layers.' in content or 'from backend.layers import' in content:
                            files.append(file_path)
                except Exception:
                    pass

    return files


def main():
    print("=" * 80)
    print("🔄 BATCH IMPORT PATH UPDATER")
    print("=" * 80)

    root_dir = Path(__file__).parent.parent

    # 1. 查找需要更新的文件
    print("\n📁 Searching for files with deprecated imports...")
    files_to_update = find_files_needing_update(root_dir)
    print(f"   Found {len(files_to_update)} files to update")

    # 2. 更新每个文件
    total_changes = 0
    updated_files = 0

    for file_path in files_to_update:
        changes_count, changes = update_file(file_path)
        if changes_count > 0:
            print(f"\n✅ {file_path.relative_to(root_dir)}")
            for change in changes:
                print(f"   {change}")
            total_changes += changes_count
            updated_files += 1

    # 3. 总结
    print("\n" + "=" * 80)
    print("✅ UPDATE COMPLETE!")
    print("=" * 80)
    print(f"   Updated files: {updated_files}")
    print(f"   Total changes: {total_changes}")

    if updated_files > 0:
        print("\n💡 Next steps:")
        print("   1. Verify imports work correctly")
        print("   2. Run tests to ensure nothing broke")
        print("   3. Consider removing backend/layers/ directory")


if __name__ == "__main__":
    main()
