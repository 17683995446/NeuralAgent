"""Simple SiliconFlow Test - 简化的硅基流动测试

直接使用litellm测试API，不依赖项目其他模块。
"""

import os
import asyncio

# 设置硅基流动配置
os.environ["OPENAI_API_KEY"] = "REDACTED_API_KEY"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"


async def test_siliconflow_simple():
    """简单测试硅基流动API"""
    print("=" * 70)
    print("🧪 测试硅基流动API (简化版)")
    print("=" * 70)
    
    print("\n📦 导入litellm...")
    try:
        import litellm
        litellm.set_verbose = False
        print("   ✅ litellm 导入成功!")
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return
    
    # 测试模型
    model = "Qwen/Qwen2.5-72B-Instruct"
    
    print(f"\n🤖 测试聊天模型: {model}")
    print("   发送请求...")
    
    try:
        # 简单聊天请求
        messages = [
            {"role": "user", "content": "你好，请用一句话介绍你自己，控制在50字以内。"}
        ]
        
        print("   等待响应...")
        response = await litellm.acompletion(
            model=f"openai/{model}",  # 使用openai兼容接口
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            api_base=os.environ["OPENAI_API_BASE"],
            api_key=os.environ["OPENAI_API_KEY"]
        )
        
        # 解析响应
        if hasattr(response, 'choices') and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"\n   ✅ 成功!")
            print(f"   回复: {content}")
        else:
            print(f"\n   ❌ 响应格式异常: {response}")
        
    except Exception as e:
        print(f"\n   ❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试嵌入
    print("\n📊 测试嵌入模型: BAAI/bge-large-zh-v1.5")
    try:
        embedding_response = await litellm.aembedding(
            model=f"openai/BAAI/bge-large-zh-v1.5",
            input=["Hello, NeuralAgent!"],
            api_base=os.environ["OPENAI_API_BASE"],
            api_key=os.environ["OPENAI_API_KEY"]
        )
        
        if hasattr(embedding_response, 'data') and len(embedding_response.data) > 0:
            embedding = embedding_response.data[0]['embedding']
            print(f"   ✅ 成功!")
            print(f"   嵌入维度: {len(embedding)}")
        else:
            print(f"   ❌ 响应格式异常")
        
    except Exception as e:
        print(f"   ❌ 嵌入失败: {e}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_siliconflow_simple())
