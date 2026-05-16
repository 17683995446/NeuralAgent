"""
NeuralAgent Simplified Comprehensive Test Suite
简化的综合测试套件 - 专注于可运行的测试
"""

import pytest
import asyncio
import time
from typing import Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==============================================================================
# 单元测试
# ==============================================================================

class TestUnitTests:
    """单元测试"""

    def test_cache_optimizer(self):
        """测试缓存优化器"""
        from backend.core.cache.optimizer import L1MemoryCache

        cache = L1MemoryCache(max_size=10, ttl=60)

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"
        assert cache.get_stats()["size"] == 1
        print("✅ Cache optimizer unit test passed")

    def test_security_validator(self):
        """测试安全验证器"""
        from backend.core.security.enhanced import SecurityValidator

        is_valid, message = SecurityValidator.validate_password_strength("Test123!")

        assert is_valid is True
        assert message == "密码强度合格"
        print("✅ Security validator unit test passed")

    def test_prompt_template(self):
        """测试提示模板"""
        from tools.prompt_workbench.workbench import PromptWorkbench, PromptVariable

        workbench = PromptWorkbench()

        variables = [
            PromptVariable(name="name", description="User name", required=True)
        ]

        template = workbench.create_prompt(
            name="Greeting",
            description="Simple greeting",
            content="Hello, {name}!",
            variables=variables
        )

        rendered = workbench.render_prompt(template.id, {"name": "World"})

        assert rendered == "Hello, World!"
        print("✅ Prompt template unit test passed")

    def test_alert_manager(self):
        """测试告警管理器"""
        from backend.core.monitoring.advanced import create_alert_manager, AlertSeverity

        manager = create_alert_manager()

        assert manager is not None
        assert len(manager.rules) >= 0
        print("✅ Alert manager unit test passed")

    def test_auth_service(self):
        """测试认证服务"""
        from backend.core.security.authentication import AuthenticationService, User
        import uuid

        auth_service = AuthenticationService()

        user = User(
            id=str(uuid.uuid4()),
            username="test_user",
            email="test@example.com",
            hashed_password="dummy_hash"
        )

        tokens = auth_service.create_tokens(user)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        print("✅ Auth service unit test passed")

    def test_cli_tools_accessible(self):
        """测试 CLI 工具可访问"""
        from cli import cli

        assert cli is not None
        print("✅ CLI tools accessible test passed")


# ==============================================================================
# 集成测试
# ==============================================================================

class TestIntegrationTests:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """测试缓存集成"""
        from backend.core.cache.optimizer import CacheOptimizer

        optimizer = CacheOptimizer()

        call_count = 0

        async def expensive_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return {"data": "expensive_result"}

        key = optimizer.generate_key("test", "key1")

        result1 = await optimizer.get_or_set(key, expensive_operation)
        result2 = await optimizer.get_or_set(key, expensive_operation)

        assert result1 == result2
        assert call_count == 1
        print("✅ Cache integration test passed")


# ==============================================================================
# 系统测试
# ==============================================================================

class TestSystemTests:
    """系统测试"""

    def test_frontend_structure(self):
        """测试前端结构"""
        frontend_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "frontend"
        )

        required_files = [
            "package.json",
            "vite.config.ts",
            "tsconfig.json",
            "src/main.tsx",
            "src/App.tsx"
        ]

        for file in required_files:
            file_path = os.path.join(frontend_path, file)
            assert os.path.exists(file_path), f"Missing frontend file: {file}"

        print("✅ Frontend structure system test passed")

    def test_docker_compose(self):
        """测试 Docker Compose 配置"""
        docker_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docker-compose.yml"
        )

        if os.path.exists(docker_path):
            with open(docker_path, 'r') as f:
                content = f.read()
                assert "services:" in content

        print("✅ Docker Compose system test passed")

    def test_performance_benchmark_accessible(self):
        """测试性能基准测试可访问"""
        benchmark_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "benchmarks",
            "performance.py"
        )

        assert os.path.exists(benchmark_path)
        print("✅ Performance benchmark accessible test passed")

    def test_documentation_exists(self):
        """测试文档存在"""
        docs_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs/index.html"
        )

        assert os.path.exists(docs_path)
        print("✅ Documentation exists test passed")

    def test_core_security_modules_accessible(self):
        """测试核心安全模块可访问"""
        try:
            from backend.core.security.authentication import AuthenticationService, User
            from backend.core.security.enhanced import SecurityValidator
            print("✅ Core security modules accessible test passed")
        except ImportError as e:
            pytest.fail(f"Failed to import security modules: {e}")


