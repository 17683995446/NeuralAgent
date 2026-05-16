"""
并行处理引擎 - 支持线程池、优先级队列、任务取消、重试机制
增强线程安全性和资源管理
"""
from typing import List, Dict, Any, Optional, Callable, Generic, TypeVar
from functools import partial
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, Future, TimeoutError
from dataclasses import dataclass, field
from queue import PriorityQueue, Empty, Queue
from threading import Event, Lock, RLock, Semaphore
import logging
import time
import uuid
import threading
import atexit

logger = logging.getLogger(__name__)

# Ray支持（可选）
try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    logger.warning("Ray not available, will use thread pool only")

T = TypeVar('T')


@dataclass
class ProcessingStats:
    """处理统计"""
    total: int
    processed: int
    failed: int
    execution_time: float
    items_per_second: float
    avg_task_time: float = 0.0
    max_task_time: float = 0.0


@dataclass(order=True)
class PrioritizedItem(Generic[T]):
    """优先级队列项"""
    priority: int
    item: Any = field(compare=False)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time, compare=False)


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    retry_count: int = 0


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    retry_on_timeout: bool = True


@dataclass
class ProcessorConfig:
    """处理器配置"""
    max_workers: int = 10
    max_queue_size: int = 1000
    task_timeout: float = 300.0  # 任务超时时间（秒）
    shutdown_timeout: float = 30.0  # 关闭超时时间（秒）
    enable_metrics: bool = True
    enable_progress: bool = True


class ThreadSafeCounter:
    """线程安全的计数器"""
    
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = Lock()
    
    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value
    
    def decrement(self) -> int:
        with self._lock:
            self._value -= 1
            return self._value
    
    def get(self) -> int:
        with self._lock:
            return self._value
    
    def set(self, value: int):
        with self._lock:
            self._value = value


class TaskRegistry:
    """线程安全的任务注册表"""
    
    def __init__(self):
        self._tasks: Dict[str, 'TaskInfo'] = {}
        self._lock = RLock()
    
    def add(self, task_id: str, task_info: 'TaskInfo'):
        with self._lock:
            self._tasks[task_id] = task_info
    
    def get(self, task_id: str) -> Optional['TaskInfo']:
        with self._lock:
            return self._tasks.get(task_id)
    
    def remove(self, task_id: str):
        with self._lock:
            self._tasks.pop(task_id, None)
    
    def get_all(self) -> List['TaskInfo']:
        with self._lock:
            return list(self._tasks.values())
    
    def clear(self):
        with self._lock:
            self._tasks.clear()
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._tasks)


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    priority: int
    status: str  # pending, running, completed, failed, cancelled
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    error: Optional[str] = None


