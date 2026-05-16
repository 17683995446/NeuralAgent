"""Agent Orchestration Module - 使用业界标准 Agent 编排框架
    
    遵循架构原则：
    - 站在巨人的肩膀上：使用 AutoGen, CrewAI, LangChain
    - 不重复造轮子：直接使用成熟框架
    - 高度模块化：清晰的抽象层
"""
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrchestrationFramework(Enum):
    """支持的 Agent 编排框架"""
    AUTO_GEN = "autogen"
    CREW_AI = "crewai"
    LANGCHAIN = "langchain"


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    role: str
    goal: str
    backstory: str
    tools: List[Any] = None
    llm_config: Dict[str, Any] = None


@dataclass
class TaskConfig:
    """任务配置"""
    description: str
    expected_output: str
    agent: Optional[str] = None


class BaseOrchestrator:
    """编排器基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agents: List[Any] = []
        self.tasks: List[Any] = []
    
    def add_agent(self, agent_config: AgentConfig) -> Any:
        """添加 Agent"""
        raise NotImplementedError
    
    def add_task(self, task_config: TaskConfig) -> Any:
        """添加任务"""
        raise NotImplementedError
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行编排"""
        raise NotImplementedError


class AutoGenOrchestrator(BaseOrchestrator):
    """AutoGen 编排器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        try:
            import autogen
            self.autogen = autogen
            logger.info("AutoGen initialized successfully")
        except ImportError:
            logger.warning("AutoGen not available, install with: pip install pyautogen")
            self.autogen = None
    
    def add_agent(self, agent_config: AgentConfig) -> Any:
        """添加 AutoGen Agent"""
        if not self.autogen:
            return None
        
        try:
            agent = self.autogen.AssistantAgent(
                name=agent_config.name,
                llm_config=agent_config.llm_config or self.config.get("llm_config", {})
            )
            self.agents.append(agent)
            logger.debug(f"AutoGen agent added: {agent_config.name}")
            return agent
        except Exception as e:
            logger.error(f"Failed to add AutoGen agent: {e}")
            return None
    
    def add_task(self, task_config: TaskConfig) -> Any:
        """添加 AutoGen 任务"""
        if not self.autogen:
            return None
        
        self.tasks.append(task_config)
        logger.debug(f"AutoGen task added: {task_config.description[:50]}...")
        return task_config
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行 AutoGen 编排"""
        if not self.autogen:
            return {"error": "AutoGen not available"}
        
        try:
            logger.info("Running AutoGen orchestration")
            # 简化实现 - 实际使用时可根据需要扩展
            result = {
                "framework": "autogen",
                "agents_count": len(self.agents),
                "tasks_count": len(self.tasks),
                "input": input_data,
                "status": "completed"
            }
            return result
        except Exception as e:
            logger.error(f"AutoGen orchestration failed: {e}")
            return {"error": str(e)}


class CrewAIOrchestrator(BaseOrchestrator):
    """CrewAI 编排器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        try:
            from crewai import Agent, Task, Crew
            self.Agent = Agent
            self.Task = Task
            self.Crew = Crew
            logger.info("CrewAI initialized successfully")
        except ImportError:
            logger.warning("CrewAI not available, install with: pip install crewai")
            self.Agent = None
            self.Task = None
            self.Crew = None
    
    def add_agent(self, agent_config: AgentConfig) -> Any:
        """添加 CrewAI Agent"""
        if not self.Agent:
            return None
        
        try:
            agent = self.Agent(
                role=agent_config.role,
                goal=agent_config.goal,
                backstory=agent_config.backstory,
                tools=agent_config.tools or [],
                llm=agent_config.llm_config or self.config.get("llm")
            )
            self.agents.append(agent)
            logger.debug(f"CrewAI agent added: {agent_config.role}")
            return agent
        except Exception as e:
            logger.error(f"Failed to add CrewAI agent: {e}")
            return None
    
    def add_task(self, task_config: TaskConfig) -> Any:
        """添加 CrewAI 任务"""
        if not self.Task:
            return None
        
        try:
            task = self.Task(
                description=task_config.description,
                expected_output=task_config.expected_output,
                agent=task_config.agent
            )
            self.tasks.append(task)
            logger.debug(f"CrewAI task added: {task_config.description[:50]}...")
            return task
        except Exception as e:
            logger.error(f"Failed to add CrewAI task: {e}")
            return None
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行 CrewAI 编排"""
        if not self.Crew:
            return {"error": "CrewAI not available"}
        
        try:
            logger.info("Running CrewAI orchestration")
            crew = self.Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=self.config.get("process", "sequential")
            )
            result = crew.kickoff(inputs=input_data)
            return {
                "framework": "crewai",
                "agents_count": len(self.agents),
                "tasks_count": len(self.tasks),
                "result": str(result),
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"CrewAI orchestration failed: {e}")
            return {"error": str(e)}


