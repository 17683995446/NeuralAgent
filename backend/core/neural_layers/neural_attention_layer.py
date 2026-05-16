"""Neural Attention Layer - 神经网络注意力层

Layer 6 of the NeuralAgent Deep Architecture.

功能：
- 实现自注意力机制
- 支持多头注意力
- 关注重要信息，忽略无关内容
"""

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AttentionConfig:
    """注意力层配置"""
    dimension: int = 768
    num_heads: int = 12
    head_dimension: int = 64
    dropout_rate: float = 0.1
    use_bias: bool = True
    attention_type: str = "self_attention"  # self_attention, cross_attention


@dataclass
class AttentionWeights:
    """注意力权重"""
    query_weights: List[List[float]] = field(default_factory=list)
    key_weights: List[List[float]] = field(default_factory=list)
    value_weights: List[List[float]] = field(default_factory=list)
    output_weights: List[List[float]] = field(default_factory=list)


@dataclass
class AttentionResult:
    """注意力结果"""
    output: List[List[float]]
    attention_weights: List[List[float]]
    attention_scores: List[List[float]]
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAttention(ABC):
    """注意力机制基类"""
    
    @abstractmethod
    def compute_attention(
        self,
        query: List[List[float]],
        key: List[List[float]],
        value: List[List[float]]
    ) -> AttentionResult:
        """计算注意力"""
        pass


