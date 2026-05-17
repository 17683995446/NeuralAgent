"""
NeuralAgent 产品化配置管理系统

支持多种配置源：
- YAML 文件
- 环境变量
- 配置中心
- 默认值
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Type, TypeVar, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import yaml
import os
import structlog

logger = structlog.get_logger()


T = TypeVar('T', bound='BaseConfig')


@dataclass
class ConfigSource:
    """配置源"""
    name: str
    priority: int  # 优先级高的覆盖低的
    data: Dict[str, Any] = field(default_factory=dict)


class BaseProductConfig(BaseSettings):
    """产品化配置基类 - 所有模块配置的基础"""
    
    enabled: bool = Field(default=True, description="是否启用该模块")
    log_level: str = Field(default="INFO", description="日志级别")
    
    class Config:
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"


class CacheConfig(BaseProductConfig):
    """缓存模块配置"""
    
    class Config(BaseProductConfig.Config):
        env_prefix = "CACHE_"
    
    max_size: int = Field(default=10000, description="最大缓存条目数")
    ttl: int = Field(default=3600, description="默认TTL(秒)")
    eviction_policy: str = Field(default="lru", description="淘汰策略")


class MemoryConfig(BaseProductConfig):
    """记忆模块配置"""
    
    class Config(BaseProductConfig.Config):
        env_prefix = "MEMORY_"
    
    backend: str = Field(default="memory", description="存储后端")
    redis_url: Optional[str] = Field(default=None, description="Redis URL")
    max_memory_entries: int = Field(default=100000, description="最大记忆条目")


class AgentsConfig(BaseProductConfig):
    """Agent模块配置"""
    
    class Config(BaseProductConfig.Config):
        env_prefix = "AGENTS_"
    
    max_concurrent_agents: int = Field(default=10, description="最大并发Agent数")
    task_timeout: int = Field(default=300, description="任务超时(秒)")


class LLMConfig(BaseProductConfig):
    """LLM集成配置"""
    
    class Config(BaseProductConfig.Config):
        env_prefix = "LLM_"
    
    provider: str = Field(default="openai", description="LLM提供商")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    model: str = Field(default="gpt-4", description="默认模型")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大Token数")


class SecurityConfig(BaseProductConfig):
    """安全配置"""
    
    class Config(BaseProductConfig.Config):
        env_prefix = "SECURITY_"
    
    jwt_secret: str = Field(default="dev-secret-change-in-production", description="JWT密钥")
    jwt_expiry_hours: int = Field(default=24, description="JWT过期时间(小时)")
    rate_limit_per_minute: int = Field(default=100, description="每分钟请求限制")
    enable_mfa: bool = Field(default=False, description="是否启用MFA")


class MonitoringConfig(BaseProductConfig):
    """监控配置"""
    
    class Config(BaseProductConfig.Config):
        env_prefix = "MONITORING_"
    
    enabled: bool = Field(default=True, description="是否启用监控")
    prometheus_port: int = Field(default=9090, description="Prometheus端口")
    health_check_interval: int = Field(default=60, description="健康检查间隔(秒)")
    log_sampling_rate: float = Field(default=1.0, description="日志采样率")


class GlobalConfig(BaseProductConfig):
    """全局配置"""
    
    class Config(BaseProductConfig.Config):
        env_prefix = "NEURALAGENT_"
    
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")
    timezone: str = Field(default="UTC", description="时区")
    
    cache: CacheConfig = Field(default_factory=CacheConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


class ProductConfigManager:
    """产品化配置管理器"""
    
    def __init__(self):
        self._config: Optional[GlobalConfig] = None
        self._sources: List[ConfigSource] = []
    
    def load_yaml(self, filepath: str, priority: int = 50) -> "ProductConfigManager":
        """加载 YAML 配置文件"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            self._sources.append(ConfigSource(
                name=f"yaml:{filepath}",
                priority=priority,
                data=data
            ))
            logger.info(f"Loaded config from {filepath}")
        return self
    
    def load_env(self, prefix: str = "NEURALAGENT_", priority: int = 100) -> "ProductConfigManager":
        """加载环境变量"""
        env_data = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                nested_key = key[len(prefix):].lower().replace('__', '.')
                self._set_nested(env_data, nested_key, value)
        
        if env_data:
            self._sources.append(ConfigSource(
                name="environment",
                priority=priority,
                data=env_data
            ))
            logger.info("Loaded config from environment")
        return self
    
    def load_defaults(self, priority: int = 10) -> "ProductConfigManager":
        """加载默认配置"""
        self._sources.append(ConfigSource(
            name="defaults",
            priority=priority,
            data={}
        ))
        return self
    
    def build(self) -> GlobalConfig:
        """构建最终配置"""
        self._sources.sort(key=lambda s: s.priority)
        
        merged_data = {}
        for source in self._sources:
            merged_data = self._deep_merge(merged_data, source.data)
        
        self._config = GlobalConfig(**merged_data)
        logger.info("Config built successfully", env=self._config.environment)
        return self._config
    
    def get(self) -> GlobalConfig:
        """获取当前配置"""
        if not self._config:
            self.load_defaults().load_env().build()
        return self._config
    
    @staticmethod
    def _deep_merge(dest: Dict, src: Dict) -> Dict:
        """深度合并字典"""
        for key, value in src.items():
            if key in dest and isinstance(dest[key], dict) and isinstance(value, dict):
                ProductConfigManager._deep_merge(dest[key], value)
            else:
                dest[key] = value
        return dest
    
    @staticmethod
    def _set_nested(data: Dict, key: str, value: str):
        """设置嵌套键值"""
        parts = key.split('.')
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value


_config_manager = ProductConfigManager()


def get_config() -> GlobalConfig:
    """获取全局配置（单例）"""
    return _config_manager.get()


def init_config(config_file: Optional[str] = None) -> GlobalConfig:
    """初始化配置系统"""
    manager = _config_manager.load_defaults()
    if config_file:
        manager.load_yaml(config_file)
    manager.load_env()
    return manager.build()
