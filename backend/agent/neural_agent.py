"""Neural Agent核心类和基础架构
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent类型"""
    COORDINATOR = "coordinator"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    GENERAL = "general"


class AgentState(Enum):
    """Agent状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    LEARNING = "learning"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    agent_type: AgentType
    model_name: str = "gpt-4"
    max_token: int = 4000
    temperature: float = 0.7
    system_prompt: str = ""
    tools: List[str] = field(default_factory=list)
    memory_size: int = 10
    trust_threshold: float = 0.5


@dataclass
class AgentMessage:
    """Agent消息"""
    id: str
    sender_id: str
    receiver_id: str
    content: Any
    message_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    conversation_id: str = ""
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """Agent行动"""
    action_type: str
    content: Any
    confidence: float = 1.0
    reasoning: str = ""
    tools_used: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Thought:
    """Agent思考"""
    context: str
    reasoning: str
    attention_weights: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    alternatives: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class NeuralAgent:
    """神经网络Agent核心类"""

    def __init__(
        self,
        config: AgentConfig,
        short_term_memory: Optional['ShortTermMemory'] = None,
        long_term_memory: Optional['LongTermMemory'] = None,
        trust_manager: Optional['TrustManager'] = None,
        attention_mechanism: Optional['AttentionMechanism'] = None
    ):
        self.agent_id = str(uuid.uuid4())[:8]
        self.config = config
        self.state = AgentState.IDLE

        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory
        self.trust_manager = trust_manager
        self.attention = attention_mechanism

        self.current_thought: Optional[Thought] = None
        self.action_history: List[Action] = []
        self.message_history: List[AgentMessage] = []

        self._llm_adapter = None
        self._tools: Dict[str, Callable] = {}

        logger.info(f"NeuralAgent {self.agent_id} initialized as {config.name}")

    def set_llm_adapter(self, adapter: Any):
        self._llm_adapter = adapter

    def register_tool(self, name: str, tool_func: Callable):
        self._tools[name] = tool_func
        logger.info(f"Tool registered: {name}")

    async def think(self, context: str) -> Thought:
        """思考过程 - Agent的核心认知功能"""
        self.state = AgentState.THINKING

        try:
            # 1. 编码输入
            encoded_context = self._encode_context(context)

            # 2. 从短期记忆中检索相关信息
            relevant_memories = []
            if self.short_term_memory:
                relevant_memories = self.short_term_memory.retrieve(
                    context,
                    limit=self.config.memory_size
                )

            # 3. 从长期记忆中检索知识
            knowledge = []
            if self.long_term_memory:
                knowledge = self.long_term_memory.retrieve(
                    context,
                    top_k=5
                )

            # 4. 计算注意力权重
            attention_weights = {}
            if self.attention:
                attention_weights = self.attention.compute(
                    encoded_context,
                    relevant_memories + knowledge
                )

            # 5. 生成思考
            reasoning = await self._reason(
                context,
                relevant_memories,
                knowledge,
                attention_weights
            )

            # 6. 评估置信度
            confidence = self._evaluate_confidence(
                reasoning,
                attention_weights
            )

            self.current_thought = Thought(
                context=context,
                reasoning=reasoning,
                attention_weights=attention_weights,
                confidence=confidence
            )

            # 7. 存储到短期记忆
            if self.short_term_memory:
                self.short_term_memory.add(
                    context,
                    {
                        "thought": reasoning,
                        "confidence": confidence,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            self.state = AgentState.IDLE
            return self.current_thought

        except Exception as e:
            logger.error(f"Thinking failed: {e}")
            self.state = AgentState.ERROR
            raise

    async def act(self, thought: Thought) -> Action:
        """行动过程 - 根据思考生成行动"""
        self.state = AgentState.ACTING

        try:
            action_type = self._determine_action_type(thought)

            content = await self._generate_action(
                action_type,
                thought
            )

            tools_used = []
            if action_type == "tool_use":
                tools_used = await self._execute_tools(content)
                content = self._aggregate_tool_results(tools_used)

            action = Action(
                action_type=action_type,
                content=content,
                confidence=thought.confidence,
                reasoning=thought.reasoning,
                tools_used=tools_used
            )

            self.action_history.append(action)

            if self.short_term_memory:
                self.short_term_memory.add(
                    f"action_{len(self.action_history)}",
                    action.__dict__
                )

            self.state = AgentState.IDLE
            return action

        except Exception as e:
            logger.error(f"Acting failed: {e}")
            self.state = AgentState.ERROR
            raise

    async def learn(self, feedback: Dict[str, Any]):
        """学习过程 - 根据反馈更新Agent"""
        self.state = AgentState.LEARNING

        try:
            # 1. 提取反馈信息
            success = feedback.get("success", False)
            reward = feedback.get("reward", 0.0)
            error_message = feedback.get("error", "")

            # 2. 更新信任度
            if self.trust_manager and self.current_thought:
                self.trust_manager.update_trust(
                    agent_id=self.agent_id,
                    success=success,
                    reward=reward
                )

            # 3. 存储重要经验到长期记忆
            if self.long_term_memory and self.current_thought:
                if success and reward > 0.5:
                    await self.long_term_memory.add(
                        content=self.current_thought.reasoning,
                        metadata={
                            "success": True,
                            "reward": reward,
                            "action": self.action_history[-1].__dict__ if self.action_history else {}
                        }
                    )

            # 4. 调整Attention权重
            if self.attention and feedback.get("attention_feedback"):
                self.attention.adjust_weights(
                    feedback["attention_feedback"]
                )

            self.state = AgentState.IDLE

        except Exception as e:
            logger.error(f"Learning failed: {e}")
            self.state = AgentState.ERROR
            raise

    def receive_message(self, message: AgentMessage) -> bool:
        """接收消息"""
        self.message_history.append(message)

        if self.short_term_memory:
            self.short_term_memory.add(
                f"message_{message.id}",
                {
                    "from": message.sender_id,
                    "content": message.content,
                    "type": message.message_type,
                    "timestamp": message.timestamp.isoformat()
                }
            )

        logger.info(f"Message received from {message.sender_id}")
        return True

    def send_message(
        self,
        receiver_id: str,
        content: Any,
        message_type: str = "request"
    ) -> AgentMessage:
        """发送消息"""
        message = AgentMessage(
            id=str(uuid.uuid4())[:8],
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            conversation_id=self._get_or_create_conversation()
        )

        self.message_history.append(message)
        return message

    async def process(self, context: str) -> Action:
        """完整的思考-行动流程"""
        thought = await self.think(context)
        action = await self.act(thought)
        return action

    def _encode_context(self, context: str) -> str:
        """编码上下文"""
        if self._llm_adapter:
            return self._llm_adapter.encode(context)
        return context

    async def _reason(
        self,
        context: str,
        memories: List[Any],
        knowledge: List[Any],
        attention_weights: Dict[str, float]
    ) -> str:
        """推理过程"""
        if not self._llm_adapter:
            return f"Reasoning for: {context}"

        prompt = self._build_reasoning_prompt(
            context,
            memories,
            knowledge,
            attention_weights
        )

        response = await self._llm_adapter.generate(prompt)
        return response

    def _build_reasoning_prompt(
        self,
        context: str,
        memories: List[Any],
        knowledge: List[Any],
        attention_weights: Dict[str, float]
    ) -> str:
        """构建推理提示"""
        prompt_parts = [
            f"System: {self.config.system_prompt}",
            f"\nTask: {context}",
        ]

        if memories:
            prompt_parts.append("\nRecent Context:")
            for mem in memories[:5]:
                prompt_parts.append(f"- {mem}")

        if knowledge:
            prompt_parts.append("\nRelevant Knowledge:")
            for kw in knowledge[:3]:
                prompt_parts.append(f"- {kw}")

        prompt_parts.append(f"\n{self._get_agent_instruction()}")

        return "\n".join(prompt_parts)

    def _get_agent_instruction(self) -> str:
        """获取Agent指令"""
        instructions = {
            AgentType.CODER: "Write clean, efficient code to solve this problem.",
            AgentType.REVIEWER: "Review the code and provide constructive feedback.",
            AgentType.TESTER: "Design and write comprehensive tests.",
            AgentType.RESEARCHER: "Research and provide detailed analysis.",
            AgentType.ARCHITECT: "Design scalable and maintainable architecture.",
            AgentType.COORDINATOR: "Coordinate and direct the overall workflow.",
            AgentType.GENERAL: "Help with the task to the best of your ability."
        }
        return instructions.get(self.config.agent_type, "Complete the task effectively.")

    def _evaluate_confidence(
        self,
        reasoning: str,
        attention_weights: Dict[str, float]
    ) -> float:
        """评估置信度"""
        base_confidence = 0.5

        if self.trust_manager:
            trust = self.trust_manager.get_trust_score(self.agent_id)
            base_confidence *= trust

        if attention_weights:
            max_attention = max(attention_weights.values()) if attention_weights else 0
            base_confidence += max_attention * 0.3

        if len(reasoning) > 100:
            base_confidence += 0.1

        return min(max(base_confidence, 0.0), 1.0)

    def _determine_action_type(self, thought: Thought) -> str:
        """确定行动类型"""
        if thought.confidence < 0.3:
            return "request_help"
        elif "code" in thought.context.lower():
            return "write_code"
        elif "test" in thought.context.lower():
            return "write_test"
        elif "review" in thought.context.lower():
            return "review_code"
        elif len(thought.alternatives) > 0:
            return "choose_alternative"
        else:
            return "respond"

    async def _generate_action(
        self,
        action_type: str,
        thought: Thought
    ) -> str:
        """生成行动"""
        if not self._llm_adapter:
            return f"Action: {action_type}"

        prompt = f"""
