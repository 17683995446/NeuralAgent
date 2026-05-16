"""Free Model Test - 免费模型测试

测试多种免费模型方案：
1. Mock模式（无需网络）
2. Ollama本地模型
3. 硅基流动免费模型
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_mock_mode():
    """测试Mock模式（完全免费，无需网络）"""
    print("=" * 70)
    print("🧪 测试: Mock模式（完全免费）")
    print("=" * 70)
    
    # 设置Mock模式
    from config_free_models import setup_mock_environment
    setup_mock_environment()
    
    # 使用简化的mock实现
    print("\n🤖 Mock模式测试（模拟响应）")
    print("   使用项目已有的Mock模式...")
    
    # 测试记忆系统
    print("\n🧠 测试记忆系统...")
    from backend.core.memory.enhanced_memory_system import EnhancedMemorySystem
    memory = EnhancedMemorySystem()
    
    memory.working_memory.add("test_1", "Hello from free model!")
    print("   ✅ 工作记忆添加成功")
    
    result = memory.working_memory.get("test_1")
    print(f"   ✅ 工作记忆读取成功: {result}")
    
    # 测试神经层
    print("\n🧪 测试神经层...")
    from backend.core.neural_layers.neural_input_layer import NeuralInputLayer
    input_layer = NeuralInputLayer()
    
    result = await input_layer.execute("测试输入")
    print(f"   ✅ 输入层执行成功: {result}")
    
    print("\n" + "=" * 70)
    print("✅ Mock模式测试完成！")
    print("   - 完全免费，无需网络")
    print("   - 所有核心功能正常")
    print("=" * 70)


async def test_ollama_mode():
    """测试Ollama本地模型"""
    print("=" * 70)
    print("🧪 测试: Ollama本地模型")
    print("=" * 70)
    
    from config_free_models import setup_ollama_environment
    setup_ollama_environment()
    
    # 检查Ollama是否可用
    print("\n🔍 检查Ollama服务...")
    
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        print(f"   ✅ Ollama服务运行中")
        print(f"   可用模型: {len(response.json().get('models', []))}")
    except Exception as e:
        print(f"   ❌ Ollama服务未运行: {e}")
        print(f"   📝 请安装并启动Ollama:")
        print(f"      1. 下载: https://ollama.com/")
        print(f"      2. 启动: ollama serve")
        print(f"      3. 拉取模型: ollama pull qwen2.5:7b")
        return
    
    print("\n🤖 测试Ollama聊天...")
    try:
        import litellm
        litellm.set_verbose = True
        
        messages = [{"role": "user", "content": "你好，请用一句话介绍自己。"}]
        response = await litellm.acompletion(
            model="ollama/qwen2.5:7b",
            messages=messages,
            api_base="http://localhost:11434",
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"   ✅ 成功!")
        print(f"   回复: {content}")
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        print(f"   📝 请确保已下载模型: ollama pull qwen2.5:7b")


def test_free_modes():
    """测试所有免费模式"""
    import asyncio
    
    print("\n" + "=" * 70)
    print("🚀 免费模型测试工具箱")
    print("=" * 70)
    print("\n请选择测试模式:")
    print("  1. Mock模式（默认，无需网络）")
    print("  2. Ollama本地模型（需要安装）")
    print("  3. 硅基流动免费模型（需要账户）")
    print("\n使用:")
    print("  python test_free_models.py --mock    - 测试Mock模式")
    print("  python test_free_models.py --ollama  - 测试Ollama模式")
    print("  python test_free_models.py --silicon - 测试硅基流动免费模型")
    
    # 默认测试Mock模式
    print("\n默认运行Mock模式...")
    asyncio.run(test_mock_mode())


if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--ollama":
            asyncio.run(test_ollama_mode())
        elif sys.argv[1] == "--silicon":
            from test_siliconflow_simple import test_siliconflow_simple
            asyncio.run(test_siliconflow_simple())
        else:
            asyncio.run(test_mock_mode())
    else:
        test_free_modes()
