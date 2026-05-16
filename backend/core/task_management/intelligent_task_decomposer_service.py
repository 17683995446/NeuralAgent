"""智能任务分解和追踪管理系统
支持自动分解、依赖管理、优先级计算、进度追踪
"""
from typing import List, Dict, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import uuid
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    BLOCKED = "blocked"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""
    P0_CRITICAL = 0  # 阻塞级
    P1_HIGH = 1       # 高优先级
    P2_MEDIUM = 2     # 中优先级
    P3_LOW = 3        # 低优先级


@dataclass
class SubTask:
    """子任务"""
    id: str
    title: str
    description: str = ""
    estimated_hours: float = 1.0
    priority: TaskPriority = TaskPriority.P2_MEDIUM
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    assignee: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_hours: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskMetrics:
    """任务指标"""
    total_tasks: int
    completed_tasks: int
    blocked_tasks: int
    in_progress_tasks: int
    total_estimated_hours: float
    total_actual_hours: float
    progress_percentage: float
    estimated_remaining_hours: float
    average_task_duration: float


class DependencyGraph:
    """依赖图管理"""

    def __init__(self):
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)

    def add_dependency(self, task_id: str, depends_on: str):
        self._adjacency[task_id].add(depends_on)
        self._reverse_adjacency[depends_on].add(task_id)

    def get_dependencies(self, task_id: str) -> Set[str]:
        return self._adjacency.get(task_id, set())

    def get_dependents(self, task_id: str) -> Set[str]:
        return self._reverse_adjacency.get(task_id, set())

    def topological_sort(self) -> List[List[str]]:
        in_degree = defaultdict(int)
        all_nodes = set()

        for node in self._adjacency:
            all_nodes.add(node)
            for dep in self._adjacency[node]:
                all_nodes.add(dep)

        for node in all_nodes:
            for dep in self._adjacency.get(node, []):
                in_degree[node] += 1

        layers = []
        current_layer = [n for n in all_nodes if in_degree[n] == 0]

        while current_layer:
            layers.append(sorted(current_layer))
            next_layer = []

            for node in current_layer:
                for dependent in self._reverse_adjacency.get(node, []):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_layer.append(dependent)

            current_layer = next_layer

        return layers

    def detect_cycles(self) -> List[List[str]]:
        def dfs(node, visited, rec_stack, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, visited, rec_stack, path[:])
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    return path[path.index(neighbor):] + [neighbor]

            rec_stack.remove(node)
            return None

        visited = set()
        cycles = []

        for node in set(self._adjacency.keys()) | set(self._reverse_adjacency.keys()):
            if node not in visited:
                cycle = dfs(node, visited, set(), [])
                if cycle:
                    cycles.append(cycle)

        return cycles


