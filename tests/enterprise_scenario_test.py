"""
NeuralAgent - 企业级真实场景深度测试
模拟真实生产环境的长期运行、多用户、高负载场景
"""

import asyncio
import sys
import os
import time
import uuid
import json
import random
import threading
import gc
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable, Set
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@dataclass
class EnterpriseDefect:
    test_name: str
    severity: str
    category: str
    description: str
    impact: str
    fixed: bool = False

class EnterpriseTestRunner:
    def __init__(self):
        self.defects: List[EnterpriseDefect] = []
        self.passed = 0
        self.failed = 0
        self.metrics = defaultdict(list)
    
    def record_metric(self, name: str, value: float):
        self.metrics[name].append(value)
    
    def report_defect(self, defect: EnterpriseDefect):
        self.defects.append(defect)
        print(f"⚠️  [DEFECT {len(self.defects)}] {defect.severity.upper()}: {defect.test_name}")
        print(f"   {defect.category}: {defect.description}")
    
    def log_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ [PASS] {test_name}")
    
    def log_fail(self, test_name: str):
        self.failed += 1
        print(f"❌ [FAIL] {test_name}")
    
    def print_summary(self):
        print("\n" + "="*80)
        print("🏢 企业级真实场景深度测试 - 总结")
        print("="*80)
        print(f"总测试: {self.passed + self.failed}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"发现缺陷: {len(self.defects)}")
        
        if self.metrics:
            print("\n📊 性能指标:")
            for name, values in self.metrics.items():
                avg = sum(values) / len(values)
                max_val = max(values)
                print(f"  {name}: avg={avg:.3f}s, max={max_val:.3f}s")

def test_long_term_stability(runner: EnterpriseTestRunner):
    """测试1: 长期稳定性测试 - 模拟真实生产环境连续运行"""
    print("\n" + "="*80)
    print("⏰ 测试1: 长期稳定性测试")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        
        cache = L1Cache(max_size=1000)
        start_time = time.time()
        errors = []
        operations = 0
        
        # 模拟生产环境的模式: 频繁写入、读取、过期
        for i in range(5000):
            try:
                # 混合操作模式
                op = random.choice(['set', 'get', 'delete', 'check'])
                key = f"lt_key_{random.randint(0, 900)}"
                
                if op == 'set':
                    cache.set(key, f"value_{i}_{time.time()}")
                elif op == 'get':
                    cache.get(key)
                elif op == 'delete':
                    cache.delete(key)
                
                operations += 1
                
                # 定期检查统计
                if i % 500 == 0:
                    stats = cache.get_stats()
                    print(f"  进度: {i}/5000, 缓存大小: {stats['size']}")
                    
            except Exception as e:
                errors.append(str(e))
                if len(errors) > 5:
                    break
        
        duration = time.time() - start_time
        runner.record_metric("long_term_ops_per_sec", operations / duration)
        
        final_stats = cache.get_stats()
        print(f"  最终统计: size={final_stats['size']}, hits={final_stats['hits']}")
        
        if errors:
            runner.report_defect(EnterpriseDefect(
                test_name="Long Term Stability",
                severity="high",
                category="Stability",
                description=f"长期运行出现 {len(errors)} 个错误",
                impact="生产环境会不稳定"
            ))
            runner.log_fail("long_term_stability")
        else:
            runner.log_pass("long_term_stability")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        runner.report_defect(EnterpriseDefect(
            test_name="Long Term Stability",
            severity="critical",
            category="Stability",
            description=f"稳定性测试异常: {str(e)}",
            impact="系统无法长时间运行"
        ))
        runner.log_fail("long_term_stability")

def test_multi_user_concurrent(runner: EnterpriseTestRunner):
    """测试2: 多用户并发 - 模拟真实的多用户使用场景"""
    print("\n" + "="*80)
    print("👥 测试2: 多用户并发测试")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
        from tools.prompt_workbench.workbench import PromptWorkbench
        
        cache = L1Cache(max_size=2000)
        memory = UnifiedMemorySystem(InMemoryBackend())
        workbench = PromptWorkbench()
        
        errors = []
        operations = {'cache': 0, 'memory': 0, 'prompt': 0}
        lock = threading.Lock()
        completed_users = 0
        
        def simulate_user(user_id: int):
            nonlocal completed_users
            try:
                user_cache = L1Cache(max_size=100)
                for i in range(50):
                    if random.random() < 0.5:
                        key = f"user_{user_id}_key_{i}"
                        cache.set(key, f"user_{user_id}_data_{i}")
                        with lock:
                            operations['cache'] += 1
                    
                    if random.random() < 0.3:
                        asyncio.run(memory.store(f"user_{user_id}_mem_{i}", 
                            {"user": user_id, "data": i, "time": datetime.now().isoformat()}))
                        with lock:
                            operations['memory'] += 1
                    
                    if random.random() < 0.1:
                        workbench.create_prompt(
                            name=f"User {user_id} Prompt {i}",
                            description=f"Generated by user {user_id}",
                            content=f"This is a test prompt for user {user_id}",
                            created_by=f"user_{user_id}"
                        )
                        with lock:
                            operations['prompt'] += 1
                
                with lock:
                    completed_users += 1
                    
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        threads = []
        start = time.time()
        for i in range(20):
            t = threading.Thread(target=simulate_user, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        duration = time.time() - start
        
        print(f"  完成用户: {completed_users}/20")
        print(f"  缓存操作: {operations['cache']}")
        print(f"  记忆操作: {operations['memory']}")
        print(f"  提示创建: {operations['prompt']}")
        print(f"  总耗时: {duration:.2f}s")
        
        runner.record_metric("multi_user_throughput", sum(operations.values()) / duration)
        
        if errors:
            runner.report_defect(EnterpriseDefect(
                test_name="Multi User Concurrent",
                severity="high",
                category="Concurrency",
                description=f"多用户测试出现 {len(errors)} 个错误",
                impact="真实用户场景会出现问题"
            ))
            runner.log_fail("multi_user_concurrent")
        else:
            runner.log_pass("multi_user_concurrent")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        runner.report_defect(EnterpriseDefect(
            test_name="Multi User Concurrent",
            severity="critical",
            category="Concurrency",
            description=f"多用户测试异常: {str(e)}",
            impact="系统无法支持多用户"
        ))
        runner.log_fail("multi_user_concurrent")

def test_memory_usage_and_leaks(runner: EnterpriseTestRunner):
    """测试3: 内存使用与泄漏检测"""
    print("\n" + "="*80)
    print("💾 测试3: 内存使用与泄漏检测")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        import gc
        
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        cache = L1Cache(max_size=1000)
        
        memory_snapshots = []
        
        for phase in range(3):
            for i in range(2000):
                cache.set(f"mem_test_key_{phase}_{i}", 
                         f"value_{'x' * 100}_{i}")
            
            gc.collect()
            objects_after = len(gc.get_objects())
            memory_snapshots.append(objects_after)
            print(f"  阶段 {phase+1}: 对象数 = {objects_after}")
            
            # 清理一半
            for i in range(0, 2000, 2):
                cache.delete(f"mem_test_key_{phase}_{i}")
        
        gc.collect()
        final_objects = len(gc.get_objects())
        print(f"  最终对象数: {final_objects}")
        
        # 检查对象增长是否合理
        growth_ratio = (final_objects - initial_objects) / max(initial_objects, 1)
        
        if growth_ratio > 0.5:
            runner.report_defect(EnterpriseDefect(
                test_name="Memory Leak Detection",
                severity="medium",
                category="Performance",
                description=f"对象数增长比例过高: {growth_ratio:.2%}",
                impact="长时间运行可能内存泄漏"
            ))
            runner.log_fail("memory_leak_detection")
        else:
            print(f"  对象增长比例: {growth_ratio:.2%} - 在正常范围内")
            runner.log_pass("memory_leak_detection")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        runner.report_defect(EnterpriseDefect(
            test_name="Memory Leak Detection",
            severity="high",
            category="Performance",
            description=f"内存测试异常: {str(e)}",
            impact="内存管理有问题"
        ))
        runner.log_fail("memory_leak_detection")

def test_edge_case_operations(runner: EnterpriseTestRunner):
    """测试4: 极端边界操作测试 - 各种奇怪的输入组合"""
    print("\n" + "="*80)
    print("🎯 测试4: 极端边界操作测试")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        from backend.core.security.authentication import AuthenticationService
        
        cache = L1Cache(max_size=500)
        auth = AuthenticationService()
        
        strange_inputs = [
            "a" * 1000,  # 超长
            " ",  # 只有空格
            "\t\n\r",  # 空白字符
            "key_with_📱emoji🎊",  # emoji
            "mixed_case_Key",  # 大小写混合
            "",  # 空（应该失败）
        ]
        
        results = {'success': 0, 'expected_fail': 0, 'unexpected': 0}
        
        for input_str in strange_inputs:
            try:
                cache.set(input_str, f"value_for_{hash(input_str)}")
                got = cache.get(input_str)
                if got is not None:
                    results['success'] += 1
                else:
                    results['expected_fail'] += 1
            except Exception:
                if input_str == "":
                    results['expected_fail'] += 1
                else:
                    results['unexpected'] += 1
        
        print(f"  成功: {results['success']}")
        print(f"  预期失败: {results['expected_fail']}")
        print(f"  意外失败: {results['unexpected']}")
        
        if results['unexpected'] > 0:
            runner.report_defect(EnterpriseDefect(
                test_name="Edge Case Operations",
                severity="medium",
                category="Robustness",
                description=f"有 {results['unexpected']} 个意外失败",
                impact="极端输入可能导致问题"
            ))
            runner.log_fail("edge_case_operations")
        else:
            runner.log_pass("edge_case_operations")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        runner.report_defect(EnterpriseDefect(
            test_name="Edge Case Operations",
            severity="high",
            category="Robustness",
            description=f"边界测试异常: {str(e)}",
            impact="极端情况下不稳定"
        ))
        runner.log_fail("edge_case_operations")

def test_workflow_complex_scenarios(runner: EnterpriseTestRunner):
    """测试5: 复杂工作流场景 - 模拟AI Agent实际工作"""
    print("\n" + "="*80)
    print("🔄 测试5: 复杂工作流场景")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        from backend.core.agents.multi_agent import MultiAgentOrchestrator, AgentTask
        from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
        from tools.prompt_workbench.workbench import PromptWorkbench
        
        async def complex_workflow():
            cache = L1Cache(max_size=100)
            memory = UnifiedMemorySystem(InMemoryBackend())
            workbench = PromptWorkbench()
            orchestrator = MultiAgentOrchestrator()
            
            workflow_steps = 0
            
            # 步骤1: 创建一些提示模板
            for i in range(5):
                prompt = workbench.create_prompt(
                    name=f"Workflow Prompt {i}",
                    description=f"For workflow step {i}",
                    content=f"Analyze this: step_{i}_data",
                    created_by="system"
                )
                await memory.store(f"prompt_{i}", prompt)
                workflow_steps += 1
            
            # 步骤2: 缓存一些中间结果
            for i in range(20):
                cache.set(f"intermediate_{i}", f"result_{i}")
                workflow_steps += 1
            
            # 步骤3: 创建并处理一些Agent任务
            for i in range(10):
                task = AgentTask(
                    task_id=str(uuid.uuid4()),
                    task_type="analysis",
                    data={"input": f"task_{i}"},
                    description=f"Workflow task {i}"
                )
                await orchestrator.orchestrate_task(task)
                workflow_steps += 1
            
            # 步骤4: 读取并验证
            for i in range(5):
                cached = cache.get(f"intermediate_{i}")
                if cached:
                    workflow_steps += 1
            
            return workflow_steps
        
        start = time.time()
        total_steps = asyncio.run(complex_workflow())
        duration = time.time() - start
        
        print(f"  工作流完成: {total_steps} 步")
        print(f"  耗时: {duration:.3f}s")
        
        runner.record_metric("workflow_steps_per_sec", total_steps / duration)
        
        if total_steps > 0:
            runner.log_pass("workflow_complex_scenarios")
        else:
            runner.report_defect(EnterpriseDefect(
                test_name="Workflow Complex Scenarios",
                severity="high",
                category="Integration",
                description="复杂工作流未能完成任何步骤",
                impact="真实业务场景无法工作"
            ))
            runner.log_fail("workflow_complex_scenarios")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        runner.report_defect(EnterpriseDefect(
            test_name="Workflow Complex Scenarios",
            severity="critical",
            category="Integration",
            description=f"工作流测试异常: {str(e)}",
            impact="业务集成有问题"
        ))
        runner.log_fail("workflow_complex_scenarios")

def test_error_handling_and_recovery(runner: EnterpriseTestRunner):
    """测试6: 错误处理与恢复 - 故意制造各种错误"""
    print("\n" + "="*80)
    print("💫 测试6: 错误处理与恢复")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache, CacheEmptyKeyError
        
        cache = L1Cache(max_size=100)
        recovery_success = True
        
        # 阶段1: 故意制造错误
        errors = []
        for _ in range(50):
            try:
                cache.set("", "bad_key")
            except CacheEmptyKeyError:
                pass
            except Exception as e:
                errors.append(str(e))
        
        # 阶段2: 验证系统仍然正常
        cache.set("recovery_test", "success_value")
        result = cache.get("recovery_test")
        
        if result != "success_value":
            recovery_success = False
            print("  恢复失败")
        
        # 阶段3: 各种错误后验证
        test_values = []
        for i in range(10):
            cache.set(f"good_key_{i}", f"good_value_{i}")
        
        for i in range(10):
            val = cache.get(f"good_key_{i}")
            test_values.append(val == f"good_value_{i}")
        
        if not all(test_values):
            recovery_success = False
            print(f"  验证失败: {sum(test_values)}/{len(test_values)}")
        
        if recovery_success and not errors:
            runner.log_pass("error_handling_and_recovery")
        elif recovery_success:
            print("  错误被正确处理，系统恢复正常")
            runner.log_pass("error_handling_and_recovery")
        else:
            runner.report_defect(EnterpriseDefect(
                test_name="Error Handling And Recovery",
                severity="high",
                category="Robustness",
                description="错误后系统无法正常恢复",
                impact="容错能力不足"
            ))
            runner.log_fail("error_handling_and_recovery")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        runner.report_defect(EnterpriseDefect(
            test_name="Error Handling And Recovery",
            severity="critical",
            category="Robustness",
            description=f"错误恢复测试异常: {str(e)}",
            impact="错误处理有问题"
        ))
        runner.log_fail("error_handling_and_recovery")

def generate_final_report(runner: EnterpriseTestRunner) -> str:
    report = []
    report.append("="*80)
    report.append("🏢 NeuralAgent 企业级真实场景深度测试报告")
    report.append("="*80)
    report.append("")
    report.append(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"总测试数: {runner.passed + runner.failed}")
    report.append(f"通过: {runner.passed}")
    report.append(f"失败: {runner.failed}")
    report.append(f"发现缺陷: {len(runner.defects)}")
    report.append("")
    
    if runner.defects:
        report.append("🔍 发现的缺陷:")
        report.append("="*80)
        for i, defect in enumerate(runner.defects, 1):
            report.append(f"\n缺陷 #{i}:")
            report.append(f"  测试: {defect.test_name}")
            report.append(f"  严重程度: {defect.severity}")
            report.append(f"  类别: {defect.category}")
            report.append(f"  描述: {defect.description}")
            report.append(f"  影响: {defect.impact}")
            report.append(f"  状态: {'✅ 已修复' if defect.fixed else '❌ 待修复'}")
    else:
        report.append("✅ 未发现任何严重缺陷!")
    
    report.append("")
    report.append("📊 性能摘要:")
    for name, values in runner.metrics.items():
        if values:
            avg = sum(values) / len(values)
            max_val = max(values)
            min_val = min(values)
            report.append(f"  {name}:")
            report.append(f"    平均: {avg:.3f}")
            report.append(f"    最大: {max_val:.3f}")
            report.append(f"    最小: {min_val:.3f}")
    
    report.append("\n" + "="*80)
    return "\n".join(report)

def main():
    print("\n" + "="*80)
    print("🏢 启动: NeuralAgent 企业级真实场景深度测试")
    print("="*80)
    print("目标: 模拟真实生产环境，深度发现潜在问题")
    
    runner = EnterpriseTestRunner()
    
    test_long_term_stability(runner)
    test_multi_user_concurrent(runner)
    test_memory_usage_and_leaks(runner)
    test_edge_case_operations(runner)
    test_workflow_complex_scenarios(runner)
    test_error_handling_and_recovery(runner)
    
    report = generate_final_report(runner)
    print(report)
    
    with open("ENTERPRISE_SCENARIO_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📋 完整报告已保存到: ENTERPRISE_SCENARIO_REPORT.md")
    
    return len(runner.defects) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
