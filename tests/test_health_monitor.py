"""Tests for Health Monitor Module."""

import time
import pytest
from backend.core.infrastructure.observability.health_monitor import (
    HealthStatus,
    CheckResult,
    SystemMetrics,
    ApplicationHealth,
    HealthCheck,
    HealthMonitor,
    get_health_monitor,
    check_health
)


class TestHealthStatus:
    """Tests for HealthStatus enumeration."""
    
    def test_health_status_values(self):
        """Test that health status has expected values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestCheckResult:
    """Tests for CheckResult dataclass."""
    
    def test_check_result_creation(self):
        """Test creating a check result."""
        result = CheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="Test passed",
            response_time_ms=10.5
        )
        assert result.name == "test_check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test passed"
        assert result.response_time_ms == 10.5


class TestSystemMetrics:
    """Tests for SystemMetrics dataclass."""
    
    def test_system_metrics_creation(self):
        """Test creating system metrics."""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=1024.0,
            memory_available_mb=512.0,
            disk_usage_percent=70.0,
            disk_used_mb=2048.0,
            disk_available_mb=1024.0,
            process_count=100,
            thread_count=200,
            load_average=[1.0, 0.5, 0.3],
            uptime_seconds=3600.0
        )
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 60.0
        
    def test_system_metrics_to_dict(self):
        """Test converting system metrics to dictionary."""
        metrics = SystemMetrics()
        result = metrics.to_dict()
        assert "timestamp" in result
        assert "cpu_percent" in result
        assert "memory_percent" in result


class TestApplicationHealth:
    """Tests for ApplicationHealth dataclass."""
    
    def test_application_health_creation(self):
        """Test creating application health report."""
        check = CheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="Test passed"
        )
        health = ApplicationHealth(
            overall_status=HealthStatus.HEALTHY,
            checks={"test_check": check},
            system_metrics=SystemMetrics()
        )
        assert health.overall_status == HealthStatus.HEALTHY
        assert "test_check" in health.checks
        
    def test_application_health_to_dict(self):
        """Test converting application health to dictionary."""
        check = CheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="Test passed"
        )
        health = ApplicationHealth(
            overall_status=HealthStatus.HEALTHY,
            checks={"test_check": check},
            system_metrics=SystemMetrics()
        )
        result = health.to_dict()
        assert "overall_status" in result
        assert "version" in result
        assert "checks" in result


class TestHealthCheck:
    """Tests for HealthCheck class."""
    
    def test_health_check_creation(self):
        """Test creating a health check."""
        check = HealthCheck(
            name="test_check",
            check_func=lambda: True,
            timeout_seconds=10.0,
            critical=True,
            description="Test check"
        )
        assert check.name == "test_check"
        assert check.critical == True
        
    def test_health_check_success(self):
        """Test running a successful health check."""
        check = HealthCheck(
            name="test_check",
            check_func=lambda: True,
            critical=True
        )
        result = check.run()
        assert result.status == HealthStatus.HEALTHY
        assert check.success_count == 1
        
    def test_health_check_failure(self):
        """Test running a failing health check."""
        check = HealthCheck(
            name="test_check",
            check_func=lambda: False,
            critical=True
        )
        result = check.run()
        assert result.status == HealthStatus.UNHEALTHY
        assert check.failure_count == 1
        
    def test_health_check_exception(self):
        """Test health check that raises exception."""
        def failing_check():
            raise ValueError("Test exception")
            
        check = HealthCheck(
            name="test_check",
            check_func=failing_check,
            critical=True
        )
        result = check.run()
        assert result.status == HealthStatus.UNHEALTHY
        assert "exception" in result.message


class TestHealthMonitor:
    """Tests for HealthMonitor class."""
    
    def test_health_monitor_creation(self):
        """Test creating a health monitor."""
        monitor = HealthMonitor(app_version="1.0.0")
        assert monitor._app_version == "1.0.0"
        
    def test_register_check(self):
        """Test registering a health check."""
        monitor = HealthMonitor()
        monitor.register_check(
            name="test_check",
            check_func=lambda: True,
            critical=True
        )
        assert "test_check" in monitor._checks
        
    def test_unregister_check(self):
        """Test unregistering a health check."""
        monitor = HealthMonitor()
        monitor.register_check(
            name="test_check",
            check_func=lambda: True,
            critical=True
        )
        monitor.unregister_check("test_check")
        assert "test_check" not in monitor._checks
        
    def test_run_all_checks(self):
        """Test running all health checks."""
        monitor = HealthMonitor()
        monitor.register_check(
            name="healthy_check",
            check_func=lambda: True,
            critical=True
        )
        monitor.register_check(
            name="failing_check",
            check_func=lambda: False,
            critical=False
        )
        report = monitor.run_all_checks()
        assert report.overall_status == HealthStatus.DEGRADED
        assert "healthy_check" in report.checks
        assert "failing_check" in report.checks
        
    def test_collect_system_metrics(self):
        """Test collecting system metrics (even if psutil not available)."""
        monitor = HealthMonitor()
        metrics = monitor._collect_system_metrics()
        assert metrics is not None
        assert hasattr(metrics, "timestamp")


class TestGlobalFunctions:
    """Tests for global health monitor functions."""
    
    def test_get_health_monitor(self):
        """Test getting global health monitor."""
        monitor = get_health_monitor(app_version="1.0.0")
        assert monitor is not None
        
    def test_check_health(self):
        """Test the check_health convenience function."""
        report = check_health(app_version="1.0.0")
        assert report is not None
        assert isinstance(report, ApplicationHealth)