class TaskDecomposer:
    """智能任务分解引擎"""

    def __init__(self):
        self._tasks: Dict[str, SubTask] = {}
        self._dependency_graph = DependencyGraph()
        self._observers: List[Callable] = []

    def register_observer(self, observer: Callable):
        self._observers.append(observer)

    def _notify_observers(self, event: str, task_id: str, data: Dict = None):
        for observer in self._observers:
            try:
                observer(event, task_id, data or {})
            except Exception as e:
                logger.error(f"Observer error: {e}")

    def add_task(
        self,
        title: str,
        description: str = "",
        estimated_hours: float = 1.0,
        priority: TaskPriority = TaskPriority.P2_MEDIUM,
        dependencies: List[str] = None,
        tags: List[str] = None,
        assignee: str = None
    ) -> str:
        task_id = str(uuid.uuid4())[:8]

        task = SubTask(
            id=task_id,
            title=title,
            description=description,
            estimated_hours=estimated_hours,
            priority=priority,
            dependencies=dependencies or [],
            tags=tags or [],
            assignee=assignee
        )

        self._tasks[task_id] = task

        for dep_id in task.dependencies:
            self._dependency_graph.add_dependency(task_id, dep_id)

        self._update_task_status(task_id)
        self._notify_observers("task_added", task_id)

        return task_id

    def add_tasks_batch(self, tasks_data: List[Dict]) -> List[str]:
        task_ids = []

        for task_data in tasks_data:
            priority = task_data.get("priority", TaskPriority.P2_MEDIUM)
            task_id = self.add_task(
                title=task_data["title"],
                description=task_data.get("description", ""),
                estimated_hours=task_data.get("estimated_hours", 1.0),
                priority=priority,
                dependencies=task_data.get("dependencies", []),
                tags=task_data.get("tags", []),
                assignee=task_data.get("assignee")
            )
            task_ids.append(task_id)

        return task_ids

    def _update_task_status(self, task_id: str):
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]

        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return

        dependencies = self._dependency_graph.get_dependencies(task_id)

        if not dependencies:
            if task.status == TaskStatus.BLOCKED:
                task.status = TaskStatus.READY
                self._notify_observers("task_ready", task_id)
        else:
            all_deps_completed = all(
                self._tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in dependencies
                if dep_id in self._tasks
            )

            if all_deps_completed:
                task.status = TaskStatus.READY
                self._notify_observers("task_ready", task_id)
            else:
                task.status = TaskStatus.BLOCKED

    def start_task(self, task_id: str) -> bool:
        if task_id not in self._tasks:
            logger.warning(f"Task not found: {task_id}")
            return False

        task = self._tasks[task_id]

        if task.status == TaskStatus.BLOCKED:
            logger.warning(f"Task {task_id} is blocked by dependencies")
            return False

        if task.status != TaskStatus.READY and task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} cannot be started (status: {task.status})")
            return False

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        self._notify_observers("task_started", task_id)

        return True

    def complete_task(self, task_id: str, actual_hours: Optional[float] = None):
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        if actual_hours is not None:
            task.actual_hours = actual_hours
        elif task.started_at:
            elapsed = (datetime.now() - task.started_at).total_seconds() / 3600
            task.actual_hours = elapsed

        dependents = self._dependency_graph.get_dependents(task_id)
        for dep_id in dependents:
            self._update_task_status(dep_id)

        self._notify_observers("task_completed", task_id, {
            "actual_hours": task.actual_hours
        })

    def fail_task(self, task_id: str, error: str = ""):
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]
        task.status = TaskStatus.FAILED
        task.metadata["error"] = error
        self._notify_observers("task_failed", task_id, {"error": error})

    def get_ready_tasks(self) -> List[SubTask]:
        return [
            task for task in self._tasks.values()
            if task.status == TaskStatus.READY
        ]

    def get_next_task(self, assignee: Optional[str] = None) -> Optional[SubTask]:
        ready_tasks = self.get_ready_tasks()

        if not ready_tasks:
            return None

        if assignee:
            assigned_tasks = [t for t in ready_tasks if t.assignee == assignee]
            if assigned_tasks:
                return min(assigned_tasks, key=lambda t: (t.priority.value, t.estimated_hours))

        return min(ready_tasks, key=lambda t: (t.priority.value, t.estimated_hours))

    def get_metrics(self) -> TaskMetrics:
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        blocked = sum(1 for t in self._tasks.values() if t.status == TaskStatus.BLOCKED)
        in_progress = sum(1 for t in self._tasks.values() if t.status == TaskStatus.IN_PROGRESS)

        total_estimated = sum(t.estimated_hours for t in self._tasks.values())
        total_actual = sum(t.actual_hours or 0 for t in self._tasks.values() if t.actual_hours)

        completed_tasks = [t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]
        avg_duration = (
            sum(t.actual_hours for t in completed_tasks if t.actual_hours) / len(completed_tasks)
            if completed_tasks else 0
        )

        remaining = total_estimated - total_actual

        progress = (completed / total * 100) if total > 0 else 0

        return TaskMetrics(
            total_tasks=total,
            completed_tasks=completed,
            blocked_tasks=blocked,
            in_progress_tasks=in_progress,
            total_estimated_hours=total_estimated,
            total_actual_hours=total_actual,
            progress_percentage=progress,
            estimated_remaining_hours=remaining,
            average_task_duration=avg_duration
        )

    def get_execution_plan(self) -> List[List[SubTask]]:
        layers = self._dependency_graph.topological_sort()
        result = []

        for layer_ids in layers:
            layer_tasks = [
                self._tasks[tid] for tid in layer_ids
                if tid in self._tasks
            ]
            if layer_tasks:
                result.append(layer_tasks)

        return result

    def get_critical_path(self) -> List[str]:
        remaining = {
            tid: task for tid, task in self._tasks.items()
            if task.status != TaskStatus.COMPLETED
        }

        def longest_path(task_id: str, memo: Dict) -> tuple:
            if task_id in memo:
                return memo[task_id]

            deps = self._dependency_graph.get_dependencies(task_id)
            uncompleted_deps = [d for d in deps if d in remaining]

            if not uncompleted_deps:
                task = self._tasks[task_id]
                return ([task_id], task.estimated_hours)

            max_path = ([], 0)
            for dep in uncompleted_deps:
                path, duration = longest_path(dep, memo)
                if duration > max_path[1]:
                    max_path = (path, duration)

            task = self._tasks[task_id]
            final_path = max_path[0] + [task_id]
            final_duration = max_path[1] + task.estimated_hours

            memo[task_id] = (final_path, final_duration)
            return (final_path, final_duration)

        memo = {}
        all_paths = []

        for task_id in remaining:
            path, duration = longest_path(task_id, memo)
            if path:
                all_paths.append((path, duration))

        if not all_paths:
            return []

        critical = max(all_paths, key=lambda x: x[1])
        return critical[0]

    def get_task(self, task_id: str) -> Optional[SubTask]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[SubTask]:
        return list(self._tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> List[SubTask]:
        return [t for t in self._tasks.values() if t.status == status]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[SubTask]:
        return [t for t in self._tasks.values() if t.priority == priority]

    def get_tasks_by_tag(self, tag: str) -> List[SubTask]:
        return [t for t in self._tasks.values() if tag in t.tags]

    def generate_report(self) -> Dict[str, Any]:
        metrics = self.get_metrics()
        execution_plan = self.get_execution_plan()
        critical_path = self.get_critical_path()

        report = {
            "generated_at": datetime.now().isoformat(),
            "metrics": {
                "total_tasks": metrics.total_tasks,
                "completed": metrics.completed_tasks,
                "blocked": metrics.blocked_tasks,
                "in_progress": metrics.in_progress_tasks,
                "progress_percentage": f"{metrics.progress_percentage:.1f}%",
                "total_estimated_hours": f"{metrics.total_estimated_hours:.1f}h",
                "total_actual_hours": f"{metrics.total_actual_hours:.1f}h",
                "remaining_hours": f"{metrics.estimated_remaining_hours:.1f}h",
                "average_task_duration": f"{metrics.average_task_duration:.1f}h"
            },
            "critical_path": critical_path,
            "execution_plan": [
                [t.title for t in layer]
                for layer in execution_plan
            ],
            "blocked_tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "dependencies": t.dependencies
                }
                for t in self.get_tasks_by_status(TaskStatus.BLOCKED)
            ],
            "ready_tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "priority": t.priority.name,
                    "estimated_hours": t.estimated_hours
                }
                for t in self.get_ready_tasks()
            ]
        }

        return report

    def validate(self) -> Dict[str, Any]:
        cycles = self._dependency_graph.detect_cycles()
        missing_deps = []

        for task in self._tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in self._tasks:
                    missing_deps.append({
                        "task_id": task.id,
                        "missing_dependency": dep_id
                    })

        return {
            "valid": len(cycles) == 0 and len(missing_deps) == 0,
            "cycles": cycles,
            "missing_dependencies": missing_deps
        }


