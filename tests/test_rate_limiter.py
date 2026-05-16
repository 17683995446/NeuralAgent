"""Tests for Rate Limiter Module - Product Grade."""

import pytest
import time
from backend.core.infrastructure.security.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStrategy,
    RateLimitBackend,
    RateLimitException,
    MemoryRateLimiter,
    get_rate_limiter,
    rate_limit,
    rate_limit_by_ip
)
from backend.core.infrastructure.error_handling.error_codes import ErrorCode, RateLimitError


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = RateLimitConfig()
        assert config.max_requests == 100
        assert config.window_seconds == 60
        assert config.strategy == RateLimitStrategy.SLIDING_WINDOW
        assert config.backend == RateLimitBackend.MEMORY
        assert config.enabled is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = RateLimitConfig(
            max_requests=50,
            window_seconds=30,
            strategy=RateLimitStrategy.FIXED_WINDOW,
            backend=RateLimitBackend.REDIS
        )
        assert config.max_requests == 50
        assert config.window_seconds == 30
        assert config.strategy == RateLimitStrategy.FIXED_WINDOW
        assert config.backend == RateLimitBackend.REDIS

    def test_get_key(self):
        """Test key generation."""
        config = RateLimitConfig(prefix="test:", key_prefix="user:")
        key = config.get_key("user123")
        assert key == "test:user:user123"


class TestRateLimitResult:
    """Tests for RateLimitResult."""

    def test_result_creation(self):
        """Test creating a result."""
        result = RateLimitResult(
            allowed=True,
            remaining=99,
            reset_at=time.time() + 60,
            limit=100,
            identifier="user123"
        )
        assert result.allowed is True
        assert result.remaining == 99
        assert result.limit == 100
        assert result.retry_after is None

    def test_result_denied(self):
        """Test denied result."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=time.time() + 60,
            retry_after=30,
            limit=100,
            identifier="user123"
        )
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = RateLimitResult(
            allowed=True,
            remaining=50,
            reset_at=1234567890.0,
            limit=100,
            identifier="user123"
        )
        result_dict = result.to_dict()
        assert result_dict["allowed"] is True
        assert result_dict["remaining"] == 50
        assert result_dict["limit"] == 100
        assert result_dict["retry_after"] is None


class TestMemoryRateLimiter:
    """Tests for MemoryRateLimiter."""

    def test_limiter_initialization(self):
        """Test initializing limiter."""
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        limiter = MemoryRateLimiter(config)
        assert limiter.config.max_requests == 10

    def test_first_request_allowed(self):
        """Test first request is allowed."""
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        limiter = MemoryRateLimiter(config)

        result = limiter.check("user123")
        assert result.allowed is True
        assert result.remaining == 9

    def test_multiple_requests_within_limit(self):
        """Test multiple requests within limit."""
        config = RateLimitConfig(max_requests=5, window_seconds=60)
        limiter = MemoryRateLimiter(config)

        for i in range(5):
            result = limiter.check(f"user{i}")
            assert result.allowed is True

    def test_request_exceeds_limit(self):
        """Test request exceeds limit."""
        config = RateLimitConfig(max_requests=2, window_seconds=60)
        limiter = MemoryRateLimiter(config)

        # First two requests should be allowed
        result1 = limiter.check("user123")
        assert result1.allowed is True

        result2 = limiter.check("user123")
        assert result2.allowed is True

        # Third request should be denied
        result3 = limiter.check("user123")
        assert result3.allowed is False
        assert result3.retry_after is not None

    def test_different_identifiers_independent(self):
        """Test different identifiers have independent limits."""
        config = RateLimitConfig(max_requests=2, window_seconds=60)
        limiter = MemoryRateLimiter(config)

        # Exhaust limit for user1
        limiter.check("user1")
        limiter.check("user1")
        result = limiter.check("user1")
        assert result.allowed is False

        # user2 should still have limit
        result = limiter.check("user2")
        assert result.allowed is True

    def test_reset(self):
        """Test resetting limit."""
        config = RateLimitConfig(max_requests=2, window_seconds=60)
        limiter = MemoryRateLimiter(config)

        # Exhaust limit
        limiter.check("user123")
        limiter.check("user123")
        result = limiter.check("user123")
        assert result.allowed is False

        # Reset
        limiter.reset("user123")

        # Should be allowed again
        result = limiter.check("user123")
        assert result.allowed is True

    def test_get_current_usage(self):
        """Test getting current usage."""
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        limiter = MemoryRateLimiter(config)

        limiter.check("user123")
        limiter.check("user123")
        limiter.check("user123")

        usage, limit = limiter.get_current_usage("user123")
        assert usage == 3
        assert limit == 10

    def test_disabled_limiter(self):
        """Test disabled limiter allows all requests."""
        config = RateLimitConfig(enabled=False, max_requests=1)
        limiter = MemoryRateLimiter(config)

        for i in range(100):
            result = limiter.check("user123")
            assert result.allowed is True


class TestRateLimiter:
    """Tests for RateLimiter facade."""

    def test_limiter_creation(self):
        """Test creating rate limiter."""
        limiter = RateLimiter()
        assert limiter.config is not None

    def test_limiter_uses_memory_backend(self):
        """Test limiter uses memory backend by default."""
        limiter = RateLimiter()
        assert isinstance(limiter._limiter, MemoryRateLimiter)

    def test_is_allowed(self):
        """Test quick allowed check."""
        config = RateLimitConfig(max_requests=5)
        limiter = RateLimiter(config)

        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True


class TestRateLimitException:
    """Tests for RateLimitException."""

    def test_exception_creation(self):
        """Test creating rate limit exception."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=time.time() + 60,
            retry_after=30,
            limit=100,
            identifier="user123"
        )

        exc = RateLimitException(result)
        assert exc.result == result
        assert exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED

    def test_get_or_raise_allowed(self):
        """Test get_or_raise when allowed."""
        config = RateLimitConfig(max_requests=10)
        limiter = RateLimiter(config)

        # Should not raise
        limiter.get_or_raise("user123")

    def test_get_or_raise_denied(self):
        """Test get_or_raise when denied."""
        config = RateLimitConfig(max_requests=1)
        limiter = RateLimiter(config)

        # First request
        limiter.get_or_raise("user123")

        # Second request should raise
        with pytest.raises(RateLimitException):
            limiter.get_or_raise("user123")


