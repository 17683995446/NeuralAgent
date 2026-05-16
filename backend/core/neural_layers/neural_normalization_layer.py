"""Neural Normalization Layer - 神经网络归一化层

Layer 3 of the NeuralAgent Deep Architecture.

功能：
- 对输入特征进行标准化
- 支持 Layer Normalization 和 Batch Normalization
- 稳定后续层的训练和推理
"""

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NormalizationConfig:
    """归一化层配置"""
    method: str = "layer_norm"  # layer_norm, batch_norm, instance_norm
    dimension: int = 768
    epsilon: float = 1e-6
    use_learnable_params: bool = True
    momentum: float = 0.1  # 用于 batch_norm


@dataclass
class NormalizationResult:
    """归一化结果"""
    normalized_data: List[float]
    mean: float
    std: float
    method: str
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseNormalizer(ABC):
    """归一化器基类"""
    
    @abstractmethod
    def normalize(self, data: List[float]) -> NormalizationResult:
        """归一化数据"""
        pass
    
    @abstractmethod
    def denormalize(self, normalized_data: List[float], mean: float, std: float) -> List[float]:
        """反归一化"""
        pass


class LayerNormalizer(BaseNormalizer):
    """Layer Normalization 归一化器"""
    
    def __init__(self, config: NormalizationConfig):
        self.config = config
        self.epsilon = config.epsilon
        
        self.gamma = 1.0
        self.beta = 0.0
    
    def normalize(self, data: List[float]) -> NormalizationResult:
        """Layer Normalization"""
        import time
        start_time = time.time()
        
        n = len(data)
        if n == 0:
            return NormalizationResult(
                normalized_data=[],
                mean=0.0,
                std=0.0,
                method="layer_norm",
                processing_time_ms=0.0
            )
        
        mean = sum(data) / n
        variance = sum((x - mean) ** 2 for x in data) / n
        std = math.sqrt(variance + self.epsilon)
        
        normalized = [(x - mean) / std * self.gamma + self.beta for x in data]
        
        processing_time = (time.time() - start_time) * 1000
        
        return NormalizationResult(
            normalized_data=normalized,
            mean=mean,
            std=std,
            method="layer_norm",
            processing_time_ms=processing_time
        )
    
    def denormalize(self, normalized_data: List[float], mean: float, std: float) -> List[float]:
        """反归一化"""
        return [(x - self.beta) / self.gamma * std + mean for x in normalized_data]


class BatchNormalizer(BaseNormalizer):
    """Batch Normalization 归一化器"""
    
    def __init__(self, config: NormalizationConfig):
        self.config = config
        self.epsilon = config.epsilon
        self.momentum = config.momentum
        
        self.running_mean = 0.0
        self.running_var = 1.0
        self.gamma = 1.0
        self.beta = 0.0
        self.training = True
    
    def normalize(self, data: List[float]) -> NormalizationResult:
        """Batch Normalization"""
        import time
        start_time = time.time()
        
        n = len(data)
        if n == 0:
            return NormalizationResult(
                normalized_data=[],
                mean=0.0,
                std=0.0,
                method="batch_norm",
                processing_time_ms=0.0
            )
        
        if self.training:
            mean = sum(data) / n
            variance = sum((x - mean) ** 2 for x in data) / n
            
            self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * mean
            self.running_var = (1 - self.momentum) * self.running_var + self.momentum * variance
        else:
            mean = self.running_mean
            variance = self.running_var
        
        std = math.sqrt(variance + self.epsilon)
        normalized = [(x - mean) / std * self.gamma + self.beta for x in data]
        
        processing_time = (time.time() - start_time) * 1000
        
        return NormalizationResult(
            normalized_data=normalized,
            mean=mean,
            std=std,
            method="batch_norm",
            processing_time_ms=processing_time
        )
    
    def denormalize(self, normalized_data: List[float], mean: float, std: float) -> List[float]:
        """反归一化"""
        return [(x - self.beta) / self.gamma * std + mean for x in normalized_data]


