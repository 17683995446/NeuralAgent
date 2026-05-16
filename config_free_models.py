"""Free Model Configuration - 免费模型配置

提供多种免费模型方案：
1. Ollama本地模型（完全免费，需本地安装）
2. 硅基流动免费模型（每日免费额度）
3. Mock模式（无需网络）
"""

import os

# 免费模型配置
FREE_MODEL_CONFIG = {
    # Ollama本地模型
    "ollama": {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "chat_model": "qwen2.5:7b",
        "chat_model_alt": "llama3.1:8b",
        "embedding_model": "nomic-embed-text"
    },
    
    # 硅基流动免费模型（检查免费额度）
    "siliconflow_free": {
        "provider": "openai_compatible",
        "api_key": "sk-tstaxvmmhwohgledgrnaugkbewpqzjngthwmwrvllmodqdgq",
        "base_url": "https://api.siliconflow.cn/v1",
        # 免费模型可能每日有配额
        "chat_model": "Qwen/Qwen2.5-7B-Instruct",  # 较小的模型可能免费
        "chat_model_alt": "deepseek-ai/DeepSeek-Coder-V2",
        "embedding_model": "BAAI/bge-large-zh-v1.5"
    },
    
    # Mock模式（完全免费，无需网络）
    "mock": {
        "provider": "mock",
        "chat_model": "mock-model",
        "embedding_model": "mock-embedding"
    }
}


def setup_ollama_environment():
    """设置Ollama本地模型环境"""
    config = FREE_MODEL_CONFIG["ollama"]
    
    os.environ["LLM_PROVIDER"] = "ollama"
    os.environ["LLM_MODEL"] = config["chat_model"]
    os.environ["LLM_BASE_URL"] = config["base_url"]
    os.environ["LLM_EMBEDDING_MODEL"] = config["embedding_model"]
    
    print(f"✅ Ollama本地模型已配置")
    print(f"   - Model: {os.environ['LLM_MODEL']}")
    print(f"   - Base URL: {os.environ['LLM_BASE_URL']}")
    print(f"\n⚠️ 请确保:")
    print(f"   1. 已安装Ollama: https://ollama.com/")
    print(f"   2. 已下载模型: ollama pull qwen2.5:7b")


def setup_mock_environment():
    """设置Mock模式（无需网络）"""
    config = FREE_MODEL_CONFIG["mock"]
    
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["LLM_MODEL"] = config["chat_model"]
    os.environ["LLM_EMBEDDING_MODEL"] = config["embedding_model"]
    
    # 设置Mock模式
    os.environ["NEURALAGENT_USE_MOCK_EMBEDDER"] = "true"
    
    print(f"✅ Mock模式已配置（完全免费）")
    print(f"   - 无需网络连接")
    print(f"   - 使用模拟响应")


def setup_free_model(mode: str = "mock"):
    """设置免费模型
    
    Args:
        mode: 'ollama', 'siliconflow_free', 或 'mock'
    """
    if mode == "ollama":
        setup_ollama_environment()
    elif mode == "siliconflow_free":
        setup_siliconflow_free_environment()
    else:
        setup_mock_environment()


def setup_siliconflow_free_environment():
    """设置硅基流动免费模型"""
    config = FREE_MODEL_CONFIG["siliconflow_free"]
    
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["LLM_MODEL"] = config["chat_model"]
    os.environ["LLM_API_KEY"] = config["api_key"]
    os.environ["LLM_BASE_URL"] = config["base_url"]
    os.environ["LLM_EMBEDDING_MODEL"] = config["embedding_model"]
    os.environ["OPENAI_API_KEY"] = config["api_key"]
    os.environ["OPENAI_API_BASE"] = config["base_url"]
    
    print(f"✅ 硅基流动免费模型已配置")
    print(f"   - Model: {os.environ['LLM_MODEL']}")
    print(f"   - 检查每日免费额度是否可用")


# Ollama推荐模型列表
OLLAMA_MODELS = [
    "qwen2.5:7b",          # 通义千问2.5 - 速度快，质量好
    "llama3.1:8b",         # Llama 3.1 - 质量很高
    "mistral:7b",          # Mistral - 小而强大
    "phi3:mini",           # Phi 3 - 非常小，移动端可用
    "codellama:7b",        # CodeLLama - 代码专用
    "nomic-embed-text",    # 嵌入模型
]


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "mock"
    setup_free_model(mode)
