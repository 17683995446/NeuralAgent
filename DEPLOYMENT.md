# NeuralAgent 部署指南

本文档介绍如何部署 NeuralAgent 应用到生产环境。

## 📋 目录

1. [快速开始](#快速开始)
2. [配置](#配置)
3. [Docker 部署](#docker-部署)
4. [Docker Compose](#docker-compose)
5. [环境变量](#环境变量)
6. [监控](#监控)

---

## 🚀 快速开始

### 开发模式

```bash
# 直接运行
cd neural_agent
python main.py --mode demo
```

### 生产模式

```bash
# 复制配置模板
cp app_config.example.yaml config.yaml

# 编辑配置
vim config.yaml

# 启动应用
python main.py --mode full
```

---

## ⚙️ 配置

### 配置文件

NeuralAgent 支持以下配置方式（优先级从高到低）：

1. 命令行参数
2. 环境变量
3. 配置文件（config.yaml / config.json）
4. 默认配置

### 配置文件示例

```yaml
app_name: "NeuralAgent"
environment: "production"
debug: false
log_level: "INFO"

api:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["https://your-domain.com"]
  enable_websocket: true
  enable_docs: true

llm:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "sk-your-api-key"
  base_url: ""
  temperature: 0.7
  max_tokens: 1024
  timeout: 30

cache:
  enabled: true
  l1_max_size: 1000
  l1_default_ttl: 3600
  enable_l2: true
  redis_url: "redis://redis:6379/0"

monitoring:
  enabled: true
  prometheus_port: 8001

memory:
  backend: "redis"
  redis_url: "redis://redis:6379/0"

workflow:
  enabled: true
  parallel_execution: true
  max_workflows: 100
  default_timeout: 300
```

---

## 🐳 Docker 部署

### 构建 Docker 镜像

```bash
cd neural_agent

# 构建镜像
docker build -t neural-agent:latest .
```

### 运行容器

```bash
# 基础运行
docker run -d \
  -p 8000:8000 \
  -p 8001:8001 \
  neural-agent:latest

# 使用自定义配置
docker run -d \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -p 8000:8000 \
  -p 8001:8001 \
  neural-agent:latest

# 使用环境变量
docker run -d \
  -e LLM_PROVIDER=openai \
  -e LLM_API_KEY=sk-your-key \
  -e LLM_MODEL=gpt-4o-mini \
  -p 8000:8000 \
  -p 8001:8001 \
  neural-agent:latest
```

---

## 🎯 Docker Compose

### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: neural-agent-redis
    restart: always
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  neural-agent:
    build: .
    container_name: neural-agent
    restart: always
    depends_on:
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER:-mock}
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_MODEL=${LLM_MODEL:-gpt-4o-mini}
      - REDIS_URL=redis://redis:6379/0
      - CACHE_ENABLE_L2=true
      - MEMORY_BACKEND=redis
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
    volumes:
      - ./config.yaml:/app/config.yaml:ro

volumes:
  redis_data:
```

### .env 文件

```env
# .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-api-key
LLM_MODEL=gpt-4o-mini
```

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据
docker-compose down -v
```

---

## 🔑 环境变量

### 通用配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `APP_NAME` | NeuralAgent | 应用名称 |
| `ENVIRONMENT` | development | 运行环境 (development/production) |
| `DEBUG` | true | 调试模式 |
| `LOG_LEVEL` | INFO | 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL) |

### API 配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `API_HOST` | 0.0.0.0 | API 监听地址 |
| `API_PORT` | 8000 | API 监听端口 |
| `ENABLE_WEBSOCKET` | true | 启用 WebSocket |

### LLM 配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `LLM_PROVIDER` | mock | LLM 提供商 (mock/openai/anthropic/ollama/siliconflow) |
| `LLM_MODEL` | gpt-4o-mini | 模型名称 |
| `LLM_API_KEY` | | API 密钥 |
| `LLM_BASE_URL` | | API 基础 URL |
| `LLM_TEMPERATURE` | 0.7 | 温度参数 |
| `LLM_MAX_TOKENS` | 1024 | 最大 token 数 |

### 缓存配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `CACHE_ENABLED` | true | 启用缓存 |
| `CACHE_L2_ENABLED` | false | 启用 Redis L2 缓存 |
| `REDIS_URL` | redis://localhost:6379/0 | Redis URL |

### 监控配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `MONITORING_ENABLED` | true | 启用监控 |
| `PROMETHEUS_PORT` | 8001 | Prometheus 端口 |

### 记忆系统配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `MEMORY_BACKEND` | inmemory | 记忆后端 (inmemory/redis) |

---

## 📊 监控

### Prometheus 指标

NeuralAgent 暴露以下 Prometheus 指标：

- `http_requests_total`: HTTP 请求计数
- `http_request_duration_seconds`: HTTP 请求耗时
- `cache_hits_total`: 缓存命中次数
- `cache_misses_total`: 缓存未命中次数
- `llm_requests_total`: LLM 请求次数
- `llm_request_duration_seconds`: LLM 请求耗时
- `workflow_executions_total`: 工作流执行次数

### 指标端点

```bash
# 访问 Prometheus 指标
curl http://localhost:8001/metrics
```

---

## 🔒 安全建议

1. **不要将 API 密钥提交到代码仓库**
2. **使用 Docker secrets 或环境变量管理密钥**
3. **配置适当的 CORS 策略**
4. **启用 HTTPS（生产环境）**
5. **限制 API 访问**

---

## 🛠️ 故障排除

### 检查日志

```bash
# Docker Compose
docker-compose logs -f neural-agent

# Docker
docker logs -f neural-agent
```

### 健康检查

```bash
# 检查 API
curl http://localhost:8000/health

# 检查监控
curl http://localhost:8001/health
```

### 常见问题

**Q: 无法连接到 Redis**
A: 确保 Redis 服务正在运行，且 `REDIS_URL` 配置正确

**Q: API 请求超时**
A: 检查 LLM API 密钥和网络连接

---

## 📝 下一步

- 查看 [快速开始](QUICKSTART.md)
- 查看 [API 文档](docs/API.md)
- 了解 [工作流系统](docs/WORKFLOW.md)
