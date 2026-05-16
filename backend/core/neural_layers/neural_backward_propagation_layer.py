"""Backward Propagation Layer - Feedback Iteration Layer."""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.config import settings
from backend.core.trust_management.trust_manager import TrustManager
from backend.core.memory.long_term_memory import LongTermMemory

logger = logging.getLogger(__name__)


class BackwardLayer:
    """Backward propagation layer for feedback iteration.

    Receives user feedback, calculates rewards, updates trust matrices,
    and triggers re-execution of forward propagation.
    """

    def __init__(
        self,
        task_id: str,
        trust_manager: TrustManager,
        long_term_memory: Optional[LongTermMemory] = None
    ):
        """Initialize backward layer.

        Args:
            task_id: Task identifier
            trust_manager: Trust manager for weight updates
            long_term_memory: Long-term memory for experience storage
        """
        self.task_id = task_id
        self.trust_manager = trust_manager
        self.long_term_memory = long_term_memory
        self.feedback_history: List[Dict[str, Any]] = []

    async def execute(
        self,
        user_feedback: Dict[str, Any],
        current_iteration: int,
        max_iteration: int,
        learning_rate: float
    ) -> Dict[str, Any]:
        """Execute backward propagation.

        Args:
            user_feedback: User feedback dictionary
            current_iteration: Current iteration number
            max_iteration: Maximum allowed iterations
            learning_rate: Learning rate for trust updates

        Returns:
            Backward propagation result with trust updates
        """
        logger.info(f"Starting backward propagation for task {self.task_id}, iteration {current_iteration}")

        reward = self._calculate_reward(user_feedback)

        error_signal = self._generate_error_signal(user_feedback)

        layer_updates = await self._update_layer_trust(
            reward,
            error_signal,
            learning_rate
        )

        self._save_feedback(user_feedback, reward, layer_updates)

        if self.long_term_memory:
            self._update_long_term_memory(user_feedback, reward)

        should_continue = current_iteration < max_iteration

        logger.info(f"Backward propagation completed: reward={reward}, continue={should_continue}")

        return {
            "reward": reward,
            "error_signal": error_signal,
            "layer_updates": layer_updates,
            "should_continue": should_continue,
            "next_iteration": current_iteration + 1 if should_continue else None,
            "feedback_history": self.feedback_history
        }

    def _calculate_reward(self, user_feedback: Dict[str, Any]) -> float:
        """Calculate reward from user feedback.

        Args:
            user_feedback: User feedback dictionary

        Returns:
            Reward value in range [-1, 1]
        """
        satisfaction_score = user_feedback.get("satisfaction_score", 3)

        base_reward = (satisfaction_score - 3) / 2

        feedback_items = user_feedback.get("feedback_items", [])
        for item in feedback_items:
            feedback_type = item.get("type", "")
            if feedback_type == "positive":
                base_reward += 0.1
            elif feedback_type == "negative":
                base_reward -= 0.1

        reward = max(-1.0, min(1.0, base_reward))

        logger.debug(f"Reward calculated: {reward} (base={base_reward}, satisfaction={satisfaction_score})")

        return reward

    def _generate_error_signal(self, user_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Generate error signals from feedback.

        Args:
            user_feedback: User feedback dictionary

        Returns:
            Error signal dictionary
        """
        feedback_items = user_feedback.get("feedback_items", [])

        signals = {
            "overall": 1.0 if user_feedback.get("satisfaction_score", 3) >= 3 else -1.0,
            "positive_count": sum(1 for f in feedback_items if f.get("type") == "positive"),
            "negative_count": sum(1 for f in feedback_items if f.get("type") == "negative"),
            "affected_layers": self._identify_affected_layers(feedback_items),
            "detailed_signals": feedback_items
        }

        return signals

    def _identify_affected_layers(
        self,
        feedback_items: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify which layers are affected by feedback.

        Args:
            feedback_items: List of feedback items

        Returns:
            List of affected layer names
        """
        affected = set()

        for item in feedback_items:
            affected_agent = item.get("affected_agent", "")

            if "conv" in affected_agent.lower():
                affected.add("convolution")
            elif "pool" in affected_agent.lower():
                affected.add("pooling")
            elif "fc1" in affected_agent.lower() or "understand" in affected_agent.lower():
                affected.add("fc_layer_1")
            elif "fc2" in affected_agent.lower() or "generate" in affected_agent.lower():
                affected.add("fc_layer_2")
            elif "fc3" in affected_agent.lower() or "test" in affected_agent.lower():
                affected.add("fc_layer_3")

        if not affected:
            affected.add("fc_layer_2")

        return list(affected)

    async def _update_layer_trust(
        self,
        reward: float,
        error_signal: Dict[str, Any],
        learning_rate: float
    ) -> Dict[str, Dict[str, float]]:
        """Update trust matrices for all layers.

        Args:
            reward: Reward value
            error_signal: Error signal dictionary
            learning_rate: Learning rate

        Returns:
            Dictionary mapping layer names to updated trust matrices
        """
        layers = ["convolution", "pooling", "fc_layer_1", "fc_layer_2", "fc_layer_3"]
        affected_layers = error_signal.get("affected_layers", layers)

        layer_updates = {}

        for layer in layers:
            importance = 1.0 if layer in affected_layers else 0.5

            layer_reward = reward * importance

            updated_trust = self.trust_manager.apply_reward_adjustment(
                layer_reward,
                learning_rate
            )

            layer_updates[layer] = updated_trust

            logger.debug(f"Layer {layer}: reward={layer_reward}, trust={updated_trust}")

        return layer_updates

    def _save_feedback(
        self,
        user_feedback: Dict[str, Any],
        reward: float,
        layer_updates: Dict[str, Dict[str, float]]
    ) -> None:
        """Save feedback to history.

        Args:
            user_feedback: User feedback
            reward: Calculated reward
            layer_updates: Trust updates per layer
        """
        feedback_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_feedback": user_feedback,
            "reward": reward,
            "layer_updates": layer_updates,
            "satisfaction_score": user_feedback.get("satisfaction_score", 0),
            "feedback_items_count": len(user_feedback.get("feedback_items", []))
        }

        self.feedback_history.append(feedback_record)

    def _update_long_term_memory(
        self,
        user_feedback: Dict[str, Any],
        reward: float
    ) -> None:
        """Update long-term memory with feedback.

        Args:
            user_feedback: User feedback
            reward: Calculated reward
        """
        if not self.long_term_memory:
            return

        satisfaction = user_feedback.get("satisfaction_score", 0)
        is_successful = satisfaction >= 4

        self.long_term_memory.save_memory(
            agent_id=f"backward_{self.task_id}",
            content={
                "feedback": user_feedback,
                "reward": reward,
                "satisfaction": satisfaction,
            },
            metadata={
                "task_id": self.task_id,
                "type": "feedback_experience",
                "success": is_successful,
            }
        )

    def get_feedback_history(self) -> List[Dict[str, Any]]:
        """Get feedback history.

        Returns:
            List of feedback records
        """
        return self.feedback_history.copy()

    def get_trend_analysis(self) -> Dict[str, Any]:
        """Analyze feedback trends.

        Returns:
            Trend analysis dictionary
        """
        if not self.feedback_history:
            return {"trend": "insufficient_data"}

        rewards = [f["reward"] for f in self.feedback_history]
        satisfaction_scores = [f["satisfaction_score"] for f in self.feedback_history]

        avg_reward = sum(rewards) / len(rewards)
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)

        improving = len(rewards) >= 2 and rewards[-1] > rewards[0]

        return {
            "trend": "improving" if improving else "stable",
            "average_reward": avg_reward,
            "average_satisfaction": avg_satisfaction,
            "total_feedbacks": len(self.feedback_history),
            "reward_range": [min(rewards), max(rewards)],
            "satisfaction_range": [min(satisfaction_scores), max(satisfaction_scores)],
        }


