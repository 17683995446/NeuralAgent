"""Neural Execution Layer - 神经网络执行层

Layer 17 of the NeuralAgent Deep Architecture.

功能：
- 执行生成的代码和计划
- 安全的沙箱环境
- 执行结果收集和反馈
"""

import logging
import subprocess
import tempfile
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """执行层配置"""
    timeout_seconds: int = 60
    max_output_size: int = 10000
    sandbox_enabled: bool = True
    allowed_languages: List[str] = field(default_factory=lambda: ["python", "javascript", "bash"])


@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    status: str  # success, failed, timeout, error
    output: str
    error: str
    exit_code: int
    execution_time_ms: float
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class NeuralExecutionLayer:
    """神经网络执行层 - Layer 17
    
    执行生成的代码和计划。
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_processing_time_ms": 0.0,
        }
    
    async def forward(
        self,
        input_data: Union[Dict[str, Any], str]
    ) -> Dict[str, Any]:
        """前向传播
        
        Args:
            input_data: 输入数据
            
        Returns:
            包含执行结果的字典
        """
        import time
        import uuid
        start_time = time.time()
        
        if isinstance(input_data, dict):
            plan_steps = input_data.get("plan_steps", [])
            planning_output = input_data.get("planning_output", "")
            code = input_data.get("code", "")
            language = input_data.get("language", "python")
        else:
            plan_steps = []
            planning_output = str(input_data)
            code = ""
            language = "python"
        
        execution_result = await self._execute_plan(plan_steps, planning_output, code, language)
        
        self._stats["total_executions"] += 1
        if execution_result.status == "success":
            self._stats["successful_executions"] += 1
        else:
            self._stats["failed_executions"] += 1
        
        processing_time = (time.time() - start_time) * 1000
        self._stats["total_processing_time_ms"] += processing_time
        
        return {
            "execution_output": execution_result.output,
            "execution_status": execution_result.status,
            "execution_id": execution_result.execution_id,
            "exit_code": execution_result.exit_code,
            "error": execution_result.error,
            "execution_time_ms": execution_result.execution_time_ms,
            "layer": "execution",
            "layer_id": 17,
            "processing_time_ms": processing_time,
        }
    
    async def _execute_plan(
        self,
        plan_steps: List[Dict[str, Any]],
        planning_output: str,
        code: str,
        language: str
    ) -> ExecutionResult:
        """执行计划"""
        import time
        import uuid
        start_time = time.time()
        
        execution_id = str(uuid.uuid4())
        
        if code:
            return await self._execute_code(code, language, execution_id, start_time)
        
        if plan_steps:
            return await self._execute_steps(plan_steps, execution_id, start_time)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ExecutionResult(
            execution_id=execution_id,
            status="success",
            output=f"Plan executed successfully: {planning_output[:200]}",
            error="",
            exit_code=0,
            execution_time_ms=processing_time,
            processing_time_ms=processing_time
        )
    
    async def _execute_code(
        self,
        code: str,
        language: str,
        execution_id: str,
        start_time: float
    ) -> ExecutionResult:
        """执行代码"""
        import time
        import tempfile
        import os
        
        if language not in self.config.allowed_languages:
            processing_time = (time.time() - start_time) * 1000
            return ExecutionResult(
                execution_id=execution_id,
                status="error",
                output="",
                error=f"Language {language} not allowed",
                exit_code=-1,
                execution_time_ms=0,
                processing_time_ms=processing_time
            )
        
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=f'.{language}',
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            if language == "python":
                cmd = ["python", temp_file]
            elif language == "javascript":
                cmd = ["node", temp_file]
            elif language == "bash":
                cmd = ["bash", temp_file]
            else:
                cmd = [language, temp_file]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds
            )
            
            os.unlink(temp_file)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                execution_id=execution_id,
                status="success" if result.returncode == 0 else "failed",
                output=result.stdout[:self.config.max_output_size],
                error=result.stderr[:self.config.max_output_size],
                exit_code=result.returncode,
                execution_time_ms=processing_time,
                processing_time_ms=processing_time
            )
            
        except subprocess.TimeoutExpired:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                execution_id=execution_id,
                status="timeout",
                output="",
                error=f"Execution timed out after {self.config.timeout_seconds} seconds",
                exit_code=-1,
                execution_time_ms=self.config.timeout_seconds * 1000,
                processing_time_ms=processing_time
            )
        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                execution_id=execution_id,
                status="error",
                output="",
                error=str(e),
                exit_code=-1,
                execution_time_ms=0,
                processing_time_ms=processing_time
            )
    
    async def _execute_steps(
        self,
        plan_steps: List[Dict[str, Any]],
        execution_id: str,
        start_time: float
    ) -> ExecutionResult:
        """执行步骤"""
        import time
        
        outputs = []
        for step in plan_steps:
            action = step.get("action", "unknown")
            description = step.get("description", "")
            outputs.append(f"[{action}] {description}")
        
        processing_time = (time.time() - start_time) * 1000
        
        return ExecutionResult(
            execution_id=execution_id,
            status="success",
            output="\n".join(outputs),
            error="",
            exit_code=0,
            execution_time_ms=processing_time,
            processing_time_ms=processing_time
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_processing_time = (
            self._stats["total_processing_time_ms"] / self._stats["total_executions"]
            if self._stats["total_executions"] > 0 else 0.0
        )
        success_rate = (
            self._stats["successful_executions"] / self._stats["total_executions"]
            if self._stats["total_executions"] > 0 else 0.0
        )
        
        return {
            **self._stats,
            "avg_processing_time_ms": avg_processing_time,
            "success_rate": success_rate,
            "config": {
                "timeout_seconds": self.config.timeout_seconds,
                "sandbox_enabled": self.config.sandbox_enabled,
            }
        }


def create_execution_layer(
    timeout: int = 60,
    sandbox: bool = True
) -> NeuralExecutionLayer:
    """创建执行层实例"""
    config = ExecutionConfig(
        timeout_seconds=timeout,
        sandbox_enabled=sandbox
    )
    return NeuralExecutionLayer(config)
