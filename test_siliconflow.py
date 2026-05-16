"""SiliconFlow API Test - 硅基流动API测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_siliconflow_basic():
    """测试硅基流动基本功能"""
    print("=" * 70)
    print("🧪 测试硅基流动API")
    print("=" * 70)
    
    # 设置环境变量
    from config_siliconflow import setup_siliconflow_environment
    setup_siliconflow_environment()
    
    # 导入LLM客户端
    print("\n📦 导入LLM客户端...")
    from backend.core.llm_integration.unified_llm_client_wrapper import get_llm_client
    llm_client = get_llm_client()
    
    # 测试1: 简单聊天
    print("\n🤖 测试1: 简单聊天...")
    try:
        messages = [
            {"role": "user", "content": "你好，我是一个AI助手。请用一句话介绍你自己。"}
        ]
        response = await llm_client.chat(messages, stream=False)
        
        print(f"   ✅ 成功!")
        print(f"   模型: {response.model}")
        print(f"   回复: {response.content[:100]}...")
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        print(traceback.format_exc())
    
    # 测试2: 代码生成
    print("\n💻 测试2: 代码生成...")
    try:
        messages = [
            {"role": "user", "content": "写一个Python函数，计算斐波那契数列的第n项。"}
        ]
        response = await llm_client.chat(messages, stream=False)
        
        print(f"   ✅ 成功!")
        print(f"   回复: {response.content[:150]}...")
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    # 测试3: 嵌入（如果支持）
    print("\n📊 测试3: 文本嵌入...")
    try:
        embedding_response = await llm_client.embed("Hello, NeuralAgent!")
        
        print(f"   ✅ 成功!")
        print(f"   嵌入维度: {len(embedding_response.embedding)}")
        print(f"   嵌入模型: {embedding_response.model}")
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print("\n" + "=" * 70)
    print("✅ 硅基流动API测试完成!")
    print("=" * 70)


def test_siliconflow_sync():
    """测试同步版本"""
    print("\n" + "=" * 70)
    print("🧪 测试同步硅基流动API")
    print("=" * 70)
    
    from config_siliconflow import setup_siliconflow_environment
    setup_siliconflow_environment()
    
    from backend.core.llm_integration.unified_llm_client_wrapper import get_llm_client
    llm_client = get_llm_client()
    
    print("\n🤖 测试: 同步聊天...")
    try:
        messages = [{"role": "user", "content": "用Python打印'Hello, SiliconFlow!'"}]
        response = llm_client.chat_sync(messages)
        
        print(f"   ✅ 成功!")
        print(f"   回复: {response.content[:100]}...")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        test_siliconflow_sync()
    else:
        asyncio.run(test_siliconflow_basic())
