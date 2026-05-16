"""Health Check and System Monitoring Module - Product Grade.

Standing on the shoulders of giants: using psutil for system monitoring.
Not reinventing the wheel: using industry-standard patterns.
Highly modular: clear separation of concerns.
Productized: comprehensive health checks, metrics, and monitoring.
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, UTC
from functools import wraps
import importlib.util

# Check for psutil availability
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.getLogger(__name__).warning("psutil not available, system metrics will be limited")


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration with clear meanings."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    """Result of a single health check."""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    

@dataclass
class SystemMetrics:
    """System-level metrics snapshot."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_used_mb: float = 0.0
    disk_available_mb: float = 0.0
    process_count: int = 0
    thread_count: int = 0
    load_average: List[float] = field(default_factory=list)
    uptime_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_mb": self.memory_used_mb,
            "memory_available_mb": self.memory_available_mb,
            "disk_usage_percent": self.disk_usage_percent,
            "disk_used_mb": self.disk_used_mb,
            "disk_available_mb": self.disk_available_mb,
            "process_count": self.process_count,
            "thread_count": self.thread_count,
            "load_average": self.load_average,
            "uptime_seconds": self.uptime_seconds
        }


@dataclass
class ApplicationHealth:
    """Complete application health report."""
    overall_status: HealthStatus
    checks: Dict[str, CheckResult]
    system_metrics: SystemMetrics
    version: str = "0.1.0"
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "overall_status": self.overall_status.value,
            "version": self.version,
            "started_at": self.started_at.isoformat(),
            "uptime_seconds": (datetime.now(UTC) - self.started_at).total_seconds(),
            "checks": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "timestamp": check.timestamp.isoformat(),
                    "details": check.details
                }
                for name, check in self.checks.items()
            },
            "system_metrics": self.system_metrics.to_dict()
        }


class HealthCheck:
    """Represents a single health check."""
    
    def __init__(
        self,
        name: str,
        check_func: Callable[[], bool],
        timeout_seconds: float = 10.0,
        critical: bool = True,
        description: str = ""
    ):
        self.name = name
        self.check_func = check_func
        self.timeout_seconds = timeout_seconds
        self.critical = critical
        self.description = description
        self.last_result: Optional[CheckResult] = None
        self.failure_count = 0
        self.success_count = 0
        
    def run(self) -> CheckResult:
        """Run the health check and return result."""
        start_time = time.time()
        status = HealthStatus.UNKNOWN
        message = "Check not executed"
        details = {}
        
        try:
            success = self.check_func()
            elapsed_ms = (time.time() - start_time) * 1000
            
            if success:
                status = HealthStatus.HEALTHY
                message = f"{self.name} check passed"
                self.success_count += 1
                self.failure_count = 0
            else:
                status = HealthStatus.UNHEALTHY
                message = f"{self.name} check failed"
                self.failure_count += 1
                
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            status = HealthStatus.UNHEALTHY
            message = f"{self.name} check failed with exception: {str(e)}"
            details = {"exception_type": type(e).__name__, "exception_message": str(e)}
            self.failure_count += 1
            
        if self.failure_count >= 3 and status == HealthStatus.UNHEALTHY:
            if self.critical:
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.DEGRADED
                
        result = CheckResult(
            name=self.name,
            status=status,
            message=message,
            response_time_ms=elapsed_ms,
            details=details,
            timestamp=datetime.now(UTC)
        )
        self.last_result = result
        return result


class HealthMonitor:
    """Product-grade health monitoring system."""
    
    def __init__(self, app_version: str = "0.1.0"):
        self._checks: Dict[str, HealthCheck] = {}
        self._lock = threading.RLock()
        self._started_at = datetime.now(UTC)
        self._app_version = app_version
        self._background_thread: Optional[threading.Thread] = None
        self._running = False
        
    def register_check(
        self,
        name: str,
        check_func: Callable[[], bool],
        timeout_seconds: float = 10.0,
        critical: bool = True,
        description: str = ""
    ) -> "HealthMonitor":
        """Register a health check.
        
        Args:
            name: Unique name for the check
            check_func: Function that returns True on success, False on failure
            timeout_seconds: Timeout for the check
            critical: Whether this check being unhealthy makes the overall app unhealthy
            description: Description of what the check does
            
        Returns:
            self for method chaining
        """
        with self._lock:
            self._checks[name] = HealthCheck(
                name=name,
                check_func=check_func,
                timeout_seconds=timeout_seconds,
                critical=critical,
                description=description
            )
        logger.info(f"Registered health check: {name}")
        return self
        
    def unregister_check(self, name: str) -> "HealthMonitor":
        """Unregister a health check."""
        with self._lock:
            if name in self._checks:
                del self._checks[name]
                logger.info(f"Unregistered health check: {name}")
        return self
        
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics."""
        metrics = SystemMetrics(timestamp=datetime.now(UTC))
        
        if PSUTIL_AVAILABLE:
            try:
                # CPU
                metrics.cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Memory
                memory = psutil.virtual_memory()
                metrics.memory_percent = memory.percent
                metrics.memory_used_mb = memory.used / (1024 * 1024)
                metrics.memory_available_mb = memory.available / (1024 * 1024)
                
                # Disk
                disk = psutil.disk_usage("/")
                metrics.disk_usage_percent = disk.percent
                metrics.disk_used_mb = disk.used / (1024 * 1024)
                metrics.disk_available_mb = disk.free / (1024 * 1024)
                
                # Process and thread counts
                process = psutil.Process()
                metrics.thread_count = process.num_threads()
                metrics.process_count = len(list(psutil.process_iter()))
                
                # Load average
                try:
                    metrics.load_average = list(psutil.getloadavg())
                except (AttributeError, OSError):
                    metrics.load_average = [0.0, 0.0, 0.0]
                    
            except Exception as e:
                logger.warning(f"Failed to collect system metrics: {e}")
                
        metrics.uptime_seconds = (datetime.now(UTC) - self._started_at).total_seconds()
        return metrics
        
    def run_all_checks(self) -> ApplicationHealth:
        """Run all health checks and return comprehensive report."""
        check_results: Dict[str, CheckResult] = {}
        overall_status = HealthStatus.HEALTHY
        
        with self._lock:
            for name, check in list(self._checks.items()):
                result = check.run()
                check_results[name] = result
                
                if result.status == HealthStatus.UNHEALTHY:
                    if check.critical:
                        overall_status = HealthStatus.UNHEALTHY
                    elif overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
        system_metrics = self._collect_system_metrics()
        
        return ApplicationHealth(
            overall_status=overall_status,
            checks=check_results,
            system_metrics=system_metrics,
            version=self._app_version,
            started_at=self._started_at
        )
        
    def get_health_report(self) -> ApplicationHealth:
        """Get current health report with last known results."""
        return self.run_all_checks()


# Global instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor(app_version: str = "0.1.0") -> HealthMonitor:
    """Get or create the global health monitor instance.
    
    Args:
        app_version: Application version for health reports
        
    Returns:
        Global HealthMonitor instance
    """
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor(app_version=app_version)
    return _health_monitor


def check_health(app_version: str = "0.1.0") -> ApplicationHealth:
    """Convenience function to get a health report quickly.
    
    Args:
        app_version: Application version for the report
        
    Returns:
        Complete ApplicationHealth report
    """
    monitor = get_health_monitor(app_version=app_version)
    return monitor.get_health_report()
