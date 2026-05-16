#!/usr/bin/env python3
"""
NeuralAgent - 完整的可运行示例应用

演示 NeuralAgent 核心功能的实际运行
无需复杂依赖，开箱即用
"""

import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==================== 主应用类 ====================
class NeuralAgentApp:
    """NeuralAgent 主应用类 - 简单但完整"""
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("NeuralAgent 应用初始化")
        logger.info("=" * 60)
        
        # 初始化模块
        self._init_memory()
        self._init_llm()
        self._init_neural_pipeline()
        
        logger.info("✅ NeuralAgent 应用初始化完成\n")
    
    def _init_memory(self):
        """初始化记忆系统 - 使用内存后端确保可运行"""
        try:
            from backend.core.memory.unified_memory import (
                UnifiedMemorySystem,
                InMemoryBackend
            )
            self.memory = UnifiedMemorySystem(InMemoryBackend())
            logger.info("✅ 记忆系统初始化完成 (内存模式)")
        except Exception as e:
            logger.warning(f"记忆系统初始化问题: {e}")
            self.memory = None
    
    def _init_llm(self):
        """初始化 LLM 系统"""
        try:
            from backend.core.llm_adapter import create_llm_adapter
            self.llm = create_llm_adapter(provider="mock")
            logger.info("✅ LLM 系统初始化完成 (Mock 模式)")
        except Exception as e:
            logger.warning(f"LLM 系统初始化问题: {e}")
            self.llm = None
    
    def _init_neural_pipeline(self):
        """初始化神经管道"""
        try:
            from backend.core.neural_layers import get_neural_pipeline
            self.pipeline = get_neural_pipeline()
            logger.info("✅ 神经网络初始化完成")
        except Exception as e:
            logger.warning(f"神经网络初始化问题: {e}")
            self.pipeline = None
    
    async def process_input(self, user_input: str) -> str:
        """处理用户输入 - 完整流程"""
        print("\n" + "=" * 60)
        print(f"📥 用户输入: {user_input}")
        print("=" * 60)
        
        # Step 1: 存储输入到记忆
        memory_key = f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if self.memory:
            await self.memory.store(memory_key, user_input)
            print(f"💾 已存储到记忆: {memory_key}")
        
        # Step 2: 神经管道处理
        if self.pipeline:
            print(f"🧠 开始神经网络处理...")
            result = await self.pipeline.process(user_input)
            print(f"✅ 神经网络处理完成")
        else:
            result = f"模拟处理结果: {user_input}"
        
        # Step 3: LLM 生成（Mock）
        if self.llm:
            print(f"🤖 LLM 生成响应...")
            llm_response = await self.llm.generate(user_input)
        else:
            llm_response = f"LLM 响应 (Mock): {user_input}"
        
        # Final Result
        print("=" * 60)
        print("✅ 处理完成！")
        print("=" * 60)
        
        return f"\n最终结果:\n  神经处理: {result}\n  LLM 响应: {llm_response}"


# ==================== 示例用法 ====================
async def example_basic_usage():
    """基本用法示例"""
    print("\n🧪 示例1: 基本使用")
    app = NeuralAgentApp()
    
    # 处理一些输入
    inputs = [
        "帮我分析一个简单的问题",
        "如何创建一个 Todo 应用？",
        "解释一下机器学习的基本概念"
    ]
    
    for inp in inputs:
        result = await app.process_input(inp)
        print(result)


async def example_memory_demo():
    """记忆系统演示"""
    print("\n🧪 示例2: 记忆系统")
    from backend.core.memory.unified_memory import (
        UnifiedMemorySystem,
        InMemoryBackend
    )
    
    memory = UnifiedMemorySystem(InMemoryBackend())
    
    # 存储数据
    await memory.store("key1", "这是第一个数据")
    await memory.store("key2", {"name": "测试", "value": 123})
    
    # 检索
    print(f"📦 key1: {await memory.retrieve('key1')}")
    print(f"📦 key2: {await memory.retrieve('key2')}")
    print(f"❓ key exists: {await memory.has('key1')}")


async def example_neural_pipeline():
    """神经管道演示"""
    print("\n🧪 示例3: 神经管道")
    from backend.core.neural_layers.simple_pipeline import NeuralPipeline
    
    pipeline = NeuralPipeline()
    result = await pipeline.process("这是一个测试输入")
    
    print(f"🎯 最终输出: {result}")


# ==================== 主入口 ====================
def main():
    """主入口"""
    print("\n" + "=" * 60)
    print("🚀 NeuralAgent - 完整运行示例")
    print("=" * 60)
    print("\n本示例演示 NeuralAgent 核心功能\n")
    
    try:
        # 运行示例
        asyncio.run(example_memory_demo())
        asyncio.run(example_neural_pipeline())
        asyncio.run(example_basic_usage())
        
        print("\n" + "=" * 60)
        print("🎉 所有示例运行完成！")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
