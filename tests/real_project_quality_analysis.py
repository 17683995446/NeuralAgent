#!/usr/bin/env python3
"""
真实 GitHub 项目分析 - 发现代码质量与架构问题
这个测试分析真实代码，并从中发现实际问题
"""

import json
import logging
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class IssueSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class CodeIssue:
    """发现的代码问题"""
    issue_type: str
    severity: IssueSeverity
    file_path: str
    line_number: Optional[int] = None
    description: str = ""
    code_snippet: str = ""
    suggested_fix: str = ""


@dataclass
class FileAnalysis:
    """单个文件的分析结果"""
    file_path: str
    file_size_kb: float
    line_count: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    imports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    issues: List[CodeIssue] = field(default_factory=list)


@dataclass
class ProjectAnalysis:
    """项目整体分析结果"""
    name: str
    url: str
    total_files: int = 0
    python_files: int = 0
    total_lines: int = 0
    total_code_lines: int = 0
    total_comment_lines: int = 0
    total_blank_lines: int = 0
    files: List[FileAnalysis] = field(default_factory=list)
    all_issues: List[CodeIssue] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)


class CodeQualityAnalyzer:
    """代码质量分析器"""

    def __init__(self):
        self.issues: List[CodeIssue] = []
        self.analysis: Optional[ProjectAnalysis] = None

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """分析单个文件"""
        analysis = FileAnalysis(
            file_path=str(file_path),
            file_size_kb=0,
            line_count=0,
            code_lines=0,
            comment_lines=0,
            blank_lines=0
        )

        if not file_path.exists():
            return analysis

        try:
            analysis.file_size_kb = file_path.stat().st_size / 1024

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
                analysis.line_count = len(lines)

                # 分析每一行
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped:
                        analysis.blank_lines += 1
                    elif stripped.startswith('#') or stripped.startswith('//'):
                        analysis.comment_lines += 1
                    else:
                        analysis.code_lines += 1

                # 识别导入
                import_matches = re.findall(r'^(?:import|from)\s+([^\n]+)', content, re.MULTILINE)
                analysis.imports = [m.strip() for m in import_matches[:50]]  # 只取前50个

                # 识别类
                class_matches = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                analysis.classes = class_matches

                # 识别函数
                func_matches = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
                analysis.functions = func_matches

                # 查找常见问题
                file_issues = self._check_common_issues(content, lines, str(file_path))
                analysis.issues = file_issues
                self.issues.extend(file_issues)

        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")

        return analysis

    def _check_common_issues(self, content: str, lines: List[str], file_path: str) -> List[CodeIssue]:
        """检查常见代码问题"""
        issues: List[CodeIssue] = []

        # 1. 检查文件是否过长
        if len(lines) > 500:
            issues.append(CodeIssue(
                issue_type="long_file",
                severity=IssueSeverity.MEDIUM,
                file_path=file_path,
                description=f"File has {len(lines)} lines, consider splitting",
                suggested_fix="Split into multiple modular files"
            ))

        # 2. 检查 TODO / FIXME 注释
        for i, line in enumerate(lines, 1):
            if 'TODO' in line or 'FIXME' in line:
                issues.append(CodeIssue(
                    issue_type="todo_fixme",
                    severity=IssueSeverity.LOW,
                    file_path=file_path,
                    line_number=i,
                    description="Found TODO/FIXME comment",
                    code_snippet=line.strip()
                ))

        # 3. 检查长函数（通过计算缩进）
        function_depth = 0
        func_start_line = -1
        func_name = ""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('def '):
                func_start_line = i
                function_depth = len(line) - len(line.lstrip())
                match = re.match(r'def\s+(\w+)', stripped)
                if match:
                    func_name = match.group(1)
            elif func_start_line >= 0 and stripped:
                current_depth = len(line) - len(line.lstrip())
                if current_depth <= function_depth and not stripped.startswith(('if', 'elif', 'else', 'for', 'while', 'try', 'except')):
                    func_length = i - func_start_line
                    if func_length > 50:
                        issues.append(CodeIssue(
                            issue_type="long_function",
                            severity=IssueSeverity.MEDIUM,
                            file_path=file_path,
                            line_number=func_start_line,
                            description=f"Function '{func_name}' has {func_length} lines",
                            suggested_fix="Refactor into smaller functions"
                        ))
                    func_start_line = -1

        # 4. 检查复杂条件
        for i, line in enumerate(lines, 1):
            if 'if ' in line and line.count(' and ') > 2 or line.count(' or ') > 2:
                issues.append(CodeIssue(
                    issue_type="complex_condition",
                    severity=IssueSeverity.LOW,
                    file_path=file_path,
                    line_number=i,
                    description="Complex condition, consider simplifying",
                    code_snippet=line.strip()
                ))

        return issues

    def analyze_project(self, project_path: Path, project_name: str, project_url: str) -> ProjectAnalysis:
        """分析整个项目"""
        logger.info(f"Starting deep analysis of {project_name}...")
        start_time = time.time()

        analysis = ProjectAnalysis(
            name=project_name,
            url=project_url
        )

        for root, dirs, files in os.walk(project_path):
            # 跳过不需要分析的目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', 'venv', '.venv']]

            for file in files:
                if file.endswith('.py'):
                    analysis.total_files += 1
                    analysis.python_files += 1
                    file_path = Path(root) / file
                    try:
                        file_analysis = self.analyze_file(file_path)
                        analysis.files.append(file_analysis)

                        analysis.total_lines += file_analysis.line_count
                        analysis.total_code_lines += file_analysis.code_lines
                        analysis.total_comment_lines += file_analysis.comment_lines
                        analysis.total_blank_lines += file_analysis.blank_lines

                    except Exception as e:
                        logger.warning(f"Failed to process {file_path}: {e}")

        analysis.all_issues = self.issues

        # 分析项目模式
        analysis.patterns = self._identify_project_patterns(project_path)

        elapsed = time.time() - start_time
        logger.info(f"✓ Analysis complete in {elapsed:.1f}s - {analysis.total_files} files")

        return analysis

    def _identify_project_patterns(self, project_path: Path) -> List[str]:
        """识别项目模式"""
        patterns = []

        files_to_check = ['pyproject.toml', 'setup.py', 'requirements.txt', 'README.md', 'Dockerfile']
        for file in files_to_check:
            if (project_path / file).exists():
                patterns.append(file)

        # 检查架构模式
        has_backend = (project_path / 'backend').exists()
        has_frontend = (project_path / 'frontend').exists()
        has_tests = (project_path / 'tests').exists()
        has_api = (project_path / 'api').exists()

        if has_backend:
            patterns.append('backend_architecture')
        if has_frontend:
            patterns.append('frontend_architecture')
        if has_tests:
            patterns.append('has_tests')
        if has_api:
            patterns.append('api_structure')

        return patterns


