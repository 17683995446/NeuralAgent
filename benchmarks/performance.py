"""
NeuralAgent Performance Benchmark Suite
性能基准测试套件
"""

import time
import asyncio
import statistics
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from unittest.mock import Mock, patch
import numpy as np


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    mean_time: float
    median_time: float
    std_dev: float
    min_time: float
    max_time: float
    operations_per_second: float


class PerformanceBenchmark:
    """性能基准测试基类"""

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results: List[BenchmarkResult] = []

    def benchmark_function(self, name: str, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """测试函数性能"""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 转换为毫秒

        result = BenchmarkResult(
            name=name,
            iterations=self.iterations,
            mean_time=statistics.mean(times),
            median_time=statistics.median(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0,
            min_time=min(times),
            max_time=max(times),
            operations_per_second=1000 / statistics.mean(times)
        )

        self.results.append(result)
        return result

    async def benchmark_async_function(self, name: str, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """测试异步函数性能"""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            await func(*args, **kwargs)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        result = BenchmarkResult(
            name=name,
            iterations=self.iterations,
            mean_time=statistics.mean(times),
            median_time=statistics.median(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0,
            min_time=min(times),
            max_time=max(times),
            operations_per_second=1000 / statistics.mean(times)
        )

        self.results.append(result)
        return result

    def print_results(self):
        """打印测试结果"""
        print("\n" + "="*80)
        print("🎯 Performance Benchmark Results")
        print("="*80)

        for result in self.results:
            print(f"\n📊 {result.name}")
            print(f"   Iterations:        {result.iterations}")
            print(f"   Mean Time:         {result.mean_time:.3f} ms")
            print(f"   Median Time:       {result.median_time:.3f} ms")
            print(f"   Std Dev:           {result.std_dev:.3f} ms")
            print(f"   Min/Max:           {result.min_time:.3f} / {result.max_time:.3f} ms")
            print(f"   Throughput:        {result.operations_per_second:.2f} ops/s")

            if result.mean_time < 100:
                print(f"   ✅ Status: EXCELLENT")
            elif result.mean_time < 500:
                print(f"   ⚠️  Status: GOOD")
            else:
                print(f"   ❌ Status: NEEDS OPTIMIZATION")

        print("\n" + "="*80)


class AgentPerformanceBenchmark(PerformanceBenchmark):
    """Agent 性能基准测试"""

    def benchmark_agent_creation(self):
        """测试 Agent 创建性能"""
        def create_agent():
            from backend.core.agent_framework.agent import Agent

            agent = Agent(
                name="benchmark_agent",
                agent_type="test",
                description="Benchmark agent"
            )
            return agent

        return self.benchmark_function("Agent Creation", create_agent)

    def benchmark_agent_execution(self):
        """测试 Agent 执行性能"""
        from backend.core.agent_framework.agent import Agent

        agent = Agent(
            name="benchmark_agent",
            agent_type="test",
            description="Benchmark agent"
        )

        def execute_agent():
            try:
                result = asyncio.run(agent.execute("test task"))
                return result
            except Exception:
                return "mock_result"

        return self.benchmark_function("Agent Execution", execute_agent)

    def benchmark_memory_operations(self):
        """测试记忆系统操作性能"""

        def memory_write():
            from backend.core.memory.unified import UnifiedMemoryStore

            memory = UnifiedMemoryStore()
            memory.add("test_key", "test_content", "test_type")

        def memory_read():
            from backend.core.memory.unified import UnifiedMemoryStore

            memory = UnifiedMemoryStore()
            memory.get("test_key")

        self.benchmark_function("Memory Write", memory_write)
        self.benchmark_function("Memory Read", memory_read)


class VectorStoreBenchmark(PerformanceBenchmark):
    """向量数据库性能基准测试"""

    def __init__(self, iterations: int = 100):
        super().__init__(iterations)
        self.vector_size = 768
        self.collection_size = 1000

    def benchmark_vector_search(self):
        """测试向量搜索性能"""
        from backend.core.vector_store.milvus import MilvusVectorStore
        from backend.core.vector_store.config import VectorStoreConfig, VectorStoreType

        config = VectorStoreConfig(
            type=VectorStoreType.IN_MEMORY,
            collection_name="benchmark"
        )

        store = MilvusVectorStore(config)

        vectors = np.random.rand(100, self.vector_size).tolist()
        for i, vec in enumerate(vectors):
            store.add(VectorDocument(
                id=f"doc_{i}",
                content=f"Document {i}",
                embedding=vec
            ))

        query_vector = np.random.rand(self.vector_size).tolist()

        def search():
            return store.search(query_vector, top_k=10)

        return self.benchmark_function("Vector Search (100 docs, top_k=10)", search)

    def benchmark_vector_indexing(self):
        """测试向量索引性能"""
        from backend.core.vector_store.milvus import MilvusVectorStore
        from backend.core.vector_store.config import VectorStoreConfig, VectorStoreType

        def index_vectors():
            config = VectorStoreConfig(
                type=VectorStoreType.IN_MEMORY,
                collection_name="benchmark_index"
            )

            store = MilvusVectorStore(config)

            vectors = np.random.rand(self.collection_size, self.vector_size).tolist()
            for i, vec in enumerate(vectors):
                store.add(VectorDocument(
                    id=f"doc_{i}",
                    content=f"Document {i}",
                    embedding=vec
                ))

        return self.benchmark_function(
            f"Vector Indexing ({self.collection_size} vectors)",
            index_vectors
        )

    def benchmark_batch_operations(self):
        """测试批量操作性能"""
        from backend.core.vector_store.milvus import MilvusVectorStore
        from backend.core.vector_store.config import VectorStoreConfig, VectorStoreType

        config = VectorStoreConfig(
            type=VectorStoreType.IN_MEMORY,
            collection_name="benchmark_batch"
        )

        store = MilvusVectorStore(config)

        batch_size = 100
        vectors = np.random.rand(batch_size, self.vector_size).tolist()
        docs = [
            VectorDocument(
                id=f"doc_{i}",
                content=f"Document {i}",
                embedding=vec
            )
            for i, vec in enumerate(vectors)
        ]

        def batch_add():
            for doc in docs:
                store.add(doc)

        return self.benchmark_function(f"Batch Add ({batch_size} docs)", batch_add)


class APIBenchmark(PerformanceBenchmark):
    """API 性能基准测试"""

    def benchmark_json_serialization(self):
        """测试 JSON 序列化性能"""
        import json
        from pydantic import BaseModel

        class TestModel(BaseModel):
            id: str
            name: str
            data: Dict[str, Any]
            items: List[Dict]

        model = TestModel(
            id="test_id",
            name="test_name",
            data={"key1": "value1", "key2": "value2"},
            items=[{"item": i} for i in range(100)]
        )

        def serialize():
            return model.json()

        def deserialize():
            json_str = model.json()
            return TestModel.parse_raw(json_str)

        self.benchmark_function("JSON Serialization", serialize)
        self.benchmark_function("JSON Deserialization", deserialize)

    def benchmark_validation(self):
        """测试数据验证性能"""
        from pydantic import BaseModel, Field

        class ValidatedModel(BaseModel):
            id: str = Field(..., min_length=1)
            email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
            count: int = Field(..., ge=0, le=100)

        valid_data = {
            "id": "test_id",
            "email": "test@example.com",
            "count": 50
        }

        def validate():
            return ValidatedModel(**valid_data)

        return self.benchmark_function("Pydantic Validation", validate)


def run_all_benchmarks():
    """运行所有基准测试"""
    print("\n🚀 Starting NeuralAgent Performance Benchmarks")
    print("=" * 80)

    benchmark_suite = PerformanceBenchmark(iterations=50)

    print("\n📊 Running Agent Benchmarks...")
    agent_benchmark = AgentPerformanceBenchmark(iterations=50)
    agent_benchmark.benchmark_agent_creation()

    print("\n📊 Running Vector Store Benchmarks...")
    vector_benchmark = VectorStoreBenchmark(iterations=50)
    vector_benchmark.benchmark_vector_indexing()

    print("\n📊 Running API Benchmarks...")
    api_benchmark = APIBenchmark(iterations=100)
    api_benchmark.benchmark_json_serialization()

    print("\n✅ All benchmarks completed!")
    print("\n" + "=" * 80)
    print("📈 Summary")
    print("=" * 80)

    all_results = (
        agent_benchmark.results +
        vector_benchmark.results +
        api_benchmark.results
    )

    for result in all_results:
        print(f"{result.name:.<50} {result.mean_time:>8.3f} ms")

    print("\n🎯 Performance Targets:")
    print("   - API Response: < 200ms  ✅" if all(r.mean_time < 200 for r in all_results) else "   - API Response: < 200ms  ❌")
    print("   - Vector Search: < 100ms ✅" if any("Vector Search" in r.name and r.mean_time < 100 for r in all_results) else "   - Vector Search: < 100ms ❌")

    return all_results


if __name__ == "__main__":
    results = run_all_benchmarks()