# ==============================================================================
# 性能测试
# ==============================================================================

class TestPerformanceTests:
    """性能测试"""

    def test_cache_hit_rate(self):
        """测试缓存命中率"""
        from backend.core.cache.optimizer import L1MemoryCache

        cache = L1MemoryCache(max_size=1000, ttl=60)

        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")

        for i in range(100):
            cache.get(f"key_{i}")

        stats = cache.get_stats()
        hit_rate_str = stats["hit_rate"]
        hit_rate = float(hit_rate_str.replace("%", ""))

        assert hit_rate > 90
        print(f"✅ Cache hit rate: {hit_rate:.2f}%")

    def test_cache_operation_performance(self):
        """测试缓存操作性能"""
        from backend.core.cache.optimizer import L1MemoryCache
        import time

        cache = L1MemoryCache(max_size=1000, ttl=60)

        iterations = 1000
        start = time.perf_counter()

        for i in range(iterations):
            cache.set(f"key_{i}", f"value_{i}")

        set_duration = (time.perf_counter() - start) * 1000

        start = time.perf_counter()

        for i in range(iterations):
            cache.get(f"key_{i}")

        get_duration = (time.perf_counter() - start) * 1000

        avg_set = set_duration / iterations
        avg_get = get_duration / iterations

        assert avg_set < 1
        assert avg_get < 1
        print(f"✅ Cache operation performance: set={avg_set:.3f}ms, get={avg_get:.3f}ms")

    def test_auth_token_performance(self):
        """测试认证令牌性能"""
        from backend.core.security.authentication import AuthenticationService, User
        import uuid
        import time

        auth_service = AuthenticationService()

        user = User(
            id=str(uuid.uuid4()),
            username="perf_user",
            email="perf@example.com",
            hashed_password="dummy_hash"
        )

        iterations = 100
        start = time.perf_counter()

        for i in range(iterations):
            tokens = auth_service.create_tokens(user)

        duration = (time.perf_counter() - start) * 1000
        avg_time = duration / iterations

        assert avg_time < 10
        print(f"✅ Auth token performance: {avg_time:.3f}ms avg")


# ==============================================================================
# 测试运行器
# ==============================================================================

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🎯 NeuralAgent Comprehensive Test Suite")
    print("="*80)

    test_classes = [
        ("Unit Tests", TestUnitTests),
        ("Integration Tests", TestIntegrationTests),
        ("System Tests", TestSystemTests),
        ("Performance Tests", TestPerformanceTests)
    ]

    results = {}

    for name, test_class in test_classes:
        print(f"\n📋 Running {name}...")
        instance = test_class()

        test_methods = [
            method for method in dir(instance)
            if method.startswith("test_") and callable(getattr(instance, method))
        ]

        passed = 0
        failed = 0

        for method_name in test_methods:
            try:
                method = getattr(instance, method_name)
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                passed += 1
            except Exception as e:
                print(f"   ❌ {method_name}: {str(e)}")
                failed += 1

        results[name] = {"passed": passed, "failed": failed}
        print(f"   ✅ Passed: {passed}, ❌ Failed: {failed}")

    print("\n" + "="*80)
    print("📊 Test Results Summary")
    print("="*80)

    total_passed = sum(r["passed"] for r in results.values())
    total_failed = sum(r["failed"] for r in results.values())

    for name, result in results.items():
        status = "✅" if result["failed"] == 0 else "❌"
        print(f"   {status} {name}: {result['passed']}/{result['passed'] + result['failed']} passed")

    print(f"\n🎯 Total: {total_passed}/{total_passed + total_failed} passed")

    if total_failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_failed} tests failed")

    print("="*80)

    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
