"""
NeuralAgent 请求限流系统
提供基于令牌桶算法的请求限流功能
"""

import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10


@dataclass
class RateLimitResult:
    """限流结果"""
    allowed: bool
    remaining: int
    limit: int
    reset_at: datetime
    retry_after_seconds: Optional[int] = None


class TokenBucket:
    """令牌桶算法实现"""
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        refill_period_seconds: float = 60.0
    ):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period_seconds
        self.last_refill = time.time()
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        
        periods = elapsed / self.refill_period
        tokens_to_add = periods * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """消费令牌"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_tokens(self) -> float:
        """获取当前令牌数"""
        self._refill()
        return self.tokens


class RateLimiter:
    """请求限流器"""
    
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._request_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._window_starts: Dict[str, datetime] = {}
        self._limits: Dict[str, RateLimitConfig] = {}
    
    @staticmethod
    def _get_key(identifier: str, limit_type: str = "default") -> str:
        """生成限流键"""
        return f"{identifier}:{limit_type}"
    
    def set_limit(self, identifier: str, config: RateLimitConfig):
        """设置限流配置"""
        self._limits[identifier] = config
        
        requests_per_minute = config.requests_per_minute
        refill_rate = requests_per_minute / 60.0
        
        self._buckets[f"{identifier}:minute"] = TokenBucket(
            capacity=config.burst_size,
            refill_rate=refill_rate,
            refill_period_seconds=60.0
        )
        
        self._window_starts[f"{identifier}:hour"] = datetime.now()
        self._window_starts[f"{identifier}:day"] = datetime.now()
    
    def check_limit(
        self,
        identifier: str,
        limit_type: str = "default"
    ) -> RateLimitResult:
        """检查限流"""
        key = self._get_key(identifier, limit_type)
        
        config = self._limits.get(identifier, RateLimitConfig())
        
        minute_bucket = self._buckets.get(f"{identifier}:minute")
        if not minute_bucket:
            self.set_limit(identifier, config)
            minute_bucket = self._buckets[f"{identifier}:minute"]
        
        allowed = minute_bucket.consume()
        
        if allowed:
            self._increment_counter(identifier, "minute")
            self._increment_counter(identifier, "hour")
            self._increment_counter(identifier, "day")
        
        remaining_minute = int(minute_bucket.get_tokens())
        reset_at = datetime.now() + timedelta(minutes=1)
        
        if not allowed:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=config.requests_per_minute,
                reset_at=reset_at,
                retry_after_seconds=60
            )
        
        current_hour = self._get_counter(identifier, "hour")
        if current_hour >= config.requests_per_hour:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=config.requests_per_hour,
                reset_at=self._window_starts.get(f"{identifier}:hour", datetime.now()) + timedelta(hours=1),
                retry_after_seconds=3600
            )
        
        current_day = self._get_counter(identifier, "day")
        if current_day >= config.requests_per_day:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=config.requests_per_day,
                reset_at=self._window_starts.get(f"{identifier}:day", datetime.now()) + timedelta(days=1),
                retry_after_seconds=86400
            )
        
        return RateLimitResult(
            allowed=True,
            remaining=config.requests_per_minute - self._get_counter(identifier, "minute"),
            limit=config.requests_per_minute,
            reset_at=reset_at
        )
    
    def _increment_counter(self, identifier: str, period: str):
        """增加计数器"""
        key = f"{identifier}:{period}"
        
        window_start = self._window_starts.get(key)
        if not window_start or self._is_window_expired(window_start, period):
            self._request_counts[identifier][period] = 0
            self._window_starts[key] = datetime.now()
        
        self._request_counts[identifier][period] += 1
    
    def _get_counter(self, identifier: str, period: str) -> int:
        """获取计数器值"""
        window_start = self._window_starts.get(f"{identifier}:{period}")
        if not window_start or self._is_window_expired(window_start, period):
            return 0
        
        return self._request_counts[identifier].get(period, 0)
    
    def _is_window_expired(self, window_start: datetime, period: str) -> bool:
        """检查时间窗口是否过期"""
        now = datetime.now()
        
        if period == "minute":
            return now - window_start > timedelta(minutes=1)
        elif period == "hour":
            return now - window_start > timedelta(hours=1)
        elif period == "day":
            return now - window_start > timedelta(days=1)
        
        return True
    
    def reset_limit(self, identifier: str):
        """重置限流"""
        for period in ["minute", "hour", "day"]:
            key = f"{identifier}:{period}"
            if key in self._request_counts:
                del self._request_counts[identifier][period]
            if key in self._window_starts:
                del self._window_starts[key]
            if key in self._buckets:
                del self._buckets[key]
    
    def get_stats(self, identifier: str) -> Dict:
        """获取限流统计"""
        return {
            "identifier": identifier,
            "minute_requests": self._get_counter(identifier, "minute"),
            "hour_requests": self._get_counter(identifier, "hour"),
            "day_requests": self._get_counter(identifier, "day"),
            "config": self._limits.get(identifier, RateLimitConfig())
        }


class RateLimitMiddleware:
    """限流中间件"""
    
    def __init__(self):
        self._limiter = RateLimiter()
        self._default_config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_size=10
        )
    
    def check_request(
        self,
        identifier: str,
        limit_type: str = "default"
    ) -> RateLimitResult:
        """检查请求是否允许"""
        if identifier not in self._limiter._limits:
            self._limiter.set_limit(identifier, self._default_config)
        
        return self._limiter.check_limit(identifier, limit_type)
    
    async def check_request_async(
        self,
        identifier: str,
        limit_type: str = "default"
    ) -> RateLimitResult:
        """异步检查请求"""
        return self.check_request(identifier, limit_type)
    
    def set_custom_limit(
        self,
        identifier: str,
        requests_per_minute: int,
        requests_per_hour: int,
        requests_per_day: int,
        burst_size: int = 10
    ):
        """设置自定义限流"""
        config = RateLimitConfig(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day,
            burst_size=burst_size
        )
        self._limiter.set_limit(identifier, config)
    
    def get_stats(self, identifier: str) -> Dict:
        """获取统计"""
        return self._limiter.get_stats(identifier)


_global_rate_limiter = None
_global_middleware = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter


def get_rate_limit_middleware() -> RateLimitMiddleware:
    """获取全局限流中间件"""
    global _global_middleware
    if _global_middleware is None:
        _global_middleware = RateLimitMiddleware()
    return _global_middleware
