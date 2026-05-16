#!/usr/bin/env python3
"""Generate Project Tree - 生成项目目录树
"""

import os
from pathlib import Path


def print_tree(root_path: Path, prefix: str = ""):
    """递归打印目录树
    
    Args:
        root_path: 根目录路径
        prefix: 前缀（用于缩进）
    """
    # 获取目录内容
    items = sorted(list(root_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
    
    # 过滤项
    filtered_items = []
    for item in items:
        # 跳过一些不需要显示的
        if item.name in ['.git', '__pycache__', 'node_modules', '.pytest_cache', '.env']:
            continue
        if item.name.endswith('.pyc'):
            continue
        filtered_items.append(item)
    
    items = filtered_items
    
    # 打印
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        
        # 选择连接符号
        connector = "└── " if is_last else "├── "
        
        print(prefix + connector + item.name)
        
        # 如果是目录，递归
        if item.is_dir():
            # 新的前缀
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(item, new_prefix)


def main():
    """主函数"""
    project_root = Path("/workspace/neural_agent")
    
    print("=" * 70)
    print("📁 NeuralAgent 项目目录结构")
    print("=" * 70)
    print()
    
    print_tree(project_root)
    
    print()
    print("=" * 70)
    print("✅ 目录树生成完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
