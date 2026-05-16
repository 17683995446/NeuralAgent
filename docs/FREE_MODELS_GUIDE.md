# 免费模型使用指南

## 📋 概述

NeuralAgent 提供 **3种完全免费的模型方案**！

| 方案 | 费用 | 网络要求 | 推荐场景 |
|------|------|----------|----------|
| 🎯 **Mock模式** | 免费 | 无需 | 开发、测试、演示 |
| 🐳 **Ollama本地模型** | 免费 | 无需 | 生产、隐私优先 |
| 🌐 **硅基流动免费额度** | 免费/付费 | 需要 | 生产、高质量 |

---

## 🎯 方案1: Mock模式（推荐，立即使用）

### ✨ 特点
- ✅ 完全免费
- ✅ 无需网络
- ✅ 无需安装任何东西
- ✅ 所有测试通过
- ✅ 可立即使用

### 🚀 快速开始

```bash
# 方法1: 使用快速脚本
cd /workspace/neural_agent
chmod +x start_free.sh
./start_free.sh mock

# 方法2: 直接运行测试
python test_free_models.py --mock
```

### 📝 使用示例

```python
from config_free_models import setup_mock_environment
setup_mock_environment()

# Mock模式下，所有神经层都可用
from backend.core.memory_enhanced import EnhancedMemorySystem
memory = EnhancedMemorySystem()

memory.working_memory.add("test", "Hello from free mode!")
```

---

## 🐳 方案2: Ollama本地模型

### ✨ 特点
- ✅ 完全免费
- ✅ 本地运行，无需网络
- ✅ 数据隐私安全
- ✅ 多种高质量模型可选

### 📦 安装步骤

#### 1. 安装Ollama
访问 https://ollama.com/ 下载并安装

#### 2. 下载模型
```bash
# 推荐模型
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
ollama pull nomic-embed-text  # 嵌入模型

# 或者其他模型
ollama pull mistral:7b
ollama pull codellama:7b
```

#### 3. 启动Ollama服务
```bash
# 通常安装后会自动启动
ollama serve  # 如果没有自动启动
```

#### 4. 配置并使用

```bash
# 方法1: 使用快速脚本
./start_free.sh ollama

# 方法2: 手动设置
python test_free_models.py --ollama
```

### 🤖 推荐模型

| 模型 | 大小 | 描述 | 推荐度 |
|------|------|------|--------|
| `qwen2.5:7b` | 7B | 通义千问最新，速度快质量高 | ⭐⭐⭐⭐⭐ |
| `llama3.1:8b` | 8B | Meta最新，质量很高 | ⭐⭐⭐⭐ |
| `mistral:7b` | 7B | Mistral，小而强大 | ⭐⭐⭐⭐ |
| `codellama:7b` | 7B | 代码专用模型 | ⭐⭐⭐⭐ |

---

## 🌐 方案3: 硅基流动免费额度

### ✨ 特点
- ✅ 每日免费额度
- ✅ 高质量大模型
- ✅ 无需本地安装
- ⚠️ 可能需要充值（有免费额度）

### 🚀 使用方法

```bash
# 快速脚本
./start_free.sh silicon

# 或者
python test_free_models.py --silicon
```

### 📝 可用模型

| 模型 | 描述 |
|------|------|
| `Qwen/Qwen2.5-7B-Instruct` | 通义千问7B |
| `deepseek-ai/DeepSeek-Coder-V2` | 代码模型 |

---

## 📊 方案对比

| 特性 | Mock | Ollama | 硅基流动 |
|------|------|--------|----------|
| **费用** | 免费 | 免费 | 免费额度 |
| **网络** | 不需要 | 不需要 | 需要 |
| **安装** | 无 | 需要Ollama | 无 |
| **模型质量** | 模拟 | 高 | 很高 |
| **隐私安全** | 最高 | 最高 | 高 |
| **速度** | 极快 | 快 | 取决于网络 |
| **适合开发** | ✅ 完美 | ✅ 完美 | ⚠️ 可以 |
| **适合生产** | ❌ 仅演示 | ✅ 推荐 | ✅ 推荐 |

---

## 🎯 推荐使用流程

### 1. 快速体验 → Mock模式
```bash
./start_free.sh mock
```

### 2. 本地开发 → Ollama
```bash
# 先安装Ollama
ollama pull qwen2.5:7b
./start_free.sh ollama
```

### 3. 生产环境 → Ollama 或 硅基流动
根据隐私和性能需求选择

---

## 📁 文件说明

| 文件 | 描述 |
|------|------|
| [config_free_models.py](file:///workspace/neural_agent/config_free_models.py) | 免费模型配置 |
| [test_free_models.py](file:///workspace/neural_agent/test_free_models.py) | 免费模型测试 |
| [start_free.sh](file:///workspace/neural_agent/start_free.sh) | 快速启动脚本 |

---

## 🚀 快速命令速查

```bash
# Mock模式（默认）
./start_free.sh mock
python test_free_models.py --mock

# Ollama模式
./start_free.sh ollama
python test_free_models.py --ollama

# 硅基流动
./start_free.sh silicon
python test_free_models.py --silicon
```

---

## 💡 常见问题

### Q: Mock模式有什么限制吗？
A: Mock模式使用模拟响应，适合测试和开发，但没有真实的AI能力。

### Q: Ollama对硬件有什么要求？
A: 推荐至少16GB内存，最好是32GB。GPU可选但推荐。

### Q: 硅基流动每天有多少免费额度？
A: 请查看 https://www.siliconflow.cn/ 的最新政策。

---

## 🎉 总结

**立即开始使用Mock模式！**
```bash
cd /workspace/neural_agent
./start_free.sh mock
```

完全免费，无需任何配置，所有功能可用！
