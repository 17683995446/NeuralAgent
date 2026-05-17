"""
NeuralAgent 完整优化验证运行

运行完整测试，输出综合评分
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def main():
    print("\n" + "="*80)
    print("NeuralAgent 完整验证与评分")
    print("="*80)
    
    # 1. 运行产品化测试
    print("\n[1/4] 运行产品化测试...")
    from backend.core.modular.testing import ProductTestRunner
    
    runner = ProductTestRunner()
    test_results = runner.run_all()
    
    print(f"\n测试完成！")
    print(f"总测试: {test_results['summary']['total_tests']}")
    print(f"通过: {test_results['summary']['passed']}")
    print(f"失败: {test_results['summary']['failed']}")
    print(f"通过率: {test_results['summary']['pass_rate']:.1%}")
    print(f"总耗时: {test_results['summary']['total_duration']:.2f}秒")
    
    for suite in test_results['suites']:
        print(f"\n  {suite['name']}:")
        print(f"    总数: {suite['total']}, 通过: {suite['passed']}, 失败: {suite['failed']}")
        print(f"    通过率: {suite['pass_rate']:.1%}")
    
    # 2. 生成多维度综合评分
    print("\n[2/4] 生成多维度综合评分...")
    from backend.core.modular.scoring import run_comprehensive_scoring, save_report
    
    report = run_comprehensive_scoring(test_results)
    
    report_file = "COMPREHENSIVE_SCORING_REPORT.json"
    save_report(report, report_file)
    print(f"\n评分报告已保存到: {report_file}")
    
    # 3. 验证产品化模块
    print("\n[3/4] 验证产品化模块...")
    from backend.core.modular import registry
    
    all_modules = registry.list_all()
    print(f"\n已注册模块: {len(all_modules)}")
    for mod in all_modules:
        print(f"  - {mod.name} v{mod.version} ({mod.status.value} - {mod.category.value})")
        print(f"    {mod.description}")
    
    # 4. 验证配置系统
    print("\n[4/4] 验证配置系统...")
    from backend.core.modular.config import init_config
    
    config = init_config()
    print(f"\n配置系统初始化成功!")
    print(f"  环境: {config.environment}")
    print(f"  调试: {config.debug}")
    print(f"  缓存已启用: {config.cache.enabled}")
    print(f"  记忆已启用: {config.memory.enabled}")
    
    print("\n" + "="*80)
    print("✅ 完整验证完成！")
    print("="*80)
    
    return 0 if test_results['summary']['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
