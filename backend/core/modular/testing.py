"""
NeuralAgent 完整测试体系

包含：
1. 单元测试 - 单个函数/类
2. 集成测试 - 多模块协作
3. 系统测试 - 完整流程
4. 性能测试 - 基准性能
"""

import pytest
import time
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class TestCategory(Enum):
    """测试分类"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """测试结果"""
    name: str
    category: TestCategory
    status: TestStatus
    duration: float = 0.0
    error: str = ""
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class TestSuite:
    """测试套件"""
    name: str
    tests: List[TestResult]
    
    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.PASSED)
    
    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.FAILED)
    
    @property
    def total(self) -> int:
        return len(self.tests)
    
    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


class ProductTestRunner:
    """产品化测试运行器"""
    
    def __init__(self):
        self.suites: List[TestSuite] = []
        self._start_time: float = 0
    
    def run_unit_tests(self) -> TestSuite:
        """运行单元测试"""
        logger.info("Running unit tests")
        
        tests = [
            self._test_cache_basic(),
            self._test_memory_basic(),
            self._test_config_validation(),
            self._test_structured_logging(),
            self._test_validation_utils(),
        ]
        
        suite = TestSuite(name="Unit Tests", tests=tests)
        self.suites.append(suite)
        return suite
    
    def run_integration_tests(self) -> TestSuite:
        """运行集成测试"""
        logger.info("Running integration tests")
        
        tests = [
            self._test_cache_memory_integration(),
            self._test_agent_workflow_integration(),
            self._test_config_initialization(),
        ]
        
        suite = TestSuite(name="Integration Tests", tests=tests)
        self.suites.append(suite)
        return suite
    
    def run_system_tests(self) -> TestSuite:
        """运行系统测试"""
        logger.info("Running system tests")
        
        tests = [
            self._test_full_agent_workflow(),
            self._test_error_recovery_system(),
        ]
        
        suite = TestSuite(name="System Tests", tests=tests)
        self.suites.append(suite)
        return suite
    
    def run_performance_tests(self) -> TestSuite:
        """运行性能测试"""
        logger.info("Running performance tests")
        
        tests = [
            self._test_cache_performance(),
            self._test_memory_throughput(),
        ]
        
        suite = TestSuite(name="Performance Tests", tests=tests)
        self.suites.append(suite)
        return suite
    
    def run_all(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("Starting complete test suite")
        self._start_time = time.time()
        
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_system_tests()
        self.run_performance_tests()
        
        total_duration = time.time() - self._start_time
        
        return self._generate_report(total_duration)
    
    # === 测试实现 ===
    
    def _test_cache_basic(self) -> TestResult:
        """单元测试：缓存基础操作"""
        start = time.time()
        try:
            from backend.core.cache.multi_level_cache import L1Cache
            
            cache = L1Cache(max_size=100)
            cache.set("test_key", "test_value")
            value = cache.get("test_key")
            
            if value != "test_value":
                return TestResult(
                    name="Cache Basic Operations",
                    category=TestCategory.UNIT,
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    error=f"Expected test_value, got {value}"
                )
            
            return TestResult(
                name="Cache Basic Operations",
                category=TestCategory.UNIT,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Cache Basic Operations",
                category=TestCategory.UNIT,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_memory_basic(self) -> TestResult:
        """单元测试：记忆基础操作"""
        start = time.time()
        try:
            from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
            
            memory = UnifiedMemorySystem(InMemoryBackend())
            asyncio.run(memory.store("test_key", "test_value"))
            value = asyncio.run(memory.retrieve("test_key"))
            
            if value != "test_value":
                return TestResult(
                    name="Memory Basic Operations",
                    category=TestCategory.UNIT,
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    error=f"Expected test_value, got {value}"
                )
            
            return TestResult(
                name="Memory Basic Operations",
                category=TestCategory.UNIT,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Memory Basic Operations",
                category=TestCategory.UNIT,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_config_validation(self) -> TestResult:
        """单元测试：配置验证"""
        start = time.time()
        try:
            from backend.core.modular.config import CacheConfig
            
            config = CacheConfig(max_size=1000, ttl=300)
            assert config.max_size == 1000
            assert config.ttl == 300
            
            return TestResult(
                name="Config Validation",
                category=TestCategory.UNIT,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Config Validation",
                category=TestCategory.UNIT,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_structured_logging(self) -> TestResult:
        """单元测试：结构化日志"""
        start = time.time()
        try:
            import structlog
            logger_test = structlog.get_logger("test")
            logger_test.info("Test log message", extra_field="extra_value")
            
            return TestResult(
                name="Structured Logging",
                category=TestCategory.UNIT,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Structured Logging",
                category=TestCategory.UNIT,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_validation_utils(self) -> TestResult:
        """单元测试：验证工具"""
        start = time.time()
        try:
            from backend.core.utils.validator import InputValidator
            
            valid, error = InputValidator.validate_cache_key("valid_key_123")
            assert valid
            assert error is None
            
            return TestResult(
                name="Validation Utils",
                category=TestCategory.UNIT,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Validation Utils",
                category=TestCategory.UNIT,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_cache_memory_integration(self) -> TestResult:
        """集成测试：缓存+记忆"""
        start = time.time()
        try:
            from backend.core.cache.multi_level_cache import L1Cache
            from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
            
            cache = L1Cache(max_size=100)
            memory = UnifiedMemorySystem(InMemoryBackend())
            
            cache.set("cache_key", "cached_data")
            asyncio.run(memory.store("memory_key", "memory_data"))
            
            cache_val = cache.get("cache_key")
            memory_val = asyncio.run(memory.retrieve("memory_key"))
            
            if cache_val != "cached_data" or memory_val != "memory_data":
                return TestResult(
                    name="Cache-Memory Integration",
                    category=TestCategory.INTEGRATION,
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    error="Values don't match"
                )
            
            return TestResult(
                name="Cache-Memory Integration",
                category=TestCategory.INTEGRATION,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Cache-Memory Integration",
                category=TestCategory.INTEGRATION,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_agent_workflow_integration(self) -> TestResult:
        """集成测试：Agent工作流"""
        start = time.time()
        try:
            from backend.core.agents.multi_agent import MultiAgentOrchestrator, AgentTask, TaskStatus
            
            orchestrator = MultiAgentOrchestrator()
            task = AgentTask(
                task_id="test_integration",
                task_type="test",
                data={"input": "test"},
                description="Test task"
            )
            orchestrator.add_task(task)
            
            return TestResult(
                name="Agent Workflow Integration",
                category=TestCategory.INTEGRATION,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Agent Workflow Integration",
                category=TestCategory.INTEGRATION,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_config_initialization(self) -> TestResult:
        """集成测试：配置初始化"""
        start = time.time()
        try:
            from backend.core.modular.config import GlobalConfig, ProductConfigManager
            
            config = GlobalConfig()
            assert config.environment == "development"
            
            manager = ProductConfigManager()
            manager.load_defaults()
            built = manager.build()
            
            assert built is not None
            
            return TestResult(
                name="Config Initialization",
                category=TestCategory.INTEGRATION,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Config Initialization",
                category=TestCategory.INTEGRATION,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_full_agent_workflow(self) -> TestResult:
        """系统测试：完整Agent工作流"""
        start = time.time()
        try:
            from backend.core.cache.multi_level_cache import L1Cache
            from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
            from backend.core.agents.multi_agent import MultiAgentOrchestrator, AgentTask
            
            cache = L1Cache(max_size=100)
            memory = UnifiedMemorySystem(InMemoryBackend())
            orchestrator = MultiAgentOrchestrator()
            
            cache.set("session_data", {"user": "test"})
            asyncio.run(memory.store("user_pref", {"theme": "dark"}))
            
            task = AgentTask(
                task_id="workflow_test",
                task_type="reasoning",
                data={"query": "test"},
                description="System test"
            )
            orchestrator.add_task(task)
            
            session_data = cache.get("session_data")
            user_pref = asyncio.run(memory.retrieve("user_pref"))
            
            assert session_data is not None
            assert user_pref is not None
            
            return TestResult(
                name="Full Agent Workflow",
                category=TestCategory.SYSTEM,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Full Agent Workflow",
                category=TestCategory.SYSTEM,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_error_recovery_system(self) -> TestResult:
        """系统测试：错误恢复"""
        start = time.time()
        try:
            from backend.core.cache.multi_level_cache import L1Cache
            
            cache = L1Cache(max_size=100)
            
            try:
                cache.set("", "invalid")
            except Exception:
                pass
            
            cache.set("recovery_test", "works")
            value = cache.get("recovery_test")
            
            if value != "works":
                return TestResult(
                    name="Error Recovery System",
                    category=TestCategory.SYSTEM,
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    error="Recovery failed"
                )
            
            return TestResult(
                name="Error Recovery System",
                category=TestCategory.SYSTEM,
                status=TestStatus.PASSED,
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="Error Recovery System",
                category=TestCategory.SYSTEM,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_cache_performance(self) -> TestResult:
        """性能测试：缓存性能"""
        start = time.time()
        try:
            from backend.core.cache.multi_level_cache import L1Cache
            
            cache = L1Cache(max_size=10000)
            operations = 10000
            
            for i in range(operations):
                cache.set(f"perf_key_{i}", f"perf_value_{i}")
            
            for i in range(operations):
                cache.get(f"perf_key_{i}")
            
            duration = time.time() - start
            ops_per_sec = (operations * 2) / duration
            
            return TestResult(
                name="Cache Performance",
                category=TestCategory.PERFORMANCE,
                status=TestStatus.PASSED,
                duration=duration,
                details={"operations_per_second": ops_per_sec, "operations": operations * 2}
            )
        except Exception as e:
            return TestResult(
                name="Cache Performance",
                category=TestCategory.PERFORMANCE,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _test_memory_throughput(self) -> TestResult:
        """性能测试：记忆吞吐量"""
        start = time.time()
        try:
            from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
            
            memory = UnifiedMemorySystem(InMemoryBackend())
            operations = 1000
            
            async def run_ops():
                for i in range(operations):
                    await memory.store(f"mem_perf_{i}", f"value_{i}")
                for i in range(operations):
                    await memory.retrieve(f"mem_perf_{i}")
            
            asyncio.run(run_ops())
            
            duration = time.time() - start
            ops_per_sec = (operations * 2) / duration
            
            return TestResult(
                name="Memory Throughput",
                category=TestCategory.PERFORMANCE,
                status=TestStatus.PASSED,
                duration=duration,
                details={"operations_per_second": ops_per_sec}
            )
        except Exception as e:
            return TestResult(
                name="Memory Throughput",
                category=TestCategory.PERFORMANCE,
                status=TestStatus.FAILED,
                duration=time.time() - start,
                error=str(e)
            )
    
    def _generate_report(self, total_duration: float) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = sum(s.total for s in self.suites)
        total_passed = sum(s.passed for s in self.suites)
        total_failed = sum(s.failed for s in self.suites)
        
        overall_pass_rate = total_passed / total_tests if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "pass_rate": overall_pass_rate,
                "total_duration": total_duration
            },
            "suites": []
        }
        
        for suite in self.suites:
            report["suites"].append({
                "name": suite.name,
                "total": suite.total,
                "passed": suite.passed,
                "failed": suite.failed,
                "pass_rate": suite.pass_rate,
                "tests": [
                    {
                        "name": t.name,
                        "category": t.category.value,
                        "status": t.status.value,
                        "duration": t.duration,
                        "error": t.error,
                        "details": t.details
                    }
                    for t in suite.tests
                ]
            })
        
        return report
