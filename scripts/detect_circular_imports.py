"""循环导入检测工具

帮助识别和解决Python模块间的循环导入问题
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import ast


class ImportAnalyzer(ast.NodeVisitor):
    """分析Python文件中的导入语句"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.imports: Set[str] = set()
        self.from_imports: Dict[str, Set[str]] = defaultdict(set)
    
    def visit_Import(self, node):
        """处理 import 语句"""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """处理 from ... import 语句"""
        if node.module:
            self.from_imports[node.module].add(node.module)
        self.generic_visit(node)


class CircularImportDetector:
    """循环导入检测器"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.modules: Dict[str, ImportAnalyzer] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
    
    def scan_directory(self, package: str = "backend") -> Dict[str, ImportAnalyzer]:
        """扫描目录中的所有Python文件"""
        package_path = self.root_dir / package
        
        if not package_path.exists():
            print(f"Package path not found: {package_path}")
            return {}
        
        for py_file in package_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            # 计算模块名
            rel_path = py_file.relative_to(self.root_dir)
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            module_name = ".".join(module_parts)
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                analyzer = ImportAnalyzer(module_name)
                analyzer.visit(tree)
                self.modules[module_name] = analyzer
                
                # 记录依赖关系
                for imported in analyzer.imports:
                    if imported.startswith(package):
                        self.dependencies[module_name].add(imported)
                
                for from_module, _ in analyzer.from_imports.items():
                    if from_module.startswith(package):
                        self.dependencies[module_name].add(from_module)
                        
            except Exception as e:
                print(f"Error parsing {py_file}: {e}")
        
        return self.modules
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """使用DFS找到循环依赖"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(module: str):
            visited.add(module)
            rec_stack.add(module)
            path.append(module)
            
            for dep in self.dependencies.get(module, set()):
                if dep not in visited:
                    dfs(dep)
                elif dep in rec_stack:
                    # 找到循环
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    cycles.append(cycle)
            
            path.pop()
            rec_stack.remove(module)
        
        for module in self.modules:
            if module not in visited:
                dfs(module)
        
        return cycles
    
    def generate_report(self) -> Dict[str, any]:
        """生成循环导入分析报告"""
        cycles = self.find_circular_dependencies()
        
        return {
            "total_modules": len(self.modules),
            "modules_with_imports": sum(1 for m in self.modules.values() if m.imports or m.from_imports),
            "circular_dependencies": cycles,
            "dependency_graph": dict(self.dependencies)
        }


def fix_circular_import_issue(file_path: str, import_statement: str) -> str:
    """生成修复循环导入的建议代码"""
    suggestions = []
    
    # 建议1: 使用 TYPE_CHECKING
    suggestions.append(f"""
# 在 {file_path} 中，建议将导入移到 TYPE_CHECKING 块中：
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    {import_statement}
""")
    
    # 建议2: 延迟导入
    suggestions.append(f"""
# 或使用延迟导入：
def get_module():
    {import_statement}
    return 模块名
""")
    
    return "\n".join(suggestions)


if __name__ == "__main__":
    # 示例使用
    root_dir = "/workspace/neural_agent"
    
    print("🔍 Analyzing circular imports in NeuralAgent project...")
    print("=" * 60)
    
    detector = CircularImportDetector(root_dir)
    detector.scan_directory("backend")
    
    report = detector.generate_report()
    
    print(f"\n📊 Analysis Results:")
    print(f"  Total modules scanned: {report['total_modules']}")
    print(f"  Modules with imports: {report['modules_with_imports']}")
    print(f"  Circular dependencies found: {len(report['circular_dependencies'])}")
    
    if report['circular_dependencies']:
        print(f"\n⚠️  Circular Dependencies Detected:")
        for i, cycle in enumerate(report['circular_dependencies'], 1):
            print(f"  {i}. {' -> '.join(cycle)}")
    else:
        print(f"\n✅ No circular dependencies detected!")
    
    # 打印依赖关系（前10个）
    print(f"\n📦 Top 10 Module Dependencies:")
    sorted_deps = sorted(
        report['dependency_graph'].items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:10]
    
    for module, deps in sorted_deps:
        if deps:
            print(f"  {module}:")
            for dep in sorted(deps)[:5]:
                print(f"    -> {dep}")
