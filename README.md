# NeuralAgent System

类神经网络多Agent协作系统 - Multi-Agent Collaboration System based on Neural Network Architecture

## 项目概述

本系统实现了一个类比深度学习神经网络架构的多Agent协作系统，用于复杂软件工程任务的自动化处理。

## 核心架构

```
输入层 → 卷积层 → 池化层 → 全连接层1 → 全连接层2 → 全连接层3 → 输出层
                                                           ↓
                                                        用户
                                                           ↓
反向传播层 ← 测试生成层 ← 代码生成层 ← 全局理解层 ← 池化层 ← 卷积层
```

## 主要特性

### 核心功能
- **8层固定分层架构**: 完全遵循CNN+全连接层结构
- **双记忆体系**: Redis短期记忆 + Milvus长期记忆
- **信任度管理**: 基于Ray RLlib的PPO算法
- **LLM统一接口**: 支持OpenAI、Anthropic、Ollama等多模型调用
- **零重复造轮子**: 所有通用能力完全复用开源项目

### 高级特性（新增）
- **🔐 安全认证系统**: JWT认证 + 角色权限控制
- **📊 性能监控**: 指标采集 + 告警系统 + 健康检查
- **⚙️ 配置管理**: 热更新 + 配置监听器 + 变更历史
- **🔄 可靠通信**: 熔断器 + 重试机制 + 指数退避
- **🧵 线程安全**: 并行处理增强 + 资源限制 + 优雅关闭
- **🧪 完整测试**: 单元测试 + 集成测试 + 场景测试
- **💾 大规模代码处理**: Tree-sitter分片 + 向量检索 + 增量更新

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置 API 密钥
```

### 3. 启动服务（开发环境）

```bash
docker-compose up -d
```

### 4. 访问API文档

打开浏览器访问: http://localhost:8000/docs

### 5. 获取认证令牌

```bash
# 获取测试令牌（开发环境）
curl -X POST http://localhost:8000/api/v1/auth/demo-token

# 或使用登录接口
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'
```

## API使用示例

### 创建任务

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_id": "test-task-001",
    "user_requirement": "重构用户认证模块",
    "code_repo_url": "https://github.com/example/project.git",
    "target_branch": "main",
    "max_iteration": 5,
    "learning_rate": 0.1
  }'
```

### 查询任务状态

```bash
curl http://localhost:8000/api/v1/tasks/test-task-001/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 提交反馈

```bash
curl -X POST http://localhost:8000/api/v1/tasks/test-task-001/feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "satisfaction_score": 4,
    "feedback_items": [
      {
        "type": "positive",
        "description": "代码质量良好",
        "suggestion": "可以继续优化"
      }
    ]
  }'
```

### 大规模代码处理

```bash
# 启动代码处理任务
curl -X POST http://localhost:8000/api/v1/code/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "repo_url": "https://github.com/example/project.git",
    "branch": "main",
    "file_pattern": ["*.py", "*.js"]
  }'
```

### 查询系统指标

```bash
curl http://localhost:8000/api/v1/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 项目结构

```
neural_agent/
├── backend/
│   ├── api/              # API路由和Pydantic模型
│   │   ├── routes.py     # API路由
│   │   ├── schemas.py    # API Schemas
│   │   ├── dependencies.py # 认证依赖
│   │   └── middleware.py # 认证中间件
│   ├── core/             # 核心组件
│   │   ├── neural_agent.py       # Agent核心单元
│   │   ├── memory.py             # 记忆系统
│   │   ├── trust_manager.py      # 信任度管理
│   │   ├── llm_adapter.py        # LLM适配层（兼容旧接口）
│   │   ├── config_manager.py     # 配置管理（支持热更新）
│   │   ├── parallel_processor.py # 并行处理（增强线程安全）
│   │   ├── vector_store.py       # 向量存储（熔断器+重试）
│   │   ├── metrics.py            # 指标采集系统
│   │   ├── metrics_integration.py # 指标集成模块
│   │   ├── auth.py               # 认证管理
│   │   ├── code_chunker.py       # 代码分片
│   │   ├── incremental_processor.py # 增量更新
│   │   ├── error_handler.py      # 错误处理
│   │   ├── performance_monitor.py # 性能监控
│   │   └── health_monitor.py     # 健康检查
│   ├── layers/           # 神经网络层实现
│   │   ├── input_layer.py
│   │   ├── convolution_layer.py
│   │   ├── pooling_layer.py
│   │   ├── fc_layer_1.py
│   │   ├── fc_layer_2.py
│   │   ├── fc_layer_3.py
│   │   ├── output_layer.py
│   │   └── backward_layer.py
│   ├── models/           # 数据库模型
│   │   └── database.py   # SQLAlchemy模型
│   ├── services/         # 业务服务层
│   │   └── database_service.py
│   ├── agent/            # Agent管理
│   ├── config.py         # 全局配置
│   ├── main.py           # FastAPI应用入口
│   └── large_scale_processor.py # 大规模代码处理
├── tests/                # 测试文件
│   ├── test_agent.py
│   ├── test_layers.py
│   ├── test_memory.py
│   ├── test_trust.py
│   ├── test_llm_adapter.py
│   ├── test_api.py
│   ├── test_enhanced_features.py
│   └── test_comprehensive.py
├── scripts/              # 工具脚本
│   └── detect_circular_imports.py
├── docs/                 # 文档模板
│   └── templates/
├── test_logs/            # 测试日志
├── docker-compose.yml     # Docker Compose配置
├── Dockerfile            # Docker镜像构建
├── pytest.ini            # Pytest配置
├── requirements.txt      # Python依赖
└── README.md             # 项目说明
```

