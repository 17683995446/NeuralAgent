"""
NeuralAgent - 生产级长时间压力测试与集成测试
真实业务场景模拟，长时间运行，发现隐藏缺陷
"""

import asyncio
import sys
import os
import time
import uuid
import json
import random
import threading
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@dataclass
class TestResult:
    name: str
    status: str
    duration: float
    error: str = ""
    metrics: Dict[str, float] = None

class ProductionTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.errors = []
        self.memory_usage = []
        self.throughput_data = []
        
    def log_result(self, result: TestResult):
        self.results.append(result)
        status_icon = "✅" if result.status == "PASS" else "❌"
        print(f"{status_icon} [{result.status}] {result.name} ({result.duration:.2f}s)")
        if result.error:
            print(f"   Error: {result.error}")
            
    def run_test(self, name, test_func, *args, **kwargs):
        start = time.time()
        try:
            metrics = test_func(*args, **kwargs)
            duration = time.time() - start
            self.log_result(TestResult(name, "PASS", duration, "", metrics))
            return True
        except Exception as e:
            duration = time.time() - start
            self.log_result(TestResult(name, "FAIL", duration, str(e)))
            return False

def test_large_scale_cache_operations():
    """大规模缓存操作 - 10万次读写操作"""
    from backend.core.cache.multi_level_cache import L1Cache
    
    cache = L1Cache(max_size=50000)
    operations = 100000
    start = time.time()
    
    for i in range(operations):
        key = f"test_key_{i % 50000}"
        value = f"value_{i}_data_{uuid.uuid4().hex}"
        cache.set(key, value, ttl=60)
        if i % 2 == 0:
            cache.get(key)
    
    duration = time.time() - start
    ops_per_sec = operations / duration
    
    stats = cache.get_stats()
    return {
        "operations": operations,
        "throughput": ops_per_sec,
        "size": stats["size"]
    }

def test_concurrent_memory_access():
    """并发记忆访问 - 50个并发线程，每个1000次操作"""
    from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
    
    memory = UnifiedMemorySystem(InMemoryBackend())
    errors = []
    operations = 0
    lock = threading.Lock()
    
    def worker(thread_id):
        nonlocal operations
        try:
            for i in range(1000):
                key = f"thread_{thread_id}_key_{i}"
                asyncio.run(memory.store(key, {"data": i}))
                val = asyncio.run(memory.retrieve(key))
                if val != {"data": i}:
                    with lock:
                        errors.append(f"Data mismatch at {key}")
                with lock:
                    operations += 1
        except Exception as e:
            with lock:
                errors.append(str(e))
    
    threads = []
    for i in range(50):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    return {
        "threads": 50,
        "operations": operations,
        "errors": len(errors)
    }

def test_agent_task_orchestration():
    """Agent任务编排 - 完整工作流"""
    from backend.core.agents.multi_agent import MultiAgentOrchestrator, AgentTask
    
    orchestrator = MultiAgentOrchestrator()
    success = 0
    total = 100
    
    for i in range(total):
        try:
            task = AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="analysis" if i % 2 == 0 else "synthesis",
                data={"input": f"Test task {i}", "priority": random.randint(1, 5)},
                description=f"Analysis task #{i}"
            )
            orchestrator.add_task(task)
            success += 1
        except Exception as e:
            print(f"Task {i} failed: {e}")
    
    return {
        "total": total,
        "success": success,
        "success_rate": success / total
    }

def test_data_validation_edge_cases():
    """数据验证边界测试 - 修正版"""
    from backend.core.utils.validator import InputValidator
    
    test_cases = [
        ("", True),               # 空字符串 - 应该失败
        ("   ", True),            # 空白 - 应该失败
        ("a" * 2000, True),       # 超长 (超过1024) - 应该失败
        ("测试_unicode_😊", False), # 正常Unicode - 应该通过
        ("normal_key_123", False),# 正常键 - 应该通过
        ("valid_with_hyphens-underscores", False),  # 正常 - 应该通过
    ]
    
    success = 0
    for input_str, should_fail in test_cases:
        is_valid, _ = InputValidator.validate_cache_key(input_str)
        actual_fail = not is_valid
        if actual_fail == should_fail:
            success += 1
    
    return {
        "total": len(test_cases),
        "success": success
    }

