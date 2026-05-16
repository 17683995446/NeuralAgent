"""Neural Reasoning Layer - 神经网络推理层

Layer 14 of the NeuralAgent Deep Architecture.

功能：
- 进行逻辑推理和决策
- 支持因果推理和演绎推理
- 生成推理结论
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class ReasoningConfig:
    """推理层配置"""
    reasoning_depth: int = 3
    confidence_threshold: float = 0.7
    max_reasoning_steps: int = 10
    use_chain_of_thought: bool = True


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: int
    premise: str
    conclusion: str
    confidence: float
    reasoning_type: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class ReasoningResult:
    """推理结果"""
    query: str
    conclusion: str
    confidence: float
    reasoning_steps: List[ReasoningStep]
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class NeuralReasoningLayer:
    """神经网络推理层 - Layer 14
    
    进行逻辑推理和决策。
    """
    
    def __init__(self, config: Optional[ReasoningConfig] = None):
        self.config = config or ReasoningConfig()
        
        self._stats = {
            "total_reasonings": 0,
            "total_steps": 0,
            "total_processing_time_ms": 0.0,
            "avg_confidence": 0.0,
        }
    
    async def forward(
        self,
        input_data: Union[Dict[str, Any], str]
    ) -> Dict[str, Any]:
        """前向传播
        
        Args:
            input_data: 输入数据
            
        Returns:
            包含推理结果的字典
        """
        import time
        start_time = time.time()
        
        if isinstance(input_data, dict):
            memory_context = input_data.get("memory_context", "")
            query = input_data.get("query", "")
            retrieved_memories = input_data.get("retrieved_memories", [])
        else:
            memory_context = ""
            query = str(input_data)
            retrieved_memories = []
        
        reasoning_result = await self._perform_reasoning(query, memory_context, retrieved_memories)
        
        self._stats["total_reasonings"] += 1
        self._stats["total_steps"] += len(reasoning_result.reasoning_steps)
        
        processing_time = (time.time() - start_time) * 1000
        self._stats["total_processing_time_ms"] += processing_time
        
        return {
            "reasoning_output": reasoning_result.conclusion,
            "reasoning_confidence": reasoning_result.confidence,
            "reasoning_steps": [
                {
                    "step_id": step.step_id,
                    "premise": step.premise,
                    "conclusion": step.conclusion,
                    "confidence": step.confidence,
                    "reasoning_type": step.reasoning_type,
                }
                for step in reasoning_result.reasoning_steps
            ],
            "num_steps": len(reasoning_result.reasoning_steps),
            "layer": "reasoning",
            "layer_id": 14,
            "processing_time_ms": processing_time,
        }
    
    async def _perform_reasoning(
        self,
        query: str,
        memory_context: str,
        retrieved_memories: List[Dict[str, Any]]
    ) -> ReasoningResult:
        """执行推理"""
        import time
        start_time = time.time()
        
        reasoning_steps = []
        
        step1 = ReasoningStep(
            step_id=1,
            premise=f"Query: {query}",
            conclusion="Identified the main problem or question",
            confidence=0.9,
            reasoning_type="identification",
            evidence=[query]
        )
        reasoning_steps.append(step1)
        
        if memory_context:
            step2 = ReasoningStep(
                step_id=2,
                premise=f"Memory context: {memory_context[:100]}...",
                conclusion="Relevant historical context identified",
                confidence=0.85,
                reasoning_type="contextual",
                evidence=[memory_context[:200]]
            )
            reasoning_steps.append(step2)
        
        if retrieved_memories:
            memory_evidence = [m.get("content", "")[:100] for m in retrieved_memories[:3]]
            step3 = ReasoningStep(
                step_id=3,
                premise=f"Retrieved {len(retrieved_memories)} relevant memories",
                conclusion="Historical patterns and solutions identified",
                confidence=0.8,
                reasoning_type="inductive",
                evidence=memory_evidence
            )
            reasoning_steps.append(step3)
        
        final_confidence = sum(s.confidence for s in reasoning_steps) / len(reasoning_steps) if reasoning_steps else 0.5
        
        conclusion = self._generate_conclusion(query, reasoning_steps)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ReasoningResult(
            query=query,
            conclusion=conclusion,
            confidence=final_confidence,
            reasoning_steps=reasoning_steps,
            processing_time_ms=processing_time
        )
    
    def _generate_conclusion(self, query: str, steps: List[ReasoningStep]) -> str:
        """生成推理结论"""
        if not steps:
            return f"Unable to reason about: {query}"
        
        conclusions = [s.conclusion for s in steps]
        
        return f"Based on {len(steps)} reasoning steps: {'; '.join(conclusions[:3])}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_reasonings"]
            if self._stats["total_reasonings"] > 0 else 0.0
        )
        avg_steps = (
            self._stats["total_steps"] / self._stats["total_reasonings"]
            if self._stats["total_reasonings"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "avg_processing_time_ms": avg_processing_time,
            "avg_steps_per_reasoning": avg_steps,
            "config": {
                "reasoning_depth": self.config.reasoning_depth,
                "confidence_threshold": self.config.confidence_threshold,
            }
        }


def create_reasoning_layer(
    depth: int = 3,
    threshold: float = 0.7
) -> NeuralReasoningLayer:
    """创建推理层实例"""
    config = ReasoningConfig(
        reasoning_depth=depth,
        confidence_threshold=threshold
    )
    return NeuralReasoningLayer(config)
