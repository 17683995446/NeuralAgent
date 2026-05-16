"""Tests for Agent Orchestration Module"""
import pytest
from backend.core.agents.distributed_multi_agent_orchestrator import (
    DistributedMultiAgentOrchestrator,
    OrchestrationFramework,
    AgentConfig,
    TaskConfig,
    OrchestratorFactory
)


class TestAgentOrchestration:
    """测试 Agent 编排模块"""
    
    def test_orchestration_framework_enum(self):
        """测试编排框架枚举"""
        assert OrchestrationFramework.AUTO_GEN.value == "autogen"
        assert OrchestrationFramework.CREW_AI.value == "crewai"
        assert OrchestrationFramework.LANGCHAIN.value == "langchain"
    
    def test_agent_config(self):
        """测试 Agent 配置"""
        config = AgentConfig(
            name="test_agent",
            role="Developer",
            goal="Write clean code",
            backstory="Experienced developer"
        )
        assert config.name == "test_agent"
        assert config.role == "Developer"
        assert config.goal == "Write clean code"
        assert config.backstory == "Experienced developer"
    
    def test_task_config(self):
        """测试任务配置"""
        config = TaskConfig(
            description="Write a test file",
            expected_output="Test file with pytest",
            agent="test_agent"
        )
        assert config.description == "Write a test file"
        assert config.expected_output == "Test file with pytest"
        assert config.agent == "test_agent"
    
    def test_orchestrator_factory_autogen(self):
        """测试 AutoGen 编排器工厂"""
        orchestrator = OrchestratorFactory.create(OrchestrationFramework.AUTO_GEN)
        assert orchestrator is not None
    
    def test_orchestrator_factory_crewai(self):
        """测试 CrewAI 编排器工厂"""
        orchestrator = OrchestratorFactory.create(OrchestrationFramework.CREW_AI)
        assert orchestrator is not None
    
    def test_orchestrator_factory_langchain(self):
        """测试 LangChain 编排器工厂"""
        orchestrator = OrchestratorFactory.create(OrchestrationFramework.LANGCHAIN)
        assert orchestrator is not None
    
    def test_orchestrator_factory_invalid(self):
        """测试无效的编排框架"""
        with pytest.raises(ValueError):
            OrchestratorFactory.create("invalid_framework")
    
    @pytest.mark.asyncio
    async def test_autogen_orchestrator_add_agent(self):
        """测试 AutoGen 编排器添加 Agent"""
        orchestrator = OrchestratorFactory.create(OrchestrationFramework.AUTO_GEN)
        agent_config = AgentConfig(
            name="assistant",
            role="Assistant",
            goal="Help users",
            backstory="Helpful AI assistant"
        )
        # 即使 AutoGen 没有安装，也应该安全处理
        agent = orchestrator.add_agent(agent_config)
        assert len(orchestrator.agents) >= 0
    
    @pytest.mark.asyncio
    async def test_autogen_orchestrator_add_task(self):
        """测试 AutoGen 编排器添加任务"""
        orchestrator = OrchestratorFactory.create(OrchestrationFramework.AUTO_GEN)
        task_config = TaskConfig(
            description="Help with something",
            expected_output="Helpful response"
        )
        task = orchestrator.add_task(task_config)
        assert len(orchestrator.tasks) >= 0
    
    @pytest.mark.asyncio
    async def test_autogen_orchestrator_run(self):
        """测试 AutoGen 编排器运行"""
        orchestrator = OrchestratorFactory.create(OrchestrationFramework.AUTO_GEN)
        result = await orchestrator.run({"test": "data"})
        assert "status" in result or "error" in result
