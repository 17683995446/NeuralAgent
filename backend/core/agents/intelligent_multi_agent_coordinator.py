"""NeuralAgent core unit based on AutoGen ConversableAgent."""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from autogen import ConversableAgent as BaseAgent, Agent as BaseAgentClass
    from autogen.agentchat.agent import Agent as AutogenAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    try:
        from autogen_agentchat.agent import ConversableAgent as BaseAgent
        AutogenAgent = object
        BaseAgentClass = object
        AUTOGEN_AVAILABLE = True
    except ImportError:
        BaseAgent = object
        BaseAgentClass = object
        AutogenAgent = object
        AUTOGEN_AVAILABLE = False

from backend.config import settings
from backend.core.memory.short_term_memory import ShortTermMemory
from backend.core.memory.long_term_memory import LongTermMemory


class NeuralAgent:
    """Neural Agent core unit.

    Extends AutoGen ConversableAgent with:
    - Dual memory system (short-term + long-term)
    - Trust matrix integration
    - Message preprocessing/postprocessing callbacks
    """

    def __init__(
        self,
        agent_id: str,
        layer_name: str,
        role: str,
        goal: str,
        llm_config: Dict[str, Any],
        trust_matrix: Optional[Dict[str, float]] = None,
        short_term_memory: Optional[ShortTermMemory] = None,
        long_term_memory: Optional[LongTermMemory] = None,
        system_message_template: Optional[str] = None,
        **kwargs
    ):
        """Initialize Neural Agent.

        Args:
            agent_id: Unique agent identifier
            layer_name: Layer name this agent belongs to
            role: Agent role name
            goal: Agent goal description
            llm_config: LLM configuration dictionary
            trust_matrix: Initial trust matrix for this agent
            short_term_memory: Short-term memory instance
            long_term_memory: Long-term memory instance
            system_message_template: Custom system message template
            **kwargs: Additional arguments for ConversableAgent
        """
        self.agent_id = agent_id
        self.layer_name = layer_name
        self.role = role
        self.goal = goal
        self.llm_config = llm_config

        self.trust_matrix = trust_matrix or self._get_default_trust_matrix()
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory

        self.system_message = system_message_template or (
            f"你是{role}，你的目标是{goal}，"
            f"你属于{layer_name}层。"
            f"你必须严格按照固定JSON格式输出结果。"
        )

        if AUTOGEN_AVAILABLE:
            super().__init__(
                name=agent_id,
                system_message=self.system_message,
                llm_config=llm_config,
                **kwargs
            )

        self._output_history: List[Dict[str, Any]] = []

    def _get_default_trust_matrix(self) -> Dict[str, float]:
        """Get default trust matrix.

        Returns:
            Default trust matrix with all weights set to 1.0
        """
        return {
            "global": 1.0,
            "confidence": 1.0,
            "accuracy": 1.0,
            "reliability": 1.0,
        }

    def _pre_process_reply(
        self,
        messages: List[Dict[str, Any]],
        sender: Any,
        config: Optional[Any] = None
    ) -> tuple[bool, List[Dict[str, Any]]]:
        """Preprocess incoming messages based on trust matrix.

        Filters out messages from low-trust sources.

        Args:
            messages: List of incoming messages
            sender: Sender agent
            config: Optional configuration

        Returns:
            Tuple of (stop, filtered_messages)
        """
        if not messages:
            return False, []

        if self.short_term_memory and self.trust_matrix:
            filtered = self.short_term_memory.filter_by_trust(
                messages,
                self.trust_matrix
            )
            logger.debug(
                f"Agent {self.agent_id}: filtered {len(messages)} messages "
                f"to {len(filtered)} based on trust"
            )
            return False, filtered

        return False, messages

    def _post_process_reply(
        self,
        messages: List[Dict[str, Any]],
        sender: Any,
        config: Optional[Any] = None
    ) -> tuple[bool, List[Dict[str, Any]]]:
        """Postprocess outgoing messages.

        Saves messages to short-term memory.

        Args:
            messages: List of outgoing messages
            sender: Sender agent
            config: Optional configuration

        Returns:
            Tuple of (stop, messages)
        """
        if messages and self.short_term_memory:
            try:
                import asyncio
                last_message = messages[-1]
                asyncio.create_task(
                    self.short_term_memory.save_message(
                        agent_id=self.agent_id,
                        message=last_message,
                        metadata={
                            "layer": self.layer_name,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to save message to memory: {e}")

            self._output_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": messages[-1],
            })

        return False, messages

    def update_trust_matrix(self, new_trust: Dict[str, float]) -> None:
        """Update trust matrix for this agent.

        Args:
            new_trust: New trust matrix
        """
        self.trust_matrix = new_trust

        if self.short_term_memory:
            try:
                import asyncio
                asyncio.create_task(
                    self.short_term_memory.save_trust_matrix(
                        agent_id=self.agent_id,
                        trust_matrix=new_trust
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to save trust matrix: {e}")

    def get_trust_score(self, source_agent_id: str) -> float:
        """Get trust score for a source agent.

        Args:
            source_agent_id: Source agent identifier

        Returns:
            Trust score (0.0 to 2.0)
        """
        return self.trust_matrix.get(source_agent_id, 1.0)

    def should_adopt_output(self, trust_score: float) -> bool:
        """Determine if output should be adopted based on trust score.

        Args:
            trust_score: Trust score for source agent

        Returns:
            True if output should be adopted
        """
        return trust_score >= settings.trust_filter_threshold

    def should_recheck_output(self, trust_score: float) -> bool:
        """Determine if output needs rechecking based on trust score.

        Args:
            trust_score: Trust score for source agent

        Returns:
            True if output needs rechecking
        """
        threshold = settings.trust_filter_threshold
        high_threshold = settings.default_confidence_threshold
        return threshold <= trust_score < high_threshold

    def save_to_long_term_memory(
        self,
        content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Save content to long-term memory.

        Args:
            content: Content to save
            metadata: Metadata dictionary

        Returns:
            Memory entry ID or None
        """
        if self.long_term_memory:
            return self.long_term_memory.save_memory(
                agent_id=self.agent_id,
                content=content,
                metadata=metadata
            )
        return None

    def retrieve_similar_experiences(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.8
    ) -> List[Any]:
        """Retrieve similar experiences from long-term memory.

        Args:
            query: Query text
            top_k: Number of results
            threshold: Similarity threshold

        Returns:
            List of similar memory entries
        """
        if self.long_term_memory:
            return self.long_term_memory.retrieve_similar(
                query=query,
                agent_id=self.agent_id,
                top_k=top_k,
                threshold=threshold
            )
        return []

    def get_output_history(self) -> List[Dict[str, Any]]:
        """Get output history for this agent.

        Returns:
            List of output records
        """
        return self._output_history.copy()

    def clear_output_history(self) -> None:
        """Clear output history."""
        self._output_history.clear()

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information.

        Returns:
            Dictionary with agent metadata
        """
        return {
            "agent_id": self.agent_id,
            "layer_name": self.layer_name,
            "role": self.role,
            "goal": self.goal,
            "trust_matrix": self.trust_matrix,
            "output_count": len(self._output_history),
        }

    def apply_feedback(self, feedback: Dict[str, Any]) -> Dict[str, float]:
        """Apply feedback to adjust trust matrix.

        Args:
            feedback: Feedback dictionary with reward

        Returns:
            Updated trust matrix
        """
        reward = feedback.get("reward", 0.0)
        learning_rate = feedback.get("learning_rate", settings.trust_update_lr)

        adjusted_trust = {}
        for key, value in self.trust_matrix.items():
            adjustment = reward * learning_rate
            new_value = value + adjustment
            adjusted_trust[key] = max(0.0, min(2.0, new_value))

        self.update_trust_matrix(adjusted_trust)
        return adjusted_trust


class ConvolutionAgent(NeuralAgent):
    """Convolution layer agent for code analysis.

    Specializes in analyzing individual code units (files/functions/modules).
    """

    def __init__(self, **kwargs):
        """Initialize convolution agent."""
        kwargs.setdefault("layer_name", "convolution")
        super().__init__(**kwargs)


class PoolingAgent(NeuralAgent):
    """Pooling layer agent for information compression.

    Specializes in compressing and aggregating information.
    """

    def __init__(self, **kwargs):
        """Initialize pooling agent."""
        kwargs.setdefault("layer_name", "pooling")
        super().__init__(**kwargs)


class FCAgent(NeuralAgent):
    """Fully connected layer agent.

    Base class for FC layer agents.
    """

    def __init__(self, fc_layer_num: int = 1, **kwargs):
        """Initialize FC agent.

        Args:
            fc_layer_num: FC layer number (1, 2, or 3)
        """
        layer_name = f"fc_layer_{fc_layer_num}"
        kwargs["layer_name"] = layer_name
        super().__init__(**kwargs)


class OutputAgent(NeuralAgent):
    """Output layer agent for document generation.

    Specializes in generating markdown documents.
    """

    def __init__(self, **kwargs):
        """Initialize output agent."""
        kwargs.setdefault("layer_name", "output")
        super().__init__(**kwargs)


class IntelligentMultiAgentCoordinator:
    """智能多代理协调器 - 核心协调组件
    
    负责协调各个神经层的代理执行，提供完整的多代理协作框架。
    """
    
    def __init__(
        self,
        task_id: str,
        config: Dict[str, Any] = None,
        short_term_memory=None,
        long_term_memory=None
    ):
        """初始化智能多代理协调器
        
        Args:
            task_id: 任务标识符
            config: 配置字典
            short_term_memory: 短期记忆实例
            long_term_memory: 长期记忆实例
        """
        self.task_id = task_id
        self.config = config or {}
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory
        self.agents = {}
        self.agent_results = {}
        logger.info(f"IntelligentMultiAgentCoordinator initialized for task {task_id}")
    
    def register_agent(self, agent_id: str, agent: NeuralAgent) -> None:
        """注册代理
        
        Args:
            agent_id: 代理标识符
            agent: 代理实例
        """
        self.agents[agent_id] = agent
        logger.debug(f"Agent registered: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[NeuralAgent]:
        """获取代理
        
        Args:
            agent_id: 代理标识符
            
        Returns:
            代理实例或 None
        """
        return self.agents.get(agent_id)
    
    async def execute_agent(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个代理
        
        Args:
            agent_id: 代理标识符
            input_data: 输入数据
            
        Returns:
            代理执行结果
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {"error": f"Agent not found: {agent_id}"}
        
        try:
            logger.info(f"Executing agent {agent_id}")
            # 这里是简化的执行逻辑
            result = {
                "agent_id": agent_id,
                "status": "completed",
                "output": f"Agent {agent_id} processed input",
                "input": input_data
            }
            self.agent_results[agent_id] = result
            return result
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "agent_id": agent_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def execute_all(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行所有代理
        
        Args:
            input_data: 输入数据
            
        Returns:
            所有代理的执行结果
        """
        logger.info(f"Executing all agents for task {self.task_id}")
        results = {}
        
        for agent_id in self.agents:
            result = await self.execute_agent(agent_id, input_data)
            results[agent_id] = result
        
        return {
            "task_id": self.task_id,
            "agents_count": len(self.agents),
            "results": results,
            "status": "completed"
        }
    
    def get_coordination_info(self) -> Dict[str, Any]:
        """获取协调信息
        
        Returns:
            协调信息字典
        """
        return {
            "task_id": self.task_id,
            "agents_registered": list(self.agents.keys()),
            "results_count": len(self.agent_results)
        }


def create_agent(
    agent_type: str,
    agent_id: str,
    role: str,
    goal: str,
    llm_config: Dict[str, Any],
    **kwargs
) -> NeuralAgent:
    """Factory function to create agents.

    Args:
        agent_type: Type of agent to create
        agent_id: Agent identifier
        role: Agent role
        goal: Agent goal
        llm_config: LLM configuration
        **kwargs: Additional arguments

    Returns:
        NeuralAgent instance
    """
    if agent_type == "convolution":
        return ConvolutionAgent(
            agent_id=agent_id,
            role=role,
            goal=goal,
            llm_config=llm_config,
            **kwargs
        )
    elif agent_type == "pooling":
        return PoolingAgent(
            agent_id=agent_id,
            role=role,
            goal=goal,
            llm_config=llm_config,
            **kwargs
        )
    elif agent_type == "fc1":
        return FCAgent(
            fc_layer_num=1,
            agent_id=agent_id,
            role=role,
            goal=goal,
            llm_config=llm_config,
            **kwargs
        )
    elif agent_type == "fc2":
        return FCAgent(
            fc_layer_num=2,
            agent_id=agent_id,
            role=role,
            goal=goal,
            llm_config=llm_config,
            **kwargs
        )
    elif agent_type == "fc3":
        return FCAgent(
            fc_layer_num=3,
            agent_id=agent_id,
            role=role,
            goal=goal,
            llm_config=llm_config,
            **kwargs
        )
    elif agent_type == "output":
        return OutputAgent(
            agent_id=agent_id,
            role=role,
            goal=goal,
            llm_config=llm_config,
            **kwargs
        )
    else:
        return NeuralAgent(
            agent_id=agent_id,
            layer_name=kwargs.get("layer_name", "default"),
            role=role,
            goal=goal,
            llm_config=llm_config,
            **kwargs
        )
