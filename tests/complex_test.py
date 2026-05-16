"""
NeuralAgent 复杂高难度实践测试
挑战边界条件、并发冲突、数据一致性等复杂场景
"""

import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import sys
import os
import traceback
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestResult:
    """测试结果"""

    def __init__(self, name: str, passed: bool, message: str = "", details: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details
        self.timestamp = time.time()


class ComplexIntegrationTester:
    """复杂集成测试器"""

    def __init__(self):
        self.results: List[TestResult] = []

    def test_module_imports(self) -> TestResult:
        """测试1: 核心模块导入测试"""
        print("\n" + "="*80)
        print("🔬 测试1: 核心模块导入测试")
        print("="*80)

        modules_to_test = [
            ("Agent Framework", "backend.core.agents.base", "Agent"),
            ("Memory System", "backend.core.memory.unified", "UnifiedMemoryStore"),
            ("Vector Store", "backend.core.vector_store.milvus", "MilvusVectorStore"),
            ("Cache Optimizer", "backend.core.cache.optimizer", "L1MemoryCache"),
            ("Auth Service", "backend.core.security.authentication", "AuthenticationService"),
            ("Alert Manager", "backend.core.monitoring.advanced", "AlertManager"),
            ("Prompt Workbench", "tools.prompt_workbench.workbench", "PromptWorkbench"),
            ("CLI Tools", "cli", "cli"),
        ]

        failed = []
        passed_count = 0

        for name, module_path, class_name in modules_to_test:
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                print(f"✅ {name}: OK")
                passed_count += 1
            except Exception as e:
                print(f"❌ {name}: {str(e)[:50]}")
                failed.append(f"{name}: {str(e)}")

        if failed:
            return TestResult(
                name="模块导入测试",
                passed=False,
                message=f"失败 {len(failed)}/{len(modules_to_test)}",
                details=failed
            )
        else:
            return TestResult(
                name="模块导入测试",
                passed=True,
                message=f"全部通过 {passed_count}/{len(modules_to_test)}"
            )

    def test_boundary_conditions(self) -> TestResult:
        """测试2: 边界条件测试"""
        print("\n" + "="*80)
        print("🔬 测试2: 边界条件测试")
        print("="*80)

        issues = []

        try:
            print("\n2.1 测试空输入...")
            from backend.core.cache.optimizer import L1MemoryCache
            cache = L1MemoryCache()

            try:
                cache.set("", "empty_key_value")
                print("⚠️  空键未被拒绝")
                issues.append("空键未验证")
            except Exception as e:
                print(f"✅ 空键正确拒绝: {type(e).__name__}")

            try:
                cache.set("valid_key", "")
                print("⚠️  空值未被拒绝")
                issues.append("空值未验证")
            except Exception as e:
                print(f"✅ 空值正确拒绝: {type(e).__name__}")

        except Exception as e:
            issues.append(f"缓存边界测试失败: {str(e)}")

        try:
            print("\n2.2 测试超大数据...")
            from backend.core.security.authentication import AuthenticationService, User

            auth = AuthenticationService()

            try:
                large_username = "x" * 10000
                user = User(
                    id=str(uuid.uuid4()),
                    username=large_username,
                    email="test@test.com",
                    hashed_password="hash"
                )
                tokens = auth.create_tokens(user)
                print("⚠️  超长用户名未被拒绝")
                issues.append("超长用户名未验证")
            except Exception as e:
                print(f"✅ 超长用户名正确拒绝: {type(e).__name__}")

        except Exception as e:
            issues.append(f"认证边界测试失败: {str(e)}")

        try:
            print("\n2.3 测试特殊字符...")
            from tools.prompt_workbench.workbench import PromptWorkbench

            workbench = PromptWorkbench()

            try:
                template = workbench.create_prompt(
                    name="<script>alert('xss')</script>",
                    description="XSS test",
                    content="Hello {name}!"
                )
                print("⚠️  XSS 风险未被过滤")
                issues.append("XSS风险未处理")
            except Exception as e:
                print(f"✅ XSS 风险正确处理: {type(e).__name__}")

        except Exception as e:
            issues.append(f"提示模板边界测试失败: {str(e)}")

        if issues:
            return TestResult(
                name="边界条件测试",
                passed=False,
                message=f"发现 {len(issues)} 个边界问题",
                details=issues
            )
        else:
            return TestResult(
                name="边界条件测试",
                passed=True,
                message="所有边界条件正确处理"
            )

    def test_concurrent_conflicts(self) -> TestResult:
        """测试3: 并发冲突测试"""
        print("\n" + "="*80)
        print("🔬 测试3: 并发冲突测试")
        print("="*80)

        issues = []
        errors = []

        def concurrent_cache_worker(worker_id: int):
            try:
                from backend.core.cache.optimizer import L1MemoryCache

                cache = L1MemoryCache(max_size=100, ttl=60)

                for i in range(100):
                    key = f"concurrent_key_{i % 10}"
                    value = f"worker_{worker_id}_value_{i}"

                    try:
                        cache.set(key, value)
                        result = cache.get(key)

                        if result != value:
                            errors.append(f"Worker {worker_id}: 数据不一致 (expected {value}, got {result})")
                    except Exception as e:
                        errors.append(f"Worker {worker_id}: {str(e)}")

                return "success"
            except Exception as e:
                errors.append(f"Worker {worker_id} 初始化失败: {str(e)}")
                return "failed"

        print("\n3.1 测试 20 个并发写入...")
        workers = 20
        iterations = 100

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(concurrent_cache_worker, i) for i in range(workers)]
            results = [f.result() for f in as_completed(futures)]

        successes = results.count("success")
        failures = results.count("failed")

        print(f"   成功: {successes}/{workers}")
        print(f"   失败: {failures}/{workers}")

        if failures > 0:
            issues.append(f"并发写入失败: {failures} workers")

        if errors:
            print(f"   发现 {len(errors)} 个错误")
            issues.extend(errors[:5])

        def concurrent_memory_worker(worker_id: int):
            try:
                from backend.core.memory.unified import UnifiedMemoryStore

                memory = UnifiedMemoryStore()

                for i in range(50):
                    key = f"mem_concurrent_{i % 20}"
                    value = f"memory_worker_{worker_id}_{i}"

                    try:
                        memory.add(key, value, "concurrent_test")
                        result = memory.get(key)
                    except Exception as e:
                        errors.append(f"Memory Worker {worker_id}: {str(e)}")

                return "success"
            except Exception as e:
                return "failed"

        print("\n3.2 测试并发记忆操作...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_memory_worker, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        print(f"   成功: {results.count('success')}/10")
        print(f"   失败: {results.count('failed')}/10")

        if issues:
            return TestResult(
                name="并发冲突测试",
                passed=False,
                message=f"发现 {len(issues)} 个并发问题",
                details=issues[:10]
            )
        else:
            return TestResult(
                name="并发冲突测试",
                passed=True,
                message="并发操作全部成功"
            )

    def test_data_consistency(self) -> TestResult:
        """测试4: 数据一致性测试"""
        print("\n" + "="*80)
        print("🔬 测试4: 数据一致性测试")
        print("="*80)

        issues = []

        try:
            print("\n4.1 测试缓存数据一致性...")
            from backend.core.cache.optimizer import L1MemoryCache

            cache = L1MemoryCache()

            cache.set("consistency_key", "initial_value")

            cache.set("consistency_key", "updated_value")

            result = cache.get("consistency_key")

            if result == "updated_value":
                print("✅ 缓存更新一致性: OK")
            else:
                print(f"❌ 缓存更新一致性失败: {result}")
                issues.append(f"缓存数据不一致: {result}")

            cache.delete("consistency_key")
            result_after_delete = cache.get("consistency_key")

            if result_after_delete is None:
                print("✅ 缓存删除一致性: OK")
            else:
                print(f"❌ 缓存删除一致性失败: {result_after_delete}")
                issues.append("缓存删除后仍存在")

        except Exception as e:
            issues.append(f"缓存一致性测试失败: {str(e)}")

        try:
            print("\n4.2 测试令牌数据一致性...")
            from backend.core.security.authentication import AuthenticationService, User

            auth = AuthenticationService()

            user = User(
                id=str(uuid.uuid4()),
                username="consistency_test_user",
                email="consistency@test.com",
                hashed_password="test_hash"
            )

            tokens = auth.create_tokens(user)

            access_token = tokens["access_token"]

            payload1 = auth.verify_token(access_token)
            payload2 = auth.verify_token(access_token)

            if payload1 == payload2 and payload1 is not None:
                print("✅ 令牌验证一致性: OK")
            else:
                issues.append("令牌验证结果不一致")

            user_id = auth.get_user_id_from_token(access_token)

            if user_id == user.id:
                print("✅ 用户ID提取一致性: OK")
            else:
                issues.append(f"用户ID不一致: expected {user.id}, got {user_id}")

        except Exception as e:
            issues.append(f"令牌一致性测试失败: {str(e)}")

        if issues:
            return TestResult(
                name="数据一致性测试",
                passed=False,
                message=f"发现 {len(issues)} 个一致性问题",
                details=issues
            )
        else:
            return TestResult(
                name="数据一致性测试",
                passed=True,
                message="所有数据一致性测试通过"
            )

    def test_error_recovery(self) -> TestResult:
        """测试5: 错误恢复测试"""
        print("\n" + "="*80)
        print("🔬 测试5: 错误恢复测试")
        print("="*80)

        issues = []

        try:
            print("\n5.1 测试无效输入后的恢复...")
            from backend.core.security.enhanced import SecurityValidator

            valid, msg = SecurityValidator.validate_password_strength("Valid123!")
            assert valid == True
            print("✅ 有效密码验证通过")

            invalid, msg = SecurityValidator.validate_password_strength("weak")
            assert invalid == False
            print("✅ 无效密码验证正确拒绝")

            valid_after, msg = SecurityValidator.validate_password_strength("NewPass123!")
            assert valid_after == True
            print("✅ 拒绝后继续工作正常")

        except Exception as e:
            issues.append(f"错误恢复测试失败: {str(e)}")

        try:
            print("\n5.2 测试快速连续操作后的恢复...")
            from backend.core.cache.optimizer import L1MemoryCache

            cache = L1MemoryCache(max_size=10)

            for i in range(20):
                cache.set(f"key_{i}", f"value_{i}")

            result = cache.get("key_15")
            print(f"✅ 超出容量后恢复: {result is not None}")

        except Exception as e:
            issues.append(f"容量恢复测试失败: {str(e)}")

        if issues:
            return TestResult(
                name="错误恢复测试",
                passed=False,
                message=f"发现 {len(issues)} 个恢复问题",
                details=issues
            )
        else:
            return TestResult(
                name="错误恢复测试",
                passed=True,
                message="错误恢复测试全部通过"
            )

    def test_performance_degradation(self) -> TestResult:
        """测试6: 性能退化测试"""
        print("\n" + "="*80)
        print("🔬 测试6: 性能退化测试")
        print("="*80)

        issues = []

        try:
            print("\n6.1 测试长时间运行的性能...")
            from backend.core.cache.optimizer import L1MemoryCache

            cache = L1MemoryCache(max_size=1000, ttl=60)

            iterations = 1000
            batch_size = 100

            start = time.perf_counter()
            for batch in range(iterations // batch_size):
                for i in range(batch_size):
                    cache.set(f"perf_key_{batch}_{i}", f"value_{i}")

                for i in range(batch_size):
                    cache.get(f"perf_key_{batch}_{i % batch_size}")

            duration = time.perf_counter() - start
            ops_per_sec = (iterations * 2) / duration

            print(f"   总操作: {iterations * 2}")
            print(f"   耗时: {duration:.3f}s")
            print(f"   吞吐量: {ops_per_sec:.0f} ops/s")

            if ops_per_sec < 10000:
                print(f"⚠️  性能可能退化: {ops_per_sec:.0f} ops/s")
                issues.append(f"性能退化: {ops_per_sec:.0f} ops/s")
            else:
                print(f"✅ 性能稳定: {ops_per_sec:.0f} ops/s")

        except Exception as e:
            issues.append(f"性能退化测试失败: {str(e)}")

        try:
            print("\n6.2 测试缓存饱和后的性能...")
            from backend.core.cache.optimizer import L1MemoryCache

            cache = L1MemoryCache(max_size=100)

            for i in range(200):
                cache.set(f"saturation_key_{i}", f"value_{i}")

            start = time.perf_counter()
            for i in range(100):
                cache.get(f"saturation_key_{i}")

            duration = time.perf_counter() - start
            avg_time = (duration / 100) * 1000

            print(f"   缓存饱和后平均读取: {avg_time:.4f}ms")

            if avg_time > 1:
                issues.append(f"缓存饱和后性能下降: {avg_time:.4f}ms")

        except Exception as e:
            issues.append(f"饱和性能测试失败: {str(e)}")

        if issues:
            return TestResult(
                name="性能退化测试",
                passed=False,
                message=f"发现 {len(issues)} 个性能问题",
                details=issues
            )
        else:
            return TestResult(
                name="性能退化测试",
                passed=True,
                message="性能退化测试通过"
            )

    def run_all_tests(self) -> List[TestResult]:
        """运行所有测试"""
        print("\n" + "="*80)
        print("🚀 NeuralAgent 复杂高难度实践测试套件")
        print("="*80)

        tests = [
            self.test_module_imports,
            self.test_boundary_conditions,
            self.test_concurrent_conflicts,
            self.test_data_consistency,
            self.test_error_recovery,
            self.test_performance_degradation,
        ]

        for test in tests:
            try:
                result = test()
                self.results.append(result)
            except Exception as e:
                self.results.append(TestResult(
                    name=test.__name__,
                    passed=False,
                    message=f"测试执行失败: {str(e)}",
                    details=traceback.format_exc()
                ))

        return self.results

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("📊 测试结果摘要")
        print("="*80)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)

        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"\n{status} - {result.name}")
            print(f"   消息: {result.message}")

            if not result.passed and result.details:
                if isinstance(result.details, list):
                    print(f"   问题数: {len(result.details)}")
                    for issue in result.details[:3]:
                        print(f"   - {str(issue)[:80]}")
                else:
                    print(f"   详情: {str(result.details)[:80]}")

        print("\n" + "="*80)
        print(f"🏁 总计: {passed} 通过 / {failed} 失败")
        print("="*80)

        if failed > 0:
            print(f"\n⚠️  发现 {failed} 个需要修复的问题")
        else:
            print("\n🎉 所有复杂测试通过!")

        return failed == 0


def main():
    """主函数"""
    tester = ComplexIntegrationTester()

    results = tester.run_all_tests()

    success = tester.print_summary()

    print("\n" + "="*80)
    print("🎯 详细问题列表")
    print("="*80)

    issues_found = []

    for result in results:
        if not result.passed:
            issues_found.extend(result.details if isinstance(result.details, list) else [result.details])

    if issues_found:
        print(f"\n发现 {len(issues_found)} 个需要优化的问题:\n")
        for i, issue in enumerate(issues_found[:20], 1):
            print(f"{i}. {str(issue)[:100]}")
    else:
        print("\n✅ 未发现任何问题!")

    print("\n" + "="*80)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
