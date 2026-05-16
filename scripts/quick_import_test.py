#!/usr/bin/env python3
"""Quick Import Test - 快速导入测试"""

import sys
sys.path.insert(0, '/workspace/neural_agent')

print("="*60)
print("Testing Core Module Imports")
print("="*60)

tests_passed = 0
tests_total = 0

def test_import(module_name, import_func):
    """测试单个导入"""
    global tests_passed, tests_total
    tests_total += 1
    try:
        import_func()
        print(f"✅ {module_name}")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"❌ {module_name}: {str(e)[:60]}")
        return False

# 测试基础模块
print("\n📦 Testing Basic Modules:")
test_import("error_handling", lambda: __import__('backend.core.infrastructure.error_handling'))
test_import("cache", lambda: __import__('backend.core.infrastructure.cache'))
test_import("security", lambda: __import__('backend.core.infrastructure.security'))

# 测试高层模块
print("\n📦 Testing High-Level Modules:")
test_import("agents", lambda: __import__('backend.core.agents'))
test_import("llm_integration", lambda: __import__('backend.core.llm_integration'))
test_import("task_management", lambda: __import__('backend.core.task_management'))
test_import("messaging", lambda: __import__('backend.core.messaging'))
test_import("memory", lambda: __import__('backend.core.memory'))
test_import("quality_assurance", lambda: __import__('backend.core.quality_assurance'))
test_import("configuration", lambda: __import__('backend.core.configuration'))
test_import("trust_management", lambda: __import__('backend.core.trust_management'))

# 统计
print("\n" + "="*60)
print(f"Results: {tests_passed}/{tests_total} modules imported successfully")
print("="*60)

if tests_passed == tests_total:
    print("🎉 All modules imported successfully!")
    sys.exit(0)
else:
    print(f"⚠️  {tests_total - tests_passed} modules failed to import")
    sys.exit(1)
