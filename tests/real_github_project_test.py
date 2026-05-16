#!/usr/bin/env python3
"""
真实GitHub项目测试 - 发现NeuralAgent中的实际问题
使用真实的开源项目来测试系统的各个组件，找出问题所在
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Issue:
    """发现的问题"""
    name: str
    description: str
    severity: Severity
    category: str
    reproduction_steps: List[str] = field(default_factory=list)
    suggested_fix: str = ""
    stack_trace: str = ""


@dataclass
class TestResult:
    """单个测试的结果"""
    test_name: str
    success: bool
    duration_ms: float
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    output: str = ""


class RealProjectTester:
    """真实GitHub项目测试器"""

    # 选择一些小到中等规模的真实项目进行测试
    TEST_PROJECTS = [
        {
            "name": "HTTPie",
            "url": "https://github.com/httpie/httpie.git",
            "description": "Modern command-line HTTP client",
            "size": "small"
        },
        {
            "name": "Click",
            "url": "https://github.com/pallets/click.git",
            "description": "Python composable command-line interface toolkit",
            "size": "small"
        },
        {
            "name": "Rich",
            "url": "https://github.com/Textualize/rich.git",
            "description": "Rich text and beautiful formatting in the terminal",
            "size": "medium"
        }
    ]

    def __init__(self, test_dir: Optional[Path] = None):
        self.test_dir = test_dir or Path(tempfile.mkdtemp(prefix="neural_agent_real_test_"))
        self.all_issues: List[Issue] = []
        self.results: Dict[str, List[TestResult]] = {}
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("RealProjectTester")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def clone_project(self, project_info: Dict[str, str]) -> Tuple[bool, Optional[Path]]:
        """克隆GitHub项目"""
        project_path = self.test_dir / project_info["name"]

        if project_path.exists():
            self.logger.info(f"Removing existing directory: {project_path}")
            shutil.rmtree(project_path)

        self.logger.info(f"Cloning {project_info['name']} from {project_info['url']}...")

        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", project_info["url"], str(project_path)],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                self.logger.info(f"✓ Cloned {project_info['name']} successfully")
                return True, project_path
            else:
                self.logger.error(f"Failed to clone {project_info['name']}: {result.stderr}")
                return False, None

        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout cloning {project_info['name']}")
            return False, None
        except Exception as e:
            self.logger.error(f"Error cloning {project_info['name']}: {e}")
            return False, None

    def analyze_project_files(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """分析项目文件"""
        self.logger.info(f"Analyzing {project_name} structure...")

        stats = {
            "python_files": 0,
            "total_lines": 0,
            "test_files": 0,
            "directories": set(),
            "file_list": []
        }

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', 'venv', '.venv']]

            for file in files:
                file_path = Path(root) / file

                if file.endswith('.py'):
                    stats["python_files"] += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count = len(f.readlines())
                            stats["total_lines"] += line_count
                    except Exception:
                        pass

                if 'test' in file.lower() and file.endswith('.py'):
                    stats["test_files"] += 1

                rel_path = file_path.relative_to(project_path)
                stats["directories"].add(str(rel_path.parent))
                stats["file_list"].append(str(rel_path))

        stats["directories"] = list(stats["directories"])
        return stats

    async def test_import_architecture(self, project_name: str) -> TestResult:
        """测试架构导入"""
        test_name = "import_architecture"
        start_time = time.time()
        issues: List[Issue] = []

        self.logger.info(f"Testing architecture imports for {project_name}...")

        # 测试核心模块导入
        import_tests = [
            ("backend.config", "Config module"),
            ("backend.api.routes", "API routes"),
            ("backend.core.memory.enhanced_memory_system", "Enhanced memory"),
            ("backend.core.llm_integration.unified_llm_client_wrapper", "LLM integration"),
            ("backend.core.infrastructure.vector_db", "Vector DB"),
        ]

        for module_path, description in import_tests:
            try:
                __import__(module_path)
                self.logger.debug(f"  ✓ {description}")
            except Exception as e:
                issue = Issue(
                    name=f"Import failure: {module_path}",
                    description=f"Failed to import {description}: {e}",
                    severity=Severity.HIGH,
                    category="architecture",
                    reproduction_steps=[
                        f"Attempt to import {module_path}",
                        f"Observe error: {e}"
                    ],
                    stack_trace=traceback.format_exc()
                )
                issues.append(issue)
                self.all_issues.append(issue)
                self.logger.error(f"  ✗ {description}: {e}")

        # 测试我们刚才重命名的文件
        renamed_files_tests = [
            ("backend.layers.neural_input_processing_layer", "Neural input layer"),
            ("backend.utils.common_helper_functions", "Common helpers"),
            ("backend.models.persistent_data_models", "Data models"),
            ("backend.services.code_processing_database_service", "DB service"),
        ]

        for module_path, description in renamed_files_tests:
            try:
                __import__(module_path)
                self.logger.debug(f"  ✓ {description}")
            except Exception as e:
                issue = Issue(
                    name=f"Renamed file import failure: {module_path}",
                    description=f"Failed to import renamed module {description}: {e}",
                    severity=Severity.CRITICAL,
                    category="file_rename",
                    reproduction_steps=[
                        f"Check if file exists at correct location",
                        f"Attempt to import {module_path}",
                    ],
                    suggested_fix="Verify file paths and update __init__.py files",
                    stack_trace=traceback.format_exc()
                )
                issues.append(issue)
                self.all_issues.append(issue)
                self.logger.error(f"  ✗ {description}: {e}")

        duration_ms = (time.time() - start_time) * 1000

        return TestResult(
            test_name=test_name,
            success=len(issues) == 0,
            duration_ms=duration_ms,
            issues=issues,
            metrics={
                "total_tests": len(import_tests) + len(renamed_files_tests),
                "failed_imports": len(issues)
            }
        )

    async def test_layer_integration(self, project_path: Path, project_name: str) -> TestResult:
        """测试神经网络层集成"""
        test_name = "layer_integration"
        start_time = time.time()
        issues: List[Issue] = []

        self.logger.info(f"Testing layer integration for {project_name}...")

        # 测试Input Layer
        try:
            from backend.core.neural_layers.neural_input_layer import InputLayer
            # 只是验证导入和基本初始化
            self.logger.debug("  ✓ InputLayer import successful")
        except Exception as e:
            issue = Issue(
                name="InputLayer integration failed",
                description=f"Cannot use InputLayer: {e}",
                severity=Severity.HIGH,
                category="layers",
                stack_trace=traceback.format_exc()
            )
            issues.append(issue)
            self.all_issues.append(issue)
            self.logger.error(f"  ✗ InputLayer: {e}")

        # 测试Output Layer
        try:
            from backend.core.neural_layers.neural_output_layer import OutputLayer
            self.logger.debug("  ✓ OutputLayer import successful")
        except Exception as e:
            issue = Issue(
                name="OutputLayer integration failed",
                description=f"Cannot use OutputLayer: {e}",
                severity=Severity.HIGH,
                category="layers",
                stack_trace=traceback.format_exc()
            )
            issues.append(issue)
            self.all_issues.append(issue)
            self.logger.error(f"  ✗ OutputLayer: {e}")

        # 测试其他层
        layer_tests = [
            ("neural_convolution_analysis_layer", "Convolution"),
            ("neural_pooling_compression_layer", "Pooling"),
            ("neural_fc_global_understanding_layer", "FC1"),
            ("neural_fc_code_generation_layer", "FC2"),
            ("neural_fc_test_generation_layer", "FC3"),
            ("neural_backward_propagation_layer", "Backward"),
        ]

        for module_name, layer_name in layer_tests:
            try:
                module = __import__(f"backend.layers.{module_name}", fromlist=[''])
                self.logger.debug(f"  ✓ {layer_name}Layer import successful")
            except Exception as e:
                issue = Issue(
                    name=f"{layer_name}Layer integration failed",
                    description=f"Cannot use {layer_name}Layer: {e}",
                    severity=Severity.HIGH,
                    category="layers",
                    stack_trace=traceback.format_exc()
                )
                issues.append(issue)
                self.all_issues.append(issue)
                self.logger.error(f"  ✗ {layer_name}Layer: {e}")

        duration_ms = (time.time() - start_time) * 1000

        return TestResult(
            test_name=test_name,
            success=len(issues) == 0,
            duration_ms=duration_ms,
            issues=issues
        )

    async def test_memory_system(self, project_name: str, stats: Dict[str, Any]) -> TestResult:
        """测试记忆系统"""
        test_name = "memory_system"
        start_time = time.time()
        issues: List[Issue] = []

        self.logger.info(f"Testing memory system with {project_name} data...")

        try:
            from backend.core.memory.enhanced_memory_system import (
                EnhancedMemorySystem,
                MemoryType,
                MemoryImportance
            )

            memory_system = EnhancedMemorySystem()

            # 测试添加记忆
            test_memory = f"Project {project_name} has {stats['python_files']} Python files with {stats['total_lines']} lines"

            memory_system.add(
                content=test_memory,
                memory_type=MemoryType.EPISODIC,
                importance=MemoryImportance.HIGH,
                tags=[project_name.lower(), "stats"],
                metadata={"project": project_name, "test": "real_project"}
            )

            # 测试检索
            results = memory_system.retrieve(project_name)
            if results.total_found == 0:
                issue = Issue(
                    name="Memory retrieval failed",
                    description="Memory system did not find any matching memories",
                    severity=Severity.MEDIUM,
                    category="memory"
                )
                issues.append(issue)
                self.all_issues.append(issue)

            # 测试上下文检索
            context, entries = memory_system.retrieve_context(project_name, max_tokens=1000)
            if not context:
                self.logger.warning("  ⚠ No context retrieved")

            self.logger.debug("  ✓ Memory system working")

        except Exception as e:
            issue = Issue(
                name="Memory system failure",
                description=f"Memory system failed: {e}",
                severity=Severity.HIGH,
                category="memory",
                stack_trace=traceback.format_exc()
            )
            issues.append(issue)
            self.all_issues.append(issue)
            self.logger.error(f"  ✗ Memory system: {e}")

        duration_ms = (time.time() - start_time) * 1000

        return TestResult(
            test_name=test_name,
            success=len(issues) == 0,
            duration_ms=duration_ms,
            issues=issues
        )

    async def test_code_processing(self, project_path: Path, project_name: str) -> TestResult:
        """测试代码处理能力"""
        test_name = "code_processing"
        start_time = time.time()
        issues: List[Issue] = []

        self.logger.info(f"Testing code processing for {project_name}...")

        # 尝试处理一些Python文件
        python_files = list(project_path.rglob("*.py"))
        test_files = python_files[:5]

        if not test_files:
            issue = Issue(
                name="No Python files found",
                description=f"No Python files found in {project_name}, cannot test code processing",
                severity=Severity.LOW,
                category="test_setup"
            )
            issues.append(issue)
            self.all_issues.append(issue)
        else:
            self.logger.debug(f"  Found {len(python_files)} Python files, testing with {len(test_files)}")

            # 测试读取代码
            for file_path in test_files[:2]:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # 简单测试
                        if content:
                            pass
                except Exception as e:
                    self.logger.warning(f"  Could not read {file_path}: {e}")

        duration_ms = (time.time() - start_time) * 1000

        return TestResult(
            test_name=test_name,
            success=len(issues) == 0,
            duration_ms=duration_ms,
            issues=issues,
            metrics={
                "python_files": len(python_files),
                "tested_files": len(test_files)
            }
        )

    def check_architecture_consistency(self, project_name: str) -> List[Issue]:
        """检查架构一致性"""
        issues: List[Issue] = []
        self.logger.info(f"Checking architecture consistency for {project_name}...")

        backend_path = Path(__file__).parent.parent / "backend"

        # 检查重复的层目录
        if (backend_path / "layers").exists() and (backend_path / "core" / "neural_layers").exists():
            issue = Issue(
                name="Duplicate layer directories",
                description="Found both 'backend/layers' and 'backend/core/neural_layers' - potential confusion",
                severity=Severity.MEDIUM,
                category="architecture",
                suggested_fix="Consolidate to a single layer directory structure"
            )
            issues.append(issue)
            self.all_issues.append(issue)
            self.logger.warning("  ⚠ Duplicate layer directories found")

        # 检查__init__.py文件
        for dir_path in [
            backend_path / "layers",
            backend_path / "core" / "neural_layers",
            backend_path / "utils",
            backend_path / "models",
            backend_path / "services"
        ]:
            if dir_path.exists():
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    issue = Issue(
                        name=f"Missing __init__.py in {dir_path.name}",
                        description=f"No __init__.py file in directory {dir_path}",
                        severity=Severity.LOW,
                        category="architecture"
                    )
                    issues.append(issue)
                    self.all_issues.append(issue)

        return issues

    async def test_single_project(self, project_info: Dict[str, str]) -> List[TestResult]:
        """测试单个项目"""
        project_name = project_info["name"]
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"TESTING: {project_name}")
        self.logger.info("=" * 80)

        results: List[TestResult] = []

        # 1. 克隆项目
        success, project_path = self.clone_project(project_info)
        if not success or not project_path:
            self.logger.error(f"Cannot proceed without {project_name}")
            return results

        # 2. 分析项目
        stats = self.analyze_project_files(project_path, project_name)
        self.logger.info(f"  Stats: {stats['python_files']} Python files, {stats['total_lines']:,} lines")

        # 3. 架构一致性检查
        consistency_issues = self.check_architecture_consistency(project_name)
        if consistency_issues:
            results.append(TestResult(
                test_name="architecture_consistency",
                success=False,
                duration_ms=0,
                issues=consistency_issues
            ))

        # 4. 测试导入
        import_result = await self.test_import_architecture(project_name)
        results.append(import_result)

        # 5. 测试层集成
        layer_result = await self.test_layer_integration(project_path, project_name)
        results.append(layer_result)

        # 6. 测试记忆系统
        memory_result = await self.test_memory_system(project_name, stats)
        results.append(memory_result)

        # 7. 测试代码处理
        code_result = await self.test_code_processing(project_path, project_name)
        results.append(code_result)

        self.results[project_name] = results
        return results

    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "test_directory": str(self.test_dir),
            "projects_tested": list(self.results.keys()),
            "summary": {
                "total_issues": len(self.all_issues),
                "issues_by_severity": {},
                "issues_by_category": {}
            },
            "issues": [],
            "project_results": {}
        }

        # 按严重程度分类
        for severity in Severity:
            count = sum(1 for issue in self.all_issues if issue.severity == severity)
            report["summary"]["issues_by_severity"][severity.value] = count

        # 按类别分类
        categories = set(issue.category for issue in self.all_issues)
        for category in categories:
            count = sum(1 for issue in self.all_issues if issue.category == category)
            report["summary"]["issues_by_category"][category] = count

        # 问题详情
        for issue in self.all_issues:
            report["issues"].append({
                "name": issue.name,
                "description": issue.description,
                "severity": issue.severity.value,
                "category": issue.category,
                "suggested_fix": issue.suggested_fix,
                "reproduction_steps": issue.reproduction_steps
            })

        # 项目结果
        for project_name, results in self.results.items():
            report["project_results"][project_name] = {
                "total_tests": len(results),
                "passed_tests": sum(1 for r in results if r.success),
                "failed_tests": sum(1 for r in results if not r.success),
                "tests": [
                    {
                        "name": r.test_name,
                        "success": r.success,
                        "duration_ms": r.duration_ms,
                        "issue_count": len(r.issues)
                    } for r in results
                ]
            }

        return report

    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("=" * 80)
        self.logger.info("NeuralAgent - REAL GITHUB PROJECT TESTING")
        self.logger.info("=" * 80)
        self.logger.info(f"Test directory: {self.test_dir}")

        for project_info in self.TEST_PROJECTS:
            await self.test_single_project(project_info)

        # 生成报告
        report = self.generate_report()

        # 保存报告
        report_file = self.test_dir / "real_project_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 打印总结
        self.logger.info("\n" + "=" * 80)
        self.logger.info("TEST REPORT SUMMARY")
        self.logger.info("=" * 80)

        for severity in Severity:
            count = report["summary"]["issues_by_severity"][severity.value]
            if count > 0:
                self.logger.error(f"  {severity.value}: {count} issues") if severity in [Severity.CRITICAL, Severity.HIGH] else self.logger.warning(f"  {severity.value}: {count} issues")

        self.logger.info(f"\n  Total issues: {report['summary']['total_issues']}")

        if report["issues"]:
            self.logger.info("\nTop issues:")
            for i, issue in enumerate(report["issues"][:5], 1):
                self.logger.info(f"  {i}. [{issue['severity']}] {issue['name']}")
                self.logger.info(f"     {issue['description']}")

        self.logger.info(f"\nFull report saved to: {report_file}")
        self.logger.info("=" * 80)

        return report


async def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    tester = RealProjectTester()

    try:
        report = await tester.run_all_tests()

        if report["summary"]["total_issues"] == 0:
            print("\n🎉 ALL TESTS PASSED! No issues found.")
        else:
            print(f"\n⚠️  Found {report['summary']['total_issues']} issues that need attention.")

        print(f"\n📁 Test results in: {tester.test_dir}")

    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
