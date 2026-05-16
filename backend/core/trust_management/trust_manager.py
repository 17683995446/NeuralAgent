"""Trust Manager using Ray RLlib for trust weight management."""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TrustUpdate:
    """Trust update record."""
    agent_id: str
    previous_trust: Dict[str, float]
    new_trust: Dict[str, float]
    reward: float
    learning_rate: float
    update_time: datetime


class TrustManager:
    """Trust manager using Ray RLlib for weight updates.

    Manages trust matrices for all agents, performs weight updates
    using PPO algorithm from RLlib.
    """

    def __init__(
        self,
        db_session: Any,
        use_rllib: bool = True
    ):
        """Initialize trust manager.

        Args:
            db_session: Database session for PostgreSQL
            use_rllib: Whether to use Ray RLlib for updates
        """
        self.db_session = db_session
        self.use_rllib = use_rllib
        self.rllib_trainer = None

        if self.use_rllib:
            self._init_rllib()

    def _init_rllib(self) -> None:
        """Initialize Ray RLlib trainer."""
        try:
            from ray.rllib.algorithms.ppo import PPOConfig
            from ray.rllib.env.multi_agent_env import MultiAgentEnv

            class DummyMultiAgentEnv(MultiAgentEnv):
                def __init__(self, config):
                    super().__init__(config)

                def reset(self):
                    return {}

                def step(self, action_dict):
                    return {}, {}, {}, {}, {}

            ppo_config = (
                PPConfig()
                .environment(env=DummyMultiAgentEnv)
                .framework("torch")
                .training(
                    lr=settings.trust_update_lr,
                    lr_schedule=[[0, settings.trust_update_lr], [1000, 0.01]],
                    gamma=0.99,
                    clip_param=0.2,
                )
            )

            from ray import tune

            self.rllib_trainer = ppo_config.build()
            logger.info("Ray RLlib PPO trainer initialized successfully")

        except ImportError:
            logger.warning("Ray RLlib not available, using fallback trust update")
            self.use_rllib = False

    def get_trust_matrix(self, agent_id: str, task_id: str) -> Dict[str, float]:
        """Get trust matrix for agent.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier

        Returns:
            Trust matrix dictionary
        """
        from backend.models.persistent_data_models import TrustModel

        result = self.db_session.query(TrustModel).filter_by(
            agent_id=agent_id,
            task_id=task_id
        ).first()

        if result:
            return result.trust_matrix

        return self._get_initial_trust_matrix(agent_id)

    def _get_initial_trust_matrix(self, agent_id: str) -> Dict[str, float]:
        """Get initial trust matrix for new agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Initial trust matrix with all weights set to 1.0
        """
        return {
            "global": 1.0,
            "confidence": 1.0,
            "accuracy": 1.0,
            "reliability": 1.0,
        }

    def update_trust_matrix(
        self,
        agent_id: str,
        task_id: str,
        new_trust_matrix: Dict[str, float]
    ) -> TrustUpdate:
        """Update trust matrix for agent.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier
            new_trust_matrix: New trust weights

        Returns:
            TrustUpdate record
        """
        from backend.models.persistent_data_models import TrustModel
        from sqlalchemy import and_

        previous_matrix = self.get_trust_matrix(agent_id, task_id)

        existing = self.db_session.query(TrustModel).filter(
            and_(
                TrustModel.agent_id == agent_id,
                TrustModel.task_id == task_id
            )
        ).first()

        if existing:
            existing.trust_matrix = new_trust_matrix
            existing.update_count += 1
            existing.updated_at = datetime.utcnow()
        else:
            from backend.models.persistent_data_models import TaskModel

            task = self.db_session.query(TaskModel).filter_by(task_id=task_id).first()
            layer_name = self._infer_layer_from_agent_id(agent_id)

            new_record = TrustModel(
                agent_id=agent_id,
                task_id=task_id,
                layer_name=layer_name,
                trust_matrix=new_trust_matrix,
                update_count=1,
            )
            self.db_session.add(new_record)

        self.db_session.commit()

        return TrustUpdate(
            agent_id=agent_id,
            previous_trust=previous_matrix,
            new_trust=new_trust_matrix,
            reward=0.0,
            learning_rate=settings.trust_update_lr,
            update_time=datetime.utcnow(),
        )

    def _infer_layer_from_agent_id(self, agent_id: str) -> str:
        """Infer layer name from agent ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Layer name
        """
        if "conv" in agent_id.lower():
            return "convolution"
        elif "pool" in agent_id.lower():
            return "pooling"
        elif "fc1" in agent_id.lower() or "understand" in agent_id.lower():
            return "fc_layer_1"
        elif "fc2" in agent_id.lower() or "generate" in agent_id.lower():
            return "fc_layer_2"
        elif "fc3" in agent_id.lower() or "test" in agent_id.lower():
            return "fc_layer_3"
        return "unknown"

    def update_by_rl_policy(
        self,
        agent_id: str,
        task_id: str,
        reward: float,
        observation: Optional[Dict[str, Any]] = None
    ) -> TrustUpdate:
        """Update trust matrix using RLlib policy.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier
            reward: Reward value from feedback
            observation: Optional observation data

        Returns:
            TrustUpdate record
        """
        current_trust = self.get_trust_matrix(agent_id, task_id)

        if self.use_rllib and self.rllib_trainer:
            try:
                policy = self.rllib_trainer.get_policy(agent_id)
                if policy:
                    current_weights = policy.get_weights()
                    new_weights = self._apply_reward_adjustment(
                        current_weights,
                        reward,
                        settings.trust_update_lr
                    )
                    policy.set_weights(new_weights)
                    current_trust = new_weights
            except Exception as e:
                logger.warning(f"RLlib policy update failed: {e}, using fallback")

        new_trust = self._apply_reward_adjustment(
            current_trust,
            reward,
            settings.trust_update_lr
        )

        return self.update_trust_matrix(agent_id, task_id, new_trust)

    def _apply_reward_adjustment(
        self,
        trust_weights: Dict[str, float],
        reward: float,
        learning_rate: float
    ) -> Dict[str, float]:
        """Apply reward-based adjustment to trust weights.

        Args:
            trust_weights: Current trust weights
            reward: Reward value
            learning_rate: Learning rate

        Returns:
            Updated trust weights
        """
        adjusted = {}
        for key, value in trust_weights.items():
            adjustment = reward * learning_rate
            new_value = value + adjustment
            adjusted[key] = max(0.0, min(2.0, new_value))

        return adjusted

    def calculate_reward(
        self,
        satisfaction_score: int,
        feedback_items: List[Dict[str, Any]]
    ) -> float:
        """Calculate reward from user feedback.

        Args:
            satisfaction_score: User satisfaction score (0-5)
            feedback_items: List of feedback items

        Returns:
            Reward value in range [-1, 1]
        """
        base_reward = (satisfaction_score - 3) / 2

        for item in feedback_items:
            feedback_type = item.get("type", "")
            if feedback_type == "positive":
                base_reward += 0.1
            elif feedback_type == "negative":
                base_reward -= 0.1

        return max(-1.0, min(1.0, base_reward))

    def filter_by_trust(
        self,
        items: List[Dict[str, Any]],
        trust_matrix: Dict[str, float],
        source_key: str = "agent_id"
    ) -> List[Dict[str, Any]]:
        """Filter items based on trust scores.

        Args:
            items: List of items with source information
            trust_matrix: Trust scores for each source
            source_key: Key to extract source identifier

        Returns:
            Filtered list with trust >= threshold
        """
        threshold = settings.trust_filter_threshold
        high_threshold = settings.default_confidence_threshold

        filtered = []
        for item in items:
            source_id = item.get(source_key, "")
            trust_score = trust_matrix.get(source_id, 1.0)

            if trust_score >= threshold:
                item["trust_score"] = trust_score
                item["high_confidence"] = trust_score >= high_threshold
                filtered.append(item)

        return filtered

    def get_layer_trust_summary(
        self,
        task_id: str,
        layer_name: str
    ) -> Dict[str, Any]:
        """Get trust summary for all agents in a layer.

        Args:
            task_id: Task identifier
            layer_name: Layer name

        Returns:
            Summary dictionary
        """
        from backend.models.persistent_data_models import TrustModel

        results = self.db_session.query(TrustModel).filter_by(
            task_id=task_id,
            layer_name=layer_name
        ).all()

        if not results:
            return {
                "layer": layer_name,
                "agent_count": 0,
                "avg_trust": 1.0,
                "agents": []
            }

        agents = []
        total_trust = 0.0

        for result in results:
            trust_values = list(result.trust_matrix.values())
            avg_trust = sum(trust_values) / len(trust_values) if trust_values else 1.0
            total_trust += avg_trust

            agents.append({
                "agent_id": result.agent_id,
                "avg_trust": avg_trust,
                "update_count": result.update_count,
                "last_reward": result.last_reward,
            })

        return {
            "layer": layer_name,
            "agent_count": len(results),
            "avg_trust": total_trust / len(results),
            "agents": agents
        }

    def get_trust_history(
        self,
        agent_id: str,
        task_id: Optional[str] = None,
        limit: int = 10
    ) -> List[TrustUpdate]:
        """Get trust update history for agent.

        Args:
            agent_id: Agent identifier
            task_id: Optional task filter
            limit: Maximum number of records

        Returns:
            List of TrustUpdate records
        """
        from backend.models.persistent_data_models import TrustModel

        query = self.db_session.query(TrustModel).filter_by(agent_id=agent_id)

        if task_id:
            query = query.filter_by(task_id=task_id)

        results = query.order_by(TrustModel.updated_at.desc()).limit(limit).all()

        history = []
        for i, result in enumerate(results):
            if i < len(results) - 1:
                prev_matrix = results[i + 1].trust_matrix
            else:
                prev_matrix = self._get_initial_trust_matrix(agent_id)

            history.append(TrustUpdate(
                agent_id=result.agent_id,
                previous_trust=prev_matrix,
                new_trust=result.trust_matrix,
                reward=result.last_reward or 0.0,
                learning_rate=settings.trust_update_lr,
                update_time=result.updated_at or result.created_at
            ))

        return history

    def reset_trust_matrix(self, agent_id: str, task_id: str) -> None:
        """Reset trust matrix to initial values.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier
        """
        from backend.models.persistent_data_models import TrustModel
        from sqlalchemy import and_

        existing = self.db_session.query(TrustModel).filter(
            and_(
                TrustModel.agent_id == agent_id,
                TrustModel.task_id == task_id
            )
        ).first()

        if existing:
            existing.trust_matrix = self._get_initial_trust_matrix(agent_id)
            existing.update_count = 0
            existing.last_reward = None
            existing.updated_at = datetime.utcnow()
            self.db_session.commit()
