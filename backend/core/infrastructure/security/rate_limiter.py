"""
Rate Limiting Module - Product Grade

Standing on the shoulders of giants: Using Redis + sliding window algorithm.
Not reinventing the wheel: Following industry standard rate limiting patterns.
Highly modular: Separate limiters, strategies, and backends.
Productized: Comprehensive configuration, monitoring, and graceful degradation.
"""

import logging
import time
from typing import Dict, Optional, Any, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import hashlib
import threading
from collections import defaultdict

from backend.core.infrastructure.error_handling.error_codes import ErrorCode, RateLimitError

logger = logging.getLogger(__name__)

# Redis availability check
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory rate limiter fallback")


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitBackend(Enum):
    """Rate limiting backend."""
    REDIS = "redis"
    MEMORY = "memory"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int = 100
    window_seconds: int = 60
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    backend: RateLimitBackend = RateLimitBackend.MEMORY
    redis_url: str = "redis://localhost:6379/1"
    prefix: str = "ratelimit:"
    key_prefix: str = ""
    enabled: bool = True

    def get_key(self, identifier: str) -> str:
        """Generate rate limit key."""
        return f"{self.prefix}{self.key_prefix}{identifier}"


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: float
    retry_after: Optional[int] = None
    limit: int = 0
    identifier: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "allowed": self.allowed,
            "remaining": self.remaining,
            "reset_at": self.reset_at,
            "retry_after": self.retry_after,
            "limit": self.limit
        }


class RateLimitException(RateLimitError):
    """Rate limit exceeded exception."""

    def __init__(self, result: RateLimitResult, message: Optional[str] = None):
        self.result = result
        super().__init__(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message or f"Rate limit exceeded. Retry after {result.retry_after} seconds",
            details=result.to_dict()
        )


