# 📋 NeuralAgent 架构速查表

## 📁 核心目录

```
backend/
├── api/              # API层
├── core/             # 核心层
│   ├── agents/
│   ├── memory/
│   ├── neural_layers/
│   ├── llm_integration/
│   ├── infrastructure/
│   ├── task_management/
│   └── ...
├── processing/        # 处理层
└── main.py           # 入口
```

## 🚀 关键流程

### 用户请求 → 18层神经网络 → 输出
1. API层接收
2. 任务分解
3. Agent协调
4. 18层神经处理
5. LLM调用
6. 质量评估
7. 返回结果

## 🧠 18层神经网络

| 阶段 | 层数 |
|------|------|
| 输入处理 | 1-3 |
| 特征提取 | 4-6 |
| 深度处理 | 7-9 |
| 全连接 | 10-12 |
| 高级认知 | 13-15 |
| 输出执行 | 16-17 |
| 反向传播 | 18 |

## 📦 快速参考

### 记忆系统
- [enhanced_memory_system.py](file:///workspace/neural_agent/backend/core/memory/enhanced_memory_system.py)

### LLM集成
- [unified_llm_client_wrapper.py](file:///workspace/neural_agent/backend/core/llm_integration/unified_llm_client_wrapper.py)

### 向量数据库
- [vector_db.py](file:///workspace/neural_agent/backend/core/infrastructure/vector_db.py)

### 配置
- [config_free_models.py](file:///workspace/neural_agent/config_free_models.py)

## 📚 完整文档

- [COMPLETE_ARCHITECTURE_DOCUMENTATION.md](file:///workspace/neural_agent/docs/COMPLETE_ARCHITECTURE_DOCUMENTATION.md)
- [FREE_MODELS_GUIDE.md](file:///workspace/neural_agent/docs/FREE_MODELS_GUIDE.md)
