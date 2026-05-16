"""Neural Residual Layer - 神经网络残差层

Layer 7-8 of the NeuralAgent Deep Architecture.

功能：
- 实现残差连接
- 支持更深的网络训练
- 缓解梯度消失问题
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ResidualConfig:
    """残差层配置"""
    dimension: int = 768
    hidden_dimension: int = 1024
    num_layers: int = 2
    dropout_rate: float = 0.1
    activation: str = "relu"  # relu, gelu, tanh
    use_layer_norm: bool = True


@dataclass
class ResidualBlockResult:
    """残差块结果"""
    output: List[List[float]]
    residual_connection: List[List[float]]
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResidualBlock:
    """残差块"""
    
    def __init__(self, config: ResidualConfig):
        self.config = config
        self.weights = self._initialize_weights()
    
    def _initialize_weights(self) -> Dict[str, List[List[float]]]:
        """初始化权重"""
        import random
        
        def random_matrix(rows: int, cols: int) -> List[List[float]]:
            scale = 1.0 / math.sqrt(cols)
            return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]
        
        return {
            "W1": random_matrix(self.config.dimension, self.config.hidden_dimension),
            "b1": [[0.0] for _ in range(self.config.hidden_dimension)],
            "W2": random_matrix(self.config.hidden_dimension, self.config.dimension),
            "b2": [[0.0] for _ in range(self.config.dimension)],
        }
    
    def forward(self, x: List[List[float]]) -> ResidualBlockResult:
        """前向传播"""
        import time
        start_time = time.time()
        
        residual = x
        
        out = self._matmul(x, self.weights["W1"])
        out = self._add_bias(out, self.weights["b1"])
        out = self._activate(out)
        
        out = self._matmul(out, self.weights["W2"])
        out = self._add_bias(out, self.weights["b2"])
        
        out = self._add(out, residual)
        
        if self.config.use_layer_norm:
            out = self._layer_norm(out)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ResidualBlockResult(
            output=out,
            residual_connection=residual,
            processing_time_ms=processing_time
        )
    
    def _matmul(self, A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
        """矩阵乘法"""
        if not A or not B:
            return A
        
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
    
    def _add_bias(self, matrix: List[List[float]], bias: List[List[float]]) -> List[List[float]]:
        """添加偏置"""
        if not bias or not matrix:
            return matrix
        
        result = []
        for row in matrix:
            new_row = [row[i] + bias[i][0] if i < len(bias) else row[i] for i in range(len(row))]
            result.append(new_row)
        
        return result
    
    def _activate(self, matrix: List[List[float]]) -> List[List[float]]:
        """激活函数"""
        if self.config.activation == "relu":
            return [[max(0, x) for x in row] for row in matrix]
        elif self.config.activation == "gelu":
            import math
            return [[0.5 * x * (1 + math.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x ** 3))) for x in row] for row in matrix]
        elif self.config.activation == "tanh":
            import math
            return [[math.tanh(x) for x in row] for row in matrix]
        else:
            return matrix
    
    def _add(self, A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
        """矩阵加法"""
        if not A or not B:
            return A
        
        return [[A[i][j] + B[i][j] if j < len(B[i]) else A[i][j] for j in range(len(A[i]))] for i in range(len(A))]
    
    def _layer_norm(self, matrix: List[List[float]]) -> List[List[float]]:
        """Layer Normalization"""
        import math
        
        result = []
        for row in matrix:
            mean = sum(row) / len(row) if row else 0
            variance = sum((x - mean) ** 2 for x in row) / len(row) if row else 0
            std = math.sqrt(variance + 1e-6)
            normalized = [(x - mean) / std for x in row]
            result.append(normalized)
        
        return result


class NeuralResidualLayer:
    """神经网络残差层 - Layer 7-8
    
    实现残差连接，支持更深的网络。
    """
    
    def __init__(self, config: Optional[ResidualConfig] = None, layer_id: int = 7):
        self.config = config or ResidualConfig()
        self.layer_id = layer_id
        self.blocks = [ResidualBlock(self.config) for _ in range(self.config.num_layers)]
        
        self._stats = {
            "total_forwards": 0,
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
            包含残差结果的字典
        """
        import time
        start_time = time.time()
        
        if isinstance(input_data, dict):
            if "attention_output" in input_data:
                data = input_data["attention_output"]
            elif "data" in input_data:
                data = input_data["data"]
            else:
                data = [[0.0] * self.config.dimension]
        else:
            data = input_data if input_data else [[0.0] * self.config.dimension]
        
        if not data or not data[0]:
            data = [[0.0] * self.config.dimension]
        
        residuals = []
        for block in self.blocks:
            result = block.forward(data)
            data = result.output
            residuals.append(result.residual_connection)
        
        self._stats["total_forwards"] += 1
        
        processing_time = (time.time() - start_time) * 1000
        self._stats["total_processing_time_ms"] += processing_time
        
        return {
            "residual_output": data,
            "residual_connections": residuals,
            "num_blocks": len(self.blocks),
            "layer": "residual",
            "layer_id": self.layer_id,
            "processing_time_ms": processing_time,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_forwards"]
            if self._stats["total_forwards"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "avg_processing_time_ms": avg_processing_time,
            "config": {
                "dimension": self.config.dimension,
                "hidden_dimension": self.config.hidden_dimension,
                "num_layers": self.config.num_layers,
            }
        }


def create_residual_layer(
    dimension: int = 768,
    hidden_dimension: int = 1024,
    layer_id: int = 7
) -> NeuralResidualLayer:
    """创建残差层实例"""
    config = ResidualConfig(
        dimension=dimension,
        hidden_dimension=hidden_dimension
    )
    return NeuralResidualLayer(config, layer_id)
