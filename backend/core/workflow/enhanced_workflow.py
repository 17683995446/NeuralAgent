"""
NeuralAgent - Enhanced Workflow Engine v2
高级工作流引擎：重试、超时、事件驱动、回滚
"""
import asyncio
import time
import random
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Dict,
    Any,
    List,
    Optional,
    Callable,
    Awaitable,
    Union,
    Type,
    Tuple
)
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import wraps


class WorkflowStatus(Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"
    ROLLING_BACK = "rolling_back"


class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class RetryStrategy(Enum):
    """重试策略"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_DELAY = "random_delay"


@dataclass
class RetryPolicy:
    """重试策略配置"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    jitter: bool = True


@dataclass
class TimeoutPolicy:
    """超时策略配置"""
    step_timeout: Optional[float] = None
    workflow_timeout: Optional[float] = None
    on_timeout: Optional[Callable[[], Awaitable[None]]] = None


@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str
    func: Callable[..., Awaitable[Any]]
    retry_policy: Optional[RetryPolicy] = None
    timeout_policy: Optional[TimeoutPolicy] = None
    depends_on: List[str] = field(default_factory=list)
    rollback_func: Optional[Callable[..., Awaitable[None]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    attempt_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0


class WorkflowEvent(ABC):
    """工作流事件基类"""
    event_type: str
    timestamp: datetime
    workflow_id: str
    
    def __init__(self, workflow_id: str):
        self.event_type = self.__class__.__name__
        self.timestamp = datetime.now()
        self.workflow_id = workflow_id


class WorkflowStartedEvent(WorkflowEvent):
    """工作流开始事件"""
    pass


class WorkflowCompletedEvent(WorkflowEvent):
    """工作流完成事件"""
    def __init__(self, workflow_id: str, result: Any):
        super().__init__(workflow_id)
        self.result = result


class WorkflowFailedEvent(WorkflowEvent):
    """工作流失败事件"""
    def __init__(self, workflow_id: str, error: Exception):
        super().__init__(workflow_id)
        self.error = error


class StepStartedEvent(WorkflowEvent):
    """步骤开始事件"""
    def __init__(self, workflow_id: str, step_name: str):
        super().__init__(workflow_id)
        self.step_name = step_name


class StepCompletedEvent(WorkflowEvent):
    """步骤完成事件"""
    def __init__(self, workflow_id: str, step_name: str, result: Any):
        super().__init__(workflow_id)
        self.step_name = step_name
        self.result = result


class StepFailedEvent(WorkflowEvent):
    """步骤失败事件"""
    def __init__(self, workflow_id: str, step_name: str, error: Exception):
        super().__init__(workflow_id)
        self.step_name = step_name
        self.error = error


class StepRetryingEvent(WorkflowEvent):
    """步骤重试事件"""
    def __init__(self, workflow_id: str, step_name: str, attempt: int, max_attempts: int):
        super().__init__(workflow_id)
        self.step_name = step_name
        self.attempt = attempt
        self.max_attempts = max_attempts


class WorkflowEventListener(ABC):
    """工作流事件监听器"""
    @abstractmethod
    async def on_event(self, event: WorkflowEvent) -> None:
        pass


class LoggingWorkflowEventListener(WorkflowEventListener):
    """日志事件监听器"""
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
    
    async def on_event(self, event: WorkflowEvent) -> None:
        log_msg = f"[Workflow {event.workflow_id}] {event.event_type}"
        if hasattr(event, 'step_name'):
            log_msg += f" - Step: {event.step_name}"
        if hasattr(event, 'error'):
            log_msg += f" - Error: {event.error}"
        if hasattr(event, 'attempt'):
            log_msg += f" - Attempt: {event.attempt}/{event.max_attempts}"
        self.logger.info(log_msg)


class EnhancedWorkflowEngine:
    """高级工作流引擎"""
    
    def __init__(self, workflow_id: Optional[str] = None):
        self.workflow_id = workflow_id or f"workflow-{int(time.time())}"
        self.steps: Dict[str, WorkflowStep] = {}
        self.step_order: List[str] = []
        self.status: WorkflowStatus = WorkflowStatus.PENDING
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[Exception] = None
        self._event_listeners: List[WorkflowEventListener] = []
        self._default_retry_policy = RetryPolicy()
        self._default_timeout_policy = TimeoutPolicy()
        self._step_results: Dict[str, Any] = {}
        self._started_steps: set = set()
    
    def add_listener(self, listener: WorkflowEventListener) -> "EnhancedWorkflowEngine":
        """添加事件监听器"""
        self._event_listeners.append(listener)
        return self
    
    async def _emit_event(self, event: WorkflowEvent) -> None:
        """发送事件"""
        for listener in self._event_listeners:
            try:
                await listener.on_event(event)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Event listener error: {e}")
    
    def add_step(
        self,
        name: str,
        func: Callable[..., Awaitable[Any]],
        retry_policy: Optional[RetryPolicy] = None,
        timeout_policy: Optional[TimeoutPolicy] = None,
        depends_on: Optional[List[str]] = None,
        rollback_func: Optional[Callable[..., Awaitable[None]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "EnhancedWorkflowEngine":
        """添加工作流步骤"""
        if name in self.steps:
            raise ValueError(f"Step with name '{name}' already exists")
        
        self.steps[name] = WorkflowStep(
            name=name,
            func=func,
            retry_policy=retry_policy or self._default_retry_policy,
            timeout_policy=timeout_policy or self._default_timeout_policy,
            depends_on=depends_on or [],
            rollback_func=rollback_func,
            metadata=metadata or {}
        )
        self.step_order.append(name)
        return self
    
    def set_default_retry_policy(self, policy: RetryPolicy) -> "EnhancedWorkflowEngine":
        """设置默认重试策略"""
        self._default_retry_policy = policy
        return self
    
    def set_default_timeout_policy(self, policy: TimeoutPolicy) -> "EnhancedWorkflowEngine":
        """设置默认超时策略"""
        self._default_timeout_policy = policy
        return self
    
    def _calculate_delay(self, retry_policy: RetryPolicy, attempt: int) -> float:
        """计算重试延迟"""
        if retry_policy.strategy == RetryStrategy.FIXED_DELAY:
            delay = retry_policy.initial_delay
        elif retry_policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = retry_policy.initial_delay * (retry_policy.backoff_factor ** (attempt - 1))
        elif retry_policy.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = retry_policy.initial_delay * attempt
        elif retry_policy.strategy == RetryStrategy.RANDOM_DELAY:
            delay = retry_policy.initial_delay + random.uniform(0, retry_policy.initial_delay)
        else:
            delay = retry_policy.initial_delay
        
        delay = min(delay, retry_policy.max_delay)
        
        if retry_policy.jitter:
            jitter = random.uniform(0.8, 1.2)
            delay = delay * jitter
        
        return delay
    
    async def _execute_step_with_retry(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Any:
        """带重试的执行步骤"""
        retry_policy = step.retry_policy or self._default_retry_policy
        last_exception = None
        
        for attempt in range(1, retry_policy.max_attempts + 1):
            try:
                step.attempt_count = attempt
                
                if attempt > 1:
                    step.status = StepStatus.RETRYING
                    await self._emit_event(
                        StepRetryingEvent(self.workflow_id, step.name, attempt, retry_policy.max_attempts)
                    )
                    delay = self._calculate_delay(retry_policy, attempt)
                    await asyncio.sleep(delay)
                
                step.status = StepStatus.RUNNING
                step.started_at = datetime.now()
                await self._emit_event(StepStartedEvent(self.workflow_id, step.name))
                
                timeout = step.timeout_policy.step_timeout if step.timeout_policy else None
                
                if timeout:
                    result = await asyncio.wait_for(
                        step.func(self._step_results, context),
                        timeout=timeout
                    )
                else:
                    result = await step.func(self._step_results, context)
                
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now()
                step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
                step.result = result
                
                await self._emit_event(StepCompletedEvent(self.workflow_id, step.name, result))
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = e
                step.status = StepStatus.TIMEOUT
                step.error = e
                if attempt == retry_policy.max_attempts:
                    raise
            except Exception as e:
                last_exception = e
                if not isinstance(e, retry_policy.retry_exceptions):
                    raise
                step.error = e
                if attempt == retry_policy.max_attempts:
                    raise
        
        raise last_exception
    
    async def _rollback_completed_steps(self, failed_step: str) -> None:
        """回滚已完成的步骤"""
        self.status = WorkflowStatus.ROLLING_BACK
        
        completed_steps = [
            name for name in self.step_order
            if self.steps[name].status == StepStatus.COMPLETED
            and self.steps[name].rollback_func is not None
        ]
        
        for step_name in reversed(completed_steps):
            step = self.steps[step_name]
            try:
                await step.rollback_func(self._step_results)
                step.status = StepStatus.SKIPPED
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Rollback failed for step {step_name}: {e}")
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """执行工作流"""
        context = context or {}
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now()
        await self._emit_event(WorkflowStartedEvent(self.workflow_id))
        
        try:
            timeout_policy = self._default_timeout_policy
            if timeout_policy.workflow_timeout:
                result = await asyncio.wait_for(
                    self._execute_steps(context),
                    timeout=timeout_policy.workflow_timeout
                )
            else:
                result = await self._execute_steps(context)
            
            self.status = WorkflowStatus.COMPLETED
            self.completed_at = datetime.now()
            self.result = result
            await self._emit_event(WorkflowCompletedEvent(self.workflow_id, result))
            return result
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.completed_at = datetime.now()
            self.error = e
            
            await self._rollback_completed_steps("")
            
            await self._emit_event(WorkflowFailedEvent(self.workflow_id, e))
            raise
    
    async def _execute_steps(self, context: Dict[str, Any]) -> Any:
        """执行所有步骤"""
        for step_name in self.step_order:
            step = self.steps[step_name]
            
            for dep in step.depends_on:
                if self.steps[dep].status != StepStatus.COMPLETED:
                    step.status = StepStatus.SKIPPED
                    continue
            
            result = await self._execute_step_with_retry(step, context)
            self._step_results[step_name] = result
        
        return self._step_results
    
    def get_summary(self) -> Dict[str, Any]:
        """获取工作流执行摘要"""
        duration = None
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds() * 1000
        
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": duration,
            "step_count": len(self.steps),
            "steps": {
                name: {
                    "status": step.status.value,
                    "attempt_count": step.attempt_count,
                    "duration_ms": step.duration_ms,
                    "has_result": step.result is not None,
                    "has_error": step.error is not None
                }
                for name, step in self.steps.items()
            }
        }


def workflow_step(
    name: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    timeout_policy: Optional[TimeoutPolicy] = None,
    depends_on: Optional[List[str]] = None,
    rollback_func: Optional[Callable] = None
):
    """工作流步骤装饰器"""
    def decorator(func):
        func._is_workflow_step = True
        func._step_name = name or func.__name__
        func._retry_policy = retry_policy
        func._timeout_policy = timeout_policy
        func._depends_on = depends_on or []
        func._rollback_func = rollback_func
        return func
    return decorator
