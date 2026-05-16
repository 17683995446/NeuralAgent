"""Test suite for enhanced system features.

This module contains comprehensive tests for:
- Configuration hot reload
- Authentication and authorization
- Metrics collection
- Parallel processor improvements
- Vector store error handling
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.core.config_manager import (
    ConfigManager,
    ConfigSchema,
    ConfigWatcher,
    HotReloadConfig,
    get_config_manager
)

from backend.core.auth import (
    AuthManager,
    UserRole,
    Permission,
    ROLE_PERMISSIONS,
    init_auth_manager,
    create_test_token
)

from backend.core.metrics import (
    MetricsCollector,
    AlertRule,
    MetricStats,
    get_metrics_collector
)

from backend.core.parallel_processor import (
    ParallelProcessor,
    ProcessorConfig,
    RetryConfig,
    TaskResult,
    TaskRegistry,
    ThreadSafeCounter
)

from backend.core.vector_store import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    RetryConfig as VectorRetryConfig,
    HealthStatus
)


class TestConfigManagerHotReload:
    """Test cases for ConfigManager hot reload functionality."""

    def test_config_watcher_creation(self):
        """Test creating a config watcher."""
        callback = MagicMock()
        watcher = ConfigWatcher(
            key="test.key",
            callback=callback,
            previous_value="old_value"
        )
        
        assert watcher.key == "test.key"
        assert watcher.callback == callback
        assert watcher.previous_value == "old_value"
        assert watcher.enabled is True

    def test_config_manager_watcher_notifications(self):
        """Test watcher notification on config change."""
        config = ConfigManager()
        callback = MagicMock()
        
        config.add_watcher("test.key", callback)
        config.set_with_notify("test.key", "new_value")
        
        callback.assert_called_once_with("test.key", "old_value", "new_value")

    def test_hot_reload_config(self):
        """Test hot reload configuration."""
        config = HotReloadConfig()
        assert config.enabled is True
        assert config.check_interval_seconds == 30
        assert config.auto_reload is True
        assert config.debounce_seconds == 1.0

    def test_config_change_history(self):
        """Test configuration change history tracking."""
        config = ConfigManager()
        config.set("key1", "value1")
        config.set("key2", "value2")
        
        history = config.get_change_history()
        assert len(history) >= 2

    def test_config_manager_singleton(self):
        """Test ConfigManager singleton pattern."""
        cm1 = get_config_manager()
        cm2 = get_config_manager()
        
        assert cm1 is cm2

    def test_config_validation(self):
        """Test configuration validation."""
        config = ConfigManager()
        
        config.add_schema(ConfigSchema(
            name="test.required",
            value_type=str,
            required=True
        ))
        
        errors = config.validate_all()
        assert any("test.required" in e for e in errors)

    def test_config_watcher_disable_enable(self):
        """Test disabling and re-enabling watchers."""
        config = ConfigManager()
        callback = MagicMock()
        
        watcher = config.add_watcher("test.key", callback)
        watcher.enabled = False
        
        config.set_with_notify("test.key", "new_value")
        callback.assert_not_called()


class TestAuthentication:
    """Test cases for authentication and authorization."""

    def test_auth_manager_initialization(self):
        """Test AuthManager initialization."""
        auth = init_auth_manager(secret_key="test-secret-key")
        assert auth.secret_key == "test-secret-key"
        assert auth.algorithm == "HS256"

    def test_token_creation_and_verification(self):
        """Test token creation and verification."""
        auth = init_auth_manager(secret_key="test-secret-key")
        
        data = {
            "sub": "user123",
            "username": "testuser",
            "role": UserRole.USER,
            "email": "test@example.com"
        }
        
        token = auth.create_access_token(data)
        payload = auth.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"

    def test_token_expiration(self):
        """Test token expiration handling."""
        auth = init_auth_manager(
            secret_key="test-secret-key",
            access_token_expire_minutes=-1  # Already expired
        )
        
        data = {"sub": "user123", "username": "test"}
        token = auth.create_access_token(data)
        
        time.sleep(0.1)
        payload = auth.verify_token(token)
        
        assert payload is None

    def test_permission_checking(self):
        """Test permission checking."""
        auth = AuthManager(secret_key="test")
        
        assert auth.has_permission(UserRole.ADMIN, Permission.ADMIN_OPERATIONS) is True
        assert auth.has_permission(UserRole.USER, Permission.CREATE_TASK) is True
        assert auth.has_permission(UserRole.GUEST, Permission.DELETE_TASK) is False

    def test_role_permissions_mapping(self):
        """Test role permissions mapping."""
        assert Permission.CREATE_TASK in ROLE_PERMISSIONS[UserRole.USER]
        assert Permission.ADMIN_OPERATIONS not in ROLE_PERMISSIONS[UserRole.GUEST]
        assert Permission.READ_TASK in ROLE_PERMISSIONS[UserRole.GUEST]

    def test_create_test_token(self):
        """Test test token creation."""
        token = create_test_token(
            user_id="test_user",
            username="test",
            role=UserRole.USER
        )
        
        assert token is not None
        assert isinstance(token, str)


class TestMetricsCollector:
    """Test cases for MetricsCollector."""

    def test_counter_increment(self):
        """Test counter increment."""
        metrics = MetricsCollector()
        
        metrics.increment("test.counter")
        assert metrics.get_counter("test.counter") == 1
        
        metrics.increment("test.counter", 5)
        assert metrics.get_counter("test.counter") == 6

    def test_gauge_set(self):
        """Test gauge value setting."""
        metrics = MetricsCollector()
        
        metrics.gauge("test.gauge", 100.5)
        assert metrics.get_gauge("test.gauge") == 100.5
        
        metrics.gauge("test.gauge", 200.0)
        assert metrics.get_gauge("test.gauge") == 200.0

    def test_timing_recording(self):
        """Test timing recording."""
        metrics = MetricsCollector()
        
        metrics.timing("test.operation", 1.5)
        metrics.timing("test.operation", 2.0)
        
        stats = metrics.get_stats("test.operation")
        assert stats is not None
        assert stats.count == 2
        assert stats.avg == 1.75
        assert stats.min == 1.5
        assert stats.max == 2.0

    def test_metric_stats(self):
        """Test MetricStats dataclass."""
        stats = MetricStats(
            name="test",
            count=10,
            sum=100.0,
            avg=10.0,
            min=5.0,
            max=15.0,
            latest=12.0,
            tags={"env": "test"}
        )
        
        assert stats.count == 10
        assert stats.avg == 10.0

    def test_alert_rule_creation(self):
        """Test alert rule creation."""
        rule = AlertRule(
            name="test_alert",
            metric_name="test.metric",
            condition=lambda x: x > 10,
            severity="warning",
            message="Value exceeded threshold"
        )
        
        assert rule.name == "test_alert"
        assert rule.severity == "warning"

    def test_global_metrics_collector(self):
        """Test global metrics collector singleton."""
        m1 = get_metrics_collector()
        m2 = get_metrics_collector()
        
        assert m1 is m2


class TestParallelProcessor:
    """Test cases for enhanced ParallelProcessor."""

    def test_processor_config(self):
        """Test ProcessorConfig."""
        config = ProcessorConfig(
            max_workers=5,
            max_queue_size=100,
            task_timeout=60.0
        )
        
        assert config.max_workers == 5
        assert config.max_queue_size == 100
        assert config.task_timeout == 60.0

    def test_thread_safe_counter(self):
        """Test ThreadSafeCounter."""
        counter = ThreadSafeCounter(initial_value=10)
        
        assert counter.get() == 10
        assert counter.increment() == 11
        assert counter.decrement() == 10
        counter.set(20)
        assert counter.get() == 20

    def test_task_registry(self):
        """Test TaskRegistry."""
        registry = TaskRegistry()
        
        from backend.core.parallel_processor import TaskInfo
        
        task = TaskInfo(
            task_id="task1",
            priority=1,
            status="pending",
            created_at=time.time()
        )
        
        registry.add("task1", task)
        assert registry.get("task1") is task
        assert len(registry) == 1
        
        registry.remove("task1")
        assert len(registry) == 0

    def test_task_result(self):
        """Test TaskResult dataclass."""
        result = TaskResult(
            task_id="task1",
            success=True,
            result="output",
            execution_time=1.5,
            retry_count=0
        )
        
        assert result.success is True
        assert result.result == "output"
        assert result.execution_time == 1.5

    def test_retry_config(self):
        """Test RetryConfig."""
        retry = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            backoff_factor=3.0,
            max_delay=120.0
        )
        
        assert retry.max_retries == 5
        assert retry.initial_delay == 2.0
        assert retry.backoff_factor == 3.0

    def test_processor_stats_retrieval(self):
        """Test processor statistics retrieval."""
        config = ProcessorConfig(max_workers=2)
        processor = ParallelProcessor(config=config)
        
        stats = processor.get_stats()
        
        assert "total_processed" in stats
        assert "total_failed" in stats
        assert "running_tasks" in stats
        assert stats["config"]["max_workers"] == 2


class TestVectorStoreErrorHandling:
    """Test cases for VectorStore error handling."""

    def test_circuit_breaker_closed_state(self):
        """Test CircuitBreaker in closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_failure_threshold(self):
        """Test CircuitBreaker failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config=config)
        
        def failing_func():
            raise Exception("Test error")
        
        for _ in range(2):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN

    def test_circuit_breaker_half_open_transition(self):
        """Test CircuitBreaker half-open transition."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1
        )
        cb = CircuitBreaker(config=config)
        
        def failing_func():
            raise Exception("Test error")
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        assert cb.state == CircuitState.OPEN
        
        time.sleep(0.2)
        
        try:
            cb.call(lambda: None)
        except Exception:
            pass
        
        assert cb.state == CircuitState.HALF_OPEN

    def test_circuit_breaker_reset(self):
        """Test CircuitBreaker reset."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.failure_count = 10
        
        cb.reset()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_vector_retry_config(self):
        """Test VectorRetryConfig."""
        retry = VectorRetryConfig(
            max_retries=3,
            initial_delay=0.5,
            backoff_factor=2.0,
            max_delay=10.0
        )
        
        assert retry.max_retries == 3
        assert retry.initial_delay == 0.5

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"


class TestIntegration:
    """Integration tests for the complete system."""

    def test_config_watcher_with_metrics(self):
        """Test config watcher integration with metrics."""
        config = ConfigManager()
        metrics = get_metrics_collector()
        
        def on_change(key, old, new):
            metrics.increment(f"config.changes.{key}")
        
        config.add_watcher("app.feature", on_change)
        config.set_with_notify("app.feature", "enabled")
        
        assert metrics.get_counter("config.changes.app.feature") == 1

    def test_auth_with_config(self):
        """Test authentication with config."""
        config = ConfigManager()
        config.set("jwt.secret", "my-secret-key")
        
        auth = init_auth_manager(secret_key=config.get("jwt.secret"))
        
        token = auth.create_access_token({
            "sub": "user1",
            "username": "testuser",
            "role": UserRole.USER
        })
        
        payload = auth.verify_token(token)
        assert payload["sub"] == "user1"

    def test_metrics_with_parallel_processor(self):
        """Test metrics integration with parallel processor."""
        metrics = get_metrics_collector()
        config = ProcessorConfig(max_workers=2)
        processor = ParallelProcessor(config=config)
        
        def sample_processor(item):
            metrics.increment("test.items.processed")
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = processor.process_items(items, sample_processor)
        
        assert len(results) == 5
        assert metrics.get_counter("test.items.processed") == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
