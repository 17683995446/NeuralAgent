#!/usr/bin/env python3
"""
安全移除废弃 layers 目录脚本
在确认所有导入更新后执行
"""

import os
import shutil
from pathlib import Path


def main():
    root_dir = Path(__file__).parent.parent
    old_layers_dir = root_dir / "backend" / "layers"
    backup_dir = root_dir / "layers_backup"

    print("=" * 80)
    print("🗑️  REMOVING DEPRECATED LAYERS DIRECTORY")
    print("=" * 80)

    # 1. 检查是否已备份
    if not backup_dir.exists():
        print("\n❌ ERROR: Backup directory not found!")
        print("   Please run scripts/unify_architecture.py first to create backup")
        return False

    print(f"\n✅ Backup directory found: {backup_dir}")

    # 2. 检查备份内容
    backup_files = list(backup_dir.glob("*.py"))
    print(f"   Backup contains {len(backup_files)} Python files")

    # 3. 确认旧目录
    if not old_layers_dir.exists():
        print(f"\n✅ Old layers directory already removed: {old_layers_dir}")
        return True

    # 4. 列出旧目录内容
    print(f"\n📁 Old layers directory: {old_layers_dir}")
    old_files = list(old_layers_dir.glob("*.py"))
    print(f"   Contains {len(old_files)} Python files:")
    for f in sorted(old_files):
        print(f"   - {f.name}")

    # 5. 安全移除
    try:
        print("\n🗑️  Removing old layers directory...")
        shutil.rmtree(old_layers_dir)
        print(f"✅ Successfully removed: {old_layers_dir}")

        print("\n" + "=" * 80)
        print("✅ ARCHITECTURE UNIFICATION COMPLETE!")
        print("=" * 80)
        print("\n🎉 NeuralAgent now uses unified architecture:")
        print("   ✅ backend/core/neural_layers/ (new, complete 18-layer architecture)")
        print("   ❌ backend/layers/ (removed)")
        print()
        print("📋 Next steps:")
        print("   1. Run tests to verify everything works")
        print("   2. Update documentation")
        print("   3. Commit changes")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: Failed to remove directory: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