class FeedbackProcessor:
    """Processor for user feedback."""

    @staticmethod
    def process_feedback_input(feedback_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate feedback input.

        Args:
            feedback_input: Raw feedback input

        Returns:
            Processed feedback dictionary
        """
        processed = {
            "satisfaction_score": feedback_input.get("satisfaction_score", 3),
            "feedback_items": [],
            "additional_comments": feedback_input.get("additional_comments", ""),
        }

        feedback_items = feedback_input.get("feedback_items", [])
        for item in feedback_items:
            processed["feedback_items"].append({
                "type": item.get("type", "neutral"),
                "description": item.get("description", ""),
                "suggestion": item.get("suggestion", ""),
                "affected_agent": item.get("affected_agent"),
            })

        return processed

    @staticmethod
    def aggregate_similar_feedback(
        feedback_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregate similar feedback items.

        Args:
            feedback_items: List of feedback items

        Returns:
            Aggregated feedback items
        """
        aggregated = {}
        keywords_map = {
            "test": ["test", "测试", "coverage"],
            "code": ["code", "代码", "implementation"],
            "documentation": ["doc", "文档", "comment"],
            "performance": ["performance", "性能", "speed"],
            "security": ["security", "安全", "vulnerability"],
        }

        for item in feedback_items:
            description = item.get("description", "").lower()

            category = "general"
            for kw, keywords in keywords_map.items():
                if any(k in description for k in keywords):
                    category = kw
                    break

            if category in aggregated:
                existing = aggregated[category]
                existing["count"] += 1
                if item.get("type") == "negative":
                    existing["negative_count"] += 1
            else:
                aggregated[category] = {
                    "category": category,
                    "description": item.get("description", ""),
                    "count": 1,
                    "negative_count": 1 if item.get("type") == "negative" else 0,
                    "suggestion": item.get("suggestion", ""),
                    "affected_agent": item.get("affected_agent"),
                }

        return list(aggregated.values())
