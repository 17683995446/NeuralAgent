#!/usr/bin/env python3
"""
NeuralAgent 文档自动更新脚本
自动扫描代码文件并更新可视化文档
"""

import os
import json
from pathlib import Path
from datetime import datetime


class DocumentationUpdater:
    """文档自动更新器"""

    def __init__(self, project_root: str = "/workspace/neural_agent"):
        self.project_root = Path(project_root)
        self.stats = {
            "python_files": 0,
            "typescript_files": 0,
            "test_files": 0,
            "total_lines": 0,
            "modules": []
        }

    def scan_project(self):
        """扫描项目结构"""
        print("🔍 扫描项目结构...")

        backend_core = self.project_root / "backend" / "core"

        if backend_core.exists():
            for module_dir in backend_core.iterdir():
                if module_dir.is_dir() and not module_dir.name.startswith('_'):
                    self.stats["modules"].append({
                        "name": module_dir.name,
                        "path": str(module_dir.relative_to(self.project_root)),
                        "files": []
                    })

                    for py_file in module_dir.rglob("*.py"):
                        if "__pycache__" not in str(py_file):
                            lines = len(py_file.read_text().splitlines())
                            self.stats["total_lines"] += lines
                            self.stats["python_files"] += 1

                            self.stats["modules"][-1]["files"].append({
                                "name": py_file.name,
                                "path": str(py_file.relative_to(self.project_root)),
                                "lines": lines
                            })

        frontend_src = self.project_root / "frontend" / "src"
        if frontend_src.exists():
            for ts_file in frontend_src.rglob("*.tsx"):
                lines = len(ts_file.read_text().splitlines())
                self.stats["total_lines"] += lines
                self.stats["typescript_files"] += 1

        test_dir = self.project_root / "tests"
        if test_dir.exists():
            for test_file in test_dir.rglob("test_*.py"):
                self.stats["test_files"] += 1

        print(f"✅ 扫描完成:")
        print(f"   - Python 文件: {self.stats['python_files']}")
        print(f"   - TypeScript 文件: {self.stats['typescript_files']}")
        print(f"   - 测试文件: {self.stats['test_files']}")
        print(f"   - 总代码行数: {self.stats['total_lines']}")
        print(f"   - 模块数: {len(self.stats['modules'])}")

        return self.stats

    def generate_architecture_data(self):
        """生成架构数据"""
        mermaid_diagrams = []

        mermaid_diagrams.append("""
```mermaid
graph TB
    subgraph Frontend["🌐 前端层"]
        F1[React Dashboard]
        F2[Agent Management]
        F3[Workflow Editor]
        F4[Monitoring UI]
    end

    subgraph API["🔌 API 层 (FastAPI)"]
        A1[REST API]
        A2[WebSocket]
        A3[Auth & Rate Limit]
    end

    subgraph Core["⚙️ 核心服务层"]
""")

        for module in self.stats["modules"][:8]:
            module_name = module["name"].replace("_", " ").title()
            mermaid_diagrams.append(f'        C_{module["name"]}[{module_name}]')

        mermaid_diagrams.append("""    end

    subgraph Data["💾 数据层"]
        D1[(Redis Cache)]
        D2[(Milvus)]
        D3[(PostgreSQL)]
    end

    Frontend --> API
    API --> Core
    Core --> Data
```
""")

        return "\n".join(mermaid_diagrams)

    def generate_metrics_data(self):
        """生成指标数据"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"""
| 指标 | 数值 |
|------|------|
| Python 文件 | {self.stats['python_files']} |
| TypeScript 文件 | {self.stats['typescript_files']} |
| 测试文件 | {self.stats['test_files']} |
| 总代码行数 | {self.stats['total_lines']:,} |
| 核心模块数 | {len(self.stats['modules'])} |
| 最后更新 | {now} |
"""

    def update_documentation(self):
        """更新文档"""
        print("\n📝 更新文档...")

        scan_data = self.scan_project()
        architecture = self.generate_architecture_data()
        metrics = self.generate_metrics_data()

        now = datetime.now().strftime('%Y-%m-%d')

        readme_content = f"""# NeuralAgent - 企业级 AI Agent 平台

> 🧠 完整的企业级 AI Agent 平台，支持多 Agent 协作、记忆系统、RAG 检索、工作流编排

## 📊 项目统计

{metrics}

## 🎯 核心功能

- ✅ **Agent 框架** - 多 Agent 协作和任务调度
- ✅ **记忆系统** - 统一记忆、分层存储
- ✅ **RAG 系统** - 检索增强生成
- ✅ **工作流引擎** - 可视化工作流编排
- ✅ **监控系统** - Prometheus + Grafana
- ✅ **安全系统** - JWT + MFA + OAuth

## 🚀 快速开始

```bash
# 克隆项目
git clone <repository-url>
cd neural_agent

# 启动服务
docker-compose up -d

# 访问界面
# 前端: http://localhost:3001
# 后端: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

## 📁 项目结构

```
neural_agent/
├── backend/               # 后端服务
│   └── core/            # 核心模块
│       ├── agents/       # Agent 框架
│       ├── memory/       # 记忆系统
│       ├── workflow/     # 工作流引擎
│       ├── rag/          # RAG 系统
│       ├── vector_store/ # 向量存储
│       └── monitoring/   # 监控系统
├── frontend/             # 前端应用
│   └── src/
│       ├── pages/       # 页面组件
│       └── components/  # UI 组件
├── tests/               # 测试文件
└── docs/                # 文档
```

## 📈 系统架构

{architecture}

## 🔧 核心模块

| 模块 | 功能 | 状态 |
|------|------|------|
"""

        for module in self.stats["modules"]:
            module_name = module["name"].replace("_", " ").title()
            files_count = len(module["files"])
            readme_content += f"| {module_name} | {files_count} 个文件 | ✅ |\n"

        readme_content += f"""
## 📚 文档

- [可视化文档](docs/index.html) - 包含架构图、流程图、时序图
- [部署指南](DEPLOYMENT_GUIDE.md) - 完整部署文档
- [优化报告](OPTIMIZATION_REPORT.md) - 性能优化建议

## 🧪 测试

```bash
# 运行所有测试
python tests/test_comprehensive.py

# 运行性能测试
python benchmarks/performance.py
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**版本**: 1.0.0  
**最后更新**: {now}
"""

        readme_path = self.project_root / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"✅ README.md 已更新")

    def run(self):
        """运行更新"""
        print("="*80)
        print("🧠 NeuralAgent 文档自动更新")
        print("="*80)

        self.update_documentation()

        print("\n" + "="*80)
        print("✅ 文档更新完成!")
        print("="*80)
        print("\n📖 查看更新后的文档:")
        print("   - 可视化文档: http://localhost:8080/")
        print("   - README: README.md")
        print()


if __name__ == "__main__":
    updater = DocumentationUpdater()
    updater.run()
