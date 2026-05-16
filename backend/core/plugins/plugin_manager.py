"""
NeuralAgent - Plugin Architecture
插件架构系统：加载、管理、钩子
"""
import importlib
import inspect
import os
import sys
from abc import ABC, abstractmethod
from typing import (
    Dict,
    Any,
    List,
    Optional,
    Callable,
    Type,
    Set,
    Union
)
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging


class PluginStatus(Enum):
    """插件状态"""
    DISABLED = "disabled"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    ERROR = "error"


class HookType(Enum):
    """钩子类型"""
    BEFORE_REQUEST = "before_request"
    AFTER_REQUEST = "after_request"
    BEFORE_WORKFLOW = "before_workflow"
    AFTER_WORKFLOW = "after_workflow"
    BEFORE_STEP = "before_step"
    AFTER_STEP = "after_step"
    ON_ERROR = "on_error"
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"
    CUSTOM = "custom"


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str = ""
    url: str = ""
    license: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class NeuralAgentPlugin(ABC):
    """NeuralAgent插件基类"""
    
    def __init__(self):
        self._hooks: Dict[HookType, List[Callable]] = {}
        self._info = self.get_info()
        self._status = PluginStatus.DISABLED
        self._config: Dict[str, Any] = {}
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        pass
    
    async def on_load(self) -> None:
        """插件加载时调用"""
        pass
    
    async def on_unload(self) -> None:
        """插件卸载时调用"""
        pass
    
    async def on_initialize(self, config: Dict[str, Any]) -> None:
        """插件初始化时调用"""
        self._config = config
    
    async def on_activate(self) -> None:
        """插件激活时调用"""
        pass
    
    async def on_deactivate(self) -> None:
        """插件停用时调用"""
        pass
    
    def register_hook(self, hook_type: HookType, func: Callable) -> None:
        """注册钩子"""
        if hook_type not in self._hooks:
            self._hooks[hook_type] = []
        self._hooks[hook_type].append(func)
    
    def get_hooks(self, hook_type: HookType) -> List[Callable]:
        """获取钩子"""
        return self._hooks.get(hook_type, [])
    
    @property
    def info(self) -> PluginInfo:
        return self._info
    
    @property
    def status(self) -> PluginStatus:
        return self._status
    
    @status.setter
    def status(self, value: PluginStatus) -> None:
        self._status = value
    
    @property
    def config(self) -> Dict[str, Any]:
        return self._config


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        self.plugins: Dict[str, NeuralAgentPlugin] = {}
        self.plugin_dirs = plugin_dirs or []
        self.hook_registry: Dict[HookType, List[Tuple[str, Callable]]] = {}
        self.logger = logging.getLogger(__name__)
        self._configs: Dict[str, Dict[str, Any]] = {}
    
    def discover_plugins(self) -> List[str]:
        """发现可用插件"""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            dir_path = Path(plugin_dir)
            if not dir_path.exists():
                continue
            
            self.logger.info(f"Discovering plugins in: {plugin_dir}")
            
            for item in dir_path.iterdir():
                if item.is_dir() and not item.name.startswith('_'):
                    if (item / "__init__.py").exists():
                        discovered.append(item.name)
                    elif item.suffix == '.py' and not item.name.startswith('_'):
                        discovered.append(item.stem)
        
        return discovered
    
    def register_plugin(self, plugin: NeuralAgentPlugin) -> "PluginManager":
        """注册插件"""
        name = plugin.info.name
        if name in self.plugins:
            self.logger.warning(f"Plugin '{name}' already registered, overwriting")
        
        self.plugins[name] = plugin
        plugin.status = PluginStatus.LOADED
        self.logger.info(f"Plugin registered: {name} v{plugin.info.version}")
        return self
    
    async def load_plugin(
        self,
        plugin_name: str,
        plugin_class: Optional[Type[NeuralAgentPlugin]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> NeuralAgentPlugin:
        """加载插件"""
        config = config or {}
        self._configs[plugin_name] = config
        
        if plugin_class:
            plugin = plugin_class()
        else:
            plugin = self._import_plugin(plugin_name)
        
        self.register_plugin(plugin)
        
        try:
            await plugin.on_load()
            plugin.status = PluginStatus.LOADED
            
            await plugin.on_initialize(config)
            plugin.status = PluginStatus.INITIALIZED
            
            await self._register_plugin_hooks(plugin)
            
            return plugin
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            plugin.status = PluginStatus.ERROR
            raise
    
    def _import_plugin(self, plugin_name: str) -> NeuralAgentPlugin:
        """导入插件"""
        for plugin_dir in self.plugin_dirs:
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            try:
                module = importlib.import_module(plugin_name)
                
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, NeuralAgentPlugin) and
                        obj != NeuralAgentPlugin):
                        self.logger.info(f"Found plugin class: {name}")
                        return obj()
                
            except ImportError as e:
                self.logger.debug(f"Could not import {plugin_name} from {plugin_dir}: {e}")
                continue
        
        raise ImportError(f"Could not find plugin: {plugin_name}")
    
    async def _register_plugin_hooks(self, plugin: NeuralAgentPlugin) -> None:
        """注册插件钩子"""
        for hook_type in HookType:
            for hook_func in plugin.get_hooks(hook_type):
                if hook_type not in self.hook_registry:
                    self.hook_registry[hook_type] = []
                self.hook_registry[hook_type].append((plugin.info.name, hook_func))
        
        self.logger.debug(f"Registered hooks for plugin: {plugin.info.name}")
    
    async def activate_plugin(self, plugin_name: str) -> None:
        """激活插件"""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin not found: {plugin_name}")
        
        plugin = self.plugins[plugin_name]
        
        if plugin.status == PluginStatus.ACTIVE:
            return
        
        await plugin.on_activate()
        plugin.status = PluginStatus.ACTIVE
        self.logger.info(f"Plugin activated: {plugin_name}")
    
    async def deactivate_plugin(self, plugin_name: str) -> None:
        """停用插件"""
        if plugin_name not in self.plugins:
            return
        
        plugin = self.plugins[plugin_name]
        
        if plugin.status != PluginStatus.ACTIVE:
            return
        
        await plugin.on_deactivate()
        plugin.status = PluginStatus.INITIALIZED
        self.logger.info(f"Plugin deactivated: {plugin_name}")
    
    async def unload_plugin(self, plugin_name: str) -> None:
        """卸载插件"""
        if plugin_name not in self.plugins:
            return
        
        plugin = self.plugins[plugin_name]
        
        await self.deactivate_plugin(plugin_name)
        
        await plugin.on_unload()
        
        for hook_type in self.hook_registry:
            self.hook_registry[hook_type] = [
                (name, func) for name, func in self.hook_registry[hook_type]
                if name != plugin_name
            ]
        
        del self.plugins[plugin_name]
        self.logger.info(f"Plugin unloaded: {plugin_name}")
    
    async def trigger_hook(
        self,
        hook_type: HookType,
        *args,
        **kwargs
    ) -> List[Any]:
        """触发钩子"""
        results = []
        
        if hook_type not in self.hook_registry:
            return results
        
        for plugin_name, hook_func in self.hook_registry[hook_type]:
            plugin = self.plugins.get(plugin_name)
            if not plugin or plugin.status != PluginStatus.ACTIVE:
                continue
            
            try:
                if inspect.iscoroutinefunction(hook_func):
                    result = await hook_func(*args, **kwargs)
                else:
                    result = hook_func(*args, **kwargs)
                results.append((plugin_name, result))
            except Exception as e:
                self.logger.error(
                    f"Hook error in plugin {plugin_name}, hook {hook_type}: {e}"
                )
        
        return results
    
    async def trigger_before_request(self, request: Any) -> None:
        """触发请求前钩子"""
        await self.trigger_hook(HookType.BEFORE_REQUEST, request)
    
    async def trigger_after_request(self, request: Any, response: Any) -> None:
        """触发请求后钩子"""
        await self.trigger_hook(HookType.AFTER_REQUEST, request, response)
    
    async def trigger_on_error(self, error: Exception, context: Any) -> None:
        """触发错误钩子"""
        await self.trigger_hook(HookType.ON_ERROR, error, context)
    
    async def trigger_on_startup(self) -> None:
        """触发启动钩子"""
        await self.trigger_hook(HookType.ON_STARTUP)
    
    async def trigger_on_shutdown(self) -> None:
        """触发关闭钩子"""
        await self.trigger_hook(HookType.ON_SHUTDOWN)
    
    def get_plugin(self, name: str) -> Optional[NeuralAgentPlugin]:
        """获取插件"""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, NeuralAgentPlugin]:
        """获取所有插件"""
        return self.plugins.copy()
    
    def get_active_plugins(self) -> List[str]:
        """获取活跃插件列表"""
        return [
            name for name, plugin in self.plugins.items()
            if plugin.status == PluginStatus.ACTIVE
        ]
    
    async def load_all_plugins(self, configs: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """加载所有发现的插件"""
        configs = configs or {}
        discovered = self.discover_plugins()
        
        for plugin_name in discovered:
            try:
                config = configs.get(plugin_name, {})
                await self.load_plugin(plugin_name, config=config)
            except Exception as e:
                self.logger.error(f"Failed to auto-load plugin {plugin_name}: {e}")
    
    async def activate_all_plugins(self) -> None:
        """激活所有已加载的插件"""
        for plugin_name in list(self.plugins.keys()):
            try:
                await self.activate_plugin(plugin_name)
            except Exception as e:
                self.logger.error(f"Failed to activate plugin {plugin_name}: {e}")
    
    async def shutdown(self) -> None:
        """关闭插件管理器"""
        await self.trigger_on_shutdown()
        
        for plugin_name in list(self.plugins.keys()):
            try:
                await self.unload_plugin(plugin_name)
            except Exception as e:
                self.logger.error(f"Error unloading plugin {plugin_name}: {e}")


_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(plugin_dirs: Optional[List[str]] = None) -> PluginManager:
    """获取全局插件管理器"""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager(plugin_dirs)
    return _global_plugin_manager


def set_plugin_manager(manager: PluginManager) -> None:
    """设置全局插件管理器"""
    global _global_plugin_manager
    _global_plugin_manager = manager


class SimpleLoggingPlugin(NeuralAgentPlugin):
    """简单日志插件示例"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="simple_logging",
            version="1.0.0",
            description="Simple logging plugin for NeuralAgent",
            author="NeuralAgent Team",
            tags=["logging", "debug"]
        )
    
    async def on_initialize(self, config: Dict[str, Any]) -> None:
        await super().on_initialize(config)
        self.register_hook(HookType.BEFORE_REQUEST, self._log_before_request)
        self.register_hook(HookType.AFTER_REQUEST, self._log_after_request)
    
    async def _log_before_request(self, request: Any) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Before request: {request}")
    
    async def _log_after_request(self, request: Any, response: Any) -> None:
        self.logger.info(f"After request: {request} -> {response}")
