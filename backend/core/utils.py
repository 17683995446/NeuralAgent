"""
NeuralAgent 核心工具模块
提供常用的工具函数
"""

import time
import uuid
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

T = TypeVar('T')


def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())


def generate_short_id() -> str:
    """生成短ID"""
    return uuid.uuid4().hex[:12]


def hash_string(s: str) -> str:
    """SHA256哈希字符串"""
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def now_iso() -> str:
    """获取当前ISO时间"""
    return datetime.now().isoformat()


def timestamp_ms() -> int:
    """获取当前毫秒时间戳"""
    return int(time.time() * 1000)


def duration_ms(start_time: float) -> float:
    """计算从start_time到现在的毫秒数"""
    return (time.time() - start_time) * 1000


def serialize_to_json(obj: Any, indent: int = 2) -> str:
    """安全序列化对象为JSON"""
    def default_converter(o):
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        if hasattr(o, '__dict__'):
            return o.__dict__
        return str(o)
    
    return json.dumps(obj, default=default_converter, indent=indent, ensure_ascii=False)


def safe_load_json(s: str) -> Optional[Any]:
    """安全加载JSON"""
    try:
        return json.loads(s)
    except (TypeError, json.JSONDecodeError):
        return None


def ensure_directory(path: str) -> Path:
    """确保目录存在"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


class Timer:
    """简单的计时器"""
    
    def __init__(self):
        self._start_time: Optional[float] = None
        self._laps: list[tuple[str, float]] = []
    
    def start(self):
        """开始计时"""
        self._start_time = time.time()
        return self
    
    def lap(self, label: str = "lap"):
        """记录一个计时段"""
        if self._start_time is None:
            raise RuntimeError("Timer not started")
        
        elapsed = (time.time() - self._start_time) * 1000
        self._laps.append((label, elapsed))
        return elapsed
    
    def stop(self) -> float:
        """停止计时，返回总耗时（毫秒）"""
        if self._start_time is None:
            raise RuntimeError("Timer not started")
        
        total = (time.time() - self._start_time) * 1000
        self._start_time = None
        return total
    
    def reset(self):
        """重置计时器"""
        self._start_time = None
        self._laps.clear()
    
    def get_laps(self) -> list[tuple[str, float]]:
        """获取所有计时段"""
        return self._laps.copy()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        if not self._laps:
            return {}
        
        times = [lap[1] for lap in self._laps]
        return {
            "count": len(times),
            "total": sum(times),
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times)
        }


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
):
    """重试装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                    
                    wait_time = delay * (backoff_factor ** (attempt - 1))
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                    
                    wait_time = delay * (backoff_factor ** (attempt - 1))
                    time.sleep(wait_time)
            
            raise last_exception
        
        # 检测是否是async函数
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def clamp(value: T, min_val: T, max_val: T) -> T:
    """限制值在范围内"""
    return max(min_val, min(value, max_val))


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def format_bytes(num_bytes: int) -> str:
    """格式化字节数为可读格式"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"