class SelfAttention(BaseAttention):
    """自注意力机制"""
    
    def __init__(self, config: AttentionConfig):
        self.config = config
        self.dimension = config.dimension
        self.num_heads = config.num_heads
        self.head_dimension = config.head_dimension
        self.dropout_rate = config.dropout_rate
        
        self.weights = self._initialize_weights()
    
    def _initialize_weights(self) -> AttentionWeights:
        """初始化权重"""
        import random
        
        def random_matrix(rows: int, cols: int) -> List[List[float]]:
            scale = 1.0 / math.sqrt(cols)
            return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]
        
        return AttentionWeights(
            query_weights=random_matrix(self.dimension, self.dimension),
            key_weights=random_matrix(self.dimension, self.dimension),
            value_weights=random_matrix(self.dimension, self.dimension),
            output_weights=random_matrix(self.dimension, self.dimension)
        )
    
    def compute_attention(
        self,
        query: List[List[float]],
        key: List[List[float]],
        value: List[List[float]]
    ) -> AttentionResult:
        """计算自注意力"""
        import time
        start_time = time.time()
        
        Q = self._matmul(query, self.weights.query_weights)
        K = self._matmul(key, self.weights.key_weights)
        V = self._matmul(value, self.weights.value_weights)
        
        Q_heads = self._split_heads(Q)
        K_heads = self._split_heads(K)
        V_heads = self._split_heads(V)
        
        attention_scores = []
        attention_weights = []
        outputs = []
        
        for h in range(self.num_heads):
            scores = self._matmul(Q_heads[h], self._transpose(K_heads[h]))
            scores = self._scale(scores, 1.0 / math.sqrt(self.head_dimension))
            weights = self._softmax(scores)
            
            attention_scores.append(scores)
            attention_weights.append(weights)
            
            output = self._matmul(weights, V_heads[h])
            outputs.append(output)
        
        concatenated = self._concat_heads(outputs)
        final_output = self._matmul(concatenated, self.weights.output_weights)
        
        processing_time = (time.time() - start_time) * 1000
        
        return AttentionResult(
            output=final_output,
            attention_weights=attention_weights,
            attention_scores=attention_scores,
            processing_time_ms=processing_time
        )
    
    def _matmul(self, A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
        """矩阵乘法"""
        if not A or not B:
            return []
        
        rows_A, cols_A = len(A), len(A[0])
        rows_B, cols_B = len(B), len(B[0])
        
        if cols_A != rows_B:
            return A
        
        result = [[0.0 for _ in range(cols_B)] for _ in range(rows_A)]
        
        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    result[i][j] += A[i][k] * B[k][j]
        
        return result
    
    def _transpose(self, matrix: List[List[float]]) -> List[List[float]]:
        """矩阵转置"""
        if not matrix:
            return []
        return [[matrix[i][j] for i in range(len(matrix))] for j in range(len(matrix[0]))]
    
    def _split_heads(self, tensor: List[List[float]]) -> List[List[List[float]]]:
        """分割多头"""
        if not tensor:
            return [[] for _ in range(self.num_heads)]
        
        seq_len = len(tensor)
        heads = [[] for _ in range(self.num_heads)]
        
        for i in range(seq_len):
            row = tensor[i]
            for h in range(self.num_heads):
                start = h * self.head_dimension
                end = start + self.head_dimension
                heads[h].append(row[start:end] if end <= len(row) else row[start:] + [0.0] * (end - len(row)))
        
        return heads
    
    def _concat_heads(self, heads: List[List[List[float]]]) -> List[List[float]]:
        """连接多头"""
        if not heads or not heads[0]:
            return []
        
        seq_len = len(heads[0])
        result = []
        
        for i in range(seq_len):
            concatenated = []
            for h in range(self.num_heads):
                concatenated.extend(heads[h][i])
            result.append(concatenated)
        
        return result
    
    def _scale(self, matrix: List[List[float]], scale: float) -> List[List[float]]:
        """缩放矩阵"""
        return [[x * scale for x in row] for row in matrix]
    
    def _softmax(self, matrix: List[List[float]]) -> List[List[float]]:
        """Softmax 函数"""
        import math
        
        result = []
        for row in matrix:
            max_val = max(row) if row else 0
            exp_vals = [math.exp(x - max_val) for x in row]
            sum_exp = sum(exp_vals) if exp_vals else 1
            result.append([e / sum_exp for e in exp_vals])
        
        return result


class CrossAttention(BaseAttention):
    """交叉注意力机制"""
    
    def __init__(self, config: AttentionConfig):
        self.config = config
        self.self_attention = SelfAttention(config)
    
    def compute_attention(
        self,
        query: List[List[float]],
        key: List[List[float]],
        value: List[List[float]]
    ) -> AttentionResult:
        """计算交叉注意力"""
        return self.self_attention.compute_attention(query, key, value)


class NeuralAttentionLayer:
    """神经网络注意力层 - Layer 6
    
    实现自注意力和交叉注意力机制。
    """
    
    def __init__(self, config: Optional[AttentionConfig] = None):
        self.config = config or AttentionConfig()
        self.attention: BaseAttention = self._create_attention()
        
        self._stats = {
            "total_attentions": 0,
            "total_processing_time_ms": 0.0,
        }
    
    def _create_attention(self) -> BaseAttention:
        """创建注意力机制"""
        if self.config.attention_type == "self_attention":
            return SelfAttention(self.config)
        elif self.config.attention_type == "cross_attention":
            return CrossAttention(self.config)
        else:
            logger.warning(f"Unknown attention type: {self.config.attention_type}, using self_attention")
            return SelfAttention(self.config)
    
    async def forward(
        self,
        input_data: Union[List[List[float]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """前向传播
        
        Args:
            input_data: 输入数据，可以是矩阵或字典
            
        Returns:
            包含注意力结果的字典
        """
        import time
        start_time = time.time()
        
        if isinstance(input_data, dict):
            if "normalized_data" in input_data:
                data = input_data["normalized_data"]
                data = [[x] for x in data] if isinstance(data, list) and data and isinstance(data[0], (int, float)) else [data]
            elif "data" in input_data:
                data = input_data["data"]
            else:
                data = [[0.0] * self.config.dimension]
        else:
            data = input_data if input_data else [[0.0] * self.config.dimension]
        
        if not data or not data[0]:
            data = [[0.0] * self.config.dimension]
        
        result = self.attention.compute_attention(data, data, data)
        
        self._stats["total_attentions"] += 1
        self._stats["total_processing_time_ms"] += result.processing_time_ms
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "attention_output": result.output,
            "attention_weights": result.attention_weights,
            "attention_scores": result.attention_scores,
            "num_heads": self.config.num_heads,
            "head_dimension": self.config.head_dimension,
            "layer": "attention",
            "layer_id": 6,
            "processing_time_ms": processing_time,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_attentions"]
            if self._stats["total_attentions"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "avg_processing_time_ms": avg_processing_time,
            "config": {
                "dimension": self.config.dimension,
                "num_heads": self.config.num_heads,
                "attention_type": self.config.attention_type,
            }
        }


def create_attention_layer(
    dimension: int = 768,
    num_heads: int = 12
) -> NeuralAttentionLayer:
    """创建注意力层实例"""
    config = AttentionConfig(
        dimension=dimension,
        num_heads=num_heads
    )
    return NeuralAttentionLayer(config)
