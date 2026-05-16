#!/usr/bin/env python3
"""
真实 GitHub 项目深度测试 - NeuralAgent 实际使用场景
测试完整的工作流程：代码分析 -> 记忆存储 -> 模式识别 -> 问题发现
"""

import asyncio
import json
import logging
import os
import shutil
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

from backend.core.memory.enhanced_memory_system import (
    EnhancedMemorySystem,
    MemoryType,
    MemoryImportance,
)

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
class TestIssue:
    """测试中发现的问题"""
    name: str
    description: str
    severity: IssueSeverity
    category: str
    reproduction_steps: List[str] = field(default_factory=list)
    suggested_fix: str = ""
    stack_trace: str = ""


@dataclass
class ProjectAnalysis:
    """项目分析结果"""
    name: str
    python_files: int = 0
    total_lines: int = 0
    test_files: int = 0
    has_tests: bool = False
    has_requirements: bool = False
    has_readme: bool = False
    has_docker: bool = False
    has_ci: bool = False
    identified_patterns: List[str] = field(default_factory=list)


class RealGitHubProjectTester:
    """真实 GitHub 项目深度测试器"""

    # 选择真实且知名的开源项目进行测试
    TEST_PROJECTS = [
        {
            "name": "Click",
            "url": "https://github.com/pallets/click.git",
            "description": "Python composable command-line interface toolkit",
            "size": "small"
        },
        {
            "name": "FastAPI",
            "url": "https://github.com/tiangolo/fastapi.git",
            "description": "Modern Python web framework",
            "size": "large"
        },
        {
            "name": "Requests",
            "url": "https://github.com/psf/requests.git",
            "description": "HTTP library for humans",
            "size": "medium"
        },
    ]

    def __init__(self, test_dir: Optional[Path] = None):
        self.test_dir = test_dir or Path(tempfile.mkdtemp(prefix="neural_agent_real_test_"))
        self.memory_system = EnhancedMemorySystem()
        self.all_issues: List[TestIssue] = []
        self.analysis_results: Dict[str, ProjectAnalysis] = {}
        logger.info(f"Test directory: {self.test_dir}")

    def clone_project(self, project_url: str, project_name: str) -> Tuple[bool, Optional[Path]]:
        """克隆 GitHub 项目"""
        clone_path = self.test_dir / project_name

        if clone_path.exists():
            logger.info(f"Cleaning existing directory: {project_name}")
            shutil.rmtree(clone_path)

        logger.info(f"Cloning {project_name} from {project_url}...")
        start_time = time.time()

        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", project_url, str(clone_path)],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                elapsed = time.time() - start_time
                logger.info(f"✓ Successfully cloned {project_name} in {elapsed:.1f}s")
                return True, clone_path
            else:
                logger.error(f"Failed to clone {project_name}: {result.stderr}")
                return False, None

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout cloning {project_name}")
            return False, None
        except Exception as e:
            logger.error(f"Error cloning {project_name}: {e}")
            return False, None

    def analyze_project(self, project_path: Path, project_name: str) -> ProjectAnalysis:
        """深度分析项目结构"""
        logger.info(f"Deep analyzing {project_name}...")

        analysis = ProjectAnalysis(name=project_name)

        if not project_path.exists():
            return analysis

        # 统计项目文件
        for root, dirs, files in os.walk(project_path):
            # 跳过常见的不需要分析的目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', 'venv', '.venv']]

            for file in files:
                file_path = Path(root) / file

                if file.endswith('.py'):
                    analysis.python_files += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            analysis.total_lines += len(f.readlines())
                    except Exception:
                        pass

                if 'test' in file.lower() and file.endswith('.py'):
                    analysis.test_files += 1

                if file.lower() in ['readme.md', 'readme.txt', 'readme']:
                    analysis.has_readme = True
                if file.lower() in ['requirements.txt', 'pyproject.toml', 'setup.py']:
                    analysis.has_requirements = True
                if file.lower() in ['dockerfile', 'docker-compose.yml']:
                    analysis.has_docker = True

            # 检查 CI 配置
            ci_dir = project_path / '.github'
            if ci_dir.exists():
                analysis.has_ci = True

        analysis.has_tests = analysis.test_files > 0

        # 尝试识别一些代码模式
        analysis.identified_patterns = self._identify_patterns(project_path)

        logger.info(f"✓ Analysis complete: {analysis.python_files} Python files, {analysis.total_lines:,} lines")

        return analysis

    def _identify_patterns(self, project_path: Path) -> List[str]:
        """识别代码库中的设计模式"""
        patterns = []

        # 简单的模式识别
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if not file.endswith('.py'):
                    continue
                try:
                    with open(Path(root) / file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                        if 'class ' in content:
                            if 'Base' in content or 'Abstract' in content:
                                if 'OOP' not in patterns:
                                    patterns.append('OOP')
                            if 'Async' in content or 'async def' in content:
                                if 'Async' not in patterns:
                                    patterns.append('Async')

                        if 'from fastapi import' in content:
                            if 'FastAPI' not in patterns:
                                patterns.append('FastAPI')

                        if 'from click import' in content:
                            if 'Click' not in patterns:
                                patterns.append('Click')

                        if 'def test_' in content:
                            if 'PyTest' not in patterns:
                                patterns.append('PyTest')
                except Exception:
                    pass

        return patterns

    async def test_memory_with_real_code(self, project_path: Path, project_name: str) -> Tuple[bool, List[TestIssue]]:
        """使用真实代码测试记忆系统"""
        logger.info(f"Testing memory system with real {project_name} code...")
        issues: List[TestIssue] = []

        try:
            # 收集一些真实代码
            code_samples = []
            sample_count = 0

            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.py') and not file.startswith('_') and sample_count < 10:
                        try:
                            file_path = Path(root) / file
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if 50 < len(content) < 5000:  # 合适大小的样本
                                    code_samples.append({
                                        'path': str(file_path.relative_to(project_path)),
                                        'content': content[:2000]
                                    })
                                    sample_count += 1
                        except Exception:
                            pass

            if not code_samples:
                issue = TestIssue(
                    name="NoCodeSamples",
                    description="No suitable Python code samples found to test memory system",
                    severity=IssueSeverity.LOW,
                    category="memory"
                )
                issues.append(issue)
                return False, issues

            # 将真实代码存入记忆系统
            start_time = time.time()
            for i, sample in enumerate(code_samples):
                await asyncio.to_thread(
                    self.memory_system.add,
                    content=f"Code snippet from {sample['path']}:\n{sample['content']}",
                    memory_type=MemoryType.EPISODIC,
                    importance=MemoryImportance.MEDIUM,
                    tags={project_name.lower(), "code_sample", sample['path'].split('/')[-1]},
                    metadata={
                        "project": project_name,
                        "file_path": sample['path'],
                        "sample_num": i
                    }
                )

            add_time = time.time() - start_time
            logger.info(f"✓ Stored {len(code_samples)} code samples in {add_time:.2f}s")

            # 测试检索
            start_time = time.time()
            test_queries = [
                "How to handle command-line arguments?",
                "API endpoints and routing",
                "Error handling patterns",
                "Testing utilities"
            ]

            for query in test_queries:
                try:
                    result = self.memory_system.retrieve(query)
                    logger.info(f"  Retrieved {result.total_found} results for: {query[:50]}...")
                except Exception as e:
                    issue = TestIssue(
                        name="MemoryRetrievalError",
                        description=f"Memory retrieval failed for query: {e}",
                        severity=IssueSeverity.HIGH,
                        category="memory",
                        reproduction_steps=[
                            f"Run query: {query}"
                        ],
                        stack_trace=str(e)
                    )
                    issues.append(issue)
                    self.all_issues.append(issue)

            retrieve_time = time.time() - start_time
            logger.info(f"✓ Memory retrieval tests completed in {retrieve_time:.2f}s")

            return True, issues

        except Exception as e:
            issue = TestIssue(
                name="MemorySystemFatalError",
                description=f"Fatal error testing memory system with real code: {e}",
                severity=IssueSeverity.CRITICAL,
                category="memory",
                stack_trace=str(e)
            )
            issues.append(issue)
            self.all_issues.append(issue)
            return False, issues

    def test_file_operations(self, project_path: Path, project_name: str) -> Tuple[bool, List[TestIssue]]:
        """测试文件操作功能"""
        logger.info(f"Testing file operations with {project_name}...")
        issues: List[TestIssue] = []

        # 测试大文件处理
        try:
            # 寻找较大的 Python 文件
            large_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = Path(root) / file
                        size = file_path.stat().st_size
                        if size > 1024 * 10:  # > 10KB
                            large_files.append((file_path, size))

            if large_files:
                # 取最大的5个测试
                large_files.sort(key=lambda x: x[1], reverse=True)
                for file_path, size in large_files[:5]:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            logger.debug(f"Read file {file_path.name} ({size:,} bytes)")
                    except Exception as e:
                        issue = TestIssue(
                            name="LargeFileReadError",
                            description=f"Failed to read large file {file_path.name}: {e}",
                            severity=IssueSeverity.MEDIUM,
                            category="file_operations"
                        )
                        issues.append(issue)
                        self.all_issues.append(issue)

        except Exception as e:
            issue = TestIssue(
                name="FileOperationError",
                description=f"File operation test failed: {e}",
                severity=IssueSeverity.HIGH,
                category="file_operations",
                stack_trace=str(e)
            )
            issues.append(issue)
            self.all_issues.append(issue)

        return len(issues) == 0, issues

    def test_path_handling(self, project_path: Path, project_name: str) -> Tuple[bool, List[TestIssue]]:
        """测试路径处理功能"""
        logger.info(f"Testing path handling with {project_name}...")
        issues: List[TestIssue] = []

        try:
            # 收集各种路径
            paths: Set[str] = set()

            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = Path(root) / file
                    paths.add(str(file_path.relative_to(project_path)))

            # 测试各种路径处理场景
            path_samples = list(paths)[:50]  # 取前50个样本
            for path_str in path_samples:
                try:
                    p = Path(project_path) / path_str
                    # 验证路径操作
                    _ = p.exists()
                    _ = p.is_file()
                    _ = p.parent
                except Exception as e:
                    issue = TestIssue(
                        name="PathHandlingError",
                        description=f"Failed to handle path {path_str}: {e}",
                        severity=IssueSeverity.MEDIUM,
                        category="path_handling"
                    )
                    issues.append(issue)
                    self.all_issues.append(issue)
                    break  # 只记录第一次

        except Exception as e:
            issue = TestIssue(
                name="PathHandlingFatal",
                description=f"Fatal error testing path handling: {e}",
                severity=IssueSeverity.HIGH,
                category="path_handling",
                stack_trace=str(e)
            )
            issues.append(issue)
            self.all_issues.append(issue)

        return len(issues) == 0, issues

    async def test_single_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个项目"""
        project_name = project["name"]
        project_url = project["url"]
        logger.info("\n" + "=" * 80)
        logger.info(f"🔥 TESTING REAL PROJECT: {project_name}")
        logger.info("=" * 80)

        project_result = {
            "name": project_name,
            "url": project_url,
            "start_time": datetime.now(),
            "tests_run": [],
            "tests_passed": 0,
            "total_tests": 0,
            "issues_found": []
        }

        # 1. 克隆项目
        clone_success, project_path = self.clone_project(project_url, project_name)
        if not clone_success or not project_path:
            issue = TestIssue(
                name="CloneFailure",
                description=f"Failed to clone {project_name}",
                severity=IssueSeverity.CRITICAL,
                category="project_setup"
            )
            self.all_issues.append(issue)
            project_result["issues_found"].append(issue)
            return project_result

        # 2. 分析项目
        analysis = self.analyze_project(project_path, project_name)
        self.analysis_results[project_name] = analysis

        # 3. 测试路径处理
        path_test_name = "path_handling"
        path_success, path_issues = self.test_path_handling(project_path, project_name)
        project_result["tests_run"].append({
            "name": path_test_name,
            "success": path_success,
            "issues": path_issues
        })
        project_result["total_tests"] += 1
        if path_success:
            project_result["tests_passed"] += 1

        # 4. 测试文件操作
        file_test_name = "file_operations"
        file_success, file_issues = self.test_file_operations(project_path, project_name)
        project_result["tests_run"].append({
            "name": file_test_name,
            "success": file_success,
            "issues": file_issues
        })
        project_result["total_tests"] += 1
        if file_success:
            project_result["tests_passed"] += 1

        # 5. 测试记忆系统（这是核心功能）
        memory_test_name = "memory_system"
        memory_success, memory_issues = await self.test_memory_with_real_code(project_path, project_name)
        project_result["tests_run"].append({
            "name": memory_test_name,
            "success": memory_success,
            "issues": memory_issues
        })
        project_result["total_tests"] += 1
        if memory_success:
            project_result["tests_passed"] += 1

        project_result["end_time"] = datetime.now()
        project_result["project_analysis"] = {
            "python_files": analysis.python_files,
            "total_lines": analysis.total_lines,
            "test_files": analysis.test_files,
            "patterns": analysis.identified_patterns
        }

        return project_result

    def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成完整报告"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 REAL GITHUB PROJECT TEST REPORT")
        logger.info("=" * 80)

        total_tests = sum(r["total_tests"] for r in results)
        total_passed = sum(r["tests_passed"] for r in results)

        # 统计问题
        issues_by_severity = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        for issue in self.all_issues:
            issues_by_severity[issue.severity].append(issue)

        overall = {
            "generated_at": datetime.now().isoformat(),
            "projects_tested": [r["name"] for r in results],
            "total_tests": total_tests,
            "total_passed": total_passed,
            "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "issues_found": {
                "total": len(self.all_issues),
                "critical": len(issues_by_severity["CRITICAL"]),
                "high": len(issues_by_severity["HIGH"]),
                "medium": len(issues_by_severity["MEDIUM"]),
                "low": len(issues_by_severity["LOW"])
            },
            "project_analyses": self.analysis_results
        }

        # 打印报告摘要
        logger.info(f"\n📈 Overall Results:")
        logger.info(f"  Projects tested: {len(results)}")
        logger.info(f"  Total tests: {total_tests}")
        logger.info(f"  Passed: {total_passed}")
        logger.info(f"  Pass rate: {overall['pass_rate']:.1f}%")

        logger.info(f"\n🐛 Issues Found:")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = len(issues_by_severity[severity])
            if count > 0:
                if severity in ["CRITICAL", "HIGH"]:
                    logger.error(f"  {severity}: {count}")
                else:
                    logger.warning(f"  {severity}: {count}")

        # 打印详细问题
        if self.all_issues:
            logger.info(f"\n🔍 Detailed Issues:")
            for i, issue in enumerate(self.all_issues[:10], 1):  # 前10个问题
                logger.info(f"\n  {i}. [{issue.severity}] {issue.name}")
                logger.info(f"     Category: {issue.category}")
                logger.info(f"     Description: {issue.description}")

        # 保存报告
        report_file = self.test_dir / "real_github_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(overall, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"\n✅ Report saved to: {report_file}")

        return overall


async def main():
    """主测试函数"""
    logger.info("=" * 80)
    logger.info("🧪 NEURALAGENT - REAL GITHUB PROJECT TESTING")
    logger.info("=" * 80)

    tester = RealGitHubProjectTester()

    all_results = []
    for project in tester.TEST_PROJECTS:
        result = await tester.test_single_project(project)
        all_results.append(result)
        tester.memory_system.forget()  # 清理记忆用于下一个项目

    # 生成报告
    tester.generate_report(all_results)

    logger.info("\n" + "=" * 80)
    logger.info("🎉 REAL GITHUB PROJECT TESTING COMPLETED!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