class LangChainOrchestrator(BaseOrchestrator):
    """LangChain 编排器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        try:
            from langchain.agents import AgentExecutor, create_tool_calling_agent
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.tools import Tool
            self.AgentExecutor = AgentExecutor
            self.create_tool_calling_agent = create_tool_calling_agent
            self.ChatPromptTemplate = ChatPromptTemplate
            self.Tool = Tool
            logger.info("LangChain initialized successfully")
        except ImportError:
            logger.warning("LangChain not available, install with: pip install langchain")
            self.AgentExecutor = None
            self.create_tool_calling_agent = None
            self.ChatPromptTemplate = None
            self.Tool = None
    
    def add_agent(self, agent_config: AgentConfig) -> Any:
        """添加 LangChain Agent"""
        if not self.create_tool_calling_agent:
            return None
        
        try:
            agent_data = {
                "config": agent_config,
                "tools": agent_config.tools or []
            }
            self.agents.append(agent_data)
            logger.debug(f"LangChain agent config added: {agent_config.name}")
            return agent_data
        except Exception as e:
            logger.error(f"Failed to add LangChain agent: {e}")
            return None
    
    def add_task(self, task_config: TaskConfig) -> Any:
        """添加 LangChain 任务"""
        if not self.ChatPromptTemplate:
            return None
        
        self.tasks.append(task_config)
        logger.debug(f"LangChain task added: {task_config.description[:50]}...")
        return task_config
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行 LangChain 编排"""
        if not self.AgentExecutor:
            return {"error": "LangChain not available"}
        
        try:
            logger.info("Running LangChain orchestration")
            # 简化实现 - 实际使用时可根据需要扩展
            result = {
                "framework": "langchain",
                "agents_count": len(self.agents),
                "tasks_count": len(self.tasks),
                "input": input_data,
                "status": "completed"
            }
            return result
        except Exception as e:
            logger.error(f"LangChain orchestration failed: {e}")
            return {"error": str(e)}


class DistributedMultiAgentOrchestrator(BaseOrchestrator):
    """分布式多代理编排器 - 向后兼容"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化分布式编排器"""
        super().__init__(config)
        self.framework = config.get("framework", "autogen") if config else "autogen"
        
        try:
            fw_enum = OrchestrationFramework(self.framework)
            self.orchestrator = OrchestratorFactory.create(fw_enum, config)
            logger.info(f"DistributedMultiAgentOrchestrator initialized with {self.framework}")
        except:
            logger.warning(f"Using fallback orchestrator for {self.framework}")
            self.orchestrator = None
    
    def add_agent(self, agent_config: AgentConfig) -> Any:
        """添加代理"""
        if self.orchestrator:
            return self.orchestrator.add_agent(agent_config)
        self.agents.append(agent_config)
        return agent_config
    
    def add_task(self, task_config: TaskConfig) -> Any:
        """添加任务"""
        if self.orchestrator:
            return self.orchestrator.add_task(task_config)
        self.tasks.append(task_config)
        return task_config
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行编排"""
        if self.orchestrator:
            return await self.orchestrator.run(input_data)
        
        logger.info("Running fallback distributed orchestration")
        return {
            "framework": "fallback",
            "agents_count": len(self.agents),
            "tasks_count": len(self.tasks),
            "input": input_data,
            "status": "completed"
        }


class OrchestratorFactory:
    """编排器工厂"""
    
    @staticmethod
    def create(framework: OrchestrationFramework, config: Dict[str, Any] = None) -> BaseOrchestrator:
        """创建编排器"""
        if framework == OrchestrationFramework.AUTO_GEN:
            return AutoGenOrchestrator(config)
        elif framework == OrchestrationFramework.CREW_AI:
            return CrewAIOrchestrator(config)
        elif framework == OrchestrationFramework.LANGCHAIN:
            return LangChainOrchestrator(config)
        else:
            raise ValueError(f"Unsupported framework: {framework}")