class NeuralAgentCodeAnalyzer:
    """分析 NeuralAgent 代码库的问题"""

    def __init__(self, neural_agent_root: Path):
        self.root = neural_agent_root
        self.issues: List[Dict[str, Any]] = []

    def analyze_architecture(self) -> List[Dict[str, Any]]:
        """分析架构问题"""
        logger.info("Analyzing NeuralAgent architecture...")
        issues: List[Dict[str, Any]] = []

        # 1. 检查重复的目录结构
        layers_dirs = [
            self.root / 'backend' / 'layers',
            self.root / 'backend' / 'core' / 'neural_layers'
        ]

        existing_layers_dirs = [str(d) for d in layers_dirs if d.exists()]
        if len(existing_layers_dirs) > 1:
            issues.append({
                'severity': 'CRITICAL',
                'issue_type': 'duplicate_layers_dirs',
                'description': f"Multiple layer directories found: {', '.join(existing_layers_dirs)}",
                'suggested_fix': 'Consolidate into one unified layer structure'
            })

        # 2. 检查缺少的 __init__.py
        core_dir = self.root / 'backend' / 'core'
        if core_dir.exists():
            for item in core_dir.iterdir():
                if item.is_dir() and not (item / '__init__.py').exists():
                    if item.name not in ['__pycache__']:
                        issues.append({
                            'severity': 'MEDIUM',
                            'issue_type': 'missing_init',
                            'description': f"Directory '{item.name}' missing __init__.py",
                            'suggested_fix': 'Add __init__.py to make it a Python package'
                        })

        # 3. 检查依赖问题
        req_file = self.root / 'requirements-minimal.txt'
        if req_file.exists():
            issues.extend(self._analyze_requirements(req_file))

        return issues

    def _analyze_requirements(self, req_file: Path) -> List[Dict[str, Any]]:
        """分析 requirements 问题"""
        issues: List[Dict[str, Any]] = []

        with open(req_file, 'r') as f:
            content = f.read()

        critical_deps = ['fastapi', 'uvicorn', 'pydantic']
        for dep in critical_deps:
            if dep not in content:
                issues.append({
                    'severity': 'HIGH',
                    'issue_type': 'missing_dependency',
                    'description': f"Critical dependency '{dep}' not found in requirements",
                    'suggested_fix': f"Add {dep} to requirements"
                })

        return issues


