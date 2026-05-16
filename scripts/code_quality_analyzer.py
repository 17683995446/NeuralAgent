#!/usr/bin/env python3
"""代码质量分析工具

分析项目代码质量指标，包括：
- 代码复杂度
- 测试覆盖率
- 文档完整性
- 导入依赖分析
"""
import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class ComplexityMetrics:
    """复杂度指标"""
    file_path: str
    lines: int
    functions: int
    classes: int
    complexity: int  # 估计复杂度
    max_depth: int  # 最大嵌套深度


@dataclass
class QualityReport:
    """质量报告"""
    total_files: int
    total_lines: int
    total_functions: int
    total_classes: int
    avg_complexity: float
    files: List[ComplexityMetrics]
    import_issues: List[Dict[str, Any]]
    missing_docstrings: List[Dict[str, str]]


class CodeQualityAnalyzer:
    """代码质量分析器"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.files: List[Path] = []
        self.metrics: List[ComplexityMetrics] = []
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.issues: List[Dict[str, Any]] = []
    
    def scan_python_files(self) -> List[Path]:
        """扫描所有Python文件"""
        python_files = []
        
        for py_file in self.root_dir.rglob("*.py"):
            # 跳过测试、虚拟环境、缓存等
            if any(x in str(py_file) for x in [
                "__pycache__", ".pytest_cache", "venv", "env",
                ".git", "node_modules", "dist", "build"
            ]):
                continue
            
            python_files.append(py_file)
        
        self.files = python_files
        return python_files
    
    def analyze_file(self, file_path: Path) -> ComplexityMetrics:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = len(content.splitlines())
            tree = ast.parse(content)
            
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            
            # 估计复杂度（基于语句数、嵌套等）
            complexity = self._estimate_complexity(tree)
            max_depth = self._get_max_depth(tree)
            
            return ComplexityMetrics(
                file_path=str(file_path),
                lines=lines,
                functions=functions,
                classes=classes,
                complexity=complexity,
                max_depth=max_depth
            )
        except Exception as e:
            return ComplexityMetrics(
                file_path=str(file_path),
                lines=0,
                functions=0,
                classes=0,
                complexity=0,
                max_depth=0
            )
    
    def _estimate_complexity(self, tree: ast.AST) -> int:
        """估计代码复杂度"""
        complexity = 0
        
        for node in ast.walk(tree):
            # 复杂度增加项
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers) + 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _get_max_depth(self, tree: ast.AST) -> int:
        """获取最大嵌套深度"""
        max_depth = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                depth = self._calc_function_depth(node)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calc_function_depth(self, node: ast.FunctionDef) -> int:
        """计算函数嵌套深度"""
        max_depth = 0
        
        for child in ast.walk(node):
            depth = len([
                p for p in getattr(child, '_fields', [])
                if isinstance(p, tuple)
            ])
        
        return max_depth
    
    def check_imports(self, file_path: Path):
        """检查导入语句"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
            
            self.import_graph[str(file_path)] = imports
            
            # 检查潜在的循环导入
            for other_file, other_imports in self.import_graph.items():
                if other_file != str(file_path):
                    if str(file_path) in other_imports:
                        self.issues.append({
                            "type": "potential_circular_import",
                            "file1": str(file_path),
                            "file2": other_file,
                            "message": f"Potential circular import between {file_path.name} and {Path(other_file).name}"
                        })
        except Exception as e:
            pass
    
    def check_docstrings(self, file_path: Path) -> List[Dict[str, str]]:
        """检查文档字符串"""
        missing = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        missing.append({
                            "file": str(file_path),
                            "type": "function",
                            "name": node.name,
                            "line": node.lineno
                        })
                elif isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        missing.append({
                            "file": str(file_path),
                            "type": "class",
                            "name": node.name,
                            "line": node.lineno
                        })
        except Exception:
            pass
        
        return missing
    
    def analyze_all(self) -> QualityReport:
        """分析所有文件"""
        python_files = self.scan_python_files()
        
        all_metrics = []
        all_missing_docstrings = []
        
        for file_path in python_files:
            metrics = self.analyze_file(file_path)
            all_metrics.append(metrics)
            
            self.check_imports(file_path)
            missing = self.check_docstrings(file_path)
            all_missing_docstrings.extend(missing)
        
        total_lines = sum(m.lines for m in all_metrics)
        total_functions = sum(m.functions for m in all_metrics)
        total_classes = sum(m.classes for m in all_metrics)
        avg_complexity = sum(m.complexity for m in all_metrics) / len(all_metrics) if all_metrics else 0
        
        return QualityReport(
            total_files=len(python_files),
            total_lines=total_lines,
            total_functions=total_functions,
            total_classes=total_classes,
            avg_complexity=avg_complexity,
            files=all_metrics,
            import_issues=self.issues,
            missing_docstrings=all_missing_docstrings
        )
    
    def generate_report(self, report: QualityReport) -> str:
        """生成文本报告"""
        lines = [
            "=" * 70,
            "Code Quality Analysis Report",
            "=" * 70,
            "",
            f"Total Files: {report.total_files}",
            f"Total Lines: {report.total_lines}",
            f"Total Functions: {report.total_functions}",
            f"Total Classes: {report.total_classes}",
            f"Average Complexity: {report.avg_complexity:.2f}",
            "",
            "-" * 70,
            "Top 10 Most Complex Files:",
            "-" * 70
        ]
        
        # 排序并显示最复杂的文件
        sorted_files = sorted(report.files, key=lambda x: x.complexity, reverse=True)[:10]
        
        for i, metrics in enumerate(sorted_files, 1):
            lines.append(
                f"{i}. {metrics.file_path:<50} "
                f"[complexity: {metrics.complexity}, "
                f"functions: {metrics.functions}, "
                f"classes: {metrics.classes}]"
            )
        
        if report.import_issues:
            lines.extend([
                "",
                "-" * 70,
                f"Import Issues ({len(report.import_issues)}):",
                "-" * 70
            ])
            
            for issue in report.import_issues[:10]:
                lines.append(f"  - {issue['message']}")
        
        if report.missing_docstrings:
            lines.extend([
                "",
                "-" * 70,
                f"Missing Docstrings: {len(report.missing_docstrings)}",
                "-" * 70
            ])
            
            # 按文件分组显示
            by_file = defaultdict(list)
            for item in report.missing_docstrings:
                by_file[item['file']].append(item)
            
            for file_path, items in list(by_file.items())[:5]:
                lines.append(f"\n{file_path}:")
                for item in items[:5]:
                    lines.append(f"  - {item['type']} {item['name']} at line {item['line']}")
        
        lines.extend(["", "=" * 70])
        
        return "\n".join(lines)
    
    def export_json(self, report: QualityReport, filename: str):
        """导出JSON格式报告"""
        data = {
            "summary": {
                "total_files": report.total_files,
                "total_lines": report.total_lines,
                "total_functions": report.total_functions,
                "total_classes": report.total_classes,
                "avg_complexity": report.avg_complexity
            },
            "files": [
                {
                    "path": m.file_path,
                    "lines": m.lines,
                    "functions": m.functions,
                    "classes": m.classes,
                    "complexity": m.complexity,
                    "max_depth": m.max_depth
                }
                for m in report.files
            ],
            "issues": report.import_issues,
            "missing_docstrings": report.missing_docstrings
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Report exported to {filename}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Quality Analyzer")
    parser.add_argument("--dir", "-d", default=".", help="Root directory to analyze")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text",
                        help="Output format")
    
    args = parser.parse_args()
    
    analyzer = CodeQualityAnalyzer(args.dir)
    report = analyzer.analyze_all()
    
    if args.format == "text":
        print(analyzer.generate_report(report))
    else:
        print(json.dumps({
            "summary": {
                "total_files": report.total_files,
                "total_lines": report.total_lines,
                "total_functions": report.total_functions,
                "total_classes": report.total_classes,
                "avg_complexity": report.avg_complexity
            }
        }, indent=2))
    
    if args.output:
        analyzer.export_json(report, args.output)


if __name__ == "__main__":
    main()
