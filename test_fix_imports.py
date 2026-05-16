#!/usr/bin/env python3
"""
测试导入修复是否有效
"""
import sys
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_import_agents_module():
    """测试 agents 模块导入"""
    print("测试 agents 模块导入...")
    try:
        from backend.core.agents import (
            IntelligentMultiAgentCoordinator,
            DistributedMultiAgentOrchestrator,
            NeuralAgent,
            ConvolutionAgent,
            PoolingAgent,
            FCAgent,
            OutputAgent,
            create_agent,
            OrchestrationFramework,
            AgentConfig,
            TaskConfig,
            BaseOrchestrator,
            AutoGenOrchestrator,
            CrewAIOrchestrator,
            LangChainOrchestrator,
            OrchestratorFactory
        )
        print("✅ agents 模块导入成功！")
        print(f"  - IntelligentMultiAgentCoordinator: {IntelligentMultiAgentCoordinator}")
        print(f"  - DistributedMultiAgentOrchestrator: {DistributedMultiAgentOrchestrator}")
        print(f"  - NeuralAgent: {NeuralAgent}")
        return True
    except Exception as e:
        print(f"❌ agents 模块导入失败: {e}")
        import traceback
        print(f"详细错误:\n{traceback.format_exc()}")
        return False


def test_import_neural_layers():
    """测试 neural_layers 模块导入"""
    print("\n测试 neural_layers 模块导入...")
    try:
        from backend.core.neural_layers import (
            NeuralInputLayer,
            NeuralPoolingLayer,
            NeuralConvolutionLayer,
            NeuralOutputLayer,
            NeuralBackwardPropagationLayer
        )
        print("✅ neural_layers 模块导入成功！")
        print(f"  - NeuralInputLayer: {NeuralInputLayer}")
        print(f"  - NeuralPoolingLayer: {NeuralPoolingLayer}")
        print(f"  - NeuralConvolutionLayer: {NeuralConvolutionLayer}")
        return True
    except Exception as e:
        print(f"❌ neural_layers 模块导入失败: {e}")
        import traceback
        print(f"详细错误:\n{traceback.format_exc()}")
        return False


def test_import_llm_adapter():
    """测试 llm_adapter 模块导入"""
    print("\n测试 llm_adapter 模块导入...")
    try:
        from backend.core.llm_adapter import (
            create_llm_adapter,
            LLMProvider,
            llm_adapter
        )
        print("✅ llm_adapter 模块导入成功！")
        print(f"  - create_llm_adapter: {create_llm_adapter}")
        print(f"  - LLMProvider: {LLMProvider}")
        print(f"  - llm_adapter (全局实例): {llm_adapter}")
        return True
    except Exception as e:
        print(f"❌ llm_adapter 模块导入失败: {e}")
        import traceback
        print(f"详细错误:\n{traceback.format_exc()}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试导入修复...")
    print("=" * 60)
    
    results = []
    
    results.append(("Agents Module", test_import_agents_module()))
    results.append(("Neural Layers", test_import_neural_layers()))
    results.append(("LLM Adapter", test_import_llm_adapter()))
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 有一些测试失败了")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