def clone_repo(url: str, dest_dir: Path) -> Tuple[bool, str]:
    """克隆仓库"""
    logger.info(f"Cloning {url}...")
    try:
        subprocess.run(
            ['git', 'clone', '--depth', '1', url, str(dest_dir)],
            capture_output=True,
            text=True,
            timeout=300,
            check=True
        )
        return True, str(dest_dir)
    except Exception as e:
        logger.error(f"Failed to clone: {e}")
        return False, str(e)


def generate_report(
    project_analysis: ProjectAnalysis,
    neural_agent_issues: List[Dict[str, Any]],
    output_dir: Path
) -> Dict[str, Any]:
    """生成报告"""

    # 统计问题
    issues_by_severity = {
        'CRITICAL': [i for i in project_analysis.all_issues if i.severity == IssueSeverity.CRITICAL],
        'HIGH': [i for i in project_analysis.all_issues if i.severity == IssueSeverity.HIGH],
        'MEDIUM': [i for i in project_analysis.all_issues if i.severity == IssueSeverity.MEDIUM],
        'LOW': [i for i in project_analysis.all_issues if i.severity == IssueSeverity.LOW],
    }

    report = {
        'generated_at': datetime.now().isoformat(),
        'project_info': {
            'name': project_analysis.name,
            'url': project_analysis.url,
            'total_files': project_analysis.total_files,
            'python_files': project_analysis.python_files,
            'total_lines': project_analysis.total_lines,
            'code_lines': project_analysis.total_code_lines,
            'comment_lines': project_analysis.total_comment_lines,
            'patterns': project_analysis.patterns
        },
        'code_quality_issues': {
            'total': len(project_analysis.all_issues),
            'by_severity': {k: len(v) for k, v in issues_by_severity.items()},
            'sample_issues': [
                {
                    'type': i.issue_type,
                    'severity': i.severity.value,
                    'file': i.file_path,
                    'line': i.line_number,
                    'description': i.description
                }
                for i in project_analysis.all_issues[:20]
            ]
        },
        'neural_agent_issues': neural_agent_issues
    }

    # 保存报告
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / 'full_analysis_report.json'

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🧪 NEURALAGENT - REAL GITHUB PROJECT & CODEBASE ANALYSIS")
    logger.info("=" * 80)

    output_dir = Path(tempfile.mkdtemp(prefix="neural_agent_analysis_"))
    logger.info(f"Output directory: {output_dir}")

    # 测试项目
    test_projects = [
        {
            'name': 'Click',
            'url': 'https://github.com/pallets/click.git'
        },
        {
            'name': 'HTTPie',
            'url': 'https://github.com/httpie/httpie.git'
        }
    ]

    all_project_analyses = []

    for project in test_projects:
        project_dir = output_dir / project['name']

        # 克隆项目
        success, message = clone_repo(project['url'], project_dir)
        if not success:
            logger.warning(f"Skipping {project['name']}: {message}")
            continue

        # 分析项目
        analyzer = CodeQualityAnalyzer()
        project_analysis = analyzer.analyze_project(project_dir, project['name'], project['url'])
        all_project_analyses.append(project_analysis)

    # 分析 NeuralAgent 自身
    neural_agent_root = Path(__file__).parent.parent
    neural_analyzer = NeuralAgentCodeAnalyzer(neural_agent_root)
    neural_agent_issues = neural_analyzer.analyze_architecture()

    # 生成报告
    if all_project_analyses:
        final_report = generate_report(
            all_project_analyses[0],  # 用第一个项目作为主分析
            neural_agent_issues,
            output_dir
        )

        # 打印报告
        logger.info("\n" + "=" * 80)
        logger.info("📊 FINAL REPORT")
        logger.info("=" * 80)

        logger.info(f"\n🎯 Project Analyzed: {all_project_analyses[0].name}")
        logger.info(f"   Total lines: {all_project_analyses[0].total_lines:,}")
        logger.info(f"   Python files: {all_project_analyses[0].python_files}")

        logger.info(f"\n🐛 Issues Found:")
        total_issues = len(all_project_analyses[0].all_issues)
        logger.info(f"   Total issues: {total_issues}")

        logger.info(f"\n🔍 NeuralAgent Architecture Issues:")
        for i, issue in enumerate(neural_agent_issues, 1):
            logger.info(f"   {i}. [{issue['severity']}] {issue['description']}")

        logger.info(f"\n📁 Report saved to: {output_dir}")

    else:
        logger.warning("No projects analyzed successfully")


if __name__ == '__main__':
    main()
