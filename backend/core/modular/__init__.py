"""
NeuralAgent 模块化产品化架构设计

核心原则：
1. 高度模块化 - 每个模块可独立使用
2. 产品化 - 每个模块有完整的API、文档、示例
3. 不重复造轮子 - 依赖成熟开源工具
4. 可观测性 - 每个模块都有监控和日志
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Type, Callable, Protocol
from enum import Enum
import structlog
from datetime import datetime

logger = structlog.get_logger()


class ModuleStatus(Enum):
    """模块状态"""
    EXPERIMENTAL = "experimental"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class ModuleCategory(Enum):
    """模块分类"""
    CORE = "core"
    INTEGRATION = "integration"
    INFRASTRUCTURE = "infrastructure"
    TOOLS = "tools"


@dataclass
class ModuleMetadata:
    """模块元数据 - 用于产品化"""
    name: str
    version: str
    category: ModuleCategory
    status: ModuleStatus
    description: str
    author: str = "NeuralAgent Team"
    dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    documentation_url: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category.value,
            "status": self.status.value,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
        }


class Module(Protocol):
    """模块协议 - 所有模块必须实现的接口"""
    
    @classmethod
    def metadata(cls) -> ModuleMetadata:
        """获取模块元数据"""
        ...
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化模块"""
        ...
    
    def health_check(self) -> bool:
        """健康检查"""
        ...
    
    def shutdown(self) -> None:
        """关闭模块"""
        ...


class ModuleRegistry:
    """
    模块注册表 - 核心产品化功能
    
    功能：
    1. 自动发现和注册模块
    2. 模块生命周期管理
    3. 依赖解析
    4. 配置管理
    """
    
    def __init__(self):
        self._modules: Dict[str, Type[Module]] = {}
        self._instances: Dict[str, Module] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        
    def register(self, module_cls: Type[Module]) -> Type[Module]:
        """装饰器：注册模块"""
        metadata = module_cls.metadata()
        self._modules[metadata.name] = module_cls
        logger.info(f"Module registered: {metadata.name} v{metadata.version}")
        return module_cls
    
    def get(self, name: str) -> Optional[Type[Module]]:
        """获取模块类"""
        return self._modules.get(name)
    
    def get_instance(self, name: str) -> Optional[Module]:
        """获取模块实例"""
        return self._instances.get(name)
    
    def initialize_module(self, name: str, config: Optional[Dict[str, Any]] = None) -> Module:
        """初始化模块"""
        module_cls = self.get(name)
        if not module_cls:
            raise ValueError(f"Module not found: {name}")
        
        metadata = module_cls.metadata()
        for dep in metadata.dependencies:
            if dep not in self._instances:
                logger.info(f"Initializing dependency: {dep}")
                self.initialize_module(dep)
        
        module = module_cls()
        config = config or self._configs.get(name, {})
        module.initialize(config)
        self._instances[name] = module
        logger.info(f"Module initialized: {name}")
        return module
    
    def set_config(self, name: str, config: Dict[str, Any]) -> None:
        """设置模块配置"""
        self._configs[name] = config
    
    def list_all(self) -> List[ModuleMetadata]:
        """列出所有模块"""
        return [mod.metadata() for mod in self._modules.values()]
    
    def list_by_category(self, category: ModuleCategory) -> List[ModuleMetadata]:
        """按分类列出模块"""
        return [
            mod.metadata()
            for mod in self._modules.values()
            if mod.metadata().category == category
        ]
    
    def health_check_all(self) -> Dict[str, bool]:
        """检查所有模块健康状态"""
        results = {}
        for name, instance in self._instances.items():
            try:
                results[name] = instance.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}", error=str(e))
                results[name] = False
        return results


registry = ModuleRegistry()
