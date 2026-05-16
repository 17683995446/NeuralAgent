#!/bin/bash
# 硅基流动API快速启动脚本

echo "=============================================="
echo "🚀 NeuralAgent + 硅基流动快速启动"
echo "=============================================="

# 设置环境变量
echo ""
echo "📝 配置硅基流动API..."

export LLM_PROVIDER="openai"  # 使用OpenAI兼容接口
export LLM_MODEL="Qwen/Qwen2.5-72B-Instruct"
export LLM_API_KEY="sk-tstaxvmmhwohgledgrnaugkbewpqzjngthwmwrvllmodqdgq"
export LLM_BASE_URL="https://api.siliconflow.cn/v1"
export LLM_EMBEDDING_MODEL="BAAI/bge-large-zh-v1.5"
export OPENAI_API_KEY="sk-tstaxvmmhwohgledgrnaugkbewpqzjngthwmwrvllmodqdgq"
export OPENAI_API_BASE="https://api.siliconflow.cn/v1"

# 可选模型：
# - Qwen/Qwen2.5-72B-Instruct
# - deepseek-ai/DeepSeek-V3
# - meta-llama/Meta-Llama-3.1-70B-Instruct

echo ""
echo "✅ 环境变量已设置"
echo "   - Model: ${LLM_MODEL}"
echo "   - Base URL: ${LLM_BASE_URL}"
echo ""

# 快速测试
echo "🧪 运行测试..."
python test_siliconflow.py 2>&1 | head -60
echo ""
echo "✅ 测试完成！"
echo ""
echo "📁 接下来可以："
echo "   - 启动API: python -m uvicorn backend.main:app --reload"
echo "   - 运行测试: python -m pytest tests/ -v"
echo ""
