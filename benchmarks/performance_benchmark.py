"""
NeuralAgent 性能基准测试框架
提供系统性能测试和监控功能
"""

import asyncio
import time
import psutil
import statistics
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    description: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    qps: float
    memory_before: float
    memory_after: float
    memory_delta: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SystemMetrics:
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.metrics_history: List[SystemMetrics] = []
    
    def measure_memory(self) -> SystemMetrics:
        """测量系统内存"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv
        )
    
    async def run_benchmark(
        self,
        name: str,
        description: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10
    ) -> BenchmarkResult:
        """运行基准测试"""
        times = []
        
        for _ in range(warmup):
            await func()
        
        memory_before = self.measure_memory()
        
        for _ in range(iterations):
            start = time.perf_counter()
            await func()
            end = time.perf_counter()
            times.append(end - start)
            
            if len(times) % 10 == 0:
                metrics = self.measure_memory()
                self.metrics_history.append(metrics)
        
        memory_after = self.measure_memory()
        
        result = BenchmarkResult(
            name=name,
            description=description,
            iterations=iterations,
            total_time=sum(times),
            avg_time=statistics.mean(times),
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0,
            qps=iterations / sum(times),
            memory_before=memory_before.memory_used_mb,
            memory_after=memory_after.memory_used_mb,
            memory_delta=memory_after.memory_used_mb - memory_before.memory_used_mb
        )
        
        self.results.append(result)
        return result
    
    def run_sync_benchmark(
        self,
        name: str,
        description: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10
    ) -> BenchmarkResult:
        """运行同步基准测试"""
        times = []
        
        for _ in range(warmup):
            func()
        
        memory_before = self.measure_memory()
        
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)
            
            if len(times) % 10 == 0:
                metrics = self.measure_memory()
                self.metrics_history.append(metrics)
        
        memory_after = self.measure_memory()
        
        result = BenchmarkResult(
            name=name,
            description=description,
            iterations=iterations,
            total_time=sum(times),
            avg_time=statistics.mean(times),
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0,
            qps=iterations / sum(times),
            memory_before=memory_before.memory_used_mb,
            memory_after=memory_after.memory_used_mb,
            memory_delta=memory_after.memory_used_mb - memory_before.memory_used_mb
        )
        
        self.results.append(result)
        return result
    
    def generate_report(self) -> str:
        """生成基准测试报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("NeuralAgent 性能基准测试报告")
        lines.append(f"生成时间: {datetime.now().isoformat()}")
        lines.append("=" * 80)
        lines.append("")
        
        for result in self.results:
            lines.append(f"\n### {result.name}")
            lines.append(f"描述: {result.description}")
            lines.append(f"迭代次数: {result.iterations}")
            lines.append(f"总耗时: {result.total_time:.4f}s")
            lines.append(f"平均耗时: {result.avg_time*1000:.4f}ms")
            lines.append(f"最小耗时: {result.min_time*1000:.4f}ms")
            lines.append(f"最大耗时: {result.max_time*1000:.4f}ms")
            lines.append(f"标准差: {result.std_dev*1000:.4f}ms")
            lines.append(f"QPS: {result.qps:.2f}")
            lines.append(f"内存变化: {result.memory_delta:.2f}MB")
            lines.append("")
        
        if self.metrics_history:
            lines.append("\n### 系统资源使用")
            avg_cpu = sum(m.cpu_percent for m in self.metrics_history) / len(self.metrics_history)
            avg_memory = sum(m.memory_percent for m in self.metrics_history) / len(self.metrics_history)
            lines.append(f"平均CPU使用率: {avg_cpu:.2f}%")
            lines.append(f"平均内存使用率: {avg_memory:.2f}%")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)
    
    def export_json(self, filepath: str):
        """导出JSON格式"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "name": r.name,
                    "description": r.description,
                    "iterations": r.iterations,
                    "total_time": r.total_time,
                    "avg_time": r.avg_time,
                    "min_time": r.min_time,
                    "max_time": r.max_time,
                    "std_dev": r.std_dev,
                    "qps": r.qps,
                    "memory_delta": r.memory_delta
                }
                for r in self.results
            ],
            "system_metrics": [
                {
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": m.memory_percent,
                    "memory_used_mb": m.memory_used_mb,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.metrics_history
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


async def run_memory_benchmark():
    """记忆系统基准测试"""
    from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
    
    memory = UnifiedMemorySystem(InMemoryBackend())
    
    async def store_and_retrieve():
        await memory.store("benchmark:test", {"data": "test value"})
        await memory.retrieve("benchmark:test")
    
    benchmark = PerformanceBenchmark()
    result = await benchmark.run_benchmark(
        name="Memory Store & Retrieve",
        description="记忆系统存储和检索性能测试",
        func=store_and_retrieve,
        iterations=100,
        warmup=10
    )
    
    print(benchmark.generate_report())
    return result


async def run_cache_benchmark():
    """缓存系统基准测试"""
    from backend.core.cache.multi_level_cache import get_cache
    
    cache = get_cache()
    
    async def cache_operations():
        await cache.set("benchmark:key", "test value")
        await cache.get("benchmark:key")
    
    benchmark = PerformanceBenchmark()
    result = await benchmark.run_benchmark(
        name="Cache Get & Set",
        description="缓存系统读写性能测试",
        func=cache_operations,
        iterations=100,
        warmup=10
    )
    
    print(benchmark.generate_report())
    return result


async def run_llm_benchmark():
    """LLM适配器基准测试"""
    from backend.core.llm_adapter import create_llm_adapter, LLMProvider
    
    llm = create_llm_adapter(LLMProvider.MOCK)
    
    async def llm_generate():
        await llm.generate("Hello, NeuralAgent!")
    
    benchmark = PerformanceBenchmark()
    result = await benchmark.run_benchmark(
        name="LLM Generate",
        description="LLM生成性能测试",
        func=llm_generate,
        iterations=50,
        warmup=5
    )
    
    print(benchmark.generate_report())
    return result


async def run_security_benchmark():
    """安全系统基准测试"""
    from backend.core.security import get_auth_service, get_api_key_manager, get_rate_limiter
    
    auth = get_auth_service()
    key_manager = get_api_key_manager()
    rate_limiter = get_rate_limiter()
    
    async def auth_operations():
        user = auth.register_user("benchmark", "benchmark@test.com", "password123")
        auth.authenticate_user("benchmark", "password123")
    
    async def key_operations():
        key_obj, key = key_manager.create_key("benchmark", KeyType.USER)
        key_manager.verify_key(key)
    
    async def rate_limit_operations():
        rate_limiter.check_limit("benchmark:user")
    
    benchmark = PerformanceBenchmark()
    
    await benchmark.run_benchmark(
        name="Authentication Operations",
        description="认证系统性能测试",
        func=auth_operations,
        iterations=100,
        warmup=10
    )
    
    await benchmark.run_benchmark(
        name="API Key Operations",
        description="API密钥操作性能测试",
        func=key_operations,
        iterations=100,
        warmup=10
    )
    
    await benchmark.run_benchmark(
        name="Rate Limiter Operations",
        description="限流系统性能测试",
        func=rate_limit_operations,
        iterations=1000,
        warmup=100
    )
    
    print(benchmark.generate_report())
    return benchmark.results


if __name__ == "__main__":
    async def main():
        print("🚀 NeuralAgent 性能基准测试")
        print("=" * 80)
        
        print("\n📊 记忆系统基准测试")
        await run_memory_benchmark()
        
        print("\n🔧 缓存系统基准测试")
        await run_cache_benchmark()
        
        print("\n🤖 LLM系统基准测试")
        await run_llm_benchmark()
        
        print("\n🔐 安全系统基准测试")
        await run_security_benchmark()
        
        print("\n✅ 基准测试完成!")
    
    asyncio.run(main())