class TaskProgressVisualizer:
    """任务进度可视化"""

    @staticmethod
    def ascii_progress_bar(metrics: TaskMetrics, width: int = 50) -> str:
        filled = int(width * metrics.progress_percentage / 100)
        bar = "█" * filled + "░" * (width - filled)

        return (
            f"Progress: [{bar}] {metrics.progress_percentage:.1f}%\n"
            f"Completed: {metrics.completed_tasks}/{metrics.total_tasks} tasks\n"
            f"Blocked: {metrics.blocked_tasks} | In Progress: {metrics.in_progress_tasks}\n"
            f"Estimated: {metrics.total_estimated_hours:.1f}h | "
            f"Remaining: {metrics.estimated_remaining_hours:.1f}h"
        )

    @staticmethod
    def generate_gantt_chart(tasks: List[SubTask]) -> str:
        lines = ["Gantt Chart:", "-" * 80]

        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        pending = [t for t in tasks if t.status in (TaskStatus.READY, TaskStatus.PENDING)]

        for task in completed:
            status_icon = "✓"
            lines.append(f"[{status_icon}] {task.title:<40} [{task.priority.name}]")

        for task in in_progress:
            status_icon = "→"
            lines.append(f"[{status_icon}] {task.title:<40} [{task.priority.name}]")

        for task in pending:
            status_icon = "○"
            lines.append(f"[{status_icon}] {task.title:<40} [{task.priority.name}]")

        return "\n".join(lines)


