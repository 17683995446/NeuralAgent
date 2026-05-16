"""Convolution Layer - Code Analysis Layer."""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from enum import Enum

from backend.config import settings
from backend.core.llm_adapter import create_llm_adapter, LLMProvider
from backend.core.memory.short_term_memory import ShortTermMemory
from backend.core.agents.intelligent_multi_agent_coordinator import ConvolutionAgent


# 兼容层 - 创建全局的 llm_adapter 实例
llm_adapter = create_llm_adapter(provider=LLMProvider.MOCK)

logger = logging.getLogger(__name__)


class ConvolutionGranularity(str, Enum):
    """Convolution kernel granularity types."""
    FILE = "file"
    FUNCTION = "function"
    MODULE = "module"


class ConvolutionLayer:
    """Convolution layer for code analysis.

    Each agent corresponds to a convolution kernel scanning code units.
    Supports file-level, function-level, and module-level granularity.
    """

    def __init__(
        self,
        task_id: str,
        code_repo_path: str,
        granularity: ConvolutionGranularity = ConvolutionGranularity.FILE,
        short_term_memory: Optional[ShortTermMemory] = None
    ):
        """Initialize convolution layer.

        Args:
            task_id: Task identifier
            code_repo_path: Path to code repository
            granularity: Convolution kernel granularity
            short_term_memory: Short-term memory instance
        """
        self.task_id = task_id
        self.code_repo_path = Path(code_repo_path)
        self.granularity = granularity
        self.short_term_memory = short_term_memory
        self.agents: List[ConvolutionAgent] = []
        self.analysis_results: Dict[str, Any] = {}

    async def execute(self) -> Dict[str, Any]:
        """Execute convolution layer analysis.

        Returns:
            Dictionary of analysis results keyed by code unit
        """
        logger.info(f"Starting convolution layer for task {self.task_id}")

        code_units = await self._scan_code_units()

        logger.info(f"Found {len(code_units)} code units to analyze")

        for unit in code_units:
            agent = self._create_agent(unit)
            self.agents.append(agent)

        results = await self._run_parallel_analysis(code_units)

        self.analysis_results = results

        pooled_results = self._aggregate_results(results)

        logger.info(f"Convolution layer completed: {len(results)} units analyzed")

        return pooled_results

    async def _scan_code_units(self) -> List[Dict[str, Any]]:
        """Scan code repository for code units.

        Returns:
            List of code unit information dictionaries
        """
        code_units = []
        valid_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
            ".rs", ".cpp", ".c", ".h", ".cs", ".rb", ".php"
        }

        if self.granularity == ConvolutionGranularity.FILE:
            for root, dirs, files in os.walk(self.code_repo_path):
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "__pycache__", ".venv", "venv"]]

                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in valid_extensions:
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(self.code_repo_path)
                        code_units.append({
                            "type": "file",
                            "path": str(file_path),
                            "relative_path": str(rel_path),
                            "name": file,
                            "extension": ext,
                        })

        elif self.granularity == ConvolutionGranularity.MODULE:
            for item in self.code_repo_path.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    code_units.append({
                        "type": "module",
                        "path": str(item),
                        "relative_path": item.name,
                        "name": item.name,
                    })

        elif self.granularity == ConvolutionGranularity.FUNCTION:
            code_units = await self._scan_functions()

        return code_units

    async def _scan_functions(self) -> List[Dict[str, Any]]:
        """Scan for individual functions/classes.

        Returns:
            List of function-level code units
        """
        code_units = []
        try:
            import tree_sitter_python as tspython
            from tree_sitter import Language, Parser

            language = Language(tspython.language())
            parser = Parser(language)

        except ImportError:
            logger.warning("tree-sitter not available, falling back to file-level granularity")
            return await self._scan_code_units()

        valid_extensions = {".py"}
        for ext in valid_extensions:
            for file_path in self.code_repo_path.rglob(f"*{ext}"):
                try:
                    with open(file_path, "rb") as f:
                        tree = parser.parse(f.read())

                    functions = self._extract_functions(tree.root_node, file_path)
                    code_units.extend(functions)

                except Exception as e:
                    logger.warning(f"Failed to parse {file_path}: {e}")

        return code_units

    def _extract_functions(self, node, file_path: Path) -> List[Dict[str, Any]]:
        """Extract function definitions from AST.

        Args:
            node: AST root node
            file_path: Source file path

        Returns:
            List of function code units
        """
        functions = []
        query = """
            (function_definition
                name: (identifier) @name
            )
            (class_definition
                name: (identifier) @name
            )
        """

        try:
            from tree_sitter import Query

            q = Query(tree_sitter_python.language(), query)
            captures = q.captures(node)

            for capture in captures:
                name = capture[0].text.decode() if isinstance(capture[0].text, bytes) else capture[0].text
                functions.append({
                    "type": "function",
                    "path": str(file_path),
                    "relative_path": str(file_path.relative_to(self.code_repo_path)),
                    "name": name,
                    "start_line": capture[0].start_point[0] + 1,
                })

        except Exception as e:
            logger.warning(f"Failed to extract functions: {e}")

        return functions

    def _create_agent(self, code_unit: Dict[str, Any]) -> ConvolutionAgent:
        """Create convolution agent for a code unit.

        Args:
            code_unit: Code unit information

        Returns:
            ConvolutionAgent instance
        """
        agent_id = f"conv_{code_unit['type']}_{code_unit['relative_path'].replace('/', '_').replace('.', '_')}"

        llm_config = {
            "model": "openai/gpt-4o",
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        role = f"代码分析工程师-{code_unit['name']}"
        goal = f"精准分析{code_unit['relative_path']}的代码结构、功能逻辑、依赖关系，为后续代码修改提供完整的分析报告"

        return ConvolutionAgent(
            agent_id=agent_id,
            layer_name="convolution",
            role=role,
            goal=goal,
            llm_config=llm_config,
            trust_matrix={"global": 1.0},
            short_term_memory=self.short_term_memory,
        )

    async def _run_parallel_analysis(
        self,
        code_units: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run parallel analysis on code units.

        Args:
            code_units: List of code units to analyze

        Returns:
            Dictionary of analysis results
        """
        results = {}

        for unit in code_units:
            try:
                result = await self._analyze_code_unit(unit)
                results[unit["relative_path"]] = result
            except Exception as e:
                logger.error(f"Analysis failed for {unit['relative_path']}: {e}")
                results[unit["relative_path"]] = {
                    "status": "failed",
                    "error": str(e),
                    "code_unit": unit,
                }

        return results

    async def _analyze_code_unit(self, code_unit: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single code unit.

        Args:
            code_unit: Code unit information

        Returns:
            Analysis result dictionary
        """
        file_path = Path(code_unit["path"])

        if not file_path.exists():
            return {"status": "failed", "error": "File not found"}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        except Exception as e:
            return {"status": "failed", "error": f"Failed to read file: {e}"}

        prompt = self._build_analysis_prompt(code_unit, content)

        response = await llm_adapter.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        try:
            analysis = json.loads(response.content)
        except json.JSONDecodeError:
            analysis = {
                "status": "partial",
                "raw_output": response.content,
                "content_summary": content[:500] + "..." if len(content) > 500 else content,
            }

        return {
            "status": "success",
            "code_unit": code_unit,
            "analysis": analysis,
            "confidence": 0.9,
            "token_usage": response.usage,
        }

    def _build_analysis_prompt(
        self,
        code_unit: Dict[str, Any],
        content: str
    ) -> str:
        """Build analysis prompt for LLM.

        Args:
            code_unit: Code unit information
            content: Source code content

        Returns:
            Analysis prompt string
        """
        max_lines = 500
        lines = content.split("\n")
        truncated_content = "\n".join(lines[:max_lines])
        if len(lines) > max_lines:
            truncated_content += f"\n... (truncated, total {len(lines)} lines)"

        return f"""分析以下{code_unit['type']}的代码，输出结构化的JSON分析报告。

文件信息:
- 路径: {code_unit['relative_path']}
- 类型: {code_unit['type']}

代码内容:
```{self._get_language_from_ext(code_unit.get('extension', '.txt'))}
{truncated_content}
```

请输出以下格式的JSON（不要输出其他内容）:
{{
    "file_summary": "文件功能概述（1-2句话）",
    "core_functions": [
        {{
            "name": "函数名",
            "description": "函数功能说明",
            "parameters": ["参数列表"],
            "return_type": "返回类型"
        }}
    ],
    "dependencies": ["依赖的模块/库列表"],
    "related_code": "与用户需求相关的代码片段",
    "potential_issues": ["潜在问题列表"],
    "modification_hints": ["修改建议"]
}}
"""

    def _get_language_from_ext(self, ext: str) -> str:
        """Get language identifier for code block.

        Args:
            ext: File extension

        Returns:
            Language identifier
        """
        lang_map = {
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
        return lang_map.get(ext.lower(), "text")

    def _aggregate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate analysis results.

        Args:
            results: Individual analysis results

        Returns:
            Aggregated results dictionary
        """
        all_functions = []
        all_dependencies = set()
        all_issues = []
        all_related_code = []

        for path, result in results.items():
            if result.get("status") != "success":
                continue

            analysis = result.get("analysis", {})
            if "core_functions" in analysis:
                all_functions.extend(analysis["core_functions"])
            if "dependencies" in analysis:
                all_dependencies.update(analysis["dependencies"])
            if "potential_issues" in analysis:
                all_issues.extend(analysis["potential_issues"])
            if "related_code" in analysis:
                all_related_code.append({
                    "file": path,
                    "code": analysis["related_code"]
                })

        return {
            "convolution_summary": {
                "total_files": len(results),
                "successful": sum(1 for r in results.values() if r.get("status") == "success"),
                "failed": sum(1 for r in results.values() if r.get("status") != "success"),
            },
            "aggregated_analysis": {
                "total_functions": len(all_functions),
                "core_functions": all_functions[:20],
                "all_dependencies": list(all_dependencies),
                "potential_issues": all_issues[:10],
                "related_code": all_related_code[:20],
            },
            "detailed_results": results,
        }

    def get_agent_count(self) -> int:
        """Get number of agents in this layer.

        Returns:
            Agent count
        """
        return len(self.agents)


class ConvolutionLayerCrew:
    """CrewAI-based convolution layer for parallel agent execution."""

    def __init__(
        self,
        task_id: str,
        code_repo_path: str,
        granularity: ConvolutionGranularity = ConvolutionGranularity.FILE
    ):
        """Initialize convolution layer crew.

        Args:
            task_id: Task identifier
            code_repo_path: Path to code repository
            granularity: Convolution kernel granularity
        """
        self.task_id = task_id
        self.code_repo_path = code_repo_path
        self.granularity = granularity
        self.layer = ConvolutionLayer(
            task_id=task_id,
            code_repo_path=code_repo_path,
            granularity=granularity
        )

    async def execute(self) -> Dict[str, Any]:
        """Execute convolution layer with crew.

        Returns:
            Execution results
        """
        return await self.layer.execute()


# 兼容性别名 - 注意必须放在类定义之后
class NeuralConvolutionLayer(ConvolutionLayer):
    """兼容性别名，与旧代码保持一致。"""
    pass
