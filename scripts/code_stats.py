#!/usr/bin/env python3
"""Code Statistics - 代码统计工具

统计项目的代码行数、文件数、模块数等。
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def count_lines_in_file(file_path: Path) -> Tuple[int, int, int]:
    """统计单个文件的行数"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if line.strip() == '')
        comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '""', "'''")))
        code_lines = total_lines - blank_lines - comment_lines
        
        return total_lines, code_lines, blank_lines + comment_lines
    except Exception as e:
        return 0, 0, 0


def is_python_file(file_path: Path) -> bool:
    """判断是否是Python文件"""
    return file_path.suffix == '.py'


def is_module_directory(dir_path: Path) -> bool:
    """判断是否是Python模块目录（有__init__.py）"""
    return (dir_path / '__init__.py').exists()


def get_directory_stats(root_path: Path) -> Dict[str, List[str]]:
    """获取目录统计"""
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'code_lines': 0,
        'comment_blank_lines': 0,
        'python_files': 0,
        'modules': 0,
        'directories': 0,
        'file_types': {}
    }
    
    modules_found = []
    
    for dir_path, subdirs, files in os.walk(root_path):
        dir_path = Path(dir_path)
        
        # 跳过特殊目录
        if '__pycache__' in dir_path.parts or '.git' in dir_path.parts:
            continue
        
        # 统计目录数
        if dir_path != root_path:
            stats['directories'] += 1
        
        # 检查是否是Python模块
        if is_module_directory(dir_path):
            stats['modules'] += 1
            modules_found.append(str(dir_path.relative_to(root_path)))
        
        for file in files:
            file_path = dir_path / file
            stats['total_files'] += 1
            
            if is_python_file(file_path):
                stats['python_files'] += 1
                
                # 统计文件
                total, code, comment = count_lines_in_file(file_path)
                stats['total_lines'] += total
                stats['code_lines'] += code
                stats['comment_blank_lines'] += comment
                
                # 文件类型统计
                ext = file_path.suffix
                if ext not in stats['file_types']:
                    stats['file_types'][ext] = 0
                stats['file_types'][ext] += 1
    
    stats['modules_found'] = modules_found
    return stats


def main():
    """主函数"""
    project_root = Path('/workspace/neural_agent')
    
    print("=" * 70)
    print("📊 NeuralAgent 代码统计")
    print("=" * 70)
    print()
    
    # 统计整个项目
    print("📁 项目根目录:", str(project_root))
    print()
    
    # 统计backend/core目录（核心模块）
    core_stats = get_directory_stats(project_root / 'backend' / 'core')
    full_stats = get_directory_stats(project_root)
    
    # 显示统计
    print("-" * 70)
    print("🎯 核心模块统计 (backend/core)")
    print("-" * 70)
    print(f"  Python文件数:     {core_stats['python_files']}")
    print(f"  模块数:        {core_stats['modules']}")
    print(f"  目录数:        {core_stats['directories']}")
    print()
    print(f"  总行数:        {core_stats['total_lines']:,}")
    print(f"  代码行数:      {core_stats['code_lines']:,}")
    print(f"  注释/空行数:  {core_stats['comment_blank_lines']:,}")
    print()
    
    print("-" * 70)
    print("🌐 完整项目统计")
    print("-" * 70)
    print(f"  总文件数:       {full_stats['total_files']}")
    print(f"  Python文件数:    {full_stats['python_files']}")
    print(f"  目录数:         {full_stats['directories']}")
    print(f"  模块数:          {full_stats['modules']}")
    print()
    print(f"  总行数:          {full_stats['total_lines']:,}")
    print(f"  代码行数:        {full_stats['code_lines']:,}")
    print(f"  注释/空行数:    {full_stats['comment_blank_lines']:,}")
    print()
    
    # 文件类型分布
    print("-" * 70)
    print("📄 文件类型分布")
    print("-" * 70)
    for ext, count in sorted(full_stats['file_types'].items()):
        print(f"  {ext:20s}: {count}")
    print()
    
    # 模块列表（前20）
    print("-" * 70)
    print("📦 核心模块列表")
    print("-" * 70)
    for i, module in enumerate(core_stats['modules_found'][:20], 1):
        print(f"  {i}. {module}")
    
    if len(core_stats['modules_found']) > 20:
        print(f"  ... 还有 {len(core_stats['modules_found']) - 20} 个模块")
    
    print()
    
    print("=" * 70)
    print("✅ 统计完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