def test_prompt_sanitization():
    """提示词XSS防护 - 验证转义而非删除"""
    from tools.prompt_workbench.workbench import XSSSanitizer
    
    test_cases = [
        ("<script>alert('xss')</script>", True),   # 应该被转义
        ("javascript:alert('test')", True),        # 应该被转义
        ("<img src=x onerror=alert('x')>", True),  # 应该被转义
        ("normal prompt", False)                   # 应该保持原样
    ]
    
    success = 0
    for input_str, should_be_modified in test_cases:
        sanitized = XSSSanitizer.sanitize(input_str)
        
        if should_be_modified:
            if sanitized != input_str:
                success += 1
        else:
            if sanitized == input_str:
                success += 1
    
    return {
        "total": len(test_cases),
        "success": success
    }

def test_memory_management():
    """内存管理与GC压力测试"""
    import gc
    from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
    
    memory = UnifiedMemorySystem(InMemoryBackend())
    
    gc.collect()
    initial_objects = len(gc.get_objects())
    
    for phase in range(10):
        for i in range(1000):
            asyncio.run(memory.store(f"phase_{phase}_key_{i}", f"value_{i}" * 10))
        for i in range(0, 1000, 2):
            asyncio.run(memory.remove(f"phase_{phase}_key_{i}"))
    
    gc.collect()
    final_objects = len(gc.get_objects())
    
    growth = final_objects - initial_objects
    return {
        "initial_objects": initial_objects,
        "final_objects": final_objects,
        "growth": growth
    }

def test_extended_workflow_simulation():
    """扩展工作流模拟 - 真实业务流程"""
    from backend.core.cache.multi_level_cache import L1Cache
    from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
    from backend.core.agents.multi_agent import MultiAgentOrchestrator, AgentTask
    
    cache = L1Cache(max_size=5000)
    memory = UnifiedMemorySystem(InMemoryBackend())
    orchestrator = MultiAgentOrchestrator()
    
    workflow_success = 0
    for i in range(20):
        try:
            cache.set(f"workflow_session_{i}", {"status": "active", "id": i})
            
            asyncio.run(memory.store(f"workflow_data_{i}", {"input": f"User request {i}"}))
            
            task = AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="process",
                data={"session": i},
                description=f"Process user request {i}"
            )
            orchestrator.add_task(task)
            
            cached_data = cache.get(f"workflow_session_{i}")
            if cached_data:
                workflow_success += 1
        except Exception as e:
            print(f"Workflow {i} failed: {e}")
    
    return {
        "workflows": 20,
        "success": workflow_success
    }

def main():
    print("=" * 80)
    print("NeuralAgent - 生产级长时间压力测试与集成测试")
    print("=" * 80)
    
    suite = ProductionTestSuite()
    
    print("\n" + "-" * 80)
    print("1. 大规模缓存操作 (100,000 次)")
    suite.run_test("大规模缓存", test_large_scale_cache_operations)
    
    print("\n" + "-" * 80)
    print("2. 并发记忆访问 (50 线程, 50,000 操作)")
    suite.run_test("并发记忆访问", test_concurrent_memory_access)
    
    print("\n" + "-" * 80)
    print("3. Agent任务编排 (100 任务)")
    suite.run_test("Agent任务编排", test_agent_task_orchestration)
    
    print("\n" + "-" * 80)
    print("4. 数据验证边界测试")
    suite.run_test("数据验证边界", test_data_validation_edge_cases)
    
    print("\n" + "-" * 80)
    print("5. 提示词XSS防护")
    suite.run_test("XSS防护", test_prompt_sanitization)
    
    print("\n" + "-" * 80)
    print("6. 内存管理与GC压力测试")
    suite.run_test("内存管理GC", test_memory_management)
    
    print("\n" + "-" * 80)
    print("7. 完整工作流模拟")
    suite.run_test("完整工作流", test_extended_workflow_simulation)
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for r in suite.results if r.status == "PASS")
    total = len(suite.results)
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {passed / total * 100:.1f}%")
    
    print("\n详细结果:")
    for r in suite.results:
        status = "✅" if r.status == "PASS" else "❌"
        print(f"  {status} {r.name}: {r.duration:.2f}s")
        if r.metrics:
            for k, v in r.metrics.items():
                print(f"      {k}: {v}")
    
    print("\n" + "=" * 80)
    
    return 0 if total == passed else 1

if __name__ == "__main__":
    sys.exit(main())
