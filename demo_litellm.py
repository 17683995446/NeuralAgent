"""
Demo showing the enhanced LiteLLM adapter
"""
import asyncio
import logging
from backend.core.llm_adapter import (
    create_llm_adapter,
    LLMProvider,
    set_global_llm_adapter,
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_mock_adapter():
    """Demo the mock adapter"""
    print("\n" + "=" * 60)
    print("🚀 Mock LLM Adapter Demo")
    print("=" * 60)
    
    adapter = create_llm_adapter(provider=LLMProvider.MOCK)
    
    # 测试生成
    result = await adapter.generate("Hello, how are you?")
    print(f"\n📝 Generate result:\n{result}")
    
    # 测试聊天
    messages = [
        {"role": "user", "content": "What is AI?"},
        {"role": "assistant", "content": "AI is artificial intelligence."},
        {"role": "user", "content": "Tell me more"}
    ]
    chat_result = await adapter.chat(messages)
    print(f"\n💬 Chat result:\n{chat_result}")
    
    # 测试嵌入
    embedding = await adapter.embed("Hello world")
    print(f"\n🔢 Embedding vector length: {len(embedding)}")
    
    # 测试批量嵌入
    batch_embeddings = await adapter.embed_batch(["Hello", "World", "AI"])
    print(f"🔢 Batch embeddings: {len(batch_embeddings)} vectors")


async def demo_siliconflow_adapter():
    """Demo the SiliconFlow adapter (if API key available)"""
    print("\n" + "=" * 60)
    print("🤖 SiliconFlow LLM Adapter Demo (Mock Fallback)")
    print("=" * 60)
    
    # 这里使用 Mock 模式，因为我们没有真实的 API key
    # 如果有真实的 API key，可以这样：
    # adapter = create_llm_adapter(
    #     provider=LLMProvider.SILICONFLOW,
    #     model="deepseek-ai/DeepSeek-Coder-V2",
    #     api_key="your-api-key-here",
    #     base_url="https://api.siliconflow.cn/v1"
    # )
    
    adapter = create_llm_adapter(
        provider=LLMProvider.SILICONFLOW,
        model="deepseek-ai/DeepSeek-Coder-V2",
        # api_key="sk-your-key-here"  # 取消注释以使用真实 API
    )
    
    result = await adapter.generate("Explain what is neural network in simple terms")
    print(f"\n📝 SiliconFlow result:\n{result}")


async def demo_multiple_providers():
    """Demo switching between providers"""
    print("\n" + "=" * 60)
    print("🔄 Multiple Providers Demo")
    print("=" * 60)
    
    providers = [
        (LLMProvider.MOCK, "Mock Provider"),
        (LLMProvider.OPENAI, "OpenAI (Mocked)"),
        (LLMProvider.ANTHROPIC, "Anthropic (Mocked)"),
        (LLMProvider.SILICONFLOW, "SiliconFlow (Mocked)"),
    ]
    
    for provider, name in providers:
        print(f"\n📋 Testing {name}...")
        adapter = create_llm_adapter(provider=provider)
        result = await adapter.generate(f"Hello from {name}!")
        print(f"   ↳ {result[:60]}...")


async def main():
    """Main demo function"""
    print("=" * 60)
    print("🎯 NeuralAgent - LiteLLM Adapter Demo")
    print("=" * 60)
    
    await demo_mock_adapter()
    await demo_siliconflow_adapter()
    await demo_multiple_providers()
    
    print("\n" + "=" * 60)
    print("✅ All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
