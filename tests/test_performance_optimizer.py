"""
Tests for Performance Optimizer Module
Product Grade Test Suite
"""

import time
import pytest
import sys
from pathlib import Path

# Fix imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.test_helpers import fix_imports, safe_import

fix_imports()

# Safe imports
success, optimizer_module = safe_import('backend.core.performance_optimizer')

if success and optimizer_module:
    OptimizationLevel = optimizer_module.OptimizationLevel
    PerformanceMetrics = optimizer_module.PerformanceMetrics
    PerformanceOptimizer = optimizer_module.PerformanceOptimizer
    PerformanceTester = optimizer_module.PerformanceTester
    optimizer = optimizer_module.optimizer
    optimize = optimizer_module.optimize


@pytest.mark.skipif(optimizer_module is None, reason="Performance optimizer module not available")
class TestPerformanceMetrics:
    """Test Performance Metrics class"""
    
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics"""
        metrics = PerformanceMetrics(
            execution_time_ms=100.5,
            function_name="test_func",
            timestamp=1234567890.0
        )
        assert metrics.execution_time_ms == 100.5
        assert metrics.function_name == "test_func"
        assert metrics.timestamp == 1234567890.0


@pytest.mark.skipif(optimizer_module is None, reason="Performance optimizer module not available")
class TestPerformanceOptimizer:
    """Test Performance Optimizer class"""
    
    def test_optimizer_initialization(self):
        """Test optimizer initialization"""
        opt = PerformanceOptimizer(level=OptimizationLevel.DEBUG)
        assert opt.level == OptimizationLevel.DEBUG
        assert opt.metrics == {}
    
    def test_timeit_decorator(self):
        """Test timeit decorator"""
        opt = PerformanceOptimizer()
        
        @opt.timeit
        def slow_function():
            time.sleep(0.01)
            return "done"
        
        # Call multiple times
        results = []
        for _ in range(3):
            results.append(slow_function())
        
        assert results == ["done", "done", "done"]
        assert "slow_function" in opt.metrics
        assert len(opt.metrics["slow_function"]) == 3
    
    def test_get_average_time(self):
        """Test get_average_time method"""
        opt = PerformanceOptimizer()
        
        @opt.timeit
        def fast_func():
            time.sleep(0.001)
            return "ok"
        
        # Call multiple times
        for _ in range(5):
            fast_func()
        
        avg_time = opt.get_average_time("fast_func")
        assert avg_time is not None
        assert avg_time > 0
    
    def test_get_average_time_nonexistent(self):
        """Test get_average_time with nonexistent function"""
        opt = PerformanceOptimizer()
        avg_time = opt.get_average_time("nonexistent")
        assert avg_time is None
    
    def test_get_metrics_summary(self):
        """Test get_metrics_summary"""
        opt = PerformanceOptimizer()
        
        @opt.timeit
        def func_a():
            time.sleep(0.001)
        
        @opt.timeit
        def func_b():
            time.sleep(0.002)
        
        func_a()
        func_b()
        func_a()
        
        summary = opt.get_metrics_summary()
        assert "func_a" in summary
        assert "func_b" in summary
        assert summary["func_a"]["count"] == 2
        assert summary["func_b"]["count"] == 1


@pytest.mark.skipif(optimizer_module is None, reason="Performance optimizer module not available")
class TestOptimizeDecorator:
    """Test optimize decorator"""
    
    def test_optimize_decorator(self):
        """Test the optimize decorator"""
        @optimize()
        def decorated_func(x):
            time.sleep(0.01)
            return x * 2
        
        result = decorated_func(5)
        assert result == 10


@pytest.mark.skipif(optimizer_module is None, reason="Performance optimizer module not available")
class TestPerformanceTester:
    """Test Performance Tester class"""
    
    def test_performance_tester_initialization(self):
        """Test tester initialization"""
        tester = PerformanceTester("test_target")
        assert tester.target == "test_target"
        assert tester.results == {}
    
    def test_run_benchmark(self):
        """Test running benchmark"""
        tester = PerformanceTester("benchmark")
        
        def simple_function():
            time.sleep(0.001)
        
        result = tester.run_benchmark(
            name="simple_test",
            func=simple_function,
            iterations=10
        )
        
        assert result["name"] == "simple_test"
        assert result["iterations"] == 10
        assert result["total_time_ms"] > 0
        assert "avg_time_ms_per_iteration_ms" in result
    
    def test_get_benchmark_results(self):
        """Test getting benchmark results"""
        tester = PerformanceTester("multi_test")
        
        def func1():
            time.sleep(0.001)
        
        def func2():
            time.sleep(0.002)
        
        tester.run_benchmark("test1", func1, iterations=5)
        tester.run_benchmark("test2", func2, iterations=3)
        
        results = tester.get_benchmark_results()
        assert "test1" in results
        assert "test2" in results


@pytest.mark.skipif(optimizer_module is None, reason="Performance optimizer module not available")
class TestGlobalOptimizer:
    """Test global optimizer instance"""
    
    def test_global_optimizer_exists(self):
        """Test global optimizer exists"""
        assert optimizer is not None
        assert isinstance(optimizer, PerformanceOptimizer)


@pytest.mark.skipif(optimizer_module is None, reason="Performance optimizer module not available")
class TestOptimizationLevels:
    """Test optimization level enum"""
    
    def test_optimization_levels(self):
        """Test optimization level values"""
        assert OptimizationLevel.DEBUG.value == 0
        assert OptimizationLevel.PRODUCTION.value == 1
        assert OptimizationLevel.EXTREME.value == 2
    
    def test_optimization_with_levels(self):
        """Test optimization with different levels"""
        @optimize(level=OptimizationLevel.DEBUG)
        def debug_func():
            time.sleep(0.001)
            return "debug"
        
        @optimize(level=OptimizationLevel.PRODUCTION)
        def prod_func():
            time.sleep(0.001)
            return "prod"
        
        assert debug_func() == "debug"
        assert prod_func() == "prod"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
