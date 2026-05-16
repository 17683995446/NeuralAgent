#!/usr/bin/env python3
"""
Project Health Check & Self-Diagnosis Tool
=========================================

A comprehensive, production-grade tool to:
- Check project structure and configuration
- Verify core module imports
- Run available tests
- Generate quick health summary report

Standing on the shoulders of giants: Uses Python standard library and pytest
Not reinventing the wheel: Follows established testing and diagnostic patterns
Highly modular: Separate checkers for different aspects
Productized: Provides clear, actionable output and recommendations
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import subprocess
import importlib


class HealthStatus(Enum):
    """Health check status levels."""
    EXCELLENT = "🟢"
    GOOD = "🟢"
    WARNING = "🟡"
    ERROR = "🔴"
    SKIPPED = "⚪"


@dataclass
class CheckResult:
    """Result from a single health check."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class HealthReport:
    """Comprehensive health report."""
    generated_at: datetime
    check_results: List[CheckResult]
    overall_status: HealthStatus
    summary: str

    def print(self):
        """Print beautiful, color-coded report."""
        print("\n" + "=" * 80)
        print("🚀 PROJECT HEALTH CHECK & SELF-DIAGNOSIS")
        print("=" * 80)
        print(f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Overall Status: {self.overall_status.value} - {self.summary}")
        print("\n" + "-" * 80)

        for result in self.check_results:
            status_icon = result.status.value
            print(f"\n{status_icon} {result.name}")
            print(f"   {result.message}")
            if result.details:
                for key, value in result.details.items():
                    print(f"   • {key}: {value}")
            if result.recommendations:
                print(f"   💡 Recommendations:")
                for rec in result.recommendations:
                    print(f"      - {rec}")

        print("\n" + "=" * 80)
        print("✅ Check complete!")
        print("=" * 80)


class ProjectHealthChecker:
    """Main health check orchestration class."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.check_results: List[CheckResult] = []

    def run_all_checks(self) -> HealthReport:
        """Run all health checks."""
        # Directory and file structure checks
        self._check_project_structure()
        self._check_configuration_files()
        self._check_requirements()

        # Module import checks
        self._check_core_module_imports()
        self._check_backend_modules()

        # Testing checks
        self._check_test_infrastructure()
        self._run_available_tests()

        # Calculate overall status
        overall_status = self._calculate_overall_status()

        return HealthReport(
            generated_at=datetime.now(),
            check_results=self.check_results,
            overall_status=overall_status,
            summary=self._generate_summary(overall_status)
        )

    def _check_project_structure(self) -> None:
        """Check project directory structure."""
        required_dirs = ["backend", "tests", "docs", "examples"]
        found_dirs = []
        missing_dirs = []

        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                found_dirs.append(dir_name)
            else:
                missing_dirs.append(dir_name)

        if not missing_dirs:
            status = HealthStatus.EXCELLENT
            message = "All required project directories found"
            recommendations = []
        else:
            status = HealthStatus.WARNING
            message = f"Missing directories: {', '.join(missing_dirs)}"
            recommendations = ["Create missing directories or verify project structure"]

        self.check_results.append(CheckResult(
            name="Project Structure",
            status=status,
            message=message,
            details={
                "Found directories": ", ".join(found_dirs),
                "Missing directories": ", ".join(missing_dirs) if missing_dirs else "None"
            },
            recommendations=recommendations
        ))

    def _check_configuration_files(self) -> None:
        """Check required configuration files."""
        required_files = [
            "README.md",
            ".env.example",
            "requirements.txt",
            "requirements-minimal.txt",
            "pytest.ini",
            "Dockerfile"
        ]

        found_files = []
        missing_files = []

        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists() and file_path.is_file():
                found_files.append(file_name)
            else:
                missing_files.append(file_name)

        if not missing_files:
            status = HealthStatus.EXCELLENT
            message = "All required configuration files present"
        elif len(missing_files) <= 2:
            status = HealthStatus.WARNING
            message = f"Some optional files missing"
        else:
            status = HealthStatus.ERROR
            message = f"Critical configuration files missing"

        self.check_results.append(CheckResult(
            name="Configuration Files",
            status=status,
            message=message,
            details={
                "Found": len(found_files),
                "Missing": len(missing_files),
                "Missing files": ", ".join(missing_files) if missing_files else "None"
            },
            recommendations=["Create any missing important configuration files"] if missing_files else []
        ))

    def _check_requirements(self) -> None:
        """Check requirements files exist and are valid."""
        req_min_path = self.project_root / "requirements-minimal.txt"
        req_full_path = self.project_root / "requirements.txt"

        details = {}
        status = HealthStatus.GOOD
        recommendations = []

        if req_min_path.exists():
            details["Requirements-minimal.txt"] = "Present"
        else:
            status = HealthStatus.WARNING
            details["Requirements-minimal.txt"] = "Missing"
            recommendations.append("Create requirements-minimal.txt for minimal installation")

        if req_full_path.exists():
            details["Requirements.txt"] = "Present"
        else:
            details["Requirements.txt"] = "Missing"

        self.check_results.append(CheckResult(
            name="Requirements Files",
            status=status,
            message=f"Requirements file check complete",
            details=details,
            recommendations=recommendations
        ))

    def _check_core_module_imports(self) -> None:
        """Check that core modules can be imported."""
        test_imports = [
            ("backend.core.config_validator", "ConfigValidator"),
            ("backend.core.error_codes", "ErrorCode"),
            ("backend.core.error_resilience", "with_retry"),
            ("backend.core.performance_optimizer", "PerformanceOptimizer"),
            ("backend.core.health_monitor", "HealthMonitor"),
            ("backend.core.cache_manager", "CacheManager"),
            ("backend.core.rate_limiter", "RateLimiter"),
            ("backend.core.enhanced_product_scoring", "generate_enhanced_report")
        ]

        successful_imports = 0
        failed_imports = []

        for module_name, symbol_name in test_imports:
            try:
                module = importlib.import_module(module_name)
                if symbol_name:
                    getattr(module, symbol_name)
                successful_imports += 1
            except Exception as e:
                failed_imports.append(f"{module_name}.{symbol_name}: {str(e)[:50]}")

        if not failed_imports:
            status = HealthStatus.EXCELLENT
            message = "All core modules import successfully"
        elif len(failed_imports) <= 3:
            status = HealthStatus.WARNING
            message = f"Some optional modules failed to import"
        else:
            status = HealthStatus.ERROR
            message = f"Multiple module import failures"

        self.check_results.append(CheckResult(
            name="Core Module Imports",
            status=status,
            message=message,
            details={
                "Successful imports": successful_imports,
                "Failed imports": len(failed_imports),
                "Failed": "\n   ".join(failed_imports[:5]) if failed_imports else "None"
            },
            recommendations=[
                "Install missing dependencies",
                "Check PYTHONPATH configuration"
            ] if failed_imports else []
        ))

    def _check_backend_modules(self) -> None:
        """Check backend modules exist."""
        backend_path = self.project_root / "backend"
        core_path = backend_path / "core"

        if not core_path.exists():
            self.check_results.append(CheckResult(
                name="Backend Core Modules",
                status=HealthStatus.ERROR,
                message="Backend core directory not found",
                recommendations=["Verify project structure"]
            ))
            return

        core_files = list(core_path.glob("*.py"))
        num_modules = len([f for f in core_files if f.is_file() and not f.name.startswith("_")])

        self.check_results.append(CheckResult(
            name="Backend Core Modules",
            status=HealthStatus.EXCELLENT if num_modules >= 20 else HealthStatus.GOOD,
            message=f"Found {num_modules} core modules",
            details={"Module count": num_modules},
            recommendations=[]
        ))

    def _check_test_infrastructure(self) -> None:
        """Check test infrastructure."""
        tests_path = self.project_root / "tests"
        pytest_ini = self.project_root / "pytest.ini"

        test_files = list(tests_path.glob("test_*.py")) if tests_path.exists() else []

        self.check_results.append(CheckResult(
            name="Test Infrastructure",
            status=HealthStatus.EXCELLENT if len(test_files) > 20 else HealthStatus.GOOD,
            message=f"Found {len(test_files)} test files",
            details={
                "pytest.ini present": pytest_ini.exists(),
                "Test directory present": tests_path.exists(),
                "Test file count": len(test_files)
            },
            recommendations=["Run the full test suite"]
        ))

    def _run_available_tests(self) -> None:
        """Run available tests that don't require optional dependencies."""
        test_modules = [
            "tests/test_config_validator.py",
            "tests/test_error_codes.py",
            "tests/test_performance_optimizer.py",
            "tests/test_error_resilience.py",
            "tests/test_cache_manager.py",
            "tests/test_health_monitor.py",
            "tests/test_prometheus_metrics.py"
        ]

        successful_tests = 0
        failed_tests = []
        total_tests = 0

        for test_module in test_modules:
            if not (self.project_root / test_module).exists():
                continue

            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", test_module, "-v", "--tb=short"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    successful_tests += 1
                    # Count how many individual tests passed
                    output_lines = result.stdout.splitlines()
                    passed_lines = [l for l in output_lines if " PASSED " in l]
                    total_tests += len(passed_lines)
                else:
                    failed_tests.append(test_module)
            except Exception as e:
                failed_tests.append(f"{test_module} (execution failed: {str(e)[:30]})")

        if not failed_tests and successful_tests > 0:
            status = HealthStatus.EXCELLENT
            message = f"All {successful_tests} test modules passed with {total_tests} individual tests"
        elif successful_tests > 0:
            status = HealthStatus.WARNING
            message = f"{successful_tests} test modules passed, {len(failed_tests)} failed"
        else:
            status = HealthStatus.ERROR
            message = "No test modules successfully executed"

        self.check_results.append(CheckResult(
            name="Test Execution",
            status=status,
            message=message,
            details={
                "Modules passed": successful_tests,
                "Modules failed": len(failed_tests),
                "Individual tests passed": total_tests,
                "Failed modules": ", ".join(failed_tests[:3]) if failed_tests else "None"
            },
            recommendations=["Run pytest directly for detailed failure information"] if failed_tests else []
        ))

    def _calculate_overall_status(self) -> HealthStatus:
        """Calculate overall health status from check results."""
        status_counts = {
            HealthStatus.EXCELLENT: 0,
            HealthStatus.GOOD: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.ERROR: 0,
            HealthStatus.SKIPPED: 0
        }

        for result in self.check_results:
            status_counts[result.status] += 1

        if status_counts[HealthStatus.ERROR] > 0:
            return HealthStatus.ERROR
        elif status_counts[HealthStatus.WARNING] > 2:
            return HealthStatus.WARNING
        elif status_counts[HealthStatus.EXCELLENT] >= 5:
            return HealthStatus.EXCELLENT
        else:
            return HealthStatus.GOOD

    def _generate_summary(self, overall_status: HealthStatus) -> str:
        """Generate human-friendly summary."""
        if overall_status == HealthStatus.EXCELLENT:
            return "Project is in excellent health! Ready for production use!"
        elif overall_status == HealthStatus.GOOD:
            return "Project is in good health. Some minor improvements could be made."
        elif overall_status == HealthStatus.WARNING:
            return "Project has some warnings that should be addressed."
        else:
            return "Project requires immediate attention."


def main():
    """Main entry point for the health check tool."""
    print("=" * 80)
    print("Starting project health check...")
    print("=" * 80)

    checker = ProjectHealthChecker()
    report = checker.run_all_checks()
    report.print()

    # Exit with appropriate code
    if report.overall_status in (HealthStatus.ERROR, HealthStatus.WARNING):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
