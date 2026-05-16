# NeuralAgent 完整使用示例和最佳实践

本文档提供NeuralAgent系统的完整使用示例，涵盖各种使用场景。

## 目录

- [快速开始](#快速开始)
- [基础用法](#基础用法)
- [高级特性](#高级特性)
- [大规模代码处理](#大规模代码处理)
- [安全认证](#安全认证)
- [性能监控](#性能监控)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## 快速开始

### 1. 启动系统

```python
from backend.main import app
from backend.config import settings

# 应用已自动初始化所有组件
# 访问 http://localhost:8000/docs 查看API文档
```

### 2. 基本任务创建

```python
import requests

# 创建新任务
response = requests.post(
    "http://localhost:8000/api/v1/tasks",
    headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "Content-Type": "application/json"
    },
    json={
        "task_id": "task-001",
        "user_requirement": "重构用户认证模块",
        "code_repo_url": "https://github.com/example/project.git",
        "target_branch": "main"
    }
)

print(response.json())
```

---

## 基础用法

### 1. 使用NeuralAgent核心

```python
from backend.core.neural_agent import NeuralAgent
from backend.core.memory import Memory
from backend.core.trust_manager import TrustManager

# 初始化组件
memory = Memory()
trust_manager = TrustManager()
agent = NeuralAgent(memory=memory, trust_manager=trust_manager)

# 创建任务
task = agent.create_task(
    requirement="优化数据库查询性能",
    context={
        "repo_url": "https://github.com/example/db-service",
        "priority": "high"
    }
)

# 执行任务
result = agent.execute_task(task)
print(f"Task completed: {result.summary}")
```

### 2. 使用LLM适配器

```python
from backend.core.llm_adapter import (
    create_llm_adapter,
    LLMProvider,
    LLMConfig
)

# 创建OpenAI适配器
config = LLMConfig(
    provider=LLMProvider.OPENAI,
    api_key="your-api-key",
    model="gpt-4",
    temperature=0.7
)

llm = create_llm_adapter(config=config)

# 生成文本
prompt = "解释什么是向量数据库"
response = await llm.generate(prompt)
print(response)

# 聊天
messages = [
    {"role": "system", "content": "你是一个代码审查助手"},
    {"role": "user", "content": "审查这段代码的安全性问题"}
]
response = await llm.chat(messages)
print(response)

# 生成embedding
text = "代码片段内容"
embedding = await llm.embed(text)
print(f"Embedding维度: {len(embedding)}")
```

### 3. 使用并行处理

```python
from backend.core.parallel_processor import (
    ParallelProcessor,
    ProcessorConfig,
    RetryConfig
)

# 配置处理器
config = ProcessorConfig(
    max_workers=10,
    max_queue_size=1000,
    task_timeout=300.0
)

retry_config = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0
)

processor = ParallelProcessor(config=config, retry_config=retry_config)

# 处理项目
items = list(range(100))
results = processor.process_items(
    items,
    processor=lambda x: x * 2,  # 处理函数
    priorities=[50] * len(items)  # 优先级
)

# 获取统计
stats = processor.get_stats()
print(f"Processed: {stats['total_processed']}")
print(f"Failed: {stats['total_failed']}")
```

---

## 高级特性

### 1. 配置热更新

```python
from backend.core.config_manager import get_config_manager

config_manager = get_config_manager()

# 添加配置变更监听器
def on_config_change(key, old_value, new_value):
    print(f"配置变更: {key}")
    print(f"  旧值: {old_value}")
    print(f"  新值: {new_value}")

config_manager.add_watcher("app.feature.enabled", on_config_change)

# 动态更新配置
config_manager.set_with_notify("app.feature.enabled", True)

# 查看变更历史
history = config_manager.get_change_history(limit=10)
for change in history:
    print(f"{change['key']}: {change['old_value']} -> {change['new_value']}")
```

### 2. 性能指标采集

```python
from backend.core.metrics import get_metrics_collector

metrics = get_metrics_collector()

# 计数器
metrics.increment("user.login.success", tags={"method": "password"})
metrics.increment("user.login.success", tags={"method": "oauth"})

# 计时器
metrics.timing("api.request.latency", 0.125, tags={"endpoint": "/api/v1/tasks"})

# 仪表盘
metrics.gauge("queue.size", 42)

# 使用计时器上下文管理器
with metrics.timer("operation.duration"):
    do_something()

# 获取统计
stats = metrics.get_stats("api.request.latency")
print(f"平均延迟: {stats.avg:.2f}ms")
print(f"P95延迟: {stats.get_percentile(0.95):.2f}ms")
```

### 3. 向量存储操作

```python
from backend.core.vector_store import create_vector_store

# 创建向量存储
store = create_vector_store(
    backend="chroma",
    timeout=30.0
)

# 添加向量
success = store.add(
    ids=["chunk-001", "chunk-002"],
    texts=[
        "def calculate_metrics(data): ...",
        "class DataProcessor: ..."
    ],
    embeddings=[
        [0.1, 0.2, 0.3, ...],  # 1536维
        [0.4, 0.5, 0.6, ...]
    ],
    metadata=[
        {"file": "utils.py", "line": 42},
        {"file": "processor.py", "line": 1}
    ]
)

# 搜索相似向量
results = store.search(
    query_embedding=[0.1, 0.2, 0.3, ...],
    top_k=5,
    filter_expr=None
)

for result in results:
    print(f"ID: {result.id}")
    print(f"相似度: {result.score:.4f}")
    print(f"内容: {result.content[:100]}...")

# 健康检查
health = store.health_check()
print(f"状态: {health['status']}")
print(f"熔断器: {health['circuit_breaker']}")
```

---

## 大规模代码处理

### 1. 初始化大规模处理器

```python
from backend.large_scale_processor import LargeScaleCodeProcessor

processor = LargeScaleCodeProcessor(
    chunk_size=2000,
    overlap=200,
    max_workers=10,
    vector_backend="chroma"
)
```

### 2. 处理代码仓库

```python
from backend.core.llm_adapter import init_llm_adapter, LLMProvider

# 初始化LLM
llm = init_llm_adapter(provider=LLMProvider.OPENAI)

# 处理仓库
job = await processor.process_repository(
    repo_url="https://github.com/example/large-project.git",
    branch="main",
    file_patterns=["*.py", "*.js", "*.java"]
)

print(f"Job ID: {job.job_id}")
print(f"状态: {job.status}")

# 查询状态
status = await processor.get_processing_status(job.job_id)
print(f"已处理: {status['processed_chunks']}/{status['total_chunks']}")
```

### 3. 增量处理

```python
# 检测Git变更
incremental = processor.get_incremental_changes(
    repo_url="https://github.com/example/project.git",
    since_commit="abc123"
)

print(f"新增文件: {len(incremental['added_files'])}")
print(f"修改文件: {len(incremental['modified_files'])}")
print(f"删除文件: {len(incremental['deleted_files'])}")

# 只处理变更的部分
if incremental['modified_files']:
    job = await processor.process_repository(
        repo_url="...",
        incremental_only=True,
        since_commit=incremental['since_commit']
    )
```

---

## 安全认证

### 1. 用户登录和令牌获取

```python
# 登录获取令牌
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "username": "user@example.com",
        "password": "secure_password"
    }
)

token = response.json()["access_token"]
print(f"Token: {token[:50]}...")
```

### 2. 使用令牌访问受保护资源

```python
# 访问需要认证的端点
response = requests.get(
    "http://localhost:8000/api/v1/tasks",
    headers={
        "Authorization": f"Bearer {token}"
    }
)

print(f"状态码: {response.status_code}")
print(f"任务列表: {response.json()}")
```

### 3. 检查用户权限

```python
from backend.core.auth import AuthManager, UserRole, Permission

auth = AuthManager(secret_key="your-secret")

# 检查权限
user_role = UserRole.USER
has_permission = auth.has_permission(user_role, Permission.CREATE_TASK)
print(f"USER可以创建任务: {has_permission}")  # True

has_permission = auth.has_permission(user_role, Permission.DELETE_TASK)
print(f"USER可以删除任务: {has_permission}")  # True

has_permission = auth.has_permission(user_role, Permission.ADMIN_OPERATIONS)
print(f"USER可以执行管理操作: {has_permission}")  # False
```

### 4. 在API中使用认证

```python
from backend.api.dependencies import require_auth, require_permission
from backend.core.auth import Permission

# 在路由中使用
@router.post("/tasks")
@require_permission(Permission.CREATE_TASK)
async def create_task(request: Request, task_data: TaskInput):
    current_user = request.state.current_user
    print(f"创建者: {current_user['username']}")
    # 处理任务创建...
```

---

## 性能监控

### 1. 使用性能监控器

```python
from backend.core.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()

# 跟踪操作
monitor.record_operation("code_analysis", 0.125, has_error=False)
monitor.record_operation("vector_search", 0.045, has_error=False)
monitor.record_operation("api_request", 0.200, has_error=False)

# 获取指标
metrics = monitor.get_metrics("code_analysis")
print(f"平均耗时: {metrics.avg_time*1000:.2f}ms")
print(f"P95耗时: {metrics.p95_time*1000:.2f}ms")
print(f"吞吐量: {metrics.throughput:.2f}/s")

# 生成报告
report = monitor.generate_report(duration_seconds=60)
print(report)
```

### 2. 使用装饰器跟踪

```python
from backend.core.performance_monitor import track

monitor = get_performance_monitor()

@track("my_operation")
def slow_operation():
    import time
    time.sleep(1)
    return "done"

result = slow_operation()
```

### 3. 系统资源监控

```python
# 获取系统快照
snapshot = monitor.get_recent_system_snapshot()
print(f"CPU: {snapshot.get('cpu_percent', 0):.1f}%")
print(f"内存: {snapshot.get('process_memory_mb', 0):.1f}MB")

# 获取历史指标
cpu_history = monitor.get_system_metrics("cpu_percent", duration_seconds=300)
for point in cpu_history[-10:]:
    print(f"{point.timestamp}: {point.value:.1f}%")
```

---

## 错误处理

### 1. 使用重试装饰器

```python
from backend.core.error_handler import retry, RetryConfig

@retry(max_attempts=3, delay=1.0, exponential_base=2.0)
def unreliable_operation():
    import random
    if random.random() < 0.7:
        raise ConnectionError("Network error")
    return "success"

# 最多重试3次，延迟分别为1s, 2s, 4s
result = unreliable_operation()
```

### 2. 使用熔断器

```python
from backend.core.error_handler import CircuitBreaker, CircuitBreakerOpenError

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)

def risky_operation():
    # 可能失败的操作
    pass

# 熔断器保护
try:
    result = breaker.call(risky_operation)
except CircuitBreakerOpenError:
    print("服务暂时不可用，请稍后重试")
```

### 3. 错误处理上下文

```python
from backend.core.error_handler import get_error_handler

handler = get_error_handler()

try:
    # 可能失败的操作
    process_data()
except Exception as e:
    ctx = handler.handle_error(
        error=e,
        context="data_processing",
        retryable=True,
        tags={"user_id": "123", "operation": "process"}
    )
    
    print(f"错误已记录: {ctx.error_message}")
    print(f"时间: {ctx.timestamp}")

# 获取错误统计
stats = handler.get_error_stats(duration_seconds=3600)
print(f"最近1小时错误数: {stats['total_errors']}")
print(f"可重试错误: {stats['retryable_errors']}")
```

---

## 最佳实践

### 1. 配置管理

```python
# ✅ 推荐：使用配置管理器
config = get_config_manager()
config.add_watcher("app.mode", on_mode_change)
config.set_with_notify("app.mode", "production")

# ❌ 避免：硬编码配置
MAX_WORKERS = 10  # 硬编码
```

### 2. 异步操作

```python
# ✅ 推荐：使用异步LLM调用
result = await llm.generate(prompt)

# ❌ 避免：阻塞调用
result = llm.generate_sync(prompt)
```

### 3. 资源清理

```python
# ✅ 推荐：使用上下文管理器
with ParallelProcessor() as processor:
    results = processor.process_items(items, handler)
# 自动清理

# ❌ 避免：手动清理
processor = ParallelProcessor()
results = processor.process_items(items, handler)
processor.shutdown()  # 容易忘记
```

### 4. 错误处理

```python
# ✅ 推荐：使用重试机制
@retry(max_attempts=3, delay=1.0)
def call_api():
    return requests.get(url)

# ❌ 避免：无限重试
while True:
    try:
        call_api()
    except:
        pass
```

### 5. 性能优化

```python
# ✅ 推荐：批量操作
embeddings = await llm.embed_batch(texts)  # 批量

# ❌ 避免：循环单个调用
embeddings = []
for text in texts:
    embeddings.append(await llm.embed(text))
```

---

## 故障排查

### 常见问题

#### 1. JWT Token过期

```python
# 重新登录获取新令牌
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "...", "password": "..."}
)
new_token = response.json()["access_token"]
```

#### 2. 配置未生效

```bash
# 强制重新加载配置
curl -X POST http://localhost:8000/api/v1/config/reload \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. 服务连接失败

```bash
# 检查服务状态
docker ps

# 查看日志
docker logs neural_agent-api-1
```

---

## 更多资源

- [API文档](http://localhost:8000/docs)
- [项目README](../README.md)
- [架构文档](../docs/ARCHITECTURE.md)
- [测试用例](../tests/)

---

*最后更新: 2026-05-12*
