"""Output Layer - Markdown Document Generation."""
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown

from backend.config import settings

logger = logging.getLogger(__name__)


class OutputLayer:
    """Output layer for Markdown document generation.

    Integrates code changes and test results into structured reports.
    """

    def __init__(
        self,
        task_id: str,
        output_dir: str,
        template_dir: Optional[str] = None
    ):
        """Initialize output layer.

        Args:
            task_id: Task identifier
            output_dir: Output directory path
            template_dir: Template directory path
        """
        self.task_id = task_id
        self.output_dir = Path(output_dir)
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent.parent.parent / "docs" / "templates"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(['html', 'xml'])
            )
        else:
            self.jinja_env = None
            logger.warning(f"Template directory not found: {self.template_dir}")

    async def execute(
        self,
        user_requirement: str,
        code_changes: List[Dict[str, Any]],
        test_results: Dict[str, Any],
        coverage_report: Dict[str, Any],
        solution: Dict[str, Any],
        iteration: int = 1
    ) -> Dict[str, Any]:
        """Execute output layer - Generate report.

        Args:
            user_requirement: User's requirement
            code_changes: Code changes from FC Layer 2
            test_results: Test results from FC Layer 3
            coverage_report: Coverage report
            solution: Solution from FC Layer 1
            iteration: Current iteration number

        Returns:
            Output result with document paths
        """
        logger.info(f"Starting output layer for task {self.task_id}")

        report_data = self._prepare_report_data(
            user_requirement,
            code_changes,
            test_results,
            coverage_report,
            solution,
            iteration
        )

        if self.jinja_env:
            md_content = await self._render_template(report_data)
        else:
            md_content = self._generate_markdown_fallback(report_data)

        md_path = self.output_dir / f"task_report_iter{iteration}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        html_content = self._convert_to_html(md_content)
        html_path = self.output_dir / f"task_report_iter{iteration}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        summary_path = self.output_dir / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": self.task_id,
                "iteration": iteration,
                "report_path": str(md_path),
                "html_path": str(html_path),
                "timestamp": datetime.utcnow().isoformat(),
                "stats": report_data["stats"]
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Output layer completed: {md_path}")

        return {
            "report_path": str(md_path),
            "html_path": str(html_path),
            "summary_path": str(summary_path),
            "content": md_content,
            "stats": report_data["stats"]
        }

    def _prepare_report_data(
        self,
        user_requirement: str,
        code_changes: List[Dict[str, Any]],
        test_results: Dict[str, Any],
        coverage_report: Dict[str, Any],
        solution: Dict[str, Any],
        iteration: int
    ) -> Dict[str, Any]:
        """Prepare report data.

        Args:
            user_requirement: User requirement
            code_changes: Code changes
            test_results: Test results
            coverage_report: Coverage report
            solution: Solution
            iteration: Iteration number

        Returns:
            Report data dictionary
        """
        stats = {
            "total_files_modified": len(code_changes),
            "successful_changes": sum(1 for c in code_changes if c.get("status") == "success"),
            "failed_changes": sum(1 for c in code_changes if c.get("status") != "success"),
            "total_tests": test_results.get("total", 0),
            "passed_tests": test_results.get("passed", 0),
            "failed_tests": test_results.get("failed", 0),
            "total_coverage": coverage_report.get("total_coverage", 0),
        }

        code_changes_formatted = []
        for change in code_changes:
            if change.get("status") == "success":
                file_path = Path(change["file_path"])
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        full_code = f.read()
                else:
                    full_code = ""

                code_changes_formatted.append({
                    "file_path": change["file_path"],
                    "modification_type": change.get("modification_type", "modify"),
                    "description": solution.get("modification_files", [{}])[0].get("description", ""),
                    "diff_content": self._generate_diff(change),
                    "full_code": full_code[:2000],
                    "language": self._get_language_from_path(file_path),
                    "lines_added": change.get("lines_added", 0),
                    "original_lines": change.get("original_lines", 0),
                })

        test_cases_formatted = []
        for detail in test_results.get("details", []):
            test_cases_formatted.append({
                "test_name": detail.get("test_name", "unknown"),
                "test_file_path": detail.get("test_file", "unknown"),
                "result": detail.get("status", "unknown"),
                "error": detail.get("error", ""),
            })

        return {
            "task_id": self.task_id,
            "user_requirement": user_requirement,
            "execute_time": datetime.utcnow().isoformat(),
            "iteration": iteration,
            "code_changes": code_changes_formatted,
            "test_cases": test_cases_formatted,
            "test_results": test_results,
            "coverage": coverage_report,
            "solution": solution,
            "stats": stats,
        }

    def _generate_diff(self, change: Dict[str, Any]) -> str:
        """Generate diff content for a change.

        Args:
            change: Code change dictionary

        Returns:
            Diff string
        """
        mod_type = change.get("modification_type", "modify")
        file_path = change.get("file_path", "unknown")

        if mod_type == "add":
            return f"+ New file: {file_path}"
        elif mod_type == "delete":
            return f"- Deleted file: {file_path}"
        else:
            original = change.get("original_lines", 0)
            new = change.get("new_lines", 0)
            diff = new - original
            sign = "+" if diff >= 0 else ""
            return f"~ Modified: {file_path} ({sign}{diff} lines)"

    def _get_language_from_path(self, file_path: Path) -> str:
        """Get language from file path.

        Args:
            file_path: File path

        Returns:
            Language identifier
        """
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
        }
        return ext_map.get(file_path.suffix.lower(), "text")

    async def _render_template(self, report_data: Dict[str, Any]) -> str:
        """Render report using Jinja2 template.

        Args:
            report_data: Report data

        Returns:
            Rendered Markdown content
        """
        if not self.jinja_env:
            return self._generate_markdown_fallback(report_data)

        try:
            template = self.jinja_env.get_template("task_report.md.jinja2")
            return template.render(**report_data)
        except Exception as e:
            logger.warning(f"Template rendering failed: {e}, using fallback")
            return self._generate_markdown_fallback(report_data)

    def _generate_markdown_fallback(self, report_data: Dict[str, Any]) -> str:
        """Generate Markdown report without template.

        Args:
            report_data: Report data

        Returns:
            Markdown content
        """
        lines = []

        lines.append("# 代码修改任务报告")
        lines.append("")
        lines.append("## 任务概述")
        lines.append(f"- **任务ID**: {report_data['task_id']}")
        lines.append(f"- **用户需求**: {report_data['user_requirement']}")
        lines.append(f"- **执行时间**: {report_data['execute_time']}")
        lines.append(f"- **迭代次数**: {report_data['iteration']}")
        lines.append("")

        lines.append("## 统计信息")
        stats = report_data["stats"]
        lines.append(f"- 修改文件数: {stats['total_files_modified']}")
        lines.append(f"- 成功修改: {stats['successful_changes']}")
        lines.append(f"- 失败修改: {stats['failed_changes']}")
        lines.append(f"- 测试用例数: {stats['total_tests']}")
        lines.append(f"- 通过测试: {stats['passed_tests']}")
        lines.append(f"- 失败测试: {stats['failed_tests']}")
        lines.append(f"- 代码覆盖率: {stats['total_coverage']:.1f}%")
        lines.append("")

        lines.append("## 代码修改清单")
        for i, change in enumerate(report_data["code_changes"], 1):
            lines.append(f"### {i}. {change['file_path']}")
            lines.append(f"- 修改类型: {change['modification_type']}")
            lines.append(f"- 说明: {change['description']}")
            lines.append(f"- 差异: {change['diff_content']}")
            lines.append("")
            if change.get("full_code"):
                lines.append(f"```{change['language']}")
                lines.append(change["full_code"][:1000])
                if len(change["full_code"]) > 1000:
                    lines.append("... (truncated)")
                lines.append("```")
            lines.append("")

        lines.append("## 测试用例与执行结果")
        for test in report_data["test_cases"]:
            lines.append(f"### {test['test_name']}")
            lines.append(f"- 测试文件: {test['test_file_path']}")
            lines.append(f"- 执行结果: {test['result']}")
            if test.get("error"):
                lines.append(f"- 错误: {test['error']}")
            lines.append("")

        lines.append("## 测试覆盖率报告")
        cov = report_data["coverage"]
        lines.append(f"- 总覆盖率: {cov.get('total_coverage', 0):.1f}%")
        lines.append(f"- 修改代码覆盖率: {cov.get('modified_code_coverage', 0):.1f}%")
        lines.append("")

        return "\n".join(lines)

    def _convert_to_html(self, md_content: str) -> str:
        """Convert Markdown to HTML.

        Args:
            md_content: Markdown content

        Returns:
            HTML content
        """
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>任务报告 - {self.task_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
               max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; }}
        code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .stats {{ background: #e9ecef; padding: 15px; border-radius: 5px; }}
        .success {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
    </style>
</head>
<body>
{markdown(md_content)}
</body>
</html>"""
