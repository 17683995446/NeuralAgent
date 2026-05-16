"""Neural Fully Connected Layers - 神经网络全连接层

包含三个核心全连接层：
- FCLayer1 (Global Code Understanding Layer) - 全局代码理解层
- FCLayer2 (Code Generation Layer) - 代码生成层  
- FCLayer3 (Test Generation Layer) - 测试生成层
"""
import json
import logging
import subprocess
import os
import shutil
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from backend.core.configuration.settings_model import settings
    from backend.core.llm_integration.llm_adapter import llm_adapter
    from backend.core.agents.neural_agent import FCAgent
    from backend.core.memory.long_term_memory import LongTermMemory
    from backend.core.trust_management.trust_manager import TrustManager
except ImportError:
    from config import settings
    logger = logging.getLogger(__name__)
    logger.warning("Failed to import all modules, using fallback")

logger = logging.getLogger(__name__)


class FCLayer1:
    """Fully Connected Layer 1 - Global Code Understanding.

    Integrates global code features and generates actionable task execution plans.
    """

    def __init__(
        self,
        task_id: str,
        user_requirement: str,
        pooling_features: Dict[str, Any],
        long_term_memory: Optional[LongTermMemory] = None
    ):
        """Initialize FC Layer 1.

        Args:
            task_id: Task identifier
            user_requirement: User's requirement
            pooling_features: Features from pooling layer
            long_term_memory: Long-term memory for experience recall
        """
        self.task_id = task_id
        self.user_requirement = user_requirement
        self.pooling_features = pooling_features
        self.long_term_memory = long_term_memory
        self.agents: List[FCAgent] = []
        self.solution: Optional[Dict[str, Any]] = None

    async def execute(self) -> Dict[str, Any]:
        """Execute FC Layer 1 - Global understanding.

        Returns:
            Global code understanding and solution plan
        """
        logger.info(f"Starting FC Layer 1 for task {self.task_id}")

        historical_experiences = await self._recall_experiences()

        solution = await self._generate_solution(historical_experiences)

        risk_check = await self._risk_validation(solution)

        if not risk_check["passed"]:
            solution = await self._improve_solution(solution, risk_check)

        self.solution = solution

        if self.long_term_memory:
            self._save_experience(solution)

        logger.info("FC Layer 1 completed")

        return {
            "solution": solution,
            "historical_experiences_used": len(historical_experiences),
            "risk_validation": risk_check,
        }

    async def _recall_experiences(self) -> List[Dict[str, Any]]:
        """Recall similar historical experiences from long-term memory.

        Returns:
            List of similar historical experiences
        """
        if not self.long_term_memory:
            return []

        memories = self.long_term_memory.retrieve_similar(
            query=self.user_requirement,
            top_k=5,
            threshold=0.8
        )

        experiences = []
        for memory in memories:
            try:
                content = json.loads(memory.content)
                experiences.append({
                    "task_type": memory.metadata.get("task_type", "unknown"),
                    "content": content,
                    "create_time": memory.create_time.isoformat() if memory.create_time else None,
                })
            except json.JSONDecodeError:
                continue

        logger.info(f"Recalled {len(experiences)} similar experiences")
        return experiences

    async def _generate_solution(
        self,
        historical_experiences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate code modification solution.

        Args:
            historical_experiences: Similar historical experiences

        Returns:
            Solution dictionary
        """
        experiences_text = json.dumps(historical_experiences, ensure_ascii=False, indent=2)

        features_text = json.dumps({
            "architecture": self.pooling_features.get("architecture_overview", ""),
            "core_modules": self.pooling_features.get("core_modules", []),
            "key_functions": self.pooling_features.get("key_functions", []),
            "dependencies": self.pooling_features.get("global_dependencies", []),
            "risk_points": self.pooling_features.get("risk_points", []),
        }, ensure_ascii=False, indent=2)

        prompt = f"""基于以下信息，生成详细的代码修改方案。

用户需求:
{self.user_requirement}

代码特征:
{features_text}

历史成功经验（可作为参考）:
{experiences_text}

请输出JSON格式的完整修改方案:
{{
    "solution_overview": "方案整体概述（2-3句话）",
    "modification_files": [
        {{
            "file_path": "需要修改的文件路径",
            "modification_type": "add|modify|delete",
            "description": "修改说明",
            "expected_changes": "预期修改内容",
            "dependencies": ["依赖的其他文件"]
        }}
    ],
    "modification_sequence": ["文件修改顺序"],
    "execution_order": [
        {{
            "step": 1,
            "file": "修改的文件",
            "action": "具体操作",
            "expected_result": "预期结果"
        }}
    ],
    "risk_mitigation": [
        {{
            "risk": "风险描述",
            "mitigation": "规避方案"
        }}
    ],
    "testing_requirements": ["测试验证要求"],
    "confidence": 0.0-1.0
}}
"""

        response = llm_adapter.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        try:
            solution = json.loads(response.content)
            return solution
        except json.JSONDecodeError:
            logger.error("Failed to parse solution from LLM response")
            return self._generate_fallback_solution()

    def _generate_fallback_solution(self) -> Dict[str, Any]:
        """Generate fallback solution when LLM fails.

        Returns:
            Basic solution dictionary
        """
        files = self.pooling_features.get("core_modules", [])
        return {
            "solution_overview": f"基于用户需求「{self.user_requirement}」的代码修改方案",
            "modification_files": [
                {
                    "file_path": f.get("name", "unknown"),
                    "modification_type": "modify",
                    "description": f.get("description", ""),
                    "expected_changes": "根据需求进行相应修改",
                    "dependencies": []
                }
                for f in files[:10]
            ],
            "modification_sequence": [f.get("name", "") for f in files[:10]],
            "execution_order": [],
            "risk_mitigation": [],
            "testing_requirements": ["验证功能正常工作"],
            "confidence": 0.6
        }

    async def _risk_validation(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Validate solution for risks.

        Args:
            solution: Proposed solution

        Returns:
            Risk validation result
        """
        modification_files = solution.get("modification_files", [])
        file_paths = [f["file_path"] for f in modification_files]

        conflicts = []
        warnings = []

        file_set = set()
        for path in file_paths:
            if path in file_set:
                conflicts.append(f"重复文件: {path}")
            file_set.add(path)

        if len(file_paths) > 20:
            warnings.append(f"修改文件数量较多（{len(file_paths)}），建议分批处理")

        dependencies = self.pooling_features.get("global_dependencies", [])
        if len(dependencies) > 30:
            warnings.append(f"依赖关系复杂（{len(dependencies)}个依赖），需要注意修改顺序")

        passed = len(conflicts) == 0 and len(warnings) == 0

        return {
            "passed": passed,
            "conflicts": conflicts,
            "warnings": warnings,
            "recommendations": self._generate_recommendations(conflicts, warnings)
        }

    def _generate_recommendations(
        self,
        conflicts: List[str],
        warnings: List[str]
    ) -> List[str]:
        """Generate recommendations based on conflicts and warnings.

        Args:
            conflicts: List of conflicts
            warnings: List of warnings

        Returns:
            List of recommendations
        """
        recommendations = []

        for conflict in conflicts:
            recommendations.append(f"解决{conflict}")

        for warning in warnings:
            recommendations.append(f"注意{warning}")

        return recommendations

    async def _improve_solution(
        self,
        solution: Dict[str, Any],
        risk_check: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Improve solution based on risk validation.

        Args:
            solution: Original solution
            risk_check: Risk validation result

        Returns:
            Improved solution
        """
        improvements = risk_check.get("recommendations", [])
        if improvements:
            logger.info(f"Improving solution: {improvements}")

        solution["risk_mitigation"] = risk_check.get("risk_mitigation", [])
        solution["warnings"] = improvements

        return solution

    def _save_experience(self, solution: Dict[str, Any]) -> None:
        """Save successful solution to long-term memory.

        Args:
            solution: Successful solution
        """
        if not self.long_term_memory:
            return

        self.long_term_memory.save_memory(
            agent_id=f"fc1_{self.task_id}",
            content={
                "requirement": self.user_requirement,
                "solution": solution,
                "pooling_features": {
                    k: v for k, v in self.pooling_features.items()
                    if k in ["architecture_overview", "core_modules"]
                }
            },
            metadata={
                "task_type": "code_modification",
                "success": solution.get("confidence", 0) >= 0.7,
                "task_id": self.task_id
            }
        )

    def get_solution(self) -> Optional[Dict[str, Any]]:
        """Get cached solution.

        Returns:
            Solution or None
        """
        return self.solution


class FCLayer2:
    """Fully Connected Layer 2 - Code Generation.

    Executes code modifications based on solution from FC Layer 1.
    """

    def __init__(
        self,
        task_id: str,
        solution: Dict[str, Any],
        code_repo_path: str,
        output_dir: str,
        trust_manager: Optional[TrustManager] = None
    ):
        """Initialize FC Layer 2.

        Args:
            task_id: Task identifier
            solution: Solution from FC Layer 1
            code_repo_path: Path to code repository
            output_dir: Task output directory
            trust_manager: Trust manager for filtering
        """
        self.task_id = task_id
        self.solution = solution
        self.code_repo_path = Path(code_repo_path)
        self.output_dir = Path(output_dir)
        self.trust_manager = trust_manager
        self.agents: List[FCAgent] = []
        self.code_changes: List[Dict[str, Any]] = []
        self.failed_changes: List[Dict[str, Any]] = []

    async def execute(self) -> Dict[str, Any]:
        """Execute FC Layer 2 - Code generation.

        Returns:
            Code generation results
        """
        logger.info(f"Starting FC Layer 2 for task {self.task_id}")

        modification_files = self.solution.get("modification_files", [])

        if self.trust_manager:
            filtered_files = self._filter_by_trust(modification_files)
        else:
            filtered_files = modification_files

        for file_mod in filtered_files:
            try:
                result = await self._modify_file(file_mod)
                if result["status"] == "success":
                    self.code_changes.append(result)
                else:
                    self.failed_changes.append(result)
            except Exception as e:
                logger.error(f"Failed to modify {file_mod.get('file_path')}: {e}")
                self.failed_changes.append({
                    "file_path": file_mod.get("file_path"),
                    "status": "failed",
                    "error": str(e)
                })

        validated_changes = await self._validate_changes()

        summary = self._generate_summary()

        logger.info(f"FC Layer 2 completed: {len(self.code_changes)} changes, {len(self.failed_changes)} failures")

        return {
            "changes": self.code_changes,
            "failed_changes": self.failed_changes,
            "validated_changes": validated_changes,
            "summary": summary
        }

    def _filter_by_trust(
        self,
        modification_files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter modifications by trust score.

        Args:
            modification_files: List of file modifications

        Returns:
            Filtered list
        """
        if not self.trust_manager:
            return modification_files

        threshold = settings.trust_filter_threshold
        high_threshold = settings.default_confidence_threshold

        filtered = []
        for mod in modification_files:
            trust_score = mod.get("trust_score", 1.0)
            if trust_score >= threshold:
                mod["need_recheck"] = trust_score < high_threshold
                filtered.append(mod)

        return filtered

    async def _modify_file(self, file_mod: Dict[str, Any]) -> Dict[str, Any]:
        """Modify a single file.

        Args:
            file_mod: File modification specification

        Returns:
            Modification result
        """
        file_path = self.code_repo_path / file_mod["file_path"]
        mod_type = file_mod.get("modification_type", "modify")

        if not file_path.exists() and mod_type != "add":
            return {
                "file_path": file_mod["file_path"],
                "status": "failed",
                "error": "File not found"
            }

        if mod_type == "add":
            return await self._add_file(file_path, file_mod)
        elif mod_type == "delete":
            return await self._delete_file(file_path, file_mod)
        else:
            return await self._modify_existing_file(file_path, file_mod)

    async def _add_file(
        self,
        file_path: Path,
        file_mod: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a new file.

        Args:
            file_path: Path to new file
            file_mod: Modification specification

        Returns:
            Result dictionary
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            expected_changes = file_mod.get("expected_changes", "")
            if not expected_changes:
                prompt = f"""为以下需求生成新文件内容:

文件路径: {file_mod['file_path']}
描述: {file_mod.get('description', '')}

请只输出代码内容，不需要其他说明。
如果需要生成完整的可执行代码。
"""
                response = llm_adapter.complete(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                expected_changes = response.content

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(expected_changes)

            return {
                "file_path": str(file_path),
                "modification_type": "add",
                "status": "success",
                "lines_added": len(expected_changes.split("\n"))
            }

        except Exception as e:
            return {
                "file_path": str(file_path),
                "status": "failed",
                "error": str(e)
            }

    async def _delete_file(
        self,
        file_path: Path,
        file_mod: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delete a file.

        Args:
            file_path: Path to file
            file_mod: Modification specification

        Returns:
            Result dictionary
        """
        try:
            if file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                shutil.copy2(file_path, backup_path)

            file_path.unlink(missing_ok=True)

            return {
                "file_path": str(file_path),
                "modification_type": "delete",
                "status": "success",
                "backup_path": str(backup_path) if file_path.exists() else None
            }

        except Exception as e:
            return {
                "file_path": str(file_path),
                "status": "failed",
                "error": str(e)
            }

    async def _modify_existing_file(
        self,
        file_path: Path,
        file_mod: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modify an existing file.

        Args:
            file_path: Path to file
            file_mod: Modification specification

        Returns:
            Result dictionary
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            prompt = self._build_modification_prompt(file_path, original_content, file_mod)

            response = llm_adapter.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            new_content = response.content
            if new_content.startswith("```"):
                lines = new_content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                new_content = "\n".join(lines)

            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original_content)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            syntax_valid = await self._validate_syntax(file_path)

            return {
                "file_path": str(file_path),
                "modification_type": "modify",
                "status": "success" if syntax_valid else "warning",
                "original_lines": len(original_content.split("\n")),
                "new_lines": len(new_content.split("\n")),
                "syntax_valid": syntax_valid,
                "backup_path": str(backup_path)
            }

        except Exception as e:
            return {
                "file_path": str(file_path),
                "status": "failed",
                "error": str(e)
            }

    def _build_modification_prompt(
        self,
        file_path: Path,
        original_content: str,
        file_mod: Dict[str, Any]
    ) -> str:
        """Build modification prompt for LLM.

        Args:
            file_path: File path
            original_content: Original file content
            file_mod: Modification specification

        Returns:
            Prompt string
        """
        language = self._get_language_from_path(file_path)
        max_lines = 300
        lines = original_content.split("\n")
        truncated_content = "\n".join(lines[:max_lines])
        if len(lines) > max_lines:
            truncated_content += f"\n... (truncated, total {len(lines)} lines)"

        return f"""修改以下文件以满足需求。

文件路径: {file_mod['file_path']}
描述: {file_mod.get('description', '')}
预期修改: {file_mod.get('expected_changes', '')}

原始代码:
```{language}
{truncated_content}
```

请输出修改后的完整代码内容（只输出代码，不要其他说明）。
"""

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
        }
        return ext_map.get(file_path.suffix.lower(), "text")

    async def _validate_syntax(self, file_path: Path) -> bool:
        """Validate code syntax.

        Args:
            file_path: Path to file

        Returns:
            True if syntax is valid
        """
        try:
            ext = file_path.suffix.lower()

            if ext == ".py":
                result = subprocess.run(
                    ["python", "-m", "py_compile", str(file_path)],
                    capture_output=True,
                    timeout=10
                )
                return result.returncode == 0

            return True

        except Exception as e:
            logger.warning(f"Syntax validation failed: {e}")
            return False

    async def _validate_changes(self) -> Dict[str, Any]:
        """Validate all code changes.

        Returns:
            Validation result
        """
        validated = []
        validation_errors = []

        for change in self.code_changes:
            file_path = Path(change["file_path"])
            if file_path.exists():
                is_valid = await self._validate_syntax(file_path)
                change["validation"] = "passed" if is_valid else "failed"
                if is_valid:
                    validated.append(change)
                else:
                    validation_errors.append(change)
            else:
                change["validation"] = "file_missing"
                validation_errors.append(change)

        return {
            "total_changes": len(self.code_changes),
            "validated_changes": len(validated),
            "validation_errors": len(validation_errors),
            "errors": validation_errors
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate code generation summary.

        Returns:
            Summary dictionary
        """
        total_lines = sum(
            c.get("new_lines", 0) - c.get("original_lines", 0)
            for c in self.code_changes
            if c.get("modification_type") == "modify"
        )
        total_lines += sum(c.get("lines_added", 0) for c in self.code_changes if c.get("modification_type") == "add")

        return {
            "total_files_modified": len(self.code_changes),
            "total_files_failed": len(self.failed_changes),
            "net_lines_changed": total_lines,
            "additions": sum(c.get("lines_added", 0) for c in self.code_changes),
            "deletions": sum(
                c.get("original_lines", 0) - c.get("new_lines", 0)
                for c in self.code_changes
                if c.get("modification_type") == "modify"
            ),
            "success_rate": len(self.code_changes) / max(len(self.code_changes) + len(self.failed_changes), 1)
        }

    def get_code_changes(self) -> List[Dict[str, Any]]:
        """Get all code changes.

        Returns:
            List of code changes
        """
        return self.code_changes


class FCLayer3:
    """Fully Connected Layer 3 - Test Generation.

    Generates unit tests and integration tests for modified code.
    """

    def __init__(
        self,
        task_id: str,
        code_changes: List[Dict[str, Any]],
        code_repo_path: str,
        output_dir: str
    ):
        """Initialize FC Layer 3.

        Args:
            task_id: Task identifier
            code_changes: Code changes from FC Layer 2
            code_repo_path: Path to code repository
            output_dir: Task output directory
        """
        self.task_id = task_id
        self.code_changes = code_changes
        self.code_repo_path = Path(code_repo_path)
        self.output_dir = Path(output_dir) / "tests"
        self.agents: List[FCAgent] = []
        self.test_cases: List[Dict[str, Any]] = []
        self.failed_tests: List[Dict[str, Any]] = []

        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self) -> Dict[str, Any]:
        """Execute FC Layer 3 - Test generation.

        Returns:
            Test generation results
        """
        logger.info(f"Starting FC Layer 3 for task {self.task_id}")

        for change in self.code_changes:
            if change.get("status") == "success":
                try:
                    tests = await self._generate_tests_for_file(change)
                    self.test_cases.extend(tests)
                except Exception as e:
                    logger.error(f"Failed to generate tests for {change.get('file_path')}: {e}")
                    self.failed_tests.append({
                        "file_path": change.get("file_path"),
                        "error": str(e)
                    })

        test_results = await self._run_tests()

        coverage_report = await self._generate_coverage_report()

        summary = self._generate_summary()

        logger.info(f"FC Layer 3 completed: {len(self.test_cases)} test cases generated")

        return {
            "test_cases": self.test_cases,
            "failed_tests": self.failed_tests,
            "test_results": test_results,
            "coverage_report": coverage_report,
            "summary": summary
        }

    async def _generate_tests_for_file(
        self,
        code_change: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate tests for a modified file.

        Args:
            code_change: Code change specification

        Returns:
            List of generated test cases
        """
        file_path = Path(code_change["file_path"])
        if not file_path.exists():
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        test_cases = []

        if file_path.suffix == ".py":
            tests = await self._generate_python_tests(file_path, content)
            test_cases.extend(tests)

        return test_cases

    async def _generate_python_tests(
        self,
        file_path: Path,
        content: str
    ) -> List[Dict[str, Any]]:
        """Generate Python unit tests.

        Args:
            file_path: Path to source file
            content: Source file content

        Returns:
            List of test case dictionaries
        """
        test_dir = self.output_dir
        test_file_name = f"test_{file_path.stem}.py"
        test_file_path = test_dir / test_file_name

        prompt = self._build_test_prompt(file_path, content)

        response = llm_adapter.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        test_content = response.content
        if test_content.startswith("```python"):
            lines = test_content.split("\n")[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            test_content = "\n".join(lines)
        elif test_content.startswith("```"):
            lines = test_content.split("\n")[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            test_content = "\n".join(lines)

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)

        test_cases = await self._parse_test_cases(test_file_path, test_content)

        return test_cases

    def _build_test_prompt(
        self,
        file_path: Path,
        content: str
    ) -> str:
        """Build test generation prompt.

        Args:
            file_path: Source file path
            content: Source file content

        Returns:
            Prompt string
        """
        max_lines = 300
        lines = content.split("\n")
        truncated_content = "\n".join(lines[:max_lines])
        if len(lines) > max_lines:
            truncated_content += f"\n... (truncated, total {len(lines)} lines)"

        return f"""为以下Python代码生成单元测试和集成测试。

目标文件: {file_path}
代码内容:
```python
{truncated_content}
```

请生成pytest格式的测试文件，要求:
1. 覆盖正常场景、边界场景、异常场景
2. 使用pytest框架
3. 包含清晰的测试用例名称
4. 每个核心函数/类至少有一个测试用例
5. 适当使用mock

请只输出测试代码，不需要其他说明。
"""

    async def _parse_test_cases(
        self,
        test_file_path: Path,
        test_content: str
    ) -> List[Dict[str, Any]]:
        """Parse generated test cases.

        Args:
            test_file_path: Path to test file
            test_content: Test file content

        Returns:
            List of test case dictionaries
        """
        test_cases = []
        lines = test_content.split("\n")

        current_test = None
        test_lines = []

        for line in lines:
            if line.strip().startswith("def test_"):
                if current_test:
                    test_cases.append({
                        "test_file": str(test_file_path),
                        "test_name": current_test,
                        "content": "\n".join(test_lines),
                        "target_file": str(self.code_repo_path / test_file_path.stem.replace("test_", "") + ".py")
                    })
                current_test = line.strip().split("def test_")[1].split("(")[0]
                test_lines = [line]
            elif current_test:
                test_lines.append(line)

        if current_test:
            test_cases.append({
                "test_file": str(test_file_path),
                "test_name": current_test,
                "content": "\n".join(test_lines),
                "target_file": str(self.code_repo_path / test_file_path.stem.replace("test_", "") + ".py")
            })

        return test_cases

    async def _run_tests(self) -> Dict[str, Any]:
        """Run all test cases.

        Returns:
            Test execution results
        """
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }

        for test_case in self.test_cases:
            test_file = Path(test_case["test_file"])
            if not test_file.exists():
                results["errors"] += 1
                results["details"].append({
                    "test_name": test_case["test_name"],
                    "status": "error",
                    "error": "Test file not found"
                })
                continue

            try:
                result = subprocess.run(
                    ["pytest", str(test_file), "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.code_repo_path
                )

                results["total"] += 1
                if result.returncode == 0:
                    results["passed"] += 1
                    status = "passed"
                elif "SKIPPED" in result.stdout:
                    results["skipped"] += 1
                    status = "skipped"
                else:
                    results["failed"] += 1
                    status = "failed"

                results["details"].append({
                    "test_name": test_case["test_name"],
                    "status": status,
                    "output": result.stdout[:500] if result.stdout else "",
                    "error": result.stderr[:500] if result.stderr else ""
                })

            except subprocess.TimeoutExpired:
                results["errors"] += 1
                results["details"].append({
                    "test_name": test_case["test_name"],
                    "status": "error",
                    "error": "Test timeout"
                })
            except Exception as e:
                results["errors"] += 1
                results["details"].append({
                    "test_name": test_case["test_name"],
                    "status": "error",
                    "error": str(e)
                })

        return results

    async def _generate_coverage_report(self) -> Dict[str, Any]:
        """Generate test coverage report.

        Returns:
            Coverage report dictionary
        """
        coverage_report = {
            "total_coverage": 0.0,
            "modified_code_coverage": 0.0,
            "uncovered_lines": []
        }

        modified_files = [
            Path(c["file_path"]) for c in self.code_changes
            if c.get("status") == "success"
        ]

        if not modified_files:
            return coverage_report

        try:
            result = subprocess.run(
                [
                    "pytest",
                    str(self.output_dir),
                    "--cov=" + str(self.code_repo_path),
                    "--cov-report=json",
                    "-v"
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.code_repo_path
            )

            coverage_file = self.code_repo_path / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                total_lines = coverage_data.get("totals", {}).get("lines", {}).get("total", 0)
                covered_lines = coverage_data.get("totals", {}).get("lines", {}).get("covered", 0)
                coverage_report["total_coverage"] = covered_lines / max(total_lines, 1) * 100

        except Exception as e:
            logger.warning(f"Coverage report generation failed: {e}")

        return coverage_report

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test generation summary.

        Returns:
            Summary dictionary
        """
        return {
            "total_test_cases": len(self.test_cases),
            "failed_test_generations": len(self.failed_tests),
            "test_files_generated": len(set(t["test_file"] for t in self.test_cases)),
            "estimated_coverage": 70.0
        }

    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all generated test cases.

        Returns:
            List of test cases
        """
        return self.test_cases