class TestGlobalRateLimiter:
    """Tests for global rate limiter."""

    def test_get_rate_limiter(self):
        """Test getting global rate limiter."""
        limiter = get_rate_limiter()
        assert limiter is not None
        assert isinstance(limiter, RateLimiter)

    def test_get_rate_limiter_with_config(self):
        """Test getting rate limiter with custom config."""
        config = RateLimitConfig(max_requests=50)
        limiter = get_rate_limiter(config)
        assert limiter.config.max_requests == 50


class TestRateLimitDecorator:
    """Tests for rate limit decorator."""

    def test_rate_limit_decorator_allowed(self):
        """Test rate limit decorator allows requests."""
        call_count = 0

        @rate_limit(max_requests=5, window_seconds=60)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        for i in range(5):
            result = test_func()
            assert result == "success"

        assert call_count == 5

    def test_rate_limit_decorator_denied(self):
        """Test rate limit decorator denies after limit."""
        @rate_limit(max_requests=2, window_seconds=60)
        def test_func():
            return "success"

        test_func()
        test_func()

        # Third call should raise
        with pytest.raises(RateLimitException):
            test_func()


class TestRateLimitByIP:
    """Tests for rate limit by IP decorator."""

    def test_rate_limit_by_ip(self):
        """Test rate limit by IP decorator."""
        @rate_limit_by_ip(max_requests=3, window_seconds=60)
        def test_func(request):
            return {"client_ip": request["client_ip"]}

        request1 = {"client_ip": "192.168.1.1"}
        request2 = {"client_ip": "192.168.1.2"}

        # Each IP has separate limit
        for i in range(3):
            result = test_func(request1)
            assert result["client_ip"] == "192.168.1.1"

        for i in range(3):
            result = test_func(request2)
            assert result["client_ip"] == "192.168.1.2"
