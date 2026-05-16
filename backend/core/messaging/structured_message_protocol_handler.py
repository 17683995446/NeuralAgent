"""Message protocol for layer-to-layer communication."""
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class MessageType(str, Enum):
    """Message type enumeration."""
    CODE_ANALYSIS = "code_analysis"
    FEATURE_COMPRESSION = "feature_compression"
    GLOBAL_SOLUTION = "global_solution"
    CODE_GENERATION = "code_generation"
    TEST_GENERATION = "test_generation"
    FEEDBACK = "feedback"


class LayerInfo(BaseModel):
    """Layer information model."""
    layer: str = Field(description="Layer name")
    agent_id: str = Field(description="Agent identifier")


class ForwardMessage(BaseModel):
    """Forward propagation message model.

    Used for messages sent between layers in forward propagation.
    """
    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Global unique message ID"
    )
    task_id: str = Field(description="Task identifier")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Message timestamp"
    )
    sender: LayerInfo = Field(description="Sender information")
    receiver: LayerInfo = Field(description="Receiver information")
    message_type: Literal[
        "code_analysis",
        "feature_compression",
        "global_solution",
        "code_generation",
        "test_generation"
    ] = Field(description="Message type")
    content: Dict[str, Any] = Field(description="Message content")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Output confidence"
    )
    memory_ref: Optional[Dict[str, str]] = Field(
        default=None,
        description="Memory reference"
    )

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "ForwardMessage":
        """Create message from JSON string."""
        return cls.model_validate_json(json_str)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return self.model_dump()


class FeedbackContent(BaseModel):
    """Feedback content model."""
    feedback_type: Literal["positive", "negative"] = Field(
        description="Feedback type"
    )
    description: str = Field(description="Feedback description")
    error_signal: float = Field(
        description="Error signal (-1 or +1)"
    )
    suggestion: str = Field(description="Improvement suggestion")


class BackwardMessage(BaseModel):
    """Backward propagation message model.

    Used for feedback messages in backpropagation.
    """
    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Global unique message ID"
    )
    task_id: str = Field(description="Task identifier")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Message timestamp"
    )
    sender: LayerInfo = Field(description="Sender information")
    receiver: LayerInfo = Field(description="Receiver information")
    message_type: Literal["feedback"] = Field(
        default="feedback",
        description="Message type"
    )
    content: FeedbackContent = Field(description="Feedback content")
    reward: float = Field(
        ge=-1.0,
        le=1.0,
        description="Reward value"
    )
    trust_update: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Trust update configuration"
    )
    learning_rate: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="Learning rate for this update"
    )

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "BackwardMessage":
        """Create message from JSON string."""
        return cls.model_validate_json(json_str)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return self.model_dump()


@dataclass
class MessageEnvelope:
    """Message envelope for RabbitMQ."""
    exchange: str
    routing_key: str
    message: Any
    properties: Dict[str, Any]

    def to_bytes(self) -> bytes:
        """Serialize envelope to bytes."""
        if isinstance(self.message, (ForwardMessage, BackwardMessage)):
            return self.message.to_json().encode("utf-8")
        return json.dumps(self.message).encode("utf-8")


class MessageProtocol:
    """Message protocol handler for layer communication.

    Provides serialization/deserialization and validation
    for forward and backward messages.
    """

    FORWARD_EXCHANGE = "neural.forward"
    BACKWARD_EXCHANGE = "neural.backward"

    LAYER_ROUTING_KEYS = {
        "input": "layer.input",
        "convolution": "layer.convolution",
        "pooling": "layer.pooling",
        "fc_layer_1": "layer.fc1",
        "fc_layer_2": "layer.fc2",
        "fc_layer_3": "layer.fc3",
        "output": "layer.output",
    }

    @classmethod
    def create_forward_message(
        cls,
        task_id: str,
        sender_layer: str,
        sender_agent: str,
        receiver_layer: str,
        receiver_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        confidence: float = 1.0,
        memory_ref: Optional[Dict[str, str]] = None
    ) -> ForwardMessage:
        """Create forward propagation message.

        Args:
            task_id: Task identifier
            sender_layer: Sender layer name
            sender_agent: Sender agent ID
            receiver_layer: Receiver layer name
            receiver_agent: Receiver agent ID
            message_type: Message type
            content: Message content
            confidence: Output confidence
            memory_ref: Optional memory reference

        Returns:
            ForwardMessage instance
        """
        return ForwardMessage(
            task_id=task_id,
            sender=LayerInfo(layer=sender_layer, agent_id=sender_agent),
            receiver=LayerInfo(layer=receiver_layer, agent_id=receiver_agent),
            message_type=message_type.value,
            content=content,
            confidence=confidence,
            memory_ref=memory_ref
        )

    @classmethod
    def create_backward_message(
        cls,
        task_id: str,
        sender_layer: str,
        sender_agent: str,
        receiver_layer: str,
        receiver_agent: str,
        feedback_type: str,
        feedback_description: str,
        suggestion: str,
        reward: float,
        learning_rate: float = 0.1
    ) -> BackwardMessage:
        """Create backward propagation message.

        Args:
            task_id: Task identifier
            sender_layer: Sender layer name
            sender_agent: Sender agent ID
            receiver_layer: Receiver layer name
            receiver_agent: Receiver agent ID
            feedback_type: Feedback type (positive/negative)
            feedback_description: Feedback description
            suggestion: Improvement suggestion
            reward: Reward value
            learning_rate: Learning rate

        Returns:
            BackwardMessage instance
        """
        error_signal = 1.0 if feedback_type == "positive" else -1.0

        return BackwardMessage(
            task_id=task_id,
            sender=LayerInfo(layer=sender_layer, agent_id=sender_agent),
            receiver=LayerInfo(layer=receiver_layer, agent_id=receiver_agent),
            content=FeedbackContent(
                feedback_type=feedback_type,
                description=feedback_description,
                error_signal=error_signal,
                suggestion=suggestion
            ),
            reward=reward,
            learning_rate=learning_rate
        )

    @classmethod
    def get_routing_key(cls, layer_name: str) -> str:
        """Get routing key for layer.

        Args:
            layer_name: Layer name

        Returns:
            Routing key string
        """
        return cls.LAYER_ROUTING_KEYS.get(layer_name, f"layer.{layer_name}")

    @classmethod
    def serialize_message(cls, message: Any) -> bytes:
        """Serialize message to bytes.

        Args:
            message: ForwardMessage or BackwardMessage

        Returns:
            Serialized bytes
        """
        if isinstance(message, (ForwardMessage, BackwardMessage)):
            return message.to_json().encode("utf-8")
        return json.dumps(message).encode("utf-8")

    @classmethod
    def deserialize_forward(cls, data: bytes) -> ForwardMessage:
        """Deserialize forward message.

        Args:
            data: Serialized bytes

        Returns:
            ForwardMessage instance
        """
        return ForwardMessage.from_json(data.decode("utf-8"))

    @classmethod
    def deserialize_backward(cls, data: bytes) -> BackwardMessage:
        """Deserialize backward message.

        Args:
            data: Serialized bytes

        Returns:
            BackwardMessage instance
        """
        return BackwardMessage.from_json(data.decode("utf-8"))
