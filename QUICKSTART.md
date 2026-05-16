# NeuralAgent 快速开始指南

让你在 5 分钟内运行 NeuralAgent！

---

## 🚀 一步启动（最简模式）

```bash
cd neural_agent

# 运行演示模式
python main.py --mode demo
```

就这么简单！🎉

---

## 📋 完整步骤

### 1. 进入项目目录

```bash
cd neural_agent
```

### 2. 配置（可选）

```bash
# 复制配置模板
cp app_config.example.yaml config.yaml

# 编辑配置（可选）
vim config.yaml
```

### 3. 运行应用

选择你想要的模式：

#### 📋 演示模式
```bash
python main.py --mode demo
```
快速看到所有功能的演示。

#### 💬 交互式模式
```bash
python main.py --mode interactive
```
和 NeuralAgent 直接对话！

#### 🌐 API 模式
```bash
python main.py --mode api --port 8000
```
启动 REST API 服务器。

#### ⚡ 完整模式（生产/开发）
```bash
python main.py --mode full
```
启动完整功能（API + 监控）。

---

## 🎯 模式详解

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `demo` | 运行演示，显示所有功能 | 快速了解 |
| `interactive` | 交互式对话 | 测试和探索 |
| `api` | 仅启动 API 服务器 | 生产部署 |
| `full` | API + 监控 | 完整部署 |

---

## 🐳 Docker 部署

想要更快？用 Docker！

```bash
# 启动完整服务（含 Redis）
docker-compose up -d

# 查看日志
docker-compose logs -f neural-agent

# 停止服务
docker-compose down
```

访问：
- API: http://localhost:8000
- 监控: http://localhost:8001

---

## 🌐 API 使用

启动 API 服务器后：

```bash
# 健康检查
curl http://localhost:8000/health

# 存储记忆
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "Hello, NeuralAgent!"}'

# 检索记忆
curl http://localhost:8000/api/v1/memory/test
```

---

## ⚙️ 配置选项

### 通过环境变量

```bash
# 设置 LLM 提供商
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export LLM_API_KEY=sk-your-key

# 启用 Redis 缓存
export CACHE_ENABLE_L2=true
export REDIS_URL=redis://localhost:6379/0

# 运行应用
python main.py --mode full
```

### 通过配置文件

编辑 `config.yaml`：
```yaml
app_name: "My NeuralAgent"
environment: "development"
debug: true

llm:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "sk-your-key"
```

---

## 📊 监控

Prometheus 指标在 `http://localhost:8001/metrics`

---

## 🧪 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_integration.py -v

# 测试增强记忆系统
python -m pytest tests/test_enhanced_memory_v2.py -v
```

---

## 🎓 下一步

- 查看 [部署指南](DEPLOYMENT.md)
- 查看 [阶段8总结](PHASE_8_SUMMARY.md)
- 查看 [所有阶段文档](.)
