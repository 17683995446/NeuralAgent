#!/usr/bin/env python3
"""
全面缺陷审计脚本 - 深度检查 NeuralAgent 系统的问题
"""

import ast
import logging
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IssueCategory(str, Enum):
    IMPORT_ERROR = "Import Error"
    DEPENDENCY_MISSING = "Missing Dependency"
    ARCHITECTURE = "Architecture"
    CODE_QUALITY = "Code Quality"
    DOCUMENTATION = "Documentation"
    TESTING = "Testing"
    CONFIGURATION = "Configuration"


@dataclass
class Defect:
    """发现的缺陷"""
    category: IssueCategory
    severity: Severity
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggested_fix: str = ""
    reproducible: bool = True


class SystemAuditor:
    """系统审计器"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.defects: List[Defect] = []
        self.stats: Dict[str, Any] = defaultdict(int)

    def audit_all(self):
        """执行完整审计"""
        logger.info("=" * 80)
        logger.info("🔍 STARTING FULL SYSTEM AUDIT")
        logger.info("=" * 80)

        # 1. 导入审计
        self.audit_imports()

        # 2. 依赖审计
        self.audit_dependencies()

        # 3. 架构审计
        self.audit_architecture()

        # 4. 代码质量审计
        self.audit_code_quality()

        # 5. 文档审计
        self.audit_documentation()

        # 6. 测试审计
        self.audit_testing()

        # 7. 配置审计
        self.audit_configuration()

        return self.generate_report()

    def audit_imports(self):
        """审计导入问题"""
        logger.info("\n📦 Audit 1: Import Statements")
        py_files = list(self.root_dir.rglob("*.py"))
        logger.info(f"Checking {len(py_files)} Python files...")

        import_errors = 0

        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # 检查导入问题
                lines = content.splitlines()
                for i, line in enumerate(lines, 1):
                    if line.strip().startswith(('import', 'from')):
                        # 检查是否有废弃的导入
                        if 'backend.layers.' in line:
                            defect = Defect(
                                category=IssueCategory.IMPORT_ERROR,
                                severity=Severity.MEDIUM,
                                description="Import from deprecated 'backend.layers' directory",
                                file_path=str(py_file.relative_to(self.root_dir)),
                                line_number=i,
                                code_snippet=line.strip(),
                                suggested_fix="Change to 'backend.core.neural_layers'"
                            )
                            self.defects.append(defect)

            except Exception as e:
                continue

        logger.info(f"✓ Import audit complete: found {len([d for d in self.defects if d.category == IssueCategory.IMPORT_ERROR])} issues")

    def audit_dependencies(self):
        """审计依赖问题"""
        logger.info("\n🔌 Audit 2: Dependencies")

        req_files = [
            "requirements.txt",
            "requirements-minimal.txt",
            "setup.py",
            "pyproject.toml"
        ]

        found_req = []
        for req_file in req_files:
            path = self.root_dir / req_file
            if path.exists():
                found_req.append(req_file)

        if not found_req:
            self.defects.append(Defect(
                category=IssueCategory.DEPENDENCY_MISSING,
                severity=Severity.HIGH,
                description="No requirements files found!",
                suggested_fix="Create requirements.txt or pyproject.toml"
            ))
        else:
            logger.info(f"Found requirements files: {', '.join(found_req)}")

            # 检查缺失的关键依赖
            critical_deps = ['fastapi', 'uvicorn', 'pydantic', 'redis']
            req_path = self.root_dir / "requirements-minimal.txt"
            if req_path.exists():
                with open(req_path, 'r') as f:
                    req_content = f.read()

                for dep in critical_deps:
                    if dep not in req_content:
                        self.defects.append(Defect(
                            category=IssueCategory.DEPENDENCY_MISSING,
                            severity=Severity.HIGH,
                            description=f"Critical dependency '{dep}' not found in requirements-minimal.txt",
                            file_path="requirements-minimal.txt",
                            suggested_fix=f"Add '{dep}' to requirements"
                        ))

        logger.info(f"✓ Dependency audit complete: found {len([d for d in self.defects if d.category == IssueCategory.DEPENDENCY_MISSING])} issues")

    def audit_architecture(self):
        """审计架构问题"""
        logger.info("\n🏗️  Audit 3: Architecture")

        # 检查重复目录
        backend_dir = self.root_dir / "backend"
        if backend_dir.exists():
            layers_dir = backend_dir / "layers"
            core_layers_dir = backend_dir / "core" / "neural_layers"

            if layers_dir.exists() and core_layers_dir.exists():
                self.defects.append(Defect(
                    category=IssueCategory.ARCHITECTURE,
                    severity=Severity.CRITICAL,
                    description="Duplicate layer directories: layers/ and core/neural_layers/",
                    file_path="backend/layers",
                    suggested_fix="Consolidate into backend/core/neural_layers (already started, complete removal recommended)"
                ))

            # 检查缺少 __init__.py 的目录
            core_dir = backend_dir / "core"
            if core_dir.exists():
                for item in core_dir.iterdir():
                    if item.is_dir() and not (item / "__init__.py").exists():
                        if item.name != "__pycache__":
                            self.defects.append(Defect(
                                category=IssueCategory.ARCHITECTURE,
                                severity=Severity.MEDIUM,
                                description=f"Directory '{item.name}' missing __init__.py",
                                file_path=f"backend/core/{item.name}",
                                suggested_fix="Add __init__.py to make it a proper Python package"
                            ))

        logger.info(f"✓ Architecture audit complete: found {len([d for d in self.defects if d.category == IssueCategory.ARCHITECTURE])} issues")

    def audit_code_quality(self):
        """审计代码质量"""
        logger.info("\n✨ Audit 4: Code Quality")

        py_files = list(self.root_dir.rglob("*.py"))
        for py_file in py_files:
            if "__pycache__" in str(py_file) or "test_" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.splitlines()

                    # 1. 检查文件长度
                    if len(lines) > 500:
                        self.defects.append(Defect(
                            category=IssueCategory.CODE_QUALITY,
                            severity=Severity.LOW,
                            description=f"File is very long ({len(lines)} lines)",
                            file_path=str(py_file.relative_to(self.root_dir)),
                            suggested_fix="Consider splitting into smaller modules"
                        ))

                    # 2. 检查 TODO/FIXME
                    for i, line in enumerate(lines, 1):
                        if 'TODO' in line or 'FIXME' in line:
                            self.defects.append(Defect(
                                category=IssueCategory.CODE_QUALITY,
                                severity=Severity.LOW,
                                description="Found TODO/FIXME comment",
                                file_path=str(py_file.relative_to(self.root_dir)),
                                line_number=i,
                                code_snippet=line.strip()
                            ))

                    # 3. 尝试 AST 解析
                    try:
                        ast.parse(content)
                    except SyntaxError as e:
                        self.defects.append(Defect(
                            category=IssueCategory.CODE_QUALITY,
                            severity=Severity.HIGH,
                            description=f"Syntax error: {e.msg}",
                            file_path=str(py_file.relative_to(self.root_dir)),
                            line_number=e.lineno
                        ))

            except Exception as e:
                continue

        logger.info(f"✓ Code quality audit complete: found {len([d for d in self.defects if d.category == IssueCategory.CODE_QUALITY])} issues")

    def audit_documentation(self):
        """审计文档"""
        logger.info("\n📚 Audit 5: Documentation")

        # 检查根目录 README
        readme_files = ["README.md", "README", "readme.md"]
        readme_exists = any((self.root_dir / f).exists() for f in readme_files)

        if not readme_exists:
            self.defects.append(Defect(
                category=IssueCategory.DOCUMENTATION,
                severity=Severity.MEDIUM,
                description="No README file found at project root",
                suggested_fix="Create a README.md with project overview and getting started guide"
            ))

        # 检查 docs 目录
        docs_dir = self.root_dir / "docs"
        if docs_dir.exists():
            doc_files = list(docs_dir.rglob("*.md"))
            logger.info(f"Found {len(doc_files)} documentation files")
        else:
            self.defects.append(Defect(
                category=IssueCategory.DOCUMENTATION,
                severity=Severity.LOW,
                description="No docs/ directory found",
                suggested_fix="Create docs/ directory for documentation"
            ))

        logger.info(f"✓ Documentation audit complete: found {len([d for d in self.defects if d.category == IssueCategory.DOCUMENTATION])} issues")

    def audit_testing(self):
        """审计测试"""
        logger.info("\n🧪 Audit 6: Testing")

        tests_dir = self.root_dir / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.rglob("test_*.py"))
            logger.info(f"Found {len(test_files)} test files")
        else:
            self.defects.append(Defect(
                category=IssueCategory.TESTING,
                severity=Severity.MEDIUM,
                description="No tests/ directory found",
                suggested_fix="Create tests/ directory with test files"
            ))

        # 检查是否有 pytest.ini 或 pyproject.toml
        pytest_ini = self.root_dir / "pytest.ini"
        if not pytest_ini.exists():
            self.defects.append(Defect(
                category=IssueCategory.TESTING,
                severity=Severity.LOW,
                description="No pytest.ini found",
                suggested_fix="Create pytest.ini or configure in pyproject.toml"
            ))

        logger.info(f"✓ Testing audit complete: found {len([d for d in self.defects if d.category == IssueCategory.TESTING])} issues")

    def audit_configuration(self):
        """审计配置"""
        logger.info("\n⚙️  Audit 7: Configuration")

        env_files = [".env", ".env.example"]
        for env_file in env_files:
            if not (self.root_dir / env_file).exists():
                self.defects.append(Defect(
                    category=IssueCategory.CONFIGURATION,
                    severity=Severity.LOW,
                    description=f"No {env_file} file found",
                    suggested_fix=f"Create {env_file} for environment configuration"
                ))

        logger.info(f"✓ Configuration audit complete: found {len([d for d in self.defects if d.category == IssueCategory.CONFIGURATION])} issues")

    def generate_report(self) -> Dict[str, Any]:
        """生成报告"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 AUDIT REPORT")
        logger.info("=" * 80)

        # 按类别和严重程度统计
        stats = {
            'total_defects': len(self.defects),
            'by_category': defaultdict(int),
            'by_severity': defaultdict(int)
        }

        for defect in self.defects:
            stats['by_category'][defect.category] += 1
            stats['by_severity'][defect.severity] += 1

        # 打印摘要
        logger.info(f"\n🔴 CRITICAL: {stats['by_severity'][Severity.CRITICAL]}")
        logger.info(f"🟡 HIGH:     {stats['by_severity'][Severity.HIGH]}")
        logger.info(f"🟢 MEDIUM:   {stats['by_severity'][Severity.MEDIUM]}")
        logger.info(f"🔵 LOW:      {stats['by_severity'][Severity.LOW]}")
        logger.info(f"\n📦 Total:    {len(self.defects)} defects")

        logger.info(f"\n📁 By Category:")
        for category, count in stats['by_category'].items():
            logger.info(f"   {category}: {count}")

        # 打印前20个缺陷
        logger.info(f"\n🔥 Top Defects:")
        for i, defect in enumerate(self.defects[:20], 1):
            logger.info(f"\n   {i}. [{defect.severity}] {defect.description}")
            if defect.file_path:
                logger.info(f"      → {defect.file_path}")
            if defect.suggested_fix:
                logger.info(f"      💡 {defect.suggested_fix}")

        # 生成完整报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'stats': dict(stats),
            'defects': [
                {
                    'category': d.category.value,
                    'severity': d.severity.value,
                    'description': d.description,
                    'file_path': d.file_path,
                    'line_number': d.line_number,
                    'code_snippet': d.code_snippet,
                    'suggested_fix': d.suggested_fix
                }
                for d in self.defects
            ]
        }

        # 保存报告
        report_file = self.root_dir / "docs" / "FULL_DEFECT_AUDIT_REPORT.json"
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✅ Full audit report saved to: {report_file}")

        return report


def main():
    root_dir = Path(__file__).parent.parent
    auditor = SystemAuditor(root_dir)
    auditor.audit_all()


if __name__ == "__main__":
    main()
