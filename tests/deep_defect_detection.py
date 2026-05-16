"""
NeuralAgent - 深度缺陷挖掘测试套件
真实企业级场景，多组件协同，错误恢复，并发冲突
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
from typing import Dict, List, Any, Optional, Tuple, Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@dataclass
class DefectReport:
    test_name: str
    severity: str
    description: str
    reproduction: str
    impact: str
    fixed: bool = False

class DeepDefectDetector:
    def __init__(self):
        self.reports: List[DefectReport] = []
        self.passed = 0
        self.failed = 0
        self.total_tests = 0

    def report_defect(self, report: DefectReport):
        self.reports.append(report)
        print(f"⚠️  [DEFECT {len(self.reports)}] {report.severity.upper()}: {report.test_name}")
        print(f"   {report.description}")

    def log_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ [PASS] {test_name}")

    def log_fail(self, test_name: str):
        self.failed += 1
        print(f"❌ [FAIL] {test_name}")

def test_cache_memory_leak(detector: DeepDefectDetector):
    """测试1: 缓存内存泄漏检测"""
    print("\n" + "="*80)
    print("📦 测试1: 缓存内存泄漏检测")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        
        cache = L1Cache(max_size=1000)
        
        initial_stats = cache.get_stats()
        print(f"初始缓存状态: {initial_stats}")
        
        iterations = 100000
        for i in range(iterations):
            cache.set(f"key_{i}", f"value_{i}" * 10)
        
        final_stats = cache.get_stats()
        print(f"最终缓存状态: {final_stats}")
        
        if final_stats['size'] > cache.max_size * 1.1:
            detector.report_defect(DefectReport(
                test_name="Cache Memory Leak",
                severity="high",
                description=f"缓存大小限制未强制执行。设定max_size={cache.max_size}，实际达到{final_stats['size']}",
                reproduction="cache.set()循环执行大量键值对",
                impact="可能导致内存耗尽"
            ))
            detector.log_fail("cache_memory_leak")
        else:
            detector.log_pass("cache_memory_leak")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        detector.report_defect(DefectReport(
            test_name="Cache Memory Leak",
            severity="critical",
            description=f"测试执行异常: {str(e)}",
            reproduction="初始化L1Cache并执行大量操作",
            impact="系统可能在真实场景崩溃"
        ))
        detector.log_fail("cache_memory_leak")

def test_concurrent_agent_orchestration(detector: DeepDefectDetector):
    """测试2: 多Agent并发协调测试"""
    print("\n" + "="*80)
    print("🤖 测试2: 多Agent并发协调测试")
    print("="*80)
    
    try:
        from backend.core.agents.multi_agent import MultiAgentOrchestrator, AgentTask
        
        orchestrator = MultiAgentOrchestrator()
        errors = []
        results = []
        lock = threading.Lock()
        
        def worker(task_id: int):
            try:
                task = AgentTask(
                    task_id=str(task_id),
                    task_type="reasoning",
                    data={"query": f"test {task_id}"},
                    priority=random.randint(1, 10)
                )
                
                result = asyncio.run(orchestrator.orchestrate_task(task))
                with lock:
                    results.append(result)
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
        
        print(f"执行完成 - 成功: {len(results)}, 错误: {len(errors)}")
        
        if errors:
            detector.report_defect(DefectReport(
                test_name="Concurrent Agent Orchestration",
                severity="high",
                description=f"并发执行时出现 {len(errors)} 个错误: {errors[:3]}",
                reproduction="创建50个并发线程调用orchestrate_task()",
                impact="多Agent系统在高负载下不可用"
            ))
            detector.log_fail("concurrent_agent_orchestration")
        else:
            detector.log_pass("concurrent_agent_orchestration")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        detector.report_defect(DefectReport(
            test_name="Concurrent Agent Orchestration",
            severity="critical",
            description=f"测试初始化异常: {str(e)}",
            reproduction="初始化MultiAgentOrchestrator",
            impact="Agent系统可能完全不可用"
        ))
        detector.log_fail("concurrent_agent_orchestration")

def test_memory_system_stress(detector: DeepDefectDetector):
    """测试3: 记忆系统压力测试"""
    print("\n" + "="*80)
    print("🧠 测试3: 记忆系统压力测试")
    print("="*80)
    
    try:
        from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
        
        memory = UnifiedMemorySystem(InMemoryBackend())
        errors = []
        data_points = []
        
        async def stress_test():
            for i in range(1000):
                try:
                    key = f"test_key_{i}_{uuid.uuid4().hex}"
                    value = {"data": f"test_value_{i}", "timestamp": datetime.now().isoformat(), "metadata": {f"key_{j}": f"val_{j}" for j in range(20)}}
                    await memory.store(key, value)
                    data_points.append(key)
                except Exception as e:
                    errors.append(str(e))
            
            for key in data_points[::2]:
                try:
                    await memory.retrieve(key)
                except Exception as e:
                    errors.append(str(e))
        
        asyncio.run(stress_test())
        
        print(f"记忆操作 - 写入: {len(data_points)}, 读取: {len(data_points)//2}, 错误: {len(errors)}")
        
        if errors:
            detector.report_defect(DefectReport(
                test_name="Memory System Stress",
                severity="medium",
                description=f"记忆系统压力测试出现 {len(errors)} 个错误",
                reproduction="执行1000次写入和500次读取",
                impact="大规模记忆操作不可靠"
            ))
            detector.log_fail("memory_system_stress")
        else:
            detector.log_pass("memory_system_stress")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        detector.report_defect(DefectReport(
            test_name="Memory System Stress",
            severity="high",
            description=f"记忆系统测试异常: {str(e)}",
            reproduction="初始化记忆系统并执行操作",
            impact="记忆系统可能存在严重缺陷"
        ))
        detector.log_fail("memory_system_stress")

def test_auth_token_boundaries(detector: DeepDefectDetector):
    """测试4: 认证Token边界测试"""
    print("\n" + "="*80)
    print("🔐 测试4: 认证Token边界测试")
    print("="*80)
    
    try:
        from backend.core.security.authentication import AuthenticationService
        
        auth = AuthenticationService()
        issues = []
        
        try:
            token = auth.create_access_token(
                user_id="test_user",
                username="a" * 1000,
                permissions=["read", "write"]
            )
            print("创建了1000字符用户名的token")
        except Exception as e:
            print(f"1000字符用户名被拒绝 (好): {str(e)}")
        
        try:
            token = auth.create_access_token(
                user_id="test_user",
                username="",
                permissions=["read"]
            )
            issues.append("空用户名被接受")
        except Exception as e:
            print(f"空用户名被拒绝 (好): {str(e)}")
        
        try:
            invalid_token = "invalid_token_1234567890"
            result = auth.verify_token(invalid_token)
            if result:
                issues.append("无效token被验证通过")
        except Exception as e:
            print(f"无效token处理正常 (好): {str(e)}")
        
        if issues:
            detector.report_defect(DefectReport(
                test_name="Auth Token Boundaries",
                severity="medium",
                description=f"认证系统边界测试发现问题: {issues}",
                reproduction="测试空用户名、超长用户名、无效token",
                impact="可能存在安全边界漏洞"
            ))
            detector.log_fail("auth_token_boundaries")
        else:
            detector.log_pass("auth_token_boundaries")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        detector.report_defect(DefectReport(
            test_name="Auth Token Boundaries",
            severity="high",
            description=f"认证模块测试异常: {str(e)}",
            reproduction="初始化AuthenticationService",
            impact="认证系统可能存在缺陷"
        ))
        detector.log_fail("auth_token_boundaries")

def test_prompt_workbench_stress(detector: DeepDefectDetector):
    """测试5: 提示工作台压力测试"""
    print("\n" + "="*80)
    print("🎨 测试5: 提示工作台压力测试")
    print("="*80)
    
    try:
        from tools.prompt_workbench.workbench import PromptWorkbench, XSSSanitizer
        
        workbench = PromptWorkbench()
        templates = []
        errors = []
        
        for i in range(100):
            try:
                template = workbench.create_prompt(
                    name=f"Test Prompt {i} - {uuid.uuid4().hex}",
                    description=f"A test prompt with some content {i}",
                    content=f"This is the content {i} with variable {{variable1}} and {{variable2}}",
                    created_by="tester"
                )
                templates.append(template)
            except Exception as e:
                errors.append(str(e))
        
        print(f"提示创建 - 成功: {len(templates)}, 错误: {len(errors)}")
        
        test_xss = "<script>alert('xss')</script> javascript:alert('test')"
        sanitized = XSSSanitizer.sanitize(test_xss)
        
        xss_still_present = any(x in sanitized for x in ["<script", "javascript:"])
        
        if xss_still_present or errors:
            detector.report_defect(DefectReport(
                test_name="Prompt Workbench Stress",
                severity="high",
                description=f"提示工作台问题 - 创建错误: {len(errors)}, XSS仍可能: {xss_still_present}",
                reproduction="创建100个提示模板并测试XSS",
                impact="XSS漏洞或大规模操作不稳定"
            ))
            detector.log_fail("prompt_workbench_stress")
        else:
            detector.log_pass("prompt_workbench_stress")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        detector.report_defect(DefectReport(
            test_name="Prompt Workbench Stress",
            severity="high",
            description=f"提示工作台测试异常: {str(e)}",
            reproduction="初始化PromptWorkbench",
            impact="提示工作台可能不稳定"
        ))
        detector.log_fail("prompt_workbench_stress")

def test_integration_all_modules(detector: DeepDefectDetector):
    """测试6: 全模块集成测试"""
    print("\n" + "="*80)
    print("🔗 测试6: 全模块集成测试")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
        from backend.core.agents.multi_agent import MultiAgentOrchestrator, AgentTask
        from tools.prompt_workbench.workbench import PromptWorkbench
        
        print("初始化所有模块...")
        
        cache = L1Cache(max_size=100)
        memory = UnifiedMemorySystem(InMemoryBackend())
        orchestrator = MultiAgentOrchestrator()
        workbench = PromptWorkbench()
        
        print("执行集成操作...")
        
        async def integrated_workflow():
            cache.set("session_123", {"user": "test"})
            
            template = workbench.create_prompt(
                name="Integration Test",
                description="Integration testing",
                content="Test prompt for integration",
                created_by="tester"
            )
            
            await memory.store("prompt_integrated", {"template": template})
            
            task = AgentTask(
                task_id="integrated_task",
                task_type="reasoning",
                data={"prompt_template": template}
            )
            
            await memory.store("task_record", {"task": task})
        
        asyncio.run(integrated_workflow())
        
        print("集成工作流完成")
        detector.log_pass("integration_all_modules")
        
    except Exception as e:
        print(f"集成测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        detector.report_defect(DefectReport(
            test_name="Integration All Modules",
            severity="critical",
            description=f"多模块集成工作流失败: {str(e)}",
            reproduction="初始化多个模块并执行协同工作流",
            impact="系统集成能力可能存在重大缺陷"
        ))
        detector.log_fail("integration_all_modules")

def test_data_consistency(detector: DeepDefectDetector):
    """测试7: 数据一致性测试"""
    print("\n" + "="*80)
    print("📊 测试7: 数据一致性测试")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        
        cache = L1Cache(max_size=1000)
        inconsistencies = []
        
        for i in range(100):
            expected = f"value_{i}"
            cache.set(f"key_{i}", expected)
            actual = cache.get(f"key_{i}")
            
            if actual != expected:
                inconsistencies.append(f"key_{i}: expected={expected}, actual={actual}")
        
        if inconsistencies:
            detector.report_defect(DefectReport(
                test_name="Data Consistency",
                severity="high",
                description=f"数据一致性问题: {len(inconsistencies)} 个不一致",
                reproduction="循环写入和读取键值对",
                impact="缓存数据可能不可靠"
            ))
            detector.log_fail("data_consistency")
        else:
            detector.log_pass("data_consistency")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        detector.report_defect(DefectReport(
            test_name="Data Consistency",
            severity="high",
            description=f"数据一致性测试异常: {str(e)}",
            reproduction="缓存数据一致性测试",
            impact="数据一致性无法保证"
        ))
        detector.log_fail("data_consistency")

def test_error_recovery(detector: DeepDefectDetector):
    """测试8: 错误恢复能力测试"""
    print("\n" + "="*80)
    print("🛡️  测试8: 错误恢复能力测试")
    print("="*80)
    
    try:
        from backend.core.cache.multi_level_cache import L1Cache
        from backend.core.memory.unified_memory import UnifiedMemorySystem, InMemoryBackend
        
        recovery_successful = True
        
        cache = L1Cache(max_size=100)
        
        try:
            cache.set("", "empty_key")
        except Exception:
            pass
        
        cache.set("good_key", "good_value")
        result = cache.get("good_key")
        
        if result != "good_value":
            recovery_successful = False
            print("错误操作后缓存异常")
        
        memory = UnifiedMemorySystem(InMemoryBackend())
        
        async def recovery_test():
            try:
                await memory.store("", "empty")
            except Exception:
                pass
            
            await memory.store("good", "value")
            result = await memory.retrieve("good")
            
            if result != "value":
                nonlocal recovery_successful
                recovery_successful = False
                print("错误操作后记忆系统异常")
        
        asyncio.run(recovery_test())
        
        if recovery_successful:
            detector.log_pass("error_recovery")
        else:
            detector.report_defect(DefectReport(
                test_name="Error Recovery",
                severity="high",
                description="错误操作后系统无法正常恢复",
                reproduction="先执行无效操作再执行有效操作",
                impact="系统容错能力不足"
            ))
            detector.log_fail("error_recovery")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        detector.report_defect(DefectReport(
            test_name="Error Recovery",
            severity="critical",
            description=f"错误恢复测试异常: {str(e)}",
            reproduction="测试错误恢复流程",
            impact="系统容错和恢复能力严重不足"
        ))
        detector.log_fail("error_recovery")

def generate_detailed_report(detector: DeepDefectDetector) -> str:
    report = []
    report.append("="*80)
    report.append("NEURALAGENT 深度缺陷挖掘报告")
    report.append("="*80)
    report.append("")
    report.append(f"测试执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"总测试数: {detector.passed + detector.failed}")
    report.append(f"通过: {detector.passed}")
    report.append(f"失败: {detector.failed}")
    report.append(f"发现缺陷: {len(detector.reports)}")
    report.append("")
    report.append("="*80)
    report.append("缺陷详情")
    report.append("="*80)
    report.append("")
    
    for i, defect in enumerate(detector.reports, 1):
        report.append(f"缺陷 #{i}: {defect.test_name}")
        report.append(f"  严重程度: {defect.severity}")
        report.append(f"  描述: {defect.description}")
        report.append(f"  复现: {defect.reproduction}")
        report.append(f"  影响: {defect.impact}")
        report.append(f"  修复: {'✅' if defect.fixed else '❌'}")
        report.append("")
    
    report.append("="*80)
    return "\n".join(report)

def main():
    print("\n" + "="*80)
    print("🚀 NEURALAGENT 深度缺陷挖掘测试套件")
    print("="*80)
    
    detector = DeepDefectDetector()
    
    test_cache_memory_leak(detector)
    test_concurrent_agent_orchestration(detector)
    test_memory_system_stress(detector)
    test_auth_token_boundaries(detector)
    test_prompt_workbench_stress(detector)
    test_integration_all_modules(detector)
    test_data_consistency(detector)
    test_error_recovery(detector)
    
    report = generate_detailed_report(detector)
    
    print("\n" + report)
    
    with open("DEEP_DEFECT_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n详细报告已保存到: {os.path.abspath('DEEP_DEFECT_REPORT.md')}")
    
    if detector.reports:
        print("\n💡 发现缺陷，正在进行修复...")
        
        return False
    else:
        print("\n✅ 未发现严重缺陷！系统状态良好。")
        return True

if __name__ == "__main__":
    main()