Based on the following reasoning:
{thought.reasoning}

Generate an action of type: {action_type}
"""
        return await self._llm_adapter.generate(prompt)

    async def _execute_tools(self, tool_names: Any) -> List[Dict]:
        """执行工具"""
        results = []

        if isinstance(tool_names, str):
            tool_list = [tool_names]
        elif isinstance(tool_names, list):
            tool_list = tool_names
        else:
            tool_list = []

        for tool_name in tool_list:
            if tool_name in self._tools:
                try:
                    result = await self._tools[tool_name]()
                    results.append({
                        "tool": tool_name,
                        "success": True,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "tool": tool_name,
                        "success": False,
                        "error": str(e)
                    })

        return results

    def _aggregate_tool_results(self, results: List[Dict]) -> str:
        """聚合工具结果"""
        if not results:
            return "No tool results"

        summary_parts = []
        for result in results:
            if result["success"]:
                summary_parts.append(
                    f"{result['tool']}: Success - {result.get('result', 'Done')}"
                )
            else:
                summary_parts.append(
                    f"{result['tool']}: Failed - {result.get('error', 'Unknown error')}"
                )

        return "\n".join(summary_parts)

    def _get_or_create_conversation(self) -> str:
        """获取或创建会话ID"""
        for msg in reversed(self.message_history):
            if msg.conversation_id:
                return msg.conversation_id
        return str(uuid.uuid4())[:8]

    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "type": self.config.agent_type.value,
            "state": self.state.value,
            "thoughts_count": 1 if self.current_thought else 0,
            "actions_count": len(self.action_history),
            "messages_count": len(self.message_history),
            "trust_score": self.trust_manager.get_trust_score(self.agent_id) if self.trust_manager else 0.5
        }

    def __repr__(self) -> str:
        return f"NeuralAgent(id={self.agent_id}, name={self.config.name}, type={self.config.agent_type.value})"


# 导入需要的基础类（这里使用字符串避免循环导入）
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.core.memory import ShortTermMemory, LongTermMemory
    from backend.core.trust import TrustManager
    from backend.core.attention import AttentionMechanism

