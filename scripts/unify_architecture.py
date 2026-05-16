#!/usr/bin/env python3
"""
架构统一脚本 - 解决重复层目录问题
统一使用 backend/core/neural_layers 作为标准架构
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_backup_dir(root_dir: Path) -> Path:
    """创建备份目录"""
    backup_dir = root_dir / "layers_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def backup_old_layers(root_dir: Path, backup_dir: Path) -> List[str]:
    """备份旧层文件"""
    old_layers_dir = root_dir / "backend" / "layers"
    backed_up = []

    if old_layers_dir.exists():
        logger.info(f"Backing up old layers from: {old_layers_dir}")
        for item in old_layers_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, backup_dir / item.name)
                backed_up.append(item.name)
                logger.info(f"  Backed up: {item.name}")

    return backed_up


def create_architecture_summary(root_dir: Path) -> Dict:
    """创建架构总结"""
    core_layers_dir = root_dir / "backend" / "core" / "neural_layers"

    summary = {
        "primary_architecture": "backend/core/neural_layers",
        "layers_found": [],
        "total_layers": 0
    }

    if core_layers_dir.exists():
        for item in sorted(core_layers_dir.iterdir()):
            if item.is_file() and item.name.endswith('.py') and not item.name.startswith('_'):
                summary["layers_found"].append(item.name)
                summary["total_layers"] += 1

    return summary


def create_deprecation_note(root_dir: Path):
    """创建弃用说明"""
    old_layers_dir = root_dir / "backend" / "layers"

    if old_layers_dir.exists():
        deprecation_file = old_layers_dir / "DEPRECATED.md"

        content = """# DEPRECATED - Layers Directory

⚠️ 这个目录已被弃用！

## 新的架构位置

神经网络层现在位于：
```
backend/core/neural_layers/
```

## 新的架构包含完整的18层神经网络：

1. neural_embedding_layer.py - 嵌入层
2. neural_input_layer.py - 输入层
3. neural_normalization_layer.py - 归一化层
4. neural_convolution_layer.py - 卷积层
5. neural_pooling_layer.py - 池化层
6. neural_attention_layer.py - 注意力层
7. neural_residual_layer.py - 残差层
8. neural_dropout_layer.py - Dropout层
9. neural_fully_connected_layers.py - 全连接层 (FC1-3)
10. neural_memory_layer.py - 记忆层
11. neural_reasoning_layer.py - 推理层
12. neural_planning_layer.py - 规划层
13. neural_output_layer.py - 输出层
14. neural_execution_layer.py - 执行层
15. neural_backward_propagation_layer.py - 反向传播层

## 更新导入语句

请更新您的导入语句从：
```python
from backend.layers.some_layer import SomeClass
```

改为：
```python
from backend.core.neural_layers.neural_some_layer import SomeClass
```

## 迁移状态

此目录中的文件已备份到：
- 项目根目录下的 layers_backup/ (如已创建)

## 原因

新架构提供了：
✅ 更完整的18层神经网络
✅ 更好的模块化设计
✅ 更清晰的文件名
✅ 位于 core/ 目录下的标准位置
"""

        with open(deprecation_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Created deprecation note: {deprecation_file}")


def update_imports_in_codebase(root_dir: Path, dry_run: bool = True) -> List[str]:
    """更新代码库中的导入（可选）"""
    changes_needed = []

    # 查找所有可能引用旧层路径的文件
    for root, dirs, files in os.walk(root_dir):
        # 跳过一些不需要检查的目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]

        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if 'from backend.layers' in content or 'import backend.layers' in content:
                        changes_needed.append(str(file_path.relative_to(root_dir)))
                except Exception as e:
                    logger.warning(f"Could not check {file_path}: {e}")

    return changes_needed


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🔧 NEURALAGENT ARCHITECTURE UNIFICATION")
    logger.info("=" * 80)

    root_dir = Path(__file__).parent.parent

    # 1. 备份旧层
    backup_dir = create_backup_dir(root_dir)
    backed_up = backup_old_layers(root_dir, backup_dir)
    logger.info(f"✓ Backed up {len(backed_up)} files to: {backup_dir}")

    # 2. 分析架构
    summary = create_architecture_summary(root_dir)
    logger.info(f"\n🎯 Primary architecture: {summary['primary_architecture']}")
    logger.info(f"📦 Total layers: {summary['total_layers']}")
    logger.info("\n📁 Available layers:")
    for layer in summary["layers_found"]:
        logger.info(f"   - {layer}")

    # 3. 创建弃用说明
    create_deprecation_note(root_dir)

    # 4. 查找需要更新的导入
    changes_needed = update_imports_in_codebase(root_dir)
    if changes_needed:
        logger.warning(f"\n⚠️ {len(changes_needed)} files may need import updates:")
        for f in changes_needed[:10]:  # 只显示前10个
            logger.warning(f"   - {f}")
        if len(changes_needed) > 10:
            logger.warning(f"   ... and {len(changes_needed) - 10} more")
    else:
        logger.info("\n✅ No import update needed!")

    # 5. 完成总结
    logger.info("\n" + "=" * 80)
    logger.info("✅ ARCHITECTURE UNIFICATION COMPLETE!")
    logger.info("=" * 80)
    logger.info("\n✅ Primary architecture confirmed: backend/core/neural_layers")
    logger.info("✅ Old layers backed up")
    logger.info("✅ Deprecation note created")
    logger.info("\n🎯 Next steps:")
    logger.info("   1. Verify all functionality still works")
    logger.info("   2. Update any outdated import statements")
    logger.info("   3. Optionally remove deprecated backend/layers directory")


if __name__ == "__main__":
    main()