def create_sample_project() -> TaskDecomposer:
    """创建示例项目"""
    decomposer = TaskDecomposer()

    task_ids = decomposer.add_tasks_batch([
        {
            "title": "需求分析",
            "estimated_hours": 2.0,
            "priority": TaskPriority.P0_CRITICAL,
            "tags": ["planning"]
        },
        {
            "title": "系统设计",
            "estimated_hours": 4.0,
            "priority": TaskPriority.P0_CRITICAL,
            "dependencies": [],
            "tags": ["design"]
        },
        {
            "title": "数据库设计",
            "estimated_hours": 3.0,
            "priority": TaskPriority.P1_HIGH,
            "dependencies": [],
            "tags": ["design", "database"]
        },
        {
            "title": "API开发",
            "estimated_hours": 8.0,
            "priority": TaskPriority.P1_HIGH,
            "dependencies": [],
            "tags": ["backend"]
        },
        {
            "title": "前端开发",
            "estimated_hours": 6.0,
            "priority": TaskPriority.P1_HIGH,
            "dependencies": [],
            "tags": ["frontend"]
        },
        {
            "title": "单元测试",
            "estimated_hours": 4.0,
            "priority": TaskPriority.P2_MEDIUM,
            "dependencies": [],
            "tags": ["testing"]
        },
        {
            "title": "集成测试",
            "estimated_hours": 3.0,
            "priority": TaskPriority.P2_MEDIUM,
            "dependencies": [],
            "tags": ["testing"]
        },
        {
            "title": "部署上线",
            "estimated_hours": 2.0,
            "priority": TaskPriority.P1_HIGH,
            "dependencies": [],
            "tags": ["deployment"]
        }
    ])

    decomposer._tasks[task_ids[1]].dependencies = [task_ids[0]]
    decomposer._tasks[task_ids[2]].dependencies = [task_ids[0]]
    decomposer._tasks[task_ids[3]].dependencies = [task_ids[1], task_ids[2]]
    decomposer._tasks[task_ids[4]].dependencies = [task_ids[1]]
    decomposer._tasks[task_ids[5]].dependencies = [task_ids[3], task_ids[4]]
    decomposer._tasks[task_ids[6]].dependencies = [task_ids[5]]
    decomposer._tasks[task_ids[7]].dependencies = [task_ids[6]]

    for task_id in task_ids:
        decomposer._update_task_status(task_id)

    return decomposer

