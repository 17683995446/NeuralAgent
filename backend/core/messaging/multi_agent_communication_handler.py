"""Agent消息协议和通信机制
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import uuid
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    PROPOSE = "propose"
    ACCEPT = "accept"
    REJECT = "reject"
    QUERY = "query"
    INFORM = "inform"
    CONFIRM = "confirm"


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """Agent消息"""
    id: str
    sender_id: str
    receiver_id: str
    content: Any
    message_type: MessageType
    timestamp: datetime = field(default_factory=datetime.now)
    conversation_id: str = ""
    priority: MessagePriority = MessagePriority.NORMAL
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """对话记录"""
    id: str
    participants: List[str]
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "active"


class MessageBus:
    """消息总线 - Agent间通信中枢"""

    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size

        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_queues: Dict[str, List[Message]] = defaultdict(list)
        self._conversations: Dict[str, Conversation] = {}
        self._agents: Dict[str, Any] = {}

        self._lock = threading.RLock()
        self._message_id_counter = 0

    def register_agent(self, agent_id: str, agent: Any):
        with self._lock:
            self._agents[agent_id] = agent
            self._message_queues[agent_id] = []
            logger.info(f"Agent registered: {agent_id}")

    def unregister_agent(self, agent_id: str):
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
            if agent_id in self._message_queues:
                del self._message_queues[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")

    def subscribe(self, agent_id: str, topics: List[MessageType], callback: Callable):
        with self._lock:
            topic_key = f"{agent_id}:{','.join(t.value for t in topics)}"
            self._subscribers[topic_key].append(callback)
            logger.info(f"Agent {agent_id} subscribed to {len(topics)} topics")

    def publish(self, message: Message) -> bool:
        with self._lock:
            if message.receiver_id == "broadcast":
                return self._broadcast(message)
            elif message.receiver_id == "multicast":
                return self._multicast(message)
            else:
                return self._send_direct(message)

    def _send_direct(self, message: Message) -> bool:
        if message.receiver_id not in self._message_queues:
            logger.warning(f"Receiver not found: {message.receiver_id}")
            return False

        self._message_queues[message.receiver_id].append(message)

        self._add_to_conversation(message)

        self._notify_subscribers(message)

        logger.debug(f"Message sent from {message.sender_id} to {message.receiver_id}")
        return True

    def _broadcast(self, message: Message) -> int:
        sent_count = 0

        for agent_id in self._message_queues:
            if agent_id != message.sender_id:
                self._message_queues[agent_id].append(message)
                sent_count += 1

        self._add_to_conversation(message)
        self._notify_subscribers(message)

        logger.info(f"Broadcast from {message.sender_id} to {sent_count} agents")
        return sent_count

    def _multicast(self, message: Message) -> int:
        targets = message.metadata.get("targets", [])
        sent_count = 0

        for target_id in targets:
            if target_id in self._message_queues and target_id != message.sender_id:
                self._message_queues[target_id].append(message)
                sent_count += 1

        self._add_to_conversation(message)
        self._notify_subscribers(message)

        logger.info(f"Multicast from {message.sender_id} to {sent_count} agents")
        return sent_count

    def receive(self, agent_id: str, timeout: float = 0) -> Optional[Message]:
        with self._lock:
            if agent_id not in self._message_queues:
                return None

            queue = self._message_queues[agent_id]

            if not queue:
                return None

            if timeout > 0:
                import time
                start_time = time.time()
                while not queue and (time.time() - start_time) < timeout:
                    time.sleep(0.01)

            if queue:
                return queue.pop(0)

            return None

    def get_messages(self, agent_id: str, limit: int = 10) -> List[Message]:
        with self._lock:
            queue = self._message_queues.get(agent_id, [])
            return queue[:limit]

    def _add_to_conversation(self, message: Message):
        if not message.conversation_id:
            return

        if message.conversation_id not in self._conversations:
            self._conversations[message.conversation_id] = Conversation(
                id=message.conversation_id,
                participants=[message.sender_id, message.receiver_id]
            )

        conversation = self._conversations[message.conversation_id]
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()

        if message.sender_id not in conversation.participants:
            conversation.participants.append(message.sender_id)
        if message.receiver_id not in conversation.participants:
            conversation.participants.append(message.receiver_id)

    def _notify_subscribers(self, message: Message):
        for topic_key, callbacks in self._subscribers.items():
            parts = topic_key.split(":")
            if len(parts) < 2:
                continue

            subscriber_id = parts[0]
            topics_str = parts[1]
            subscribed_topics = topics_str.split(",") if topics_str else []

            if message.message_type.value in subscribed_topics:
                for callback in callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    def get_agent_conversations(self, agent_id: str) -> List[Conversation]:
        return [
            conv for conv in self._conversations.values()
            if agent_id in conv.participants
        ]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_messages = sum(
                len(queue) for queue in self._message_queues.values()
            )

            return {
                "registered_agents": len(self._agents),
                "active_conversations": len(self._conversations),
                "total_queued_messages": total_messages,
                "subscribers": len(self._subscribers)
            }


class CollaborationStrategy:
    """Agent协作策略"""

    def __init__(self, message_bus: MessageBus, trust_manager: Any = None):
        self.message_bus = message_bus
        self.trust_manager = trust_manager

    def propose_task(
        self,
        proposer_id: str,
        task: Any,
        candidate_agents: List[str]
    ) -> Optional[str]:
        if self.trust_manager:
            best_agent = self.trust_manager.get_best_agent(candidate_agents)
        else:
            best_agent = candidate_agents[0] if candidate_agents else None

        if not best_agent:
            return None

        conversation_id = str(uuid.uuid4())[:8]

        propose_message = Message(
            id=str(uuid.uuid4())[:8],
            sender_id=proposer_id,
            receiver_id=best_agent,
            content=task,
            message_type=MessageType.PROPOSE,
            conversation_id=conversation_id,
            metadata={"candidate_agents": candidate_agents}
        )

        self.message_bus.publish(propose_message)

        logger.info(f"Task proposed to {best_agent}")
        return conversation_id

    def vote_on_proposal(
        self,
        agent_id: str,
        conversation_id: str,
        vote: bool,
        reasoning: str = ""
    ) -> bool:
        conversation = self.message_bus.get_conversation(conversation_id)
        if not conversation or not conversation.messages:
            return False

        proposer = conversation.messages[0].sender_id

        vote_message = Message(
            id=str(uuid.uuid4())[:8],
            sender_id=agent_id,
            receiver_id=proposer,
            content={"vote": vote, "reasoning": reasoning},
            message_type=MessageType.ACCEPT if vote else MessageType.REJECT,
            conversation_id=conversation_id,
            reply_to=conversation.messages[0].id
        )

        return self.message_bus.publish(vote_message)

    def request_help(
        self,
        requester_id: str,
        problem: str,
        required_capabilities: List[str]
    ) -> str:
        conversation_id = str(uuid.uuid4())[:8]

        request_message = Message(
            id=str(uuid.uuid4())[:8],
            sender_id=requester_id,
            receiver_id="broadcast",
            content={
                "problem": problem,
                "required_capabilities": required_capabilities
            },
            message_type=MessageType.QUERY,
            conversation_id=conversation_id,
            priority=MessagePriority.HIGH
        )

        self.message_bus.publish(request_message)

        logger.info(f"Help requested by {requester_id}")
        return conversation_id

    def share_knowledge(
        self,
        sharer_id: str,
        knowledge: Any,
        target_agents: Optional[List[str]] = None
    ) -> bool:
        if target_agents:
            conversation_id = str(uuid.uuid4())[:8]

            for target_id in target_agents:
                share_message = Message(
                    id=str(uuid.uuid4())[:8],
                    sender_id=sharer_id,
                    receiver_id=target_id,
                    content=knowledge,
                    message_type=MessageType.INFORM,
                    conversation_id=conversation_id
                )
                self.message_bus.publish(share_message)
        else:
            conversation_id = str(uuid.uuid4())[:8]

            broadcast_message = Message(
                id=str(uuid.uuid4())[:8],
                sender_id=sharer_id,
                receiver_id="broadcast",
                content=knowledge,
                message_type=MessageType.INFORM,
                conversation_id=conversation_id
            )
            self.message_bus.publish(broadcast_message)

        logger.info(f"Knowledge shared by {sharer_id}")
        return True

    def coordinate_action(
        self,
        coordinator_id: str,
        action: Any,
        participant_ids: List[str]
    ) -> str:
        conversation_id = str(uuid.uuid4())[:8]

        for participant_id in participant_ids:
            coord_message = Message(
                id=str(uuid.uuid4())[:8],
                sender_id=coordinator_id,
                receiver_id=participant_id,
                content=action,
                message_type=MessageType.REQUEST,
                conversation_id=conversation_id,
                metadata={"coordinator": coordinator_id}
            )
            self.message_bus.publish(coord_message)

        logger.info(f"Action coordinated by {coordinator_id} to {len(participant_ids)} participants")
        return conversation_id


def create_message(
    sender_id: str,
    receiver_id: str,
    content: Any,
    message_type: MessageType = MessageType.REQUEST,
    priority: MessagePriority = MessagePriority.NORMAL,
    metadata: Optional[Dict] = None
) -> Message:
    return Message(
        id=str(uuid.uuid4())[:8],
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        message_type=message_type,
        priority=priority,
        metadata=metadata or {}
    )

