"""
Workflow Engine - 智能工作流引擎

创新性功能：
1. 可视化工作流定义（YAML/JSON）
2. 条件分支和动态路由
3. 并行和串行执行
4. 错误恢复和降级
5. 实时监控和日志
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import uuid
import json

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """节点类型"""
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    WAIT = "wait"
    END = "end"


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """工作流节点"""
    id: str
    type: NodeType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None
    retry_count: int = 0
    timeout: Optional[int] = None


@dataclass
class WorkflowEdge:
    """工作流边"""
    source: str
    target: str
    condition: Optional[str] = None


@dataclass
class Workflow:
    """工作流定义"""
    id: str
    name: str
    description: str = ""
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    error_handlers: Dict[str, str] = field(default_factory=dict)
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """获取节点"""
        return next((n for n in self.nodes if n.id == node_id), None)
    
    def get_outgoing_edges(self, node_id: str) -> List[WorkflowEdge]:
        """获取出边"""
        return [e for e in self.edges if e.source == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[WorkflowEdge]:
        """获取入边"""
        return [e for e in self.edges if e.target == node_id]


@dataclass
class ExecutionContext:
    """执行上下文"""
    workflow_id: str
    execution_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    current_node: Optional[str] = None
    node_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)
    
    def add_result(self, node_id: str, result: Any):
        """添加节点结果"""
        self.node_results[node_id] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_error(self, node_id: str, error: Exception):
        """添加错误"""
        self.errors.append({
            "node_id": node_id,
            "error": str(error),
            "type": type(error).__name__,
            "timestamp": datetime.now().isoformat()
        })


@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    context: ExecutionContext
    duration: Optional[float] = None
    error: Optional[str] = None


class WorkflowMonitor:
    """工作流监控器"""
    
    def __init__(self):
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: List[ExecutionResult] = []
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        logger.info("WorkflowMonitor 初始化完成")
    
    def start_monitoring(self, execution_id: str, context: ExecutionContext):
        """开始监控"""
        self.active_executions[execution_id] = context
        logger.debug(f"开始监控执行: {execution_id}")
    
    def stop_monitoring(self, execution_id: str, result: ExecutionResult):
        """停止监控"""
        if execution_id in self.active_executions:
            del self.active_executions[execution_id]
        
        self.execution_history.append(result)
        
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        if result.duration:
            self.metrics[f"{result.workflow_id}_duration"].append(result.duration)
    
    def get_active_count(self) -> int:
        """获取活跃执行数"""
        return len(self.active_executions)
    
    def get_average_duration(self, workflow_id: str) -> Optional[float]:
        """获取平均执行时间"""
        durations = self.metrics.get(f"{workflow_id}_duration", [])
        return sum(durations) / len(durations) if durations else None
    
    def get_success_rate(self, workflow_id: str) -> float:
        """获取成功率"""
        recent = [
            r for r in self.execution_history[-100:]
            if r.workflow_id == workflow_id
        ]
        if not recent:
            return 0.0
        
        success_count = sum(1 for r in recent if r.status == ExecutionStatus.SUCCESS)
        return success_count / len(recent)


class NodeExecutor:
    """节点执行器"""
    
    def __init__(self):
        self.handlers: Dict[NodeType, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认处理器"""
        self.handlers[NodeType.TASK] = self._execute_task
        self.handlers[NodeType.CONDITION] = self._execute_condition
        self.handlers[NodeType.PARALLEL] = self._execute_parallel
        self.handlers[NodeType.LOOP] = self._execute_loop
        self.handlers[NodeType.WAIT] = self._execute_wait
        self.handlers[NodeType.END] = self._execute_end
    
    def register_handler(self, node_type: NodeType, handler: Callable):
        """注册自定义处理器"""
        self.handlers[node_type] = handler
    
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext
    ) -> Any:
        """执行节点"""
        handler = self.handlers.get(node.type)
        if not handler:
            raise ValueError(f"未知的节点类型: {node.type}")
        
        try:
            context.current_node = node.id
            result = await handler(node, context)
            context.add_result(node.id, result)
            return result
        except Exception as e:
            context.add_error(node.id, e)
            if node.retry_count > 0:
                return await self._retry_node(node, context)
            raise
    
    async def _execute_task(self, node: WorkflowNode, context: ExecutionContext) -> Any:
        """执行任务节点"""
        task_func = node.config.get("handler")
        if not task_func:
            await asyncio.sleep(0.1)
            return {"status": "completed", "node": node.id}
        
        if asyncio.iscoroutinefunction(task_func):
            return await task_func(context)
        return task_func(context)
    
    async def _execute_condition(self, node: WorkflowNode, context: ExecutionContext) -> str:
        """执行条件节点"""
        condition_func = node.config.get("condition")
        if not condition_func:
            return node.config.get("default_next", "success")
        
        if asyncio.iscoroutinefunction(condition_func):
            result = await condition_func(context)
        else:
            result = condition_func(context)
        
        return "true" if result else "false"
    
    async def _execute_parallel(self, node: WorkflowNode, context: ExecutionContext) -> List[Any]:
        """执行并行节点"""
        tasks = node.config.get("tasks", [])
        results = await asyncio.gather(
            *[self._execute_task(Task(), context) for Task in tasks],
            return_exceptions=True
        )
        return results
    
    async def _execute_loop(self, node: WorkflowNode, context: ExecutionContext) -> List[Any]:
        """执行循环节点"""
        max_iterations = node.config.get("max_iterations", 10)
        results = []
        
        for i in range(max_iterations):
            should_continue = node.config.get("condition", lambda c: True)(context)
            if not should_continue:
                break
            result = await self._execute_task(node, context)
            results.append(result)
        
        return results
    
    async def _execute_wait(self, node: WorkflowNode, context: ExecutionContext) -> None:
        """执行等待节点"""
        duration = node.config.get("duration", 1)
        await asyncio.sleep(duration)
    
    async def _execute_end(self, node: WorkflowNode, context: ExecutionContext) -> str:
        """执行结束节点"""
        return "workflow_completed"
    
    async def _retry_node(self, node: WorkflowNode, context: ExecutionContext) -> Any:
        """重试节点"""
        for attempt in range(node.retry_count):
            try:
                return await self.execute(node, context)
            except Exception as e:
                if attempt == node.retry_count - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        raise Exception("重试耗尽")