class InstanceNormalizer(BaseNormalizer):
    """Instance Normalization 归一化器"""
    
    def __init__(self, config: NormalizationConfig):
        self.config = config
        self.epsilon = config.epsilon
    
    def normalize(self, data: List[float]) -> NormalizationResult:
        """Instance Normalization"""
        import time
        start_time = time.time()
        
        n = len(data)
        if n == 0:
            return NormalizationResult(
                normalized_data=[],
                mean=0.0,
                std=0.0,
                method="instance_norm",
                processing_time_ms=0.0
            )
        
        mean = sum(data) / n
        variance = sum((x - mean) ** 2 for x in data) / n
        std = math.sqrt(variance + self.epsilon)
        
        normalized = [(x - mean) / std for x in data]
        
        processing_time = (time.time() - start_time) * 1000
        
        return NormalizationResult(
            normalized_data=normalized,
            mean=mean,
            std=std,
            method="instance_norm",
            processing_time_ms=processing_time
        )
    
    def denormalize(self, normalized_data: List[float], mean: float, std: float) -> List[float]:
        """反归一化"""
        return [x * std + mean for x in normalized_data]


class NeuralNormalizationLayer:
    """神经网络归一化层 - Layer 3
    
    对输入特征进行标准化，稳定后续处理。
    """
    
    def __init__(self, config: Optional[NormalizationConfig] = None):
        self.config = config or NormalizationConfig()
        self.normalizer: BaseNormalizer = self._create_normalizer()
        
        self._stats = {
            "total_normalizations": 0,
            "total_processing_time_ms": 0.0,
        }
    
    def _create_normalizer(self) -> BaseNormalizer:
        """创建归一化器"""
        if self.config.method == "layer_norm":
            return LayerNormalizer(self.config)
        elif self.config.method == "batch_norm":
            return BatchNormalizer(self.config)
        elif self.config.method == "instance_norm":
            return InstanceNormalizer(self.config)
        else:
            logger.warning(f"Unknown normalization method: {self.config.method}, using layer_norm")
            return LayerNormalizer(self.config)
    
    async def forward(
        self,
        input_data: Union[List[float], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """前向传播
        
        Args:
            input_data: 输入数据，可以是向量或字典
            
        Returns:
            包含归一化结果的字典
        """
        import time
        start_time = time.time()
        
        if isinstance(input_data, dict):
            if "embeddings" in input_data:
                embeddings = input_data["embeddings"]
                if embeddings and hasattr(embeddings[0], 'embedding'):
                    data = embeddings[0].embedding
                elif embeddings and isinstance(embeddings[0], dict):
                    data = embeddings[0].get("embedding", [])
                else:
                    data = []
            elif "data" in input_data:
                data = input_data["data"]
            else:
                data = []
        else:
            data = input_data
        
        if not data:
            return {
                "normalized_data": [],
                "normalization_result": None,
                "layer": "normalization",
                "layer_id": 3,
                "processing_time_ms": 0.0,
            }
        
        result = self.normalizer.normalize(data)
        
        self._stats["total_normalizations"] += 1
        self._stats["total_processing_time_ms"] += result.processing_time_ms
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "normalized_data": result.normalized_data,
            "normalization_result": {
                "mean": result.mean,
                "std": result.std,
                "method": result.method,
            },
            "original_data": data,
            "dimension": len(data),
            "layer": "normalization",
            "layer_id": 3,
            "processing_time_ms": processing_time,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_normalizations"]
            if self._stats["total_normalizations"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "avg_processing_time_ms": avg_processing_time,
            "config": {
                "method": self.config.method,
                "dimension": self.config.dimension,
            }
        }


def create_normalization_layer(
    method: str = "layer_norm",
    dimension: int = 768
) -> NeuralNormalizationLayer:
    """创建归一化层实例"""
    config = NormalizationConfig(
        method=method,
        dimension=dimension
    )
    return NeuralNormalizationLayer(config)
