"""
NeuralAgent Optimized Core Dependencies
优化的核心依赖配置 - 使用业界最佳开源工具
"""

# ==============================================================================
# 配置管理 - 使用 Dynaconf（业界标准）
# ==============================================================================
# dynconf 3.x 提供：
# - 多环境配置（YAML/TOML/JSON/ENV）
# - 环境变量自动映射
# - 敏感信息加密
# - 懒加载

# ==============================================================================
# 日志系统 - 使用 structlog（已完成）
# ==============================================================================
# structlog 24.x 提供：
# - 结构化日志输出
# - 自动请求上下文
# - 多输出目标
# - 性能优化

# ==============================================================================
# 缓存系统 - 使用 Redis + Django-redis
# ==============================================================================
# django-redis 5.x 提供：
# - 统一的缓存接口
# - 自动序列化
# - 连接池管理
# - 分布式锁

# ==============================================================================
# 监控和追踪 - 使用 OpenTelemetry
# ==============================================================================
# opentelemetry-python 1.x 提供：
# - 分布式追踪
# - 指标采集
# - 日志关联
# - 多后端支持（Jaeger, Zipkin, OTLP）

# ==============================================================================
# API 限流 - 使用 SlowApi
# ==============================================================================
# slowapi 0.1.x 提供：
# - 基于 Flask/Python 的请求限流
# - 多种限流策略
# - 自定义响应
# - Redis 支持

# ==============================================================================
# 重试机制 - 使用 Tenacity（已完成）
# ==============================================================================
# tenacity 8.x 提供：
# - 指数退避
# - Jitter
# - 条件重试
# - 统计信息

# ==============================================================================
# 断路器 - 使用 PyCircuitBreaker
# ==============================================================================
# pybreaker 1.x 提供：
# - 断路器模式
# - 故障计数
# - 自动恢复

# ==============================================================================
# 验证 - 使用 Email-Validator
# ==============================================================================
# email-validator 2.x 提供：
# - RFC 5322 验证
# - MX 记录检查
# - 类型提示

# ==============================================================================
# 数据序列化 - 使用 Orjson（已可选使用）
# ==============================================================================
# orjson 3.x 提供：
# - 3-10x 速度提升
# - 完整类型支持
# - 日期时间处理

# ==============================================================================
# HTTP 客户端 - 使用 httpx（已完成）
# ==============================================================================
# httpx 0.27.x 提供：
# - 同步/异步
# - HTTP/2 支持
# - 自动重试

# ==============================================================================
# 依赖注入 - 使用 Lagom
# ==============================================================================
# lagom 1.x 提供：
# - 轻量级 DI 容器
# - 自动装配
# - 生命周期管理

# ==============================================================================
# 配置示例
# ==============================================================================

OPTIMIZED_DEPENDENCIES = {
    # 配置管理
    "dynaconf": {
        "version": "3.2.0",
        "use": ["multi_env", "vault", "redis"],
        "alternatives": ["hydra", "omegaconf"]
    },

    # 监控和可观测性
    "opentelemetry-api": {
        "version": "1.25.0",
        "use": ["tracing", "metrics", "logging"],
        "exporters": ["jaeger", "prometheus", "otlp"]
    },

    # 限流
    "slowapi": {
        "version": "0.1.9",
        "use": ["rate_limit", "storage_redis"],
        "strategies": ["fixed", "sliding", "token_bucket"]
    },

    # 缓存
    "django-redis": {
        "version": "5.4.0",
        "use": ["cache", "session", "locks"],
        "serializers": ["pickle", "json", "msgpack"]
    },

    # 依赖注入
    "lagom": {
        "version": "1.5.0",
        "use": ["di_container", "auto_wiring"]
    },

    # 数据验证
    "email-validator": {
        "version": "2.1.0",
        "use": ["validation", "deliverability"]
    },

    # 性能
    "orjson": {
        "version": "3.10.0",
        "use": ["fast_serialization", "datetime_handling"]
    },

    # 健康检查
    "django-health-check": {
        "version": "3.18.0",
        "use": ["database", "cache", "storage"]
    }
}

# ==============================================================================
# 推荐的生产依赖组合
# ==============================================================================

PRODUCTION_STACK = """
# 推荐的 Production-ready 依赖组合

# 核心框架
fastapi==0.110.0
uvicorn[standard]==0.27.1
pydantic==2.7.0
pydantic-settings==2.2.1

# 配置管理（替换自定义配置）
dynaconf==3.2.0

# 日志和监控（业界标准）
structlog==24.4.0
opentelemetry-api==1.25.0
opentelemetry-sdk==1.25.0
opentelemetry-exporter-otlp==1.25.0
opentelemetry-instrumentation-fastapi==0.46b0

# 限流（业界标准）
slowapi==0.1.9

# 缓存（使用 Redis）
django-redis==5.4.0
redis==5.0.3

# 断路器
pybreaker==1.0.0

# 重试（已有）
tenacity==8.2.3

# 数据验证
email-validator==2.1.0

# 性能优化
orjson==3.10.0
uvloop==0.19.0

# 安全
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# 数据库
sqlalchemy==2.0.29
asyncpg==0.29.0

# 健康检查
django-health-check==3.18.0

# 测试
pytest==8.2.0
pytest-asyncio==0.23.5
pytest-cov==4.1.0
pytest-xdist==3.5.0  # 并行测试
"""

def get_optimization_recommendations():
    """获取优化建议"""
    return {
        "high_priority": [
            {
                "area": "配置管理",
                "current": "自定义配置加载",
                "recommendation": "使用 dynaconf",
                "benefits": ["多环境支持", "加密敏感信息", "环境变量映射"],
                "effort": "medium"
            },
            {
                "area": "监控追踪",
                "current": "基础 Prometheus",
                "recommendation": "使用 OpenTelemetry",
                "benefits": ["分布式追踪", "请求链路", "日志关联"],
                "effort": "medium"
            },
            {
                "area": "限流",
                "current": "自定义限流",
                "recommendation": "使用 slowapi",
                "benefits": ["多种策略", "Redis 支持", "统计信息"],
                "effort": "low"
            },
            {
                "area": "缓存",
                "current": "自实现缓存",
                "recommendation": "使用 django-redis",
                "benefits": ["统一接口", "连接池", "分布式锁"],
                "effort": "low"
            }
        ],
        "medium_priority": [
            {
                "area": "依赖注入",
                "current": "手动依赖注入",
                "recommendation": "使用 lagom",
                "benefits": ["自动装配", "生命周期管理"],
                "effort": "high"
            },
            {
                "area": "数据验证",
                "current": "基础 Pydantic",
                "recommendation": "添加 email-validator",
                "benefits": ["完整验证", "MX 检查"],
                "effort": "low"
            }
        ],
        "low_priority": [
            {
                "area": "序列化",
                "current": "标准 JSON",
                "recommendation": "使用 orjson",
                "benefits": ["3-10x 性能提升", "更好的日期处理"],
                "effort": "low"
            }
        ]
    }
