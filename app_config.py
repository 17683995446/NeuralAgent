"""
NeuralAgent 配置管理系统
支持环境变量和配置文件
"""

import os
import yaml
import json
from typing import Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from functools import lru_cache


@dataclass
class APIConfig:
    """API 配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list = field(default_factory=lambda: ["*"])
    enable_websocket: bool = True
    enable_docs: bool = True


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "mock"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    timeout: int = 30
    max_retries: int = 3


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    l1_max_size: int = 1000
    l1_default_ttl: int = 3600
    enable_l2: bool = False
    redis_url: str = "redis://localhost:6379/0"


@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    prometheus_port: int = 8001
    enable_metrics: bool = True
    enable_health_check: bool = True


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    backend: str = "inmemory"
    redis_url: Optional[str] = None
    enable_enhanced: bool = True
    enable_emotional_memory: bool = True
    enable_intent_prediction: bool = True
    enable_cross_session: bool = True


@dataclass
class WorkflowConfig:
    """工作流配置"""
    enabled: bool = True
    parallel_execution: bool = True
    max_workflows: int = 100
    default_timeout: int = 300


@dataclass
class NeuralAgentConfig:
    """完整配置"""
    app_name: str = "NeuralAgent"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    api: APIConfig = field(default_factory=APIConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    
    def __post_init__(self):
        # 从环境变量加载配置 - 仅在默认初始化时调用
        # 对于通过 from_dict/from_yaml 创建的实例，不会再次调用此方法
        pass
    
    def load_from_env(self):
        """从环境变量加载配置（手动调用）"""
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_map = {
            "APP_NAME": "app_name",
            "ENVIRONMENT": "environment",
            "DEBUG": ("debug", lambda v: v.lower() in ("true", "1", "yes")),
            "LOG_LEVEL": "log_level",
            
            "API_HOST": ("api", "host"),
            "API_PORT": ("api", "port", lambda v: int(v)),
            "ENABLE_WEBSOCKET": ("api", "enable_websocket", lambda v: v.lower() in ("true", "1", "yes")),
            
            "LLM_PROVIDER": ("llm", "provider"),
            "LLM_MODEL": ("llm", "model"),
            "LLM_API_KEY": ("llm", "api_key"),
            "LLM_BASE_URL": ("llm", "base_url"),
            "LLM_TEMPERATURE": ("llm", "temperature", lambda v: float(v)),
            "LLM_MAX_TOKENS": ("llm", "max_tokens", lambda v: int(v)),
            
            "CACHE_ENABLED": ("cache", "enabled", lambda v: v.lower() in ("true", "1", "yes")),
            "CACHE_L2_ENABLED": ("cache", "enable_l2", lambda v: v.lower() in ("true", "1", "yes")),
            "REDIS_URL": ("cache", "redis_url"),
            
            "MONITORING_ENABLED": ("monitoring", "enabled", lambda v: v.lower() in ("true", "1", "yes")),
            "PROMETHEUS_PORT": ("monitoring", "prometheus_port", lambda v: int(v)),
        }
        
        for env_key, target in env_map.items():
            value = os.environ.get(env_key)
            if value is not None:
                if isinstance(target, tuple):
                    if len(target) == 2:
                        obj_key, field_name = target
                        converter = str
                    else:
                        obj_key, field_name, converter = target
                    
                    obj = getattr(self, obj_key)
                    setattr(obj, field_name, converter(value))
                else:
                    setattr(self, target, value)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'NeuralAgentConfig':
        """从字典创建配置"""
        # 直接创建，不调用 __post_init__（不加载环境变量）
        # 先构建参数
        kwargs = {}
        
        # 处理顶级字段
        for key in ['app_name', 'environment', 'debug', 'log_level']:
            if key in config_dict:
                kwargs[key] = config_dict[key]
        
        # 处理子配置
        subconfig_classes = {
            'api': APIConfig,
            'llm': LLMConfig,
            'cache': CacheConfig,
            'monitoring': MonitoringConfig,
            'memory': MemoryConfig,
            'workflow': WorkflowConfig,
        }
        
        for key, subconfig_cls in subconfig_classes.items():
            if key in config_dict and isinstance(config_dict[key], dict):
                kwargs[key] = subconfig_cls(**config_dict[key])
        
        # 创建实例
        config = cls(**kwargs)
        
        # 注意：不调用 load_from_env，因为我们已经从 dict 加载了
        
        return config
    
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> 'NeuralAgentConfig':
        """从 YAML 文件加载"""
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {yaml_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        return cls.from_dict(config_dict or {})
    
    @classmethod
    def from_json(cls, json_path: Union[str, Path]) -> 'NeuralAgentConfig':
        """从 JSON 文件加载"""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {json_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return cls.from_dict(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "app_name": self.app_name,
            "environment": self.environment,
            "debug": self.debug,
            "log_level": self.log_level,
            "api": asdict(self.api),
            "llm": asdict(self.llm),
            "cache": asdict(self.cache),
            "monitoring": asdict(self.monitoring),
            "memory": asdict(self.memory),
            "workflow": asdict(self.workflow),
        }
    
    def to_yaml(self, yaml_path: Union[str, Path]):
        """保存为 YAML 文件"""
        with open(Path(yaml_path), 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)
    
    def to_json(self, json_path: Union[str, Path]):
        """保存为 JSON 文件"""
        with open(Path(json_path), 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    def validate(self):
        """验证配置"""
        if self.llm.provider not in ["mock", "openai", "anthropic", "ollama", "siliconflow"]:
            raise ValueError(f"不支持的 LLM provider: {self.llm.provider}")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"不支持的日志级别: {self.log_level}")
        
        return True


@lru_cache(maxsize=1)
def get_config() -> NeuralAgentConfig:
    """获取配置单例"""
    # 尝试从配置文件加载
    config_files = [
        "config.yaml",
        "config.json",
        "config/config.yaml",
        "config/config.json",
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    config = NeuralAgentConfig.from_yaml(config_file)
                    config.load_from_env()
                    return config
                elif config_file.endswith('.json'):
                    config = NeuralAgentConfig.from_json(config_file)
                    config.load_from_env()
                    return config
            except Exception as e:
                print(f"加载配置文件失败: {config_file}, 错误: {e}")
    
    # 使用默认配置
    config = NeuralAgentConfig()
    config.load_from_env()
    return config