class BaseRateLimiter:
    """Base rate limiter interface."""

    def __init__(self, config: RateLimitConfig):
        self.config = config

    def check(self, identifier: str) -> RateLimitResult:
        """Check if request is allowed."""
        raise NotImplementedError

    def acquire(self, identifier: str) -> RateLimitResult:
        """Acquire a rate limit slot."""
        raise NotImplementedError

    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier."""
        raise NotImplementedError

    def get_current_usage(self, identifier: str) -> Tuple[int, int]:
        """Get current usage and limit."""
        raise NotImplementedError


class RedisRateLimiter(BaseRateLimiter):
    """Redis-based rate limiter using sliding window."""

    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        self._redis_client = None
        if REDIS_AVAILABLE:
            self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self._redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self._redis_client.ping()
            logger.info(f"Redis rate limiter connected: {self.config.redis_url}")
        except Exception as e:
            logger.warning(f"Redis rate limiter connection failed: {e}")
            self._redis_client = None

    def check(self, identifier: str) -> RateLimitResult:
        """Check rate limit using Redis."""
        if not self.config.enabled:
            return RateLimitResult(
                allowed=True,
                remaining=self.config.max_requests,
                reset_at=time.time() + self.config.window_seconds,
                limit=self.config.max_requests,
                identifier=identifier
            )

        if self._redis_client is None:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=time.time() + self.config.window_seconds,
                retry_after=self.config.window_seconds,
                limit=self.config.max_requests,
                identifier=identifier
            )

        key = self.config.get_key(identifier)
        now = time.time()
        window_start = now - self.config.window_seconds

        try:
            pipe = self._redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.config.window_seconds)
            results = pipe.execute()

            current_count = results[1]
            allowed = current_count < self.config.max_requests
            remaining = max(0, self.config.max_requests - current_count - 1)
            reset_at = now + self.config.window_seconds

            if allowed:
                self._redis_client.zrem(key, str(now))
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_at=reset_at,
                    limit=self.config.max_requests,
                    identifier=identifier
                )
            else:
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=self.config.window_seconds,
                    limit=self.config.max_requests,
                    identifier=identifier
                )

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return RateLimitResult(
                allowed=True,
                remaining=self.config.max_requests,
                reset_at=time.time() + self.config.window_seconds,
                limit=self.config.max_requests,
                identifier=identifier
            )

    def acquire(self, identifier: str) -> RateLimitResult:
        """Acquire rate limit slot."""
        return self.check(identifier)

    def reset(self, identifier: str) -> None:
        """Reset rate limit."""
        if self._redis_client:
            key = self.config.get_key(identifier)
            self._redis_client.delete(key)

    def get_current_usage(self, identifier: str) -> Tuple[int, int]:
        """Get current usage."""
        if not self._redis_client:
            return (0, self.config.max_requests)

        key = self.config.get_key(identifier)
        now = time.time()
        window_start = now - self.config.window_seconds

        try:
            self._redis_client.zremrangebyscore(key, 0, window_start)
            count = self._redis_client.zcard(key)
            return (count, self.config.max_requests)
        except Exception:
            return (0, self.config.max_requests)


class MemoryRateLimiter(BaseRateLimiter):
    """In-memory rate limiter (for single-instance deployments)."""

    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        self._storage: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def _cleanup_window(self, identifier: str) -> None:
        """Clean up old entries from window."""
        now = time.time()
        cutoff = now - self.config.window_seconds
        self._storage[identifier] = [
            ts for ts in self._storage[identifier]
            if ts > cutoff
        ]

    def check(self, identifier: str) -> RateLimitResult:
        """Check rate limit using in-memory storage."""
        if not self.config.enabled:
            return RateLimitResult(
                allowed=True,
                remaining=self.config.max_requests,
                reset_at=time.time() + self.config.window_seconds,
                limit=self.config.max_requests,
                identifier=identifier
            )

        with self._lock:
            self._cleanup_window(identifier)
            current_count = len(self._storage[identifier])
            allowed = current_count < self.config.max_requests
            remaining = max(0, self.config.max_requests - current_count)
            reset_at = time.time() + self.config.window_seconds

            if allowed:
                self._storage[identifier].append(time.time())
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining - 1,
                    reset_at=reset_at,
                    limit=self.config.max_requests,
                    identifier=identifier
                )
            else:
                oldest = min(self._storage[identifier])
                retry_after = int(oldest + self.config.window_seconds - time.time())
                retry_after = max(1, retry_after)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                    limit=self.config.max_requests,
                    identifier=identifier
                )

    def acquire(self, identifier: str) -> RateLimitResult:
        """Acquire rate limit slot."""
        return self.check(identifier)

    def reset(self, identifier: str) -> None:
        """Reset rate limit."""
        with self._lock:
            if identifier in self._storage:
                del self._storage[identifier]

    def get_current_usage(self, identifier: str) -> Tuple[int, int]:
        """Get current usage."""
        with self._lock:
            self._cleanup_window(identifier)
            current_count = len(self._storage[identifier])
            return (current_count, self.config.max_requests)


class RateLimiter:
    """Main rate limiter class with facade pattern."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._limiter: BaseRateLimiter = self._create_limiter()

    def _create_limiter(self) -> BaseRateLimiter:
        """Create appropriate limiter backend."""
        if self.config.backend == RateLimitBackend.REDIS and REDIS_AVAILABLE:
            return RedisRateLimiter(self.config)
        return MemoryRateLimiter(self.config)

    def check(self, identifier: str) -> RateLimitResult:
        """Check rate limit."""
        return self._limiter.check(identifier)

    def acquire(self, identifier: str) -> RateLimitResult:
        """Acquire rate limit slot."""
        return self._limiter.acquire(identifier)

    def is_allowed(self, identifier: str) -> bool:
        """Quick check if request is allowed."""
        return self.check(identifier).allowed

    def reset(self, identifier: str) -> None:
        """Reset rate limit."""
        self._limiter.reset(identifier)

    def get_usage(self, identifier: str) -> Tuple[int, int]:
        """Get current usage."""
        return self._limiter.get_current_usage(identifier)

    def get_or_raise(self, identifier: str) -> None:
        """Check and raise exception if rate limited."""
        result = self.check(identifier)
        if not result.allowed:
            raise RateLimitException(result)


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get or create global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None or config is not None:
        _rate_limiter = RateLimiter(config=config)
    return _rate_limiter


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    identifier_func: Optional[Callable[..., str]] = None
):
    """Rate limit decorator.

    Args:
        max_requests: Maximum requests per window
        window_seconds: Window size in seconds
        identifier_func: Function to extract identifier from args/kwargs

    Returns:
        Decorator function
    """
    def get_identifier(*args, **kwargs) -> str:
        """Get identifier from request."""
        if identifier_func:
            return identifier_func(*args, **kwargs)

        # Default: use client IP or user ID
        for arg in args:
            if isinstance(arg, dict):
                if "client_ip" in arg:
                    return arg["client_ip"]
                if "user_id" in arg:
                    return arg["user_id"]

        if "client_ip" in kwargs:
            return kwargs["client_ip"]
        if "user_id" in kwargs:
            return kwargs["user_id"]

        # Fallback: use function name hash
        return hashlib.md5(str(args).encode()).hexdigest()[:8]

    config = RateLimitConfig(
        max_requests=max_requests,
        window_seconds=window_seconds
    )

    def decorator(func: Callable) -> Callable:
        limiter = RateLimiter(config=config)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            identifier = get_identifier(*args, **kwargs)
            limiter.get_or_raise(identifier)
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            identifier = get_identifier(*args, **kwargs)
            limiter.get_or_raise(identifier)
            return await func(*args, **kwargs)

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def rate_limit_by_ip(max_requests: int = 100, window_seconds: int = 60):
    """Rate limit by client IP."""
    def identifier_from_request(*args, **kwargs):
        for arg in args:
            if isinstance(arg, dict) and "client_ip" in arg:
                return f"ip:{arg['client_ip']}"
        if "client_ip" in kwargs:
            return f"ip:{kwargs['client_ip']}"

        for arg in args:
            if hasattr(arg, "client_ip"):
                return f"ip:{arg.client_ip}"
        if hasattr(kwargs.get("request"), "client_ip"):
            return f"ip:{kwargs['request'].client_ip}"

        return "ip:unknown"

    return rate_limit(max_requests, window_seconds, identifier_func=identifier_from_request)


