"""Short-term memory implementation using Redis."""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as aioredis

from backend.config import settings


class ShortTermMemory:
    """Short-term memory using Redis Hash for task context storage.

    Key format: st:task:{task_id}:agent:{agent_id}
    TTL: 24 hours after task completion
    """

    def __init__(self, redis_client: aioredis.Redis, task_id: str):
        """Initialize short-term memory.

        Args:
            redis_client: Redis client instance
            task_id: Current task ID
        """
        self.redis = redis_client
        self.task_id = task_id
        self.ttl = timedelta(hours=24)

    def _get_key(self, agent_id: str) -> str:
        """Generate Redis key for agent memory.

        Args:
            agent_id: Agent identifier

        Returns:
            Redis key string
        """
        return f"st:task:{self.task_id}:agent:{agent_id}"

    async def save_message(
        self,
        agent_id: str,
        message: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save message to short-term memory.

        Args:
            agent_id: Agent identifier
            message: Message content dictionary
            metadata: Optional metadata
        """
        key = self._get_key(agent_id)
        data = {
            "last_message": json.dumps(message, ensure_ascii=False),
            "update_time": datetime.utcnow().isoformat(),
        }
        if metadata:
            data["metadata"] = json.dumps(metadata, ensure_ascii=False)

        await self.redis.hset(key, mapping=data)
        await self.redis.expire(key, int(self.ttl.total_seconds()))

    async def get_message(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve latest message from short-term memory.

        Args:
            agent_id: Agent identifier

        Returns:
            Message dictionary or None
        """
        key = self._get_key(agent_id)
        data = await self.redis.hgetall(key)

        if not data:
            return None

        result = {}
        for field, value in data.items():
            field_str = field.decode() if isinstance(field, bytes) else field
            value_str = value.decode() if isinstance(value, bytes) else value
            if field_str == "last_message":
                result["message"] = json.loads(value_str)
            elif field_str == "metadata":
                result["metadata"] = json.loads(value_str)
            else:
                result[field_str] = value_str

        return result

    async def get_all_messages(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all messages for current task.

        Returns:
            Dictionary mapping agent_id to message data
        """
        pattern = f"st:task:{self.task_id}:agent:*"
        result = {}

        async for key in self.redis.scan_iter(match=pattern):
            agent_id = key.decode().split(":")[-1]
            message_data = await self.get_message(agent_id)
            if message_data:
                result[agent_id] = message_data

        return result

    def filter_by_trust(
        self,
        messages: List[Dict[str, Any]],
        trust_matrix: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Filter messages based on trust matrix.

        Args:
            messages: List of messages with sender_agent_id
            trust_matrix: Trust scores for each agent

        Returns:
            Filtered list of messages with trust >= threshold
        """
        threshold = settings.trust_filter_threshold
        filtered = []

        for msg in messages:
            sender_id = msg.get("sender_agent_id")
            if not sender_id:
                continue

            trust_score = trust_matrix.get(sender_id, 1.0)
            if trust_score >= threshold:
                msg["trust_score"] = trust_score
                filtered.append(msg)

        return filtered

    async def save_trust_matrix(
        self,
        agent_id: str,
        trust_matrix: Dict[str, float]
    ) -> None:
        """Save trust matrix for agent.

        Args:
            agent_id: Agent identifier
            trust_matrix: Trust score dictionary
        """
        key = f"st:task:{self.task_id}:agent:{agent_id}:trust"
        await self.redis.set(
            key,
            json.dumps(trust_matrix),
            ex=int(self.ttl.total_seconds())
        )

    async def get_trust_matrix(self, agent_id: str) -> Dict[str, float]:
        """Retrieve trust matrix for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Trust score dictionary
        """
        key = f"st:task:{self.task_id}:agent:{agent_id}:trust"
        data = await self.redis.get(key)

        if data:
            return json.loads(data.decode() if isinstance(data, bytes) else data)
        return {}

    async def save_context(
        self,
        agent_id: str,
        context_key: str,
        context_value: Any
    ) -> None:
        """Save context data for agent.

        Args:
            agent_id: Agent identifier
            context_key: Context key name
            context_value: Context value
        """
        key = self._get_key(agent_id)
        await self.redis.hset(key, context_key, json.dumps(context_value))
        await self.redis.expire(key, int(self.ttl.total_seconds()))

    async def get_context(
        self,
        agent_id: str,
        context_key: str
    ) -> Optional[Any]:
        """Retrieve context data for agent.

        Args:
            agent_id: Agent identifier
            context_key: Context key name

        Returns:
            Context value or None
        """
        key = self._get_key(agent_id)
        data = await self.redis.hget(key, context_key)

        if data:
            value_str = data.decode() if isinstance(data, bytes) else data
            return json.loads(value_str)
        return None

    async def clear(self, agent_id: str) -> None:
        """Clear memory for specific agent.

        Args:
            agent_id: Agent identifier
        """
        keys = [
            self._get_key(agent_id),
            f"st:task:{self.task_id}:agent:{agent_id}:trust",
        ]
        for key in keys:
            await self.redis.delete(key)

    async def clear_all(self) -> None:
        """Clear all short-term memory for current task."""
        pattern = f"st:task:{self.task_id}:agent:*"
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)


def create_redis_client() -> aioredis.Redis:
    """Create Redis client instance.

    Returns:
        Redis client
    """
    return aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=False
    )
