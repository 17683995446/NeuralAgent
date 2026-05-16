"""Pooling Layer - Information Compression Layer."""
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from backend.config import settings
from backend.core.llm_adapter import llm_adapter
from backend.core.agents.intelligent_multi_agent_coordinator import PoolingAgent

logger = logging.getLogger(__name__)


class PoolingLayer:
    """Pooling layer for information compression.

    Compresses and aggregates convolution layer outputs,
    extracting core features and filtering redundant information.
    """

    def __init__(
        self,
        task_id: str,
        user_requirement: str,
        short_term_memory: Optional[Any] = None
    ):
        """Initialize pooling layer.

        Args:
            task_id: Task identifier
            user_requirement: User's requirement description
            short_term_memory: Short-term memory instance
        """
        self.task_id = task_id
        self.user_requirement = user_requirement
        self.short_term_memory = short_term_memory
        self.agents: List[PoolingAgent] = []
        self.compressed_features: Optional[Dict[str, Any]] = None

    async def execute(self, convolution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pooling layer compression.

        Args:
            convolution_results: Results from convolution layer

        Returns:
            Compressed feature dictionary
        """
        logger.info(f"Starting pooling layer for task {self.task_id}")

        aggregated = convolution_results.get("aggregated_analysis", {})
        detailed = convolution_results.get("detailed_results", {})

        core_features = await self._extract_core_features(aggregated, detailed)

        compressed = await self._compress_information(core_features)

        global_features = await self._generate_global_features(compressed)

        self.compressed_features = global_features

        logger.info("Pooling layer completed")

        return global_features

    async def _extract_core_features(
        self,
        aggregated: Dict[str, Any],
        detailed: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract core features from convolution results.

        Args:
            aggregated: Aggregated analysis results
            detailed: Detailed analysis results

        Returns:
            Core features dictionary
        """
        relevant_files = []
        core_functions = aggregated.get("core_functions", [])
        related_code = aggregated.get("related_code", [])
        all_dependencies = aggregated.get("all_dependencies", [])
        potential_issues = aggregated.get("potential_issues", [])

        for path, result in detailed.items():
            if result.get("status") == "success":
                analysis = result.get("analysis", {})
                if "related_code" in analysis and analysis["related_code"]:
                    relevance_score = self._calculate_relevance_score(
                        analysis, self.user_requirement
                    )
                    relevant_files.append({
                        "file": path,
                        "relevance_score": relevance_score,
                        "functions": analysis.get("core_functions", []),
                        "dependencies": analysis.get("dependencies", []),
                    })

        relevant_files.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "total_files_analyzed": aggregated.get("total_files", 0),
            "relevant_files": relevant_files[:50],
            "core_functions": core_functions[:30],
            "all_dependencies": all_dependencies,
            "potential_issues": potential_issues,
            "related_code": related_code,
        }

    def _calculate_relevance_score(
        self,
        analysis: Dict[str, Any],
        user_requirement: str
    ) -> float:
        """Calculate relevance score for a file based on user requirement.

        Args:
            analysis: File analysis dictionary
            user_requirement: User requirement text

        Returns:
            Relevance score (0-1)
        """
        score = 0.5

        related_code = analysis.get("related_code", "")
        if related_code:
            requirement_keywords = self._extract_keywords(user_requirement)
            code_keywords = self._extract_keywords(related_code)
            overlap = len(set(requirement_keywords) & set(code_keywords))
            score += min(overlap * 0.1, 0.3)

        if analysis.get("potential_issues"):
            score += 0.1

        return min(score, 1.0)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text.

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "as", "is", "was",
            "are", "were", "been", "be", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may",
            "might", "must", "shall", "can", "need", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they"
        }

        words = text.lower().split()
        keywords = [
            w.strip(".,!?;:()[]{}") for w in words
            if len(w) > 3 and w.lower() not in stopwords
        ]
        return keywords

    async def _compress_information(self, core_features: Dict[str, Any]) -> Dict[str, Any]:
        """Compress information using LLM extraction.

        Args:
            core_features: Core features to compress

        Returns:
            Compressed information
        """
        prompt = self._build_compression_prompt(core_features)

        response = llm_adapter.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        try:
            compressed = json.loads(response.content)
            return compressed
        except json.JSONDecodeError:
            logger.warning("Failed to parse compressed features, using fallback")
            return {
                "architecture_overview": self.user_requirement,
                "core_modules": core_features.get("relevant_files", [])[:10],
                "key_functions": core_features.get("core_functions", [])[:20],
                "dependencies": core_features.get("all_dependencies", []),
                "risk_points": core_features.get("potential_issues", []),
            }

    def _build_compression_prompt(self, core_features: Dict[str, Any]) -> str:
        """Build compression prompt for LLM.

        Args:
            core_features: Core features to compress

        Returns:
            Compression prompt
        """
        relevant_files = json.dumps(
            core_features.get("relevant_files", [])[:20],
            ensure_ascii=False,
            indent=2
        )
        core_functions = json.dumps(
            core_features.get("core_functions", [])[:30],
            ensure_ascii=False,
            indent=2
        )
        dependencies = json.dumps(
            core_features.get("all_dependencies", []),
            ensure_ascii=False,
            indent=2
        )
        issues = json.dumps(
            core_features.get("potential_issues", []),
            ensure_ascii=False,
            indent=2
        )

        return f"""基于以下代码分析结果，提取核心特征并生成信息压缩报告。

用户需求:
{self.user_requirement}

相关文件（按相关性排序）:
{relevant_files}

核心函数:
{core_functions}

依赖关系:
{dependencies}

潜在问题:
{issues}

请输出以下格式的JSON压缩报告:
{{
    "architecture_overview": "工程整体架构概述（2-3句话）",
    "core_modules": [
        {{
            "name": "模块名",
            "description": "模块功能说明",
            "files": ["相关文件列表"],
            "importance": "high|medium|low"
        }}
    ],
    "key_functions": [
        {{
            "name": "函数名",
            "file": "所属文件",
            "description": "功能说明",
            "modification_priority": "high|medium|low"
        }}
    ],
    "global_dependencies": ["全局依赖列表"],
    "risk_points": [
        {{
            "description": "风险描述",
            "affected_files": ["受影响文件"],
            "severity": "high|medium|low"
        }}
    ],
    "modification_directions": ["代码修改方向建议"]
}}
"""

    async def _generate_global_features(self, compressed: Dict[str, Any]) -> Dict[str, Any]:
        """Generate global features for downstream layers.

        Args:
            compressed: Compressed information

        Returns:
            Global features dictionary
        """
        agent = PoolingAgent(
            agent_id=f"pool_{self.task_id}",
            layer_name="pooling",
            role="信息聚合专家",
            goal="整合压缩后的代码特征，生成全局代码理解所需的完整上下文",
            llm_config={
                "model": "openai/gpt-4o",
                "temperature": 0.3,
                "max_tokens": 4096,
            },
        )

        prompt = f"""基于以下压缩后的代码特征，生成全局代码理解报告。

用户需求: {self.user_requirement}

压缩特征:
{json.dumps(compressed, ensure_ascii=False, indent=2)}

请生成全局代码理解所需的完整上下文信息，输出JSON格式:
{{
    "project_overview": "项目整体概述",
    "target_modules": ["需要修改的核心模块列表"],
    "modification_strategy": "整体修改策略",
    "file_modification_order": ["文件修改顺序（考虑依赖关系）"],
    "expected_outcomes": ["预期结果列表"],
    "confidence_assessment": {{
        "overall_confidence": 0.0-1.0,
        "complexity": "low|medium|high",
        "risk_level": "low|medium|high"
    }}
}}
"""

        response = llm_adapter.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        try:
            global_features = json.loads(response.content)
        except json.JSONDecodeError:
            global_features = {
                "project_overview": compressed.get("architecture_overview", ""),
                "target_modules": [m.get("name") for m in compressed.get("core_modules", [])],
                "modification_strategy": "基于分析结果进行修改",
                "file_modification_order": [],
                "expected_outcomes": [],
                "confidence_assessment": {
                    "overall_confidence": 0.7,
                    "complexity": "medium",
                    "risk_level": "medium"
                }
            }

        return {
            **compressed,
            **global_features,
            "compression_stats": {
                "original_files": compressed.get("total_files_analyzed", 0),
                "compressed_files": len(compressed.get("core_modules", [])),
                "compression_ratio": len(compressed.get("core_modules", [])) / max(compressed.get("total_files_analyzed", 1), 1)
            }
        }

    def get_compressed_features(self) -> Optional[Dict[str, Any]]:
        """Get cached compressed features.

        Returns:
            Compressed features or None
        """
        return self.compressed_features
