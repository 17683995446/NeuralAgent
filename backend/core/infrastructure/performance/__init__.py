"""Performance Module - 性能优化模块"""

import logging

logger = logging.getLogger(__name__)

from .performance_optimizer import PerformanceOptimizer

__all__ = [
    "PerformanceOptimizer",
]

logger.info("Performance module loaded successfully")