## 核心组件详解

### 🔐 认证和权限系统

**用户角色**:
- `Admin`: 管理员，拥有所有权限
- `User`: 普通用户，可以创建和管理任务
- `Guest`: 访客，只读权限

**权限列表**:
- `CREATE_TASK`: 创建任务
- `READ_TASK`: 读取任务
- `UPDATE_TASK`: 更新任务
- `DELETE_TASK`: 删除任务
- `CODE_PROCESSING`: 代码处理
- `ADMIN_OPERATIONS`: 管理员操作

### 📊 性能指标系统

**内置指标**:
- API请求计数和延迟
- LLM调用统计
- 向量存储操作统计
- 并行任务处理统计
- 系统资源使用

**告警规则**:
- API高错误率告警
- LLM延迟告警
- 向量操作失败告警

### ⚙️ 配置系统

**支持功能**:
- 环境变量覆盖
- 热更新（无需重启）
- 配置变更监听器
- 配置变更历史记录

**示例配置**:
```python
from backend.core.config_manager import get_config_manager

config = get_config_manager()

# 设置配置
config.set_with_notify("app.feature.enabled", True)

# 添加监听器
def on_config_change(key, old, new):
    print(f"配置变更: {key} = {new}")

config.add_watcher("app.feature.enabled", on_config_change)
```

### 🧵 并行处理系统

**特性**:
- 任务优先级队列
- 资源限制（最大并发数）
- 任务取消支持
- 指数退避重试
- 任务超时控制
- 优雅关闭

**示例**:
```python
from backend.core.parallel_processor import ParallelProcessor, ProcessorConfig

config = ProcessorConfig(max_workers=5, task_timeout=60.0)
processor = ParallelProcessor(config=config)

results = processor.process_items([1, 2, 3, 4, 5], lambda x: x * 2)
```

### 🔄 向量存储可靠性

**特性**:
- 熔断器模式
- 指数退避重试
- 健康检查
- 操作统计
- 支持Milvus和Chroma

**示例**:
```python
from backend.core.vector_store import create_vector_store, CircuitBreaker

store = create_vector_store(
    backend="chroma",
    timeout=30.0
)

# 添加向量
success = store.add(
    ids=["chunk1"],
    texts=["代码内容"],
    embeddings=[[0.1, 0.2, ...]],
    metadata=[{"file": "test.py"}]
)

# 查询
results = store.search(query_embedding=[0.1, 0.2, ...], top_k=10)
```

## 开源组件

| 组件 | 版本 | 协议 | 用途 |
|------|------|------|------|
| AutoGen | 0.4.0 | MIT | Agent核心单元 |
| CrewAI | 0.30.0 | MIT | 多Agent编排 |
| LangChain | 0.2.0 | MIT | 上下文压缩 |
| OpenAI/Anthropic/Ollama | 最新 | 多样 | LLM接口 |
| Ray RLlib | 2.24.0 | Apache 2.0 | 反向传播 |
| FastAPI | 0.110.0 | MIT | HTTP API |
| Redis | 7.2+ | BSD | 短期记忆 |
| Milvus/Chroma | 2.4+ | Apache 2.0 | 向量存储 |
| PostgreSQL | 16+ | PostgreSQL | 元数据 |

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_enhanced_features.py -v

# 运行带覆盖率报告的测试
pytest --cov=backend --cov-report=html
```

## 健康检查和监控

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细健康检查（需要认证）
curl http://localhost:8000/api/v1/health/detailed \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取系统指标
curl http://localhost:8000/api/v1/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 配置管理

```bash
# 获取当前配置
curl http://localhost:8000/api/v1/config/info \
  -H "Authorization: Bearer YOUR_TOKEN"

# 设置配置值
curl -X PUT http://localhost:8000/api/v1/config/app.feature.enabled \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"value": "true"}'

# 强制重新加载配置
curl -X POST http://localhost:8000/api/v1/config/reload \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 开发指南

### 添加新的API端点

1. 在 `backend/api/schemas.py` 中定义数据模型
2. 在 `backend/api/routes.py` 中添加路由
3. 使用 `@require_auth` 或 `@require_permission` 装饰器添加认证

### 添加新的指标

```python
from backend.core.metrics import get_metrics_collector

metrics = get_metrics_collector()

# 计数器
metrics.increment("my.module.events")

# 计时器
with metrics.timer("my.module.operation"):
    do_something()

# 仪表盘
metrics.gauge("my.module.queue_size", 100)
```

## 故障排查

### 常见问题

1. **JWT Token过期**: 使用登录接口重新获取
2. **服务连接失败**: 检查Docker容器状态 `docker ps`
3. **配置未生效**: 检查热更新是否启用，或调用 `/api/v1/config/reload`
4. **性能下降**: 检查指标 `/api/v1/metrics` 查找瓶颈

### 日志查看

```bash
# 查看API服务日志
docker logs neural_agent-api-1

# 查看Redis日志
docker logs neural_agent-redis-1

# 查看向量数据库日志
docker logs neural_agent-milvus-1
```

## 许可证

本项目基于MIT许可证开源。
