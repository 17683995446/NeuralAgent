"""
NeuralAgent - Agent协作系统包
多Agent协作系统
"""
from .base import (
    BaseAgent,
    AgentConfig,
    AgentType,
    AgentStatus
)

from .multi_agent import (
    SimpleAgent,
    MultiAgentOrchestrator,
    AgentTask,
    CollaborationConfig,
    CollaborationMode,
    TaskStatus,
    create_multi_agent_system
)

__all__ = [
    "BaseAgent",
    "SimpleAgent",
    "MultiAgentOrchestrator",
    "AgentConfig",
    "AgentTask",
    "CollaborationConfig",
    "AgentType",
    "AgentStatus",
    "CollaborationMode",
    "TaskStatus",
    "create_multi_agent_system"
]
