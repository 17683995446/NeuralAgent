"""Task Management Module - 任务管理模块

包含智能任务分解功能。
"""

import logging

logger = logging.getLogger(__name__)

from .intelligent_task_decomposer_service import IntelligentTaskDecomposerService

__all__ = [
    "IntelligentTaskDecomposerService",
]

logger.info("Task Management module loaded successfully")
