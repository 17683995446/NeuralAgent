"""
NeuralAgent - Agent Base Module
Agent 基类定义
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class AgentType(str, Enum):
    """Agent 类型"""
    GENERAL = "general"
    RESEARCH = "research"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    SUPPORT = "support"


class AgentStatus(str, Enum):
    """Agent 状态"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    agent_type: AgentType = AgentType.GENERAL
    description: str = ""
    max_retries: int = 3
    timeout: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    """Agent 基类"""

    def __init__(self, config: AgentConfig):
        self.id = str(uuid.uuid4())
        self.config = config
        self.name = config.name
        self.agent_type = config.agent_type
        self.description = config.description
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    async def execute(self, task: str) -> Dict[str, Any]:
        """执行任务"""
        self.status = AgentStatus.RUNNING
        self.updated_at = datetime.now()

        try:
            result = await self._execute_task(task)

            self.status = AgentStatus.IDLE
            self.updated_at = datetime.now()

            return {
                "success": True,
                "agent_id": self.id,
                "result": result
            }

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.updated_at = datetime.now()

            return {
                "success": False,
                "agent_id": self.id,
                "error": str(e)
            }

    async def _execute_task(self, task: str) -> Any:
        """实际执行任务 - 子类实现"""
        return {"message": f"Agent {self.name} executed task: {task}"}

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.agent_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
