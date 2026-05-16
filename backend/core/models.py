"""
NeuralAgent - Data Validation Models
数据验证与请求模型
"""
from datetime import datetime
from typing import (
    Dict,
    Any,
    Optional,
    List,
    Union
)
from dataclasses import dataclass, field
from enum import Enum
import re


try:
    from pydantic import BaseModel, Field, field_validator, ValidationError
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object
    Field = None
    field_validator = None


# 简单的验证器实现
    class SimpleBaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def dict(self):
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    BaseModel = SimpleBaseModel
    ValidationError = ValueError


class TaskPriority(Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


if HAS_PYDANTIC:
    class BaseRequest(BaseModel):
        """基础请求模型"""
        request_id: Optional[str] = None
        timestamp: Optional[datetime] = None
        
        @field_validator('timestamp', mode='before')
        @classmethod
        def set_timestamp(cls, v):
            return v or datetime.now()


    class BaseResponse(BaseModel):
        """基础响应模型"""
        success: bool = True
        message: str = ""
        request_id: Optional[str] = None
        timestamp: datetime = Field(default_factory=datetime.now)
        data: Optional[Dict[str, Any]] = None
        errors: Optional[List[Dict[str, Any]]] = None


    class HealthResponse(BaseModel):
        """健康检查响应"""
        status: str
        version: str
        timestamp: datetime = Field(default_factory=datetime.now)
        uptime_seconds: Optional[float] = None
        checks: Dict[str, Any] = Field(default_factory=dict)


    class TaskCreateRequest(BaseModel):
        """创建任务请求"""
        title: str = Field(..., min_length=1, max_length=500)
        description: Optional[str] = None
        priority: TaskPriority = TaskPriority.MEDIUM
        metadata: Optional[Dict[str, Any]] = None
        tags: Optional[List[str]] = None
        
        @field_validator('title')
        @classmethod
        def validate_title(cls, v):
            if not v or not v.strip():
                raise ValueError('Title cannot be empty')
            return v.strip()


    class TaskUpdateRequest(BaseModel):
        """更新任务请求"""
        title: Optional[str] = None
        description: Optional[str] = None
        status: Optional[TaskStatus] = None
        priority: Optional[TaskPriority] = None
        metadata: Optional[Dict[str, Any]] = None


    class TaskResponse(BaseModel):
        """任务响应"""
        task_id: str
        title: str
        description: Optional[str] = None
        status: TaskStatus
        priority: TaskPriority
        created_at: datetime
        updated_at: Optional[datetime] = None
        completed_at: Optional[datetime] = None
        metadata: Optional[Dict[str, Any]] = None
        tags: Optional[List[str]] = None


    class WorkflowExecuteRequest(BaseModel):
        """工作流执行请求"""
        workflow_name: str = Field(..., min_length=1)
        inputs: Optional[Dict[str, Any]] = None
        context: Optional[Dict[str, Any]] = None
        options: Optional[Dict[str, Any]] = None


    class WorkflowExecuteResponse(BaseModel):
        """工作流执行响应"""
        execution_id: str
        workflow_name: str
        status: str
        started_at: datetime
        result: Optional[Dict[str, Any]] = None
        error: Optional[str] = None


    class AgentChatRequest(BaseModel):
        """Agent对话请求"""
        query: str = Field(..., min_length=1)
        session_id: Optional[str] = None
        context: Optional[Dict[str, Any]] = None
        agent_id: Optional[str] = None
        options: Optional[Dict[str, Any]] = None


    class AgentChatResponse(BaseModel):
        """Agent对话响应"""
        response: str
        session_id: str
        agent_id: Optional[str] = None
        metadata: Optional[Dict[str, Any]] = None
        thinking: Optional[str] = None


    class SearchMemoryRequest(BaseModel):
        """搜索记忆请求"""
        query: str = Field(..., min_length=1)
        limit: int = 10
        threshold: float = 0.7
        filters: Optional[Dict[str, Any]] = None


    class MemoryItem(BaseModel):
        """记忆项"""
        memory_id: str
        content: str
        metadata: Optional[Dict[str, Any]] = None
        score: Optional[float] = None
        created_at: datetime


    class MemorySearchResponse(BaseModel):
        """记忆搜索响应"""
        results: List[MemoryItem]
        total: int
        query: str


    class CodeAnalysisRequest(BaseModel):
        """代码分析请求"""
        code: str = Field(..., min_length=1)
        language: Optional[str] = None
        analysis_type: str = "full"
        options: Optional[Dict[str, Any]] = None


    class CodeIssue(BaseModel):
        """代码问题"""
        type: str
        severity: str
        location: Optional[Dict[str, int]] = None
        message: str
        suggestion: Optional[str] = None


    class CodeAnalysisResponse(BaseModel):
        """代码分析响应"""
        language: str
        issues: List[CodeIssue]
        summary: str
        suggestions: List[str]


    class APIError(BaseModel):
        """API错误模型"""
        code: str
        message: str
        field: Optional[str] = None
        details: Optional[Dict[str, Any]] = None


    class ErrorResponse(BaseModel):
        """错误响应模型"""
        success: bool = False
        message: str
        errors: Optional[List[APIError]] = None
        request_id: Optional[str] = None
        timestamp: datetime = Field(default_factory=datetime.now)


    class PaginationParams(BaseModel):
        """分页参数"""
        page: int = 1
        page_size: int = 20
        sort_by: Optional[str] = None
        sort_order: str = "desc"
        
        @field_validator('page')
        @classmethod
        def validate_page(cls, v):
            if v < 1:
                return 1
            return v
        
        @field_validator('page_size')
        @classmethod
        def validate_page_size(cls, v):
            if v < 1:
                return 20
            if v > 100:
                return 100
            return v


    class PaginatedResponse(BaseModel):
        """分页响应"""
        items: List[Any]
        page: int
        page_size: int
        total: int
        total_pages: int


    class MetricsResponse(BaseModel):
        """指标响应"""
        system: Dict[str, Any]
        custom: Optional[Dict[str, Any]] = None

else:
    # 如果没有pydantic，使用简单的类
    class BaseRequest:
        def __init__(self, **kwargs):
            self.request_id = kwargs.get('request_id')
            self.timestamp = kwargs.get('timestamp', datetime.now())
        
        def dict(self):
            return {
                'request_id': self.request_id,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None
            }


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_required(value: Any, field_name: str) -> None:
    """验证必填字段"""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} is required")


def validate_length(value: str, min_len: int = 0, max_len: int = 1000, field_name: str = "value") -> None:
    """验证字符串长度"""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if len(value) < min_len:
        raise ValueError(f"{field_name} must be at least {min_len} characters")
    if len(value) > max_len:
        raise ValueError(f"{field_name} must be at most {max_len} characters")


def validate_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float], field_name: str = "value") -> None:
    """验证数值范围"""
    if value < min_val:
        raise ValueError(f"{field_name} must be at least {min_val}")
    if value > max_val:
        raise ValueError(f"{field_name} must be at most {max_val}")
