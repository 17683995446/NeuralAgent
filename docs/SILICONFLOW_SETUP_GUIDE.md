# 硅基流动 API 集成指南

## 📋 概述

NeuralAgent 已成功集成 **硅基流动 (SiliconFlow)** API，支持100+开源大模型！

---

## 📦 配置文件已创建

| 文件 | 描述 |
|------|------|
| [config_siliconflow.py](file:///workspace/neural_agent/config_siliconflow.py) | 配置示例文件 |
| [test_siliconflow.py](file:///workspace/neural_agent/test_siliconflow.py) | 完整测试脚本 |
| [test_siliconflow_simple.py](file:///workspace/neural_agent/test_siliconflow_simple.py) | 简化测试脚本 |
| [start_siliconflow.sh](file:///workspace/neural_agent/start_siliconflow.sh) | 快速启动脚本 |

---

## ⚠️ 当前状态

**API 配置已成功，但账户余额不足**
```
Error: Sorry, your account balance is insufficient
```

### 解决方案

#### 1️⃣ 充值账户
访问 https://www.siliconflow.cn/ 充值获取免费额度

#### 2️⃣ 使用免费模型（如果可用）
硅基流动提供一些免费模型配额，请检查控制台

---

## 🎯 可用模型

### 聊天模型
| 模型 | 描述 | 推荐度 |
|------|------|--------|
| `Qwen/Qwen2.5-72B-Instruct` | 通义千问最新模型 | ⭐⭐⭐⭐⭐ |
| `deepseek-ai/DeepSeek-V3` | DeepSeek 最新模型 | ⭐⭐⭐⭐⭐ |
| `meta-llama/Meta-Llama-3.1-70B-Instruct` | Llama 3.1 | ⭐⭐⭐⭐ |
| `Qwen/Qwen2.5-32B-Instruct` | 通义千问小模型 | ⭐⭐⭐⭐ |

### 嵌入模型
| 模型 | 描述 |
|------|------|
| `BAAI/bge-large-zh-v1.5` | 中文嵌入模型 |

---

## 🚀 快速开始

### 方法1: 环境变量配置（推荐）

```bash
# 设置环境变量
export LLM_PROVIDER="openai"
export LLM_MODEL="Qwen/Qwen2.5-72B-Instruct"
export LLM_API_KEY="REDACTED_API_KEY"
export LLM_BASE_URL="https://api.siliconflow.cn/v1"
export LLM_EMBEDDING_MODEL="BAAI/bge-large-zh-v1.5"
export OPENAI_API_KEY="REDACTED_API_KEY"
export OPENAI_API_BASE="https://api.siliconflow.cn/v1"

# 运行测试
cd /workspace/neural_agent
python test_siliconflow_simple.py
```

### 方法2: 使用快速启动脚本

```bash
cd /workspace/neural_agent
chmod +x start_siliconflow.sh
./start_siliconflow.sh
```

### 方法3: 在代码中配置

```python
# 直接使用 LiteLLM
import litellm
import os

# 配置
os.environ["OPENAI_API_KEY"] = "your-api-key"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"

# 调用
response = litellm.completion(
    model="openai/Qwen/Qwen2.5-72B-Instruct",
    messages=[{"role": "user", "content": "你好!"}]
)
```

---

## 🔧 架构说明

### LiteLLM 集成

项目使用 **LiteLLM** 作为统一接口，支持:
- ✅ OpenAI 兼容接口
- ✅ 100+ 模型支持
- ✅ 异步/同步 API
- ✅ 重试和熔断机制
- ✅ 监控指标

### 文件位置

```
backend/core/llm_integration/
└── unified_llm_client_wrapper.py  # LLM客户端封装
```

---

## 📊 测试脚本说明

### `test_siliconflow_simple.py` - 简化测试

**特点**: 不依赖项目其他模块，直接测试LiteLLM

```bash
python test_siliconflow_simple.py
```

### `test_siliconflow.py` - 完整测试

**特点**: 使用项目的LLM客户端，需要依赖完整项目

```bash
python test_siliconflow.py
```

---

## 💡 使用示例

### 在NeuralAgent中使用

```python
from backend.core.llm_integration.unified_llm_client_wrapper import get_llm_client

# 获取客户端
llm_client = get_llm_client()

# 异步调用
response = await llm_client.chat([
    {"role": "user", "content": "你好，写个Python函数!"}
])

# 获取结果
print(response.content)
```

---

## 🆘 故障排查

### 问题1: 余额不足
```
Error: Sorry, your account balance is insufficient
```
**解决方案**: 访问 https://www.siliconflow.cn/ 充值

### 问题2: 模型不存在
```
Error: model not found
```
**解决方案**: 检查模型名称是否正确，使用 `SILICONFLOW_AVAILABLE_MODELS` 中的模型

### 问题3: 网络超时
```
Timeout error
```
**解决方案**: 增加 `llm_timeout` 配置

---

## 📚 参考链接

- 硅基流动官网: https://www.siliconflow.cn/
- API文档: https://docs.siliconflow.cn/
- LiteLLM文档: https://docs.litellm.ai/

---

## 🎉 下一步

1. [ ] 充值硅基流动账户
2. [ ] 选择合适的模型
3. [ ] 运行完整测试
4. [ ] 集成到生产环境

---

**配置状态**: ✅ API配置已完成  
**测试状态**: ⚠️ 等待账户充值  
**文档状态**: ✅ 完整