def rate_limit_by_user(user_id_func: Callable[[], str] = None, max_requests: int = 1000, window_seconds: int = 3600):
    """Rate limit by user ID."""
    def identifier_from_user(*args, **kwargs):
        user_id = None

        if user_id_func:
            try:
                user_id = user_id_func()
            except Exception:
                pass

        if not user_id:
            for arg in args:
                if hasattr(arg, "user_id"):
                    user_id = arg.user_id
                    break
            if not user_id and "user_id" in kwargs:
                user_id = kwargs["user_id"]

        if user_id:
            return f"user:{user_id}"
        return "user:anonymous"

    return rate_limit(max_requests, window_seconds, identifier_func=identifier_from_user)


class RateLimitMiddleware:
    """FastAPI rate limiting middleware."""

    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        self.app = app
        self.config = config or RateLimitConfig()
        self._limiter = RateLimiter(self.config)

    def __call__(self, scope, receive, send):
        """ASGI middleware."""
        if scope["type"] != "http":
            return self.app(scope, receive, send)

        async def asgi(receive, send):
            # Get client IP
            client_ip = scope.get("client")
            identifier = f"ip:{client_ip[0] if client_ip else 'unknown'}"

            # Check rate limit
            result = self._limiter.check(identifier)

            if not result.allowed:
                response_headers = [
                    (b"x-ratelimit-limit", str(result.limit).encode()),
                    (b"x-ratelimit-remaining", b"0"),
                    (b"x-ratelimit-reset", str(int(result.reset_at)).encode()),
                    (b"retry-after", str(result.retry_after).encode())
                ]

                await send({
                    "type": "http.response.start",
                    "status": 429,
                    "headers": response_headers
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"error": "Rate limit exceeded"}'
                })
                return

            # Process request
            await self.app(scope, receive, send)

        return asgi(receive, send)


class MultiTierRateLimiter:
    """Multi-tier rate limiter (e.g., per-IP and per-user)."""

    def __init__(self, ip_config: Optional[RateLimitConfig] = None, user_config: Optional[RateLimitConfig] = None):
        self.ip_limiter = RateLimiter(ip_config or RateLimitConfig(
            max_requests=100,
            window_seconds=60,
            key_prefix="ip:"
        ))
        self.user_limiter = RateLimiter(user_config or RateLimitConfig(
            max_requests=1000,
            window_seconds=3600,
            key_prefix="user:"
        ))

    def check(self, identifier: str, user_id: Optional[str] = None) -> RateLimitResult:
        """Check both IP and user rate limits."""
        ip_result = self.ip_limiter.check(f"ip:{identifier}")

        if not ip_result.allowed:
            return ip_result

        if user_id:
            user_result = self.user_limiter.check(f"user:{user_id}")
            if not user_result.allowed:
                return user_result

        return RateLimitResult(
            allowed=True,
            remaining=min(ip_result.remaining, user_result.remaining if user_id else ip_result.remaining),
            reset_at=max(ip_result.reset_at, user_result.reset_at if user_id else ip_result.reset_at),
            limit=ip_result.limit,
            identifier=identifier
        )
