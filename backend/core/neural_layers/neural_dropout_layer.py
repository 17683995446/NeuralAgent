"""Neural Dropout Layer - 神经网络Dropout层

Layer 9 of the NeuralAgent Deep Architecture.

功能：
- 防止过拟合
- 提高模型泛化能力
- 支持训练和推理模式
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DropoutConfig:
    """Dropout层配置"""
    dropout_rate: float = 0.1
    training: bool = True
    inplace: bool = False


@dataclass
class DropoutResult:
    """Dropout结果"""
    output: List[List[float]]
    dropout_mask: List[List[int]]
    num_dropped: int
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class NeuralDropoutLayer:
    """神经网络Dropout层 - Layer 9
    
    防止过拟合，提高泛化能力。
    """
    
    def __init__(self, config: Optional[DropoutConfig] = None):
        self.config = config or DropoutConfig()
        
        self._stats = {
            "total_forwards": 0,
            "total_dropped": 0,
            "total_processing_time_ms": 0.0,
        }
    
    async def forward(
        self,
        input_data: Union[List[List[float]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """前向传播
        
        Args:
            input_data: 输入数据
            
        Returns:
            包含Dropout结果的字典
        """
        import time
        start_time = time.time()
        
        if isinstance(input_data, dict):
            if "residual_output" in input_data:
                data = input_data["residual_output"]
            elif "data" in input_data:
                data = input_data["data"]
            else:
                data = [[0.0]]
        else:
            data = input_data if input_data else [[0.0]]
        
        if not data or not data[0]:
            data = [[0.0]]
        
        if self.config.training and self.config.dropout_rate > 0:
            result = self._apply_dropout(data)
        else:
            result = DropoutResult(
                output=data,
                dropout_mask=[[1 for _ in row] for row in data],
                num_dropped=0,
                processing_time_ms=0.0
            )
        
        self._stats["total_forwards"] += 1
        self._stats["total_dropped"] += result.num_dropped
        
        processing_time = (time.time() - start_time) * 1000
        self._stats["total_processing_time_ms"] += processing_time
        
        return {
            "dropout_output": result.output,
            "dropout_mask": result.dropout_mask,
            "dropout_rate": self.config.dropout_rate,
            "num_dropped": result.num_dropped,
            "training": self.config.training,
            "layer": "dropout",
            "layer_id": 9,
            "processing_time_ms": processing_time,
        }
    
    def _apply_dropout(self, data: List[List[float]]) -> DropoutResult:
        """应用Dropout"""
        import time
        start_time = time.time()
        
        output = []
        mask = []
        num_dropped = 0
        
        keep_prob = 1.0 - self.config.dropout_rate
        
        for row in data:
            new_row = []
            mask_row = []
            for value in row:
                if random.random() < self.config.dropout_rate:
                    new_row.append(0.0)
                    mask_row.append(0)
                    num_dropped += 1
                else:
                    new_row.append(value / keep_prob)
                    mask_row.append(1)
            output.append(new_row)
            mask.append(mask_row)
        
        processing_time = (time.time() - start_time) * 1000
        
        return DropoutResult(
            output=output,
            dropout_mask=mask,
            num_dropped=num_dropped,
            processing_time_ms=processing_time
        )
    
    def set_training(self, training: bool) -> None:
        """设置训练模式"""
        self.config.training = training
        logger.info(f"Dropout layer training mode set to: {training}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_dropped = (
            self._stats["total_dropped"] / self._stats["total_forwards"]
            if self._stats["total_forwards"] > 0 else 0.0
        )
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_forwards"]
            if self._stats["total_forwards"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "avg_dropped_per_forward": avg_dropped,
            "avg_processing_time_ms": avg_processing_time,
            "config": {
                "dropout_rate": self.config.dropout_rate,
                "training": self.config.training,
            }
        }


def create_dropout_layer(dropout_rate: float = 0.1) -> NeuralDropoutLayer:
    """创建Dropout层实例"""
    config = DropoutConfig(dropout_rate=dropout_rate)
    return NeuralDropoutLayer(config)
