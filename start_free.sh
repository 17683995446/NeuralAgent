#!/bin/bash
# NeuralAgent 免费模型快速启动脚本

echo "=============================================="
echo "🚀 NeuralAgent 免费模式快速启动"
echo "=============================================="

# 默认使用Mock模式（完全免费，无需网络）
MODE=${1:-mock}

echo ""
echo "📝 选择模式: $MODE"
echo ""

case $MODE in
    "mock")
        echo "✅ 使用Mock模式（完全免费，无需网络）"
        export LLM_PROVIDER="mock"
        export LLM_MODEL="mock-model"
        export LLM_EMBEDDING_MODEL="mock-embedding"
        export NEURALAGENT_USE_MOCK_EMBEDDER="true"
        ;;
        
    "ollama")
        echo "✅ 使用Ollama本地模型"
        export LLM_PROVIDER="ollama"
        export LLM_MODEL="qwen2.5:7b"
        export LLM_BASE_URL="http://localhost:11434"
        export LLM_EMBEDDING_MODEL="nomic-embed-text"
        echo ""
        echo "⚠️ 请确保: "
        echo "   1. 已安装Ollama: https://ollama.com/"
        echo "   2. 已拉取模型: ollama pull qwen2.5:7b"
        echo "   3. Ollama服务正在运行"
        ;;
        
    "silicon")
        echo "✅ 使用硅基流动免费模型"
        export LLM_PROVIDER="openai"
        export LLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
        export LLM_API_KEY="REDACTED_API_KEY"
        export LLM_BASE_URL="https://api.siliconflow.cn/v1"
        export LLM_EMBEDDING_MODEL="BAAI/bge-large-zh-v1.5"
        export OPENAI_API_KEY="REDACTED_API_KEY"
        export OPENAI_API_BASE="https://api.siliconflow.cn/v1"
        echo ""
        echo "⚠️ 检查每日免费额度"
        ;;
        
    *)
        echo "❌ 未知模式: $MODE"
        echo "可用模式: mock, ollama, silicon"
        exit 1
        ;;
esac

echo ""
echo "🚀 运行测试..."
echo ""

cd /workspace/neural_agent
python test_free_models.py --$MODE 2>&1

echo ""
echo "✅ 完成！"
echo ""
echo "📁 其他命令:"
echo "   ./start_free.sh mock       - Mock模式（默认）"
echo "   ./start_free.sh ollama     - Ollama本地模型"
echo "   ./start_free.sh silicon    - 硅基流动"
echo "   python -m pytest tests/ -v - 运行完整测试"
