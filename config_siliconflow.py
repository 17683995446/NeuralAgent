"""SiliconFlow Configuration Example - 硅基流动配置示例

使用硅基流动免费模型：
- API端点: https://api.siliconflow.cn/v1
- 模型: Qwen/Qwen2.5-72B-Instruct, deepseek-ai/DeepSeek-V3, 等
"""

import os

# 硅基流动配置示例
SILICONFLOW_CONFIG = {
    # LiteLLM provider 配置
    "provider": "openai_compatible",
    
    # API 配置
    "api_key": "sk-tstaxvmmhwohgledgrnaugkbewpqzjngthwmwrvllmodqdgq",
    "base_url": "https://api.siliconflow.cn/v1",
    
    # 推荐模型
    "chat_model": "Qwen/Qwen2.5-72B-Instruct",
    "chat_model_alt": "deepseek-ai/DeepSeek-V3",
    "embedding_model": "BAAI/bge-large-zh-v1.5"
}


def setup_siliconflow_environment():
    """设置硅基流动环境变量"""
    # 设置环境变量
    os.environ["LLM_PROVIDER"] = "openai"  # 使用openai兼容接口
    os.environ["LLM_MODEL"] = SILICONFLOW_CONFIG["chat_model"]
    os.environ["LLM_API_KEY"] = SILICONFLOW_CONFIG["api_key"]
    os.environ["LLM_BASE_URL"] = SILICONFLOW_CONFIG["base_url"]
    os.environ["LLM_EMBEDDING_MODEL"] = SILICONFLOW_CONFIG["embedding_model"]
    
    # 设置LiteLLM配置
    os.environ["OPENAI_API_KEY"] = SILICONFLOW_CONFIG["api_key"]
    os.environ["OPENAI_API_BASE"] = SILICONFLOW_CONFIG["base_url"]
    
    print(f"✅ 硅基流动配置已设置")
    print(f"   - Model: {os.environ['LLM_MODEL']}")
    print(f"   - Base URL: {os.environ['LLM_BASE_URL']}")
    print(f"   - 模型列表: Qwen/Qwen2.5-72B-Instruct, deepseek-ai/DeepSeek-V3, 等")


# 硅基流动可用模型列表
SILICONFLOW_AVAILABLE_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "deepseek-ai/DeepSeek-V3",
    "deepseek-ai/DeepSeek-Coder-V2",
    "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "meta-llama/Meta-Llama-3.1-405B-Instruct",
    "BAAI/bge-large-zh-v1.5"  # Embedding
]


if __name__ == "__main__":
    setup_siliconflow_environment()
