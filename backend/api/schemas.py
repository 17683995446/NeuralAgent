"""Pydantic schemas for API request/response validation."""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator
from uuid import UUID


class LoginRequest(BaseModel):
    """用户登录请求schema."""
    
    username: str = Field(..., description="用户名或邮箱", min_length=3, max_length=100)
    password: str = Field(..., description="密码", min_length=6)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "demo_user",
                "password": "demo_password"
            }
        }
    }


class LoginResponse(BaseModel):
    """登录响应schema."""
    
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(default=3600, description="过期时间（秒）")
    user_info: Dict[str, Any] = Field(..., description="用户信息")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user_info": {
                    "user_id": "demo_user",
                    "username": "demo_user",
                    "role": "user",
                    "email": "demo_user@example.com"
                }
            }
        }
    }


class UserInfo(BaseModel):
    """用户信息schema."""
    
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="用户角色")
    email: Optional[str] = Field(default=None, description="用户邮箱")


class TokenRefreshRequest(BaseModel):
    """令牌刷新请求schema."""
    
    refresh_token: str = Field(..., description="刷新令牌")


class TaskInput(BaseModel):
    """Task input schema for creating new tasks."""

    task_id: str = Field(
        description="Global unique task ID, UUID format",
        min_length=1,
        max_length=36
    )
    user_requirement: str = Field(
        description="User's overall requirement description",
        min_length=1
    )
    code_repo_url: Optional[str] = Field(
        default=None,
        description="Target code repository Git URL"
    )
    local_code_path: Optional[str] = Field(
        default=None,
        description="Local code project path"
    )
    target_branch: str = Field(
        default="main",
        description="Target branch name"
    )
    max_iteration: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum feedback iterations"
    )
    learning_rate: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="Learning rate for trust updates"
    )
    llm_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="LLM cloud API configuration"
    )

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task_id format."""
        try:
            UUID(v)
        except ValueError:
            if len(v) < 10:
                raise ValueError("task_id must be a valid UUID or at least 10 characters")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_requirement": "重构用户认证模块，添加JWT支持",
                "code_repo_url": "https://github.com/example/project.git",
                "target_branch": "main",
                "max_iteration": 5,
                "learning_rate": 0.1,
                "llm_config": {"model": "openai/gpt-4o", "temperature": 0.7}
            }
        }
    }


class LLMConfig(BaseModel):
    """LLM configuration schema."""

    model: str = Field(
        default="openai/gpt-4o",
        description="LLM model identifier"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0
    )
    max_tokens: int = Field(
        default=4096,
        ge=100,
        le=32000
    )
    timeout: int = Field(
        default=60,
        ge=10,
        le=300
    )


class TaskContext(BaseModel):
    """Task context schema returned after task creation."""

    task_id: str
    status: str
    user_requirement: str
    code_repo_path: Optional[str] = None
    max_iteration: int
    learning_rate: float
    created_at: str
    message: str


class TaskStatus(BaseModel):
    """Task status schema for status queries."""

    task_id: str
    status: str
    current_layer: str
    current_iteration: int
    max_iteration: int
    progress_percentage: float
    created_at: str
    updated_at: Optional[str] = None


class LayerStatus(BaseModel):
    """Layer execution status schema."""

    layer_name: str
    status: str
    agent_count: int
    completed_agents: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class FeedbackItem(BaseModel):
    """Individual feedback item schema."""

    type: Literal["positive", "negative"] = Field(
        description="Feedback type"
    )
    description: str = Field(
        description="Detailed feedback description",
        min_length=1
    )
    suggestion: Optional[str] = Field(
        default=None,
        description="Suggested improvement"
    )
    affected_agent: Optional[str] = Field(
        default=None,
        description="Affected agent ID if applicable"
    )


class FeedbackInput(BaseModel):
    """User feedback input schema."""

    satisfaction_score: int = Field(
        description="Overall satisfaction score (0-5)",
        ge=0,
        le=5
    )
    feedback_items: List[FeedbackItem] = Field(
        description="Detailed feedback items",
        min_length=1
    )
    additional_comments: Optional[str] = Field(
        default=None,
        description="Additional comments from user"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "satisfaction_score": 3,
                "feedback_items": [
                    {
                        "type": "negative",
                        "description": "测试用例未覆盖JWT刷新场景",
                        "suggestion": "添加token刷新接口的测试",
                        "affected_agent": "agent_fc3_001"
                    }
                ],
                "additional_comments": "整体代码质量不错，但测试覆盖需要加强"
            }
        }
    }


class FeedbackResult(BaseModel):
    """Feedback processing result schema."""

    task_id: str
    iteration: int
    reward: float
    trust_updates: Dict[str, Dict[str, float]]
    message: str
    next_action: str


class AgentOutput(BaseModel):
    """Agent output schema."""

    agent_id: str
    layer_name: str
    output_type: str
    content: Dict[str, Any]
    confidence: float
    processing_time_ms: Optional[int] = None


class TaskResult(BaseModel):
    """Task execution result schema."""

    task_id: str
    status: str
    output_path: str
    layers_completed: List[str]
    total_iterations: int
    final_satisfaction_score: Optional[int] = None
    execution_time_seconds: float
    created_at: str
    completed_at: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: str
    task_id: Optional[str] = None
    timestamp: str


class HealthCheck(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    components: Dict[str, str]


# ==================== 大规模代码处理相关Schemas ====================

class CodeProcessingRequest(BaseModel):
    """大规模代码处理请求schema."""

    repo_url: Optional[str] = Field(
        default=None,
        description="Git仓库URL"
    )
    local_path: Optional[str] = Field(
        default=None,
        description="本地代码路径"
    )
    branch: str = Field(
        default="main",
        description="分支名称"
    )
    languages: List[str] = Field(
        default_factory=lambda: ["python", "javascript", "typescript", "java"],
        description="需要分析的编程语言"
    )
    enable_parallel: bool = Field(
        default=True,
        description="是否启用并行处理"
    )
    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="最大并行工作线程数"
    )
    chunk_size: int = Field(
        default=2000,
        ge=500,
        le=10000,
        description="代码分片大小（token数）"
    )
    enable_incremental: bool = Field(
        default=False,
        description="是否启用增量处理"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_url": "https://github.com/example/project.git",
                "branch": "main",
                "languages": ["python", "javascript"],
                "enable_parallel": True,
                "max_workers": 8,
                "chunk_size": 2000,
                "enable_incremental": False
            }
        }
    }


class CodeProcessingStatus(BaseModel):
    """代码处理状态schema."""

    job_id: str
    status: str
    total_files: int
    processed_files: int
    total_chunks: int
    processed_chunks: int
    progress_percentage: float
    start_time: Optional[str] = None
    estimated_remaining_time: Optional[float] = None
    error_message: Optional[str] = None


class CodeChunkInfo(BaseModel):
    """代码分片信息schema."""

    chunk_id: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    size_bytes: int
    content_hash: str
    embedding_status: str


class CodeSearchRequest(BaseModel):
    """代码搜索请求schema."""

    query: str = Field(
        ...,
        description="搜索查询",
        min_length=1
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="返回结果数量"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="过滤条件"
    )


class CodeSearchResult(BaseModel):
    """代码搜索结果schema."""

    chunk_id: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    similarity_score: float
    snippet: str


class CodeProcessingResult(BaseModel):
    """代码处理完成结果schema."""

    job_id: str
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    total_chunks: int
    vector_store_size: int
    processing_time_seconds: float
    file_stats: Dict[str, int]
    chunk_stats: Dict[str, int]
    warnings: List[str]


class VectorStoreStats(BaseModel):
    """向量存储统计schema."""

    total_chunks: int
    total_vectors: int
    storage_size_bytes: int
    language_distribution: Dict[str, int]
    last_updated: Optional[str] = None
