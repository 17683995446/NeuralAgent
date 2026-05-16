# NeuralAgent - 完整部署指南

## 🎉 项目完成！

恭喜！你已经拥有了一个完整的企业级 AI Agent 平台！

## 🏗️ 项目架构概览

### 目录结构

```
neural_agent/
├── backend/                      # 后端服务 (FastAPI + Python)
│   ├── core/                    # 核心模块
│   │   ├── agent_framework/     # Agent 框架
│   │   ├── memory/             # 记忆系统
│   │   ├── monitoring/         # 监控系统
│   │   ├── reasoning/          # 推理引擎
│   │   ├── vector_store/       # 向量存储
│   │   └── ...
│   ├── api/                    # API 路由
│   └── main.py                 # 入口文件
├── frontend/                   # 前端应用 (React + TypeScript)
│   ├── src/
│   │   ├── components/        # UI 组件
│   │   ├── pages/            # 页面组件
│   │   └── main.tsx          # 入口文件
│   └── package.json
├── tests/                     # 测试文件
├── docker-compose.yml         # 开发环境配置
├── docker-compose.production.yml  # 生产环境配置
├── PHASE_5-14_PLAN*.md       # 阶段计划文档
└── README.md                  # 项目说明
```

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

#### 1. 启动完整开发环境

```bash
cd neural_agent
docker-compose up -d
```

#### 2. 访问服务

- 前端界面: http://localhost:3001
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

#### 3. 生产环境部署

```bash
docker-compose -f docker-compose.production.yml up -d
```

### 方式二：本地开发

#### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python main.py
```

#### 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 📚 功能模块

### 1. Agent 管理

- 创建、编辑、删除 Agent
- Agent 类型配置
- 实时状态监控
- 性能统计

### 2. 工作流编辑

- 拖拽式工作流构建
- 节点连接和配置
- 工作流执行
- 历史记录

### 3. 监控面板

- 系统健康指标
- 实时请求统计
- 告警管理
- 日志查看

### 4. 提示工程

- 提示模板管理
- A/B 测试
- 多维度评估
- 版本控制

### 5. 设置

- LLM 配置
- 数据库设置
- 安全配置
- 通知设置

## 🔧 配置说明

### 环境变量

创建 `.env` 文件：

```env
# LLM 配置
OPENAI_API_KEY=your-api-key
LLM_PROVIDER=openai
MODEL_NAME=gpt-4

# 向量数据库
VECTOR_STORE_TYPE=milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Redis
REDIS_URL=redis://localhost:6379/0

# 安全
JWT_SECRET_KEY=your-secret-key
```

### 向量数据库选项

- **Milvus** (生产推荐)
- **Chroma** (开发推荐)
- **Pinecone** (云服务)
- **Weaviate** (企业级)

## 📊 技术栈

### 后端

- FastAPI (Web 框架)
- Python 3.10+
- Pydantic (数据验证)
- SQLAlchemy (ORM)
- Redis (缓存)
- Milvus/Chroma (向量数据库)
- Prometheus (监控)

### 前端

- React 18
- TypeScript
- Vite (构建工具)
- Tailwind CSS (样式)
- React Flow (工作流)
- Recharts (图表)
- Lucide (图标)

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_phase14*.py -v
```

## 🔐 安全最佳实践

1. 更改默认密码和密钥
2. 启用 HTTPS
3. 配置防火墙规则
4. 定期更新依赖
5. 设置访问日志
6. 启用审计功能

## 📈 性能优化建议

1. 使用 Milvus 作为向量数据库
2. 启用 Redis 缓存
3. 配置数据库连接池
4. 使用 CDN 加速前端资源
5. 启用 Gzip 压缩
6. 配置负载均衡

## 🆘 故障排查

### 常见问题

**Q: 后端无法连接到数据库？**
A: 检查 Docker 容器状态，确认数据库服务正常运行。

**Q: 前端 API 请求失败？**
A: 确认后端服务在 8000 端口运行，检查 CORS 配置。

**Q: 向量搜索速度慢？**
A: 检查 Milvus 索引配置，考虑使用 HNSW 索引。

### 获取帮助

- 查看日志: `docker-compose logs`
- 检查状态: `docker-compose ps`
- 重启服务: `docker-compose restart`

## 🎯 下一步

1. 配置你的 LLM API 密钥
2. 创建第一个 Agent
3. 设计一个工作流
4. 配置监控告警
5. 开始使用！

---

## 🎊 恭喜！

你已经掌握了 NeuralAgent 的完整部署！现在你拥有了一个完整的企业级 AI Agent 平台！

有任何问题？查看各阶段的计划文档获取更多详细信息！
