"""
NeuralAgent - Plugins Package
插件包初始化
"""
from .plugin_manager import (
    NeuralAgentPlugin,
    PluginManager,
    PluginInfo,
    PluginStatus,
    HookType,
    SimpleLoggingPlugin,
    get_plugin_manager,
    set_plugin_manager
)

__all__ = [
    "NeuralAgentPlugin",
    "PluginManager",
    "PluginInfo",
    "PluginStatus",
    "HookType",
    "SimpleLoggingPlugin",
    "get_plugin_manager",
    "set_plugin_manager"
]