class ParallelProcessor:
    """并行处理引擎 - 支持任务取消、优先级、重试等高级功能
    
    增强线程安全性：
    - 使用RLock保护共享状态
    - 任务超时控制
    - 资源限制（信号量）
    - 优雅关闭机制
    - 任务状态跟踪
    """
    
    def __init__(
        self,
        config: Optional[ProcessorConfig] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        """初始化并行处理器
        
        Args:
            config: 处理器配置
            retry_config: 重试配置
        """
        self.config = config or ProcessorConfig()
        self.retry_config = retry_config or RetryConfig()
        
        # 线程安全的数据结构
        self._task_registry = TaskRegistry()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._shutdown_event = Event()
        self._main_lock = RLock()
        
        # 资源限制
        self._semaphore = Semaphore(self.config.max_workers)
        self._queue_semaphore = Semaphore(self.config.max_queue_size)
        
        # 统计信息
        self._stats_lock = Lock()
        self._total_processed = ThreadSafeCounter(0)
        self._total_failed = ThreadSafeCounter(0)
        self._total_cancelled = ThreadSafeCounter(0)
        self._task_times: List[float] = []
        self._max_task_time = 0.0
        
        # 注册关闭钩子
        atexit.register(self._cleanup)
        
        logger.info(f"ParallelProcessor initialized with config: max_workers={self.config.max_workers}")
    
    def _ensure_executor(self):
        """确保执行器已创建"""
        if self._executor is None:
            with self._main_lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(
                        max_workers=self.config.max_workers,
                        thread_name_prefix="ParallelProcessor"
                    )
    
    def process_items(
        self,
        items: List[Any],
        processor: Callable,
        *args,
        priorities: Optional[List[int]] = None,
        **kwargs
    ) -> List[TaskResult]:
        """并行处理列表项（带优先级）
        
        Args:
            items: 要处理的项列表
            processor: 处理函数
            priorities: 优先级列表（数字越小优先级越高）
            *args: 额外参数
            **kwargs: 额外关键字参数
            
        Returns:
            TaskResult列表
        """
        if not items:
            return []
        
        if self._shutdown_event.is_set():
            logger.warning("Processor is shutting down, rejecting new tasks")
            return []
        
        # 如果没有提供优先级，默认都为100
        if not priorities:
            priorities = [100] * len(items)
        
        # 确保有足够的队列空间
        if len(items) > self.config.max_queue_size:
            logger.warning(f"Items ({len(items)}) exceed queue size ({self.config.max_queue_size}), truncating")
            items = items[:self.config.max_queue_size]
            priorities = priorities[:self.config.max_queue_size]
        
        self._ensure_executor()
        start_time = time.time()
        results = []
        
        # 创建优先级任务队列
        task_queue = PriorityQueue()
        for item, priority in zip(items, priorities):
            task_id = str(uuid.uuid4())
            task_info = TaskInfo(
                task_id=task_id,
                priority=priority,
                status="pending",
                created_at=time.time()
            )
            self._task_registry.add(task_id, task_info)
            task_queue.put(PrioritizedItem(
                priority=priority,
                item=item,
                task_id=task_id
            ))
        
        # 提交任务到线程池
        futures: Dict[Future, str] = {}
        
        while not task_queue.empty():
            try:
                prioritized_item = task_queue.get_nowait()
                task_id = prioritized_item.task_id
                
                future = self._executor.submit(
                    self._execute_task,
                    task_id,
                    processor,
                    prioritized_item.item,
                    *args,
                    **kwargs
                )
                futures[task_id] = future
                
            except Empty:
                break
            except Exception as e:
                logger.error(f"Failed to submit task: {e}")
                break
        
        # 收集结果
        for task_id, future in futures.items():
            try:
                result = future.result(timeout=self.config.task_timeout)
                results.append(result)
            except TimeoutError:
                logger.error(f"Task {task_id} timed out")
                task_info = self._task_registry.get(task_id)
                if task_info:
                    task_info.status = "failed"
                    task_info.error = "Task timeout"
                results.append(TaskResult(
                    task_id=task_id,
                    success=False,
                    error=TimeoutError("Task execution timeout"),
                    execution_time=self.config.task_timeout
                ))
                self._total_failed.increment()
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                results.append(TaskResult(
                    task_id=task_id,
                    success=False,
                    error=e
                ))
                self._total_failed.increment()
        
        logger.info(f"Processed {len(results)} items in {time.time() - start_time:.2f}s")
        return results
    
    def _execute_task(
        self,
        task_id: str,
        processor: Callable,
        item: Any,
        *args,
        **kwargs
    ) -> TaskResult:
        """执行单个任务（带重试）"""
        start_time = time.time()
        task_info = self._task_registry.get(task_id)
        
        if task_info:
            task_info.status = "running"
            task_info.started_at = time.time()
        
        retry_count = 0
        last_error = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            # 检查是否已取消或关闭
            if self._shutdown_event.is_set():
                return TaskResult(
                    task_id=task_id,
                    success=False,
                    error=InterruptedError("Processor shutting down"),
                    execution_time=time.time() - start_time,
                    retry_count=retry_count
                )
            
            if task_info and task_info.status == "cancelled":
                return TaskResult(
                    task_id=task_id,
                    success=False,
                    error=InterruptedError("Task cancelled"),
                    execution_time=time.time() - start_time,
                    retry_count=retry_count
                )
            
            try:
                # 使用信号量限制并发
                with self._semaphore:
                    result = processor(item, *args, **kwargs)
                
                execution_time = time.time() - start_time
                
                if task_info:
                    task_info.status = "completed"
                    task_info.completed_at = time.time()
                
                # 更新统计
                self._update_stats(execution_time)
                self._total_processed.increment()
                
                return TaskResult(
                    task_id=task_id,
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    retry_count=retry_count
                )
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if task_info:
                    task_info.retry_count = retry_count
                
                # 最后一次尝试，不再重试
                if attempt >= self.retry_config.max_retries:
                    logger.error(f"Task {task_id} failed after {attempt+1} attempts: {e}")
                    break
                
                # 计算延迟并重试（指数退避）
                delay = min(
                    self.retry_config.initial_delay * (self.retry_config.backoff_factor ** attempt),
                    self.retry_config.max_delay
                )
                logger.warning(f"Task {task_id} failed (attempt {attempt+1}), retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
        
        # 任务失败
        execution_time = time.time() - start_time
        
        if task_info:
            task_info.status = "failed"
            task_info.completed_at = time.time()
            task_info.error = str(last_error)
        
        self._total_failed.increment()
        
        return TaskResult(
            task_id=task_id,
            success=False,
            error=last_error,
            execution_time=execution_time,
            retry_count=retry_count
        )
    
    def _update_stats(self, execution_time: float):
        """更新统计信息（线程安全）"""
        with self._stats_lock:
            self._task_times.append(execution_time)
            # 保持最近1000个任务的统计
            if len(self._task_times) > 1000:
                self._task_times = self._task_times[-1000:]
            self._max_task_time = max(self._max_task_time, execution_time)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._main_lock:
            task_info = self._task_registry.get(task_id)
            if not task_info:
                return False
            
            if task_info.status in ("completed", "failed", "cancelled"):
                return False
            
            task_info.status = "cancelled"
            self._total_cancelled.increment()
            logger.info(f"Task {task_id} marked as cancelled")
            return True
    
    def cancel_all_tasks(self) -> int:
        """取消所有正在运行的任务"""
        cancelled_count = 0
        for task_info in self._task_registry.get_all():
            if task_info.status == "running":
                task_info.status = "cancelled"
                cancelled_count += 1
        
        if cancelled_count > 0:
            logger.info(f"Cancelled {cancelled_count} tasks")
        
        return cancelled_count
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取正在运行的任务信息"""
        return [
            {
                "task_id": ti.task_id,
                "priority": ti.priority,
                "status": ti.status,
                "created_at": ti.created_at,
                "started_at": ti.started_at,
                "retry_count": ti.retry_count
            }
            for ti in self._task_registry.get_all()
            if ti.status == "running"
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        with self._stats_lock:
            avg_time = sum(self._task_times) / len(self._task_times) if self._task_times else 0.0
        
        return {
            "total_processed": self._total_processed.get(),
            "total_failed": self._total_failed.get(),
            "total_cancelled": self._total_cancelled.get(),
            "running_tasks": sum(1 for ti in self._task_registry.get_all() if ti.status == "running"),
            "pending_tasks": sum(1 for ti in self._task_registry.get_all() if ti.status == "pending"),
            "avg_task_time": avg_time,
            "max_task_time": self._max_task_time,
            "config": {
                "max_workers": self.config.max_workers,
                "max_queue_size": self.config.max_queue_size,
                "task_timeout": self.config.task_timeout
            }
        }
    
    def process_batches(
        self,
        items: List[Any],
        processor: Callable,
        batch_size: int = 100,
        *args,
        **kwargs
    ) -> tuple[ProcessingStats, List[Any]]:
        """批量处理（带进度）
        
        Args:
            items: 要处理的项列表
            processor: 处理函数
            batch_size: 批次大小
            *args: 额外参数
            **kwargs: 额外关键字参数
            
        Returns:
            ProcessingStats + 结果列表
        """
        start_time = time.time()
        total = len(items)
        processed = 0
        failed = 0
        
        all_results = []
        
        for i in range(0, total, batch_size):
            batch = items[i:i + batch_size]
            
            if self.config.enable_progress:
                logger.info(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
            
            batch_results = self.process_items(batch, processor, *args, **kwargs)
            
            for result in batch_results:
                if isinstance(result, TaskResult):
                    if result.success:
                        processed += 1
                        all_results.append(result.result)
                    else:
                        failed += 1
                else:
                    processed += 1
                    all_results.append(result)
            
            elapsed = time.time() - start_time
            items_per_second = processed / elapsed if elapsed > 0 else 0.0
            
            if self.config.enable_progress:
                logger.info(f"  Processed: {processed}/{total} ({items_per_second:.2f}/s)")
        
        elapsed = time.time() - start_time
        items_per_second = processed / elapsed if elapsed > 0 else 0.0
        
        stats = ProcessingStats(
            total=total,
            processed=processed,
            failed=failed,
            execution_time=elapsed,
            items_per_second=items_per_second,
            avg_task_time=elapsed / processed if processed > 0 else 0.0,
            max_task_time=self._max_task_time
        )
        
        return stats, all_results
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None):
        """关闭处理器
        
        Args:
            wait: 是否等待任务完成
            timeout: 等待超时时间
        """
        if self._shutdown_event.is_set():
            return
        
        logger.info("Shutting down ParallelProcessor...")
        self._shutdown_event.set()
        
        if self._executor:
            self._executor.shutdown(wait=wait, cancel_futures=True)
            self._executor = None
        
        self._cleanup()
        logger.info("ParallelProcessor shutdown complete")
    
    def _cleanup(self):
        """清理资源"""
        self._task_registry.clear()
        self._stats_lock = None
        self._main_lock = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.shutdown(wait=True, timeout=self.config.shutdown_timeout)
        return False


class AsyncParallelProcessor:
    """异步并行处理器"""
    
    def __init__(self, max_workers: int = 10):
        """初始化异步处理器"""
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        atexit.register(self.shutdown)
    
    async def process_item(self, item, processor, *args, **kwargs):
        """异步处理单个项"""
        import asyncio
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            partial(processor, *args, **kwargs),
            item
        )
    
    async def process_items(self, items, processor, *args, **kwargs):
        """异步处理多个项"""
        import asyncio
        
        tasks = [
            self.process_item(item, processor, *args, **kwargs)
            for item in items
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def shutdown(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)


# 为了向后兼容
def create_parallel_processor(
    max_workers: int = 10,
    use_ray: bool = False,
    **kwargs
) -> ParallelProcessor:
    """创建并行处理器工厂函数（向后兼容）"""
    config = ProcessorConfig(
        max_workers=max_workers,
        **kwargs
    )
    return ParallelProcessor(config=config)
