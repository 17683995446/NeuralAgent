"""
NeuralAgent - 超深层缺陷挖掘与生产级集成测试
专注发现隐藏缺陷、性能问题、并发问题
"""

import asyncio
import sys
import os
import time
import uuid
import threading
import gc
import traceback
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from collections import defaultdict
import random
import string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@dataclass
class TestMetrics:
    name: str
    duration: float
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    performance: Dict[str, Any] = field(default_factory=dict)

class DeepDefectDiscovery:
    """深层缺陷挖掘器"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.memory_snapshots = []
        self.performance_data = []
        
    def record(self, name: str, passed: bool, duration: float, 
               errors: List[str] = None, warnings: List[str] = None,
               performance: Dict[str, Any] = None):
        metrics = TestMetrics(
            name=name,
            duration=duration,
            passed=passed,
            errors=errors or [],
            warnings=warnings or [],
            performance=performance or {}
        )
        self.results.append(metrics)
        
        status = "✅" if passed else "❌"
        print(f"{status} [{name}] ({duration:.2f}s)")
        if errors:
            for err in errors:
                print(f"   ❗ Error: {err}")
        if warnings:
            for warn in warnings:
                print(f"   ⚠️  Warning: {warn}")
        if performance:
            for k, v in performance.items():
                print(f"      {k}: {v}")
                
    def snapshot_memory(self, label: str):
        gc.collect()
        stats = {
            'label': label,
            'timestamp': time.time(),
            'objects': len(gc.get_objects()),
            'garbage': len(gc.garbage)
        }
        self.memory_snapshots.append(stats)
        return stats

def test_cache_race_conditions():
    """并发竞态条件测试 - 多个线程同时访问缓存"""
    from backend.core.cache.multi_level_cache import L1Cache
    
    suite = DeepDefectDiscovery()
    cache = L1Cache(max_size=1000)
    errors = []
    operations_count = defaultdict(int)
    lock = threading.Lock()
    
    def worker(worker_id, iterations):
        for i in range(iterations):
            try:
                key = f"shared_key_{i % 100}"
                value = f"worker_{worker_id}_value_{i}"
                
                cache.set(key, value, ttl=60)
                retrieved = cache.get(key)
                
                with lock:
                    operations_count[f"worker_{worker_id}"] += 1
                    
                if retrieved is None:
                    errors.append(f"Worker {worker_id}: Failed to retrieve key {key}")
                    
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")
    
    # 启动10个并发线程，每个执行1000次操作
    threads = []
    iterations = 1000
    num_workers = 10
    
    suite.snapshot_memory("before_test")
    
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(i, iterations))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    suite.snapshot_memory("after_test")
    
    total_ops = sum(operations_count.values())
    errors_count = len(errors)
    
    passed = errors_count == 0
    suite.record(
        "并发竞态条件测试",
        passed,
        time.time() - suite.start_time,
        errors=[f"Found {errors_count} errors" if errors_count > 0 else ""],
        performance={
            "total_operations": total_ops,
            "workers": num_workers,
            "error_count": errors_count
        }
    )
    
    return passed

def test_memory_leak_detection():
    """内存泄漏检测 - 长时间运行"""
    from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
    
    memory = UnifiedMemorySystem(InMemoryBackend(max_size=100000))
    
    gc.collect()
    initial_objects = len(gc.get_objects())
    
    # 模拟10轮操作，每轮1000次
    for phase in range(10):
        for i in range(1000):
            key = f"leak_test_key_{phase}_{i}"
            value = {"data": f"value_{i}", "timestamp": time.time()}
            
            asyncio.run(memory.store(key, value))
            
        # 每轮后清理一半的数据
        for i in range(0, 1000, 2):
            key = f"leak_test_key_{phase}_{i}"
            asyncio.run(memory.remove(key))
    
    gc.collect()
    final_objects = len(gc.get_objects())
    
    # 检查对象增长
    growth = final_objects - initial_objects
    
    # 内存增长阈值设置为15000，考虑：
    # - 保留了5000个有效key
    # - asyncio内部对象
    # - Python GC延迟
    acceptable_growth = 15000
    passed = growth < acceptable_growth
    
    if passed:
        print(f"✅ [内存泄漏检测] (0.00s)")
        print(f"   ✓ Memory growth: {growth} objects (limit: {acceptable_growth})")
        print(f"      initial_objects: {initial_objects}")
        print(f"      final_objects: {final_objects}")
    else:
        print(f"❌ [内存泄漏检测] (0.00s)")
        print(f"   ⚠️  Warning: Memory growth: {growth} objects (limit: {acceptable_growth})")
        print(f"      initial_objects: {initial_objects}")
        print(f"      final_objects: {final_objects}")
    
    return passed

def test_workflow_state_consistency():
    """工作流状态一致性测试"""
    from backend.core.cache.multi_level_cache import L1Cache
    from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
    
    suite = DeepDefectDiscovery()
    cache = L1Cache(max_size=100)
    memory = UnifiedMemorySystem(InMemoryBackend())
    
    errors = []
    
    # 模拟复杂工作流
    workflow_id = str(uuid.uuid4())
    
    for step in range(20):
        try:
            # 更新工作流状态
            cache.set(f"workflow_{workflow_id}_step", step)
            cache.set(f"workflow_{workflow_id}_status", f"step_{step}")
            
            # 存储记忆
            asyncio.run(memory.store(
                f"workflow_{workflow_id}_memory_{step}",
                {"step": step, "timestamp": time.time()}
            ))
            
            # 验证状态一致性
            current_step = cache.get(f"workflow_{workflow_id}_step")
            current_status = cache.get(f"workflow_{workflow_id}_status")
            
            if current_step != step:
                errors.append(f"Step {step}: Expected {step}, got {current_step}")
            if current_status != f"step_{step}":
                errors.append(f"Step {step}: Expected step_{step}, got {current_status}")
                
        except Exception as e:
            errors.append(f"Step {step}: {str(e)}")
    
    passed = len(errors) == 0
    suite.record(
        "工作流状态一致性",
        passed,
        time.time() - suite.start_time,
        errors=errors
    )
    
    return passed

def test_extreme_boundary_conditions():
    """极端边界条件测试"""
    from backend.core.utils.validator import InputValidator
    
    suite = DeepDefectDiscovery()
    errors = []
    
    # 测试各种边界条件
    test_cases = [
        # 超长输入
        ("a" * 2000, False, "KEY_TOO_LONG"),
        # 空字符串
        ("", False, "EMPTY_KEY"),
        # 仅空白
        ("   ", False, "WHITESPACE_KEY"),
        # Unicode边界
        ("测试_unicode_123", True, None),
        # 特殊字符
        ("key-with-special_chars.123", True, None),
        # Null字节
        ("key\x00with\x00null", False, "INVALID_KEY"),
        # 正常键
        ("valid_key_123", True, None),
    ]
    
    for input_str, should_pass, expected_code in test_cases:
        try:
            is_valid, error = InputValidator.validate_cache_key(input_str)
            
            if should_pass and not is_valid:
                errors.append(f"Input '{input_str[:20]}...': Expected to pass but got {error.code if error else 'unknown'}")
            elif not should_pass and is_valid:
                errors.append(f"Input '{input_str[:20]}...': Expected to fail but passed")
            elif not should_pass and error and error.code != expected_code:
                errors.append(f"Input '{input_str[:20]}...': Expected code {expected_code}, got {error.code}")
        except Exception as e:
            errors.append(f"Input '{input_str[:20]}...': Exception: {str(e)}")
    
    passed = len(errors) == 0
    suite.record(
        "极端边界条件",
        passed,
        time.time() - suite.start_time,
        errors=errors
    )
    
    return passed

def test_agent_orchestration_stress():
    """Agent编排压力测试"""
    from backend.core.agents.multi_agent import MultiAgentOrchestrator, AgentTask
    
    suite = DeepDefectDiscovery()
    orchestrator = MultiAgentOrchestrator()
    errors = []
    
    # 模拟大量并发任务
    num_tasks = 500
    
    for i in range(num_tasks):
        try:
            task = AgentTask(
                task_id=str(uuid.uuid4()),
                task_type=["reasoning", "analysis", "synthesis", "planning"][i % 4],
                data={
                    "input": f"Task input {i}",
                    "priority": random.randint(1, 10),
                    "timestamp": time.time()
                },
                description=f"Complex task #{i}"
            )
            orchestrator.add_task(task)
        except Exception as e:
            errors.append(f"Task {i}: {str(e)}")
    
    # 验证任务状态
    pending_tasks = len(orchestrator.tasks)
    
    if pending_tasks != num_tasks:
        errors.append(f"Expected {num_tasks} tasks, got {pending_tasks}")
    
    passed = len(errors) == 0
    suite.record(
        "Agent编排压力测试",
        passed,
        time.time() - suite.start_time,
        errors=errors,
        performance={
            "total_tasks": num_tasks,
            "pending_tasks": pending_tasks,
            "error_count": len(errors)
        }
    )
    
    return passed

def test_concurrent_read_write_patterns():
    """并发读写模式测试"""
    from backend.core.cache.multi_level_cache import L1Cache
    
    suite = DeepDefectDiscovery()
    cache = L1Cache(max_size=500)
    errors = []
    read_count = [0]
    write_count = [0]
    lock = threading.Lock()
    
    def reader(reader_id, iterations):
        for i in range(iterations):
            try:
                key = f"shared_key_{i % 50}"
                value = cache.get(key)
                with lock:
                    read_count[0] += 1
            except Exception as e:
                errors.append(f"Reader {reader_id}: {str(e)}")
    
    def writer(writer_id, iterations):
        for i in range(iterations):
            try:
                key = f"shared_key_{i % 50}"
                value = f"writer_{writer_id}_value_{i}"
                cache.set(key, value, ttl=60)
                with lock:
                    write_count[0] += 1
            except Exception as e:
                errors.append(f"Writer {writer_id}: {str(e)}")
    
    # 启动5个读线程和5个写线程
    threads = []
    iterations = 500
    
    for i in range(5):
        threads.append(threading.Thread(target=reader, args=(i, iterations)))
        threads.append(threading.Thread(target=writer, args=(i, iterations)))
    
    suite.snapshot_memory("before_concurrent")
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    suite.snapshot_memory("after_concurrent")
    
    total_ops = read_count[0] + write_count[0]
    errors_count = len(errors)
    
    passed = errors_count == 0
    suite.record(
        "并发读写模式",
        passed,
        time.time() - suite.start_time,
        errors=[f"Found {errors_count} errors" if errors_count > 0 else ""],
        performance={
            "read_operations": read_count[0],
            "write_operations": write_count[0],
            "total_operations": total_ops,
            "error_count": errors_count
        }
    )
    
    return passed

def test_prompt_template_complex_scenarios():
    """提示模板复杂场景测试"""
    from tools.prompt_workbench.workbench import PromptWorkbench, PromptVariable
    
    suite = DeepDefectDiscovery()
    workbench = PromptWorkbench()
    errors = []
    
    # 创建多个提示模板
    for i in range(50):
        try:
            template = workbench.create_prompt(
                name=f"Template_{i}",
                description=f"Description for template {i}",
                content=f"Template content with {{variable_{i}}}",
                variables=[
                    PromptVariable(
                        name=f"variable_{i}",
                        type="string",
                        description=f"Variable {i}",
                        required=True
                    )
                ],
                tags=["test", f"category_{i % 5}"]
            )
            
            # 渲染模板
            rendered = workbench.render_prompt(
                template_id=template.id,
                variables={f"variable_{i}": f"Value_{i}"}
            )
            
            if not rendered:
                errors.append(f"Template {i}: Failed to render")
                
        except Exception as e:
            errors.append(f"Template {i}: {str(e)}")
    
    # 列出所有模板
    all_templates = workbench.list_prompts()
    
    if len(all_templates) != 50:
        errors.append(f"Expected 50 templates, got {len(all_templates)}")
    
    passed = len(errors) == 0
    suite.record(
        "提示模板复杂场景",
        passed,
        time.time() - suite.start_time,
        errors=errors,
        performance={
            "templates_created": 50,
            "templates_retrieved": len(all_templates)
        }
    )
    
    return passed

def test_data_integrity_under_load():
    """负载下的数据完整性测试"""
    from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
    
    suite = DeepDefectDiscovery()
    memory = UnifiedMemorySystem(InMemoryBackend())
    errors = []
    
    # 生成测试数据
    test_data = {
        f"key_{i}": {
            "id": i,
            "data": "".join(random.choices(string.ascii_letters, k=100)),
            "timestamp": time.time(),
            "checksum": sum(bytearray("".join(random.choices(string.ascii_letters, k=100)), 'utf-8'))
        }
        for i in range(1000)
    }
    
    # 存储数据
    start_store = time.time()
    for key, value in test_data.items():
        asyncio.run(memory.store(key, value))
    store_duration = time.time() - start_store
    
    # 验证数据完整性
    start_verify = time.time()
    for key, original_value in test_data.items():
        retrieved = asyncio.run(memory.retrieve(key))
        
        if retrieved is None:
            errors.append(f"Key {key}: Data missing")
        elif retrieved["id"] != original_value["id"]:
            errors.append(f"Key {key}: ID mismatch")
        elif retrieved["data"] != original_value["data"]:
            errors.append(f"Key {key}: Data corruption")
        elif retrieved["checksum"] != original_value["checksum"]:
            errors.append(f"Key {key}: Checksum mismatch")
            
    verify_duration = time.time() - start_verify
    
    passed = len(errors) == 0
    suite.record(
        "数据完整性测试",
        passed,
        time.time() - suite.start_time,
        errors=errors,
        performance={
            "store_duration": f"{store_duration:.2f}s",
            "verify_duration": f"{verify_duration:.2f}s",
            "total_keys": len(test_data),
            "error_count": len(errors)
        }
    )
    
    return passed

def main():
    print("=" * 80)
    print("NeuralAgent - 超深层缺陷挖掘与生产级集成测试")
    print("专注发现隐藏缺陷、性能问题、并发问题")
    print("=" * 80)
    print()
    
    suite = DeepDefectDiscovery()
    suite.start_time = time.time()
    
    tests = [
        ("并发竞态条件测试", test_cache_race_conditions),
        ("内存泄漏检测", test_memory_leak_detection),
        ("工作流状态一致性", test_workflow_state_consistency),
        ("极端边界条件", test_extreme_boundary_conditions),
        ("Agent编排压力测试", test_agent_orchestration_stress),
        ("并发读写模式", test_concurrent_read_write_patterns),
        ("提示模板复杂场景", test_prompt_template_complex_scenarios),
        ("数据完整性测试", test_data_integrity_under_load),
    ]
    
    print("\n" + "=" * 80)
    print("开始执行深层缺陷挖掘测试")
    print("=" * 80 + "\n")
    
    passed_count = 0
    for test_name, test_func in tests:
        print(f"\n{'=' * 80}")
        print(f"执行: {test_name}")
        print('=' * 80)
        
        try:
            if test_func():
                passed_count += 1
        except Exception as e:
            print(f"\n❌ 测试执行失败: {test_name}")
            print(f"错误: {str(e)}")
            print(traceback.format_exc())
    
    print("\n" + "=" * 80)
    print("深层缺陷挖掘测试总结")
    print("=" * 80)
    
    total = len(tests)
    print(f"\n总测试数: {total}")
    print(f"通过: {passed_count}")
    print(f"失败: {total - passed_count}")
    print(f"通过率: {passed_count / total * 100:.1f}%")
    
    print("\n详细结果:")
    for result in suite.results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} {result.name}: {result.duration:.2f}s")
        
        if result.errors:
            print(f"     Errors: {len(result.errors)}")
        if result.warnings:
            print(f"     Warnings: {len(result.warnings)}")
    
    if suite.memory_snapshots:
        print("\n内存快照:")
        for snapshot in suite.memory_snapshots:
            print(f"  [{snapshot['label']}] Objects: {snapshot['objects']}")
    
    print("\n" + "=" * 80)
    
    return 0 if passed_count == total else 1

if __name__ == "__main__":
    sys.exit(main())
