"""Neural Planning Layer - 神经网络规划层

Layer 15 of the NeuralAgent Deep Architecture.

功能：
- 制定执行计划和策略
- 支持层次化规划
- 任务分解和调度
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class PlanningConfig:
    """规划层配置"""
    max_plan_depth: int = 5
    max_subtasks: int = 10
    planning_strategy: str = "hierarchical"  # hierarchical, sequential, parallel
    time_limit_seconds: int = 60


@dataclass
class PlanStep:
    """规划步骤"""
    step_id: int
    action: str
    description: str
    dependencies: List[int] = field(default_factory=list)
    estimated_time: float = 0.0
    priority: int = 1
    status: str = "pending"


@dataclass
class PlanResult:
    """规划结果"""
    plan_id: str
    goal: str
    steps: List[PlanStep]
    total_estimated_time: float
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class NeuralPlanningLayer:
    """神经网络规划层 - Layer 15
    
    制定执行计划和策略。
    """
    
    def __init__(self, config: Optional[PlanningConfig] = None):
        self.config = config or PlanningConfig()
        
        self._stats = {
            "total_plans": 0,
            "total_steps": 0,
            "total_processing_time_ms": 0.0,
            "avg_plan_size": 0.0,
        }
    
    async def forward(
        self,
        input_data: Union[Dict[str, Any], str]
    ) -> Dict[str, Any]:
        """前向传播
        
        Args:
            input_data: 输入数据
            
        Returns:
            包含规划结果的字典
        """
        import time
        import uuid
        start_time = time.time()
        
        if isinstance(input_data, dict):
            reasoning_conclusion = input_data.get("reasoning_output", "")
            reasoning_confidence = input_data.get("reasoning_confidence", 0.5)
            query = input_data.get("query", "")
        else:
            reasoning_conclusion = str(input_data)
            reasoning_confidence = 0.5
            query = ""
        
        plan_result = await self._create_plan(query, reasoning_conclusion, reasoning_confidence)
        
        self._stats["total_plans"] += 1
        self._stats["total_steps"] += len(plan_result.steps)
        
        processing_time = (time.time() - start_time) * 1000
        self._stats["total_processing_time_ms"] += processing_time
        
        return {
            "planning_output": plan_result.goal,
            "plan_id": plan_result.plan_id,
            "plan_steps": [
                {
                    "step_id": step.step_id,
                    "action": step.action,
                    "description": step.description,
                    "dependencies": step.dependencies,
                    "estimated_time": step.estimated_time,
                    "priority": step.priority,
                    "status": step.status,
                }
                for step in plan_result.steps
            ],
            "total_estimated_time": plan_result.total_estimated_time,
            "num_steps": len(plan_result.steps),
            "layer": "planning",
            "layer_id": 15,
            "processing_time_ms": processing_time,
        }
    
    async def _create_plan(
        self,
        query: str,
        reasoning_conclusion: str,
        confidence: float
    ) -> PlanResult:
        """创建执行计划"""
        import time
        import uuid
        start_time = time.time()
        
        plan_id = str(uuid.uuid4())
        
        steps = []
        
        step1 = PlanStep(
            step_id=1,
            action="analyze",
            description=f"Analyze the requirement: {query[:100]}",
            dependencies=[],
            estimated_time=5.0,
            priority=1,
            status="pending"
        )
        steps.append(step1)
        
        step2 = PlanStep(
            step_id=2,
            action="design",
            description="Design solution architecture",
            dependencies=[1],
            estimated_time=10.0,
            priority=2,
            status="pending"
        )
        steps.append(step2)
        
        step3 = PlanStep(
            step_id=3,
            action="implement",
            description="Implement the solution",
            dependencies=[2],
            estimated_time=20.0,
            priority=3,
            status="pending"
        )
        steps.append(step3)
        
        step4 = PlanStep(
            step_id=4,
            action="test",
            description="Test the implementation",
            dependencies=[3],
            estimated_time=10.0,
            priority=4,
            status="pending"
        )
        steps.append(step4)
        
        step5 = PlanStep(
            step_id=5,
            action="validate",
            description="Validate and finalize",
            dependencies=[4],
            estimated_time=5.0,
            priority=5,
            status="pending"
        )
        steps.append(step5)
        
        total_time = sum(s.estimated_time for s in steps)
        
        processing_time = (time.time() - start_time) * 1000
        
        return PlanResult(
            plan_id=plan_id,
            goal=reasoning_conclusion,
            steps=steps,
            total_estimated_time=total_time,
            processing_time_ms=processing_time
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_plans"]
            if self._stats["total_plans"] > 0 else 0.0
        )
        avg_plan_size = (
            self._stats["total_steps"] / self._stats["total_plans"]
            if self._stats["total_plans"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "avg_processing_time_ms": avg_processing_time,
            "avg_plan_size": avg_plan_size,
            "config": {
                "max_plan_depth": self.config.max_plan_depth,
                "planning_strategy": self.config.planning_strategy,
            }
        }


def create_planning_layer(
    max_depth: int = 5,
    strategy: str = "hierarchical"
) -> NeuralPlanningLayer:
    """创建规划层实例"""
    config = PlanningConfig(
        max_plan_depth=max_depth,
        planning_strategy=strategy
    )
    return NeuralPlanningLayer(config)