class WorkflowEngine:
    """智能工作流引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.executor = NodeExecutor()
        self.monitor = WorkflowMonitor()
        logger.info("WorkflowEngine 初始化完成")
    
    def add_workflow(self, workflow: Workflow):
        """添加工作流"""
        self.workflows[workflow.id] = workflow
        logger.info(f"添加工作流: {workflow.id} - {workflow.name}")
    
    def add_workflow_from_dict(self, workflow_def: Dict[str, Any]) -> Workflow:
        """从字典添加工作流"""
        nodes = [
            WorkflowNode(
                id=n["id"],
                type=NodeType(n["type"]),
                name=n["name"],
                config=n.get("config", {}),
                condition=n.get("condition"),
                retry_count=n.get("retry_count", 0),
                timeout=n.get("timeout")
            )
            for n in workflow_def.get("nodes", [])
        ]
        
        edges = [
            WorkflowEdge(
                source=e["source"],
                target=e["target"],
                condition=e.get("condition")
            )
            for e in workflow_def.get("edges", [])
        ]
        
        workflow = Workflow(
            id=workflow_def["id"],
            name=workflow_def["name"],
            description=workflow_def.get("description", ""),
            nodes=nodes,
            edges=edges,
            variables=workflow_def.get("variables", {}),
            error_handlers=workflow_def.get("error_handlers", {})
        )
        
        self.add_workflow(workflow)
        return workflow
    
    def add_workflow_from_yaml(self, yaml_content: str) -> Workflow:
        """从 YAML 添加工作流"""
        try:
            import yaml
            workflow_def = yaml.safe_load(yaml_content)
            return self.add_workflow_from_dict(workflow_def)
        except ImportError:
            import json
            workflow_def = json.loads(yaml_content)
            return self.add_workflow_from_dict(workflow_def)
    
    async def execute(self, workflow_id: str, initial_context: Dict[str, Any] = None) -> ExecutionResult:
        """执行工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        execution_id = str(uuid.uuid4())
        context = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            variables={**workflow.variables, **(initial_context or {})}
        )
        
        self.monitor.start_monitoring(execution_id, context)
        start_time = datetime.now()
        
        try:
            await self._execute_workflow(workflow, context)
            status = ExecutionStatus.SUCCESS
            error = None
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            status = ExecutionStatus.FAILED
            error = str(e)
        finally:
            context.completed_at = datetime.now()
            duration = (context.completed_at - start_time).total_seconds()
        
        result = ExecutionResult(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=status,
            context=context,
            duration=duration,
            error=error
        )
        
        self.monitor.stop_monitoring(execution_id, result)
        return result
    
    async def _execute_workflow(self, workflow: Workflow, context: ExecutionContext):
        """执行工作流"""
        start_nodes = [n for n in workflow.nodes if not workflow.get_incoming_edges(n.id)]
        if not start_nodes:
            start_nodes = [workflow.nodes[0]] if workflow.nodes else []
        
        for start_node in start_nodes:
            await self._execute_node_recursive(workflow, start_node.id, context)
    
    async def _execute_node_recursive(
        self,
        workflow: Workflow,
        node_id: str,
        context: ExecutionContext
    ):
        """递归执行节点"""
        node = workflow.get_node(node_id)
        if not node:
            return
        
        if node.type == NodeType.END:
            return
        
        try:
            result = await self.executor.execute(node, context)
            
            outgoing = workflow.get_outgoing_edges(node_id)
            for edge in outgoing:
                should_execute = True
                
                if edge.condition:
                    if edge.condition == "true" and result:
                        should_execute = True
                    elif edge.condition == "false" and not result:
                        should_execute = True
                    elif edge.condition != str(result):
                        should_execute = False
                
                if should_execute:
                    await self._execute_node_recursive(workflow, edge.target, context)
        
        except Exception as e:
            if node.id in workflow.error_handlers:
                error_handler_id = workflow.error_handlers[node.id]
                await self._execute_node_recursive(workflow, error_handler_id, context)
            else:
                raise
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有工作流"""
        return [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "nodes_count": len(w.nodes),
                "edges_count": len(w.edges)
            }
            for w in self.workflows.values()
        ]
    
    def get_monitor_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        return {
            "active_executions": self.monitor.get_active_count(),
            "total_executions": len(self.monitor.execution_history),
            "workflows": self.list_workflows(),
            "success_rates": {
                w.id: self.monitor.get_success_rate(w.id)
                for w in self.workflows.values()
            }
        }


_workflow_engine = None


def get_workflow_engine() -> WorkflowEngine:
    """获取工作流引擎单例"""
    global _workflow_engine
    if not _workflow_engine:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
