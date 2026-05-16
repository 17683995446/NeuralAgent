"""
NeuralAgent - 多Agent协作系统
支持多种协作模式：顺序、并行、混合
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AgentType(Enum):
    """Agent类型"""
    RESEARCHER = "researcher"
    WRITER = "writer"
    REVIEWER = "reviewer"
    CODER = "coder"
    ANALYST = "analyst"
    PLANNER = "planner"
    EXECUTOR = "executor"
    CUSTOM = "custom"


class CollaborationMode(Enum):
    """协作模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    CONSENSUS = "consensus"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentConfig:
    """Agent配置"""
    agent_type: AgentType
    name: str
    role: str
    goals: List[str]
    backstory: Optional[str] = None
    tools: List[Dict[str, Any]] = field(default_factory=list)
    llm_config: Dict[str, Any] = field(default_factory=dict)
    memory_enabled: bool = True


@dataclass
class AgentTask:
    """Agent任务"""
    task_id: str
    description: str
    assigned_agent: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class CollaborationConfig:
    """协作配置"""
    mode: CollaborationMode = CollaborationMode.SEQUENTIAL
    max_concurrent: int = 5
    timeout_seconds: int = 3600
    retry_on_failure: bool = True
    max_retries: int = 3
    result_aggregation: str = "concat"


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.memory: List[Dict[str, Any]] = []
        self.tools = config.tools
    
    @abstractmethod
    async def execute(self, task: AgentTask, context: Dict[str, Any]) -> Any:
        """执行任务"""
        pass
    
    async def think(self, task: AgentTask) -> str:
        """思考过程"""
        return f"Agent {self.config.name} thinking about task: {task.description}"
    
    def add_memory(self, memory: Dict[str, Any]) -> None:
        """添加记忆"""
        self.memory.append({
            **memory,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取记忆"""
        return self.memory[-limit:]


class SimpleAgent(BaseAgent):
    """简单Agent实现"""
    
    async def execute(self, task: AgentTask, context: Dict[str, Any]) -> Any:
        """简单执行"""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        try:
            result = self._process_task(task, context)
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            raise
    
    def _process_task(self, task: AgentTask, context: Dict[str, Any]) -> Any:
        """处理任务"""
        return {
            "agent": self.config.name,
            "task": task.description,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }


class MultiAgentOrchestrator:
    """多Agent协调器"""
    
    def __init__(self, config: Optional[CollaborationConfig] = None):
        self.config = config or CollaborationConfig()
        self.agents: Dict[str, BaseAgent] = {}
        self.tasks: Dict[str, AgentTask] = {}
        self.results: Dict[str, Any] = {}
        self.callback: Optional[Callable] = None
    
    def register_agent(self, agent: BaseAgent) -> "MultiAgentOrchestrator":
        """注册Agent"""
        self.agents[agent.config.name] = agent
        return self
    
    def add_task(self, task: AgentTask) -> "MultiAgentOrchestrator":
        """添加任务"""
        self.tasks[task.task_id] = task
        return self
    
    def set_callback(self, callback: Callable) -> "MultiAgentOrchestrator":
        """设置回调"""
        self.callback = callback
        return self
    
    async def execute(self, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行所有任务"""
        context = initial_context or {}
        
        if self.config.mode == CollaborationMode.SEQUENTIAL:
            return await self._execute_sequential(context)
        elif self.config.mode == CollaborationMode.PARALLEL:
            return await self._execute_parallel(context)
        elif self.config.mode == CollaborationMode.HIERARCHICAL:
            return await self._execute_hierarchical(context)
        else:
            return await self._execute_sequential(context)
    
    async def _execute_sequential(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """顺序执行"""
        sorted_tasks = self._sort_tasks_by_priority()
        
        for task in sorted_tasks:
            agent = self.agents.get(task.assigned_agent)
            if agent:
                result = await agent.execute(task, context)
                self.results[task.task_id] = result
                context[task.task_id] = result
                
                if self.callback:
                    await self.callback(task, result)
        
        return self.results
    
    async def _execute_parallel(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行（简化版）"""
        import asyncio
        
        sorted_tasks = self._sort_tasks_by_priority()
        
        async def run_task(task):
            agent = self.agents.get(task.assigned_agent)
            if agent:
                result = await agent.execute(task, context)
                self.results[task.task_id] = result
                return task.task_id, result
            return task.task_id, None
        
        tasks = [run_task(task) for task in sorted_tasks]
        await asyncio.gather(*tasks[:self.config.max_concurrent])
        
        return self.results
    
    async def _execute_hierarchical(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分层执行（简化版）"""
        return await self._execute_sequential(context)
    
    def _sort_tasks_by_priority(self) -> List[AgentTask]:
        """按优先级排序任务"""
        tasks_list = list(self.tasks.values())
        tasks_list.sort(key=lambda t: (-t.priority, t.task_id))
        return tasks_list
    
    def get_status(self) -> Dict[str, Any]:
        """获取执行状态"""
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        
        return {
            "total": len(self.tasks),
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": len(self.tasks) - completed - failed - in_progress,
            "results": self.results
        }


def create_multi_agent_system(
    agents: List[BaseAgent],
    config: Optional[CollaborationConfig] = None
) -> MultiAgentOrchestrator:
    """创建多Agent系统"""
    orchestrator = MultiAgentOrchestrator(config)
    for agent in agents:
        orchestrator.register_agent(agent)
    return orchestrator
