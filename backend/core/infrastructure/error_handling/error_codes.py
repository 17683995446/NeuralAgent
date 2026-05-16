"""Error Code System - Product Grade.

Standing on the shoulders of giants: using standard HTTP status codes.
Not reinventing the wheel: using industry-standard error handling patterns.
Highly modular: clear separation of error categories.
Productized: comprehensive error codes with documentation and translations.
"""

from enum import Enum
from typing import Optional, Dict, Any

# Try to import FastAPI, fall back to dummy if not available
try:
    from fastapi import HTTPException, status
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    
    # Create dummy status codes for backward compatibility
    class DummyStatus:
        HTTP_400_BAD_REQUEST = 400
        HTTP_401_UNAUTHORIZED = 401
        HTTP_403_FORBIDDEN = 403
        HTTP_404_NOT_FOUND = 404
        HTTP_409_CONFLICT = 409
        HTTP_410_GONE = 410
        HTTP_413_REQUEST_ENTITY_TOO_LARGE = 413
        HTTP_422_UNPROCESSABLE_ENTITY = 422
        HTTP_429_TOO_MANY_REQUESTS = 429
        HTTP_500_INTERNAL_SERVER_ERROR = 500
        HTTP_502_BAD_GATEWAY = 502
        HTTP_503_SERVICE_UNAVAILABLE = 503
        HTTP_504_GATEWAY_TIMEOUT = 504
    
    status = DummyStatus()
    
    # Create dummy HTTPException
    class DummyHTTPException(Exception):
        def __init__(self, status_code: int, detail: Any = None):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"HTTP {status_code}: {detail}")
    
    HTTPException = DummyHTTPException


class ErrorCode(Enum):
    """Comprehensive error codes for the NeuralAgent system."""
    
    # Authentication & Authorization (1000-1099)
    AUTH_INVALID_CREDENTIALS = (1000, "Invalid username or password", status.HTTP_401_UNAUTHORIZED)
    AUTH_TOKEN_EXPIRED = (1001, "Access token has expired", status.HTTP_401_UNAUTHORIZED)
    AUTH_TOKEN_INVALID = (1002, "Access token is invalid", status.HTTP_401_UNAUTHORIZED)
    AUTH_TOKEN_MISSING = (1003, "Access token is missing", status.HTTP_401_UNAUTHORIZED)
    AUTH_PERMISSION_DENIED = (1004, "Permission denied for this operation", status.HTTP_403_FORBIDDEN)
    AUTH_INSUFFICIENT_PRIVILEGES = (1005, "Insufficient privileges to perform this action", status.HTTP_403_FORBIDDEN)
    AUTH_USER_DISABLED = (1006, "User account has been disabled", status.HTTP_403_FORBIDDEN)
    AUTH_USER_NOT_FOUND = (1007, "User not found", status.HTTP_404_NOT_FOUND)
    
    # Task Management (2000-2099)
    TASK_NOT_FOUND = (2000, "Task not found", status.HTTP_404_NOT_FOUND)
    TASK_ALREADY_EXISTS = (2001, "Task with this ID already exists", status.HTTP_409_CONFLICT)
    TASK_INVALID_INPUT = (2002, "Invalid task input parameters", status.HTTP_400_BAD_REQUEST)
    TASK_IN_PROGRESS = (2003, "Task is already in progress", status.HTTP_409_CONFLICT)
    TASK_CANCELLED = (2004, "Task has been cancelled", status.HTTP_410_GONE)
    TASK_TIMEOUT = (2005, "Task execution timeout", status.HTTP_504_GATEWAY_TIMEOUT)
    TASK_MAX_ITERATIONS = (2006, "Maximum iterations reached", status.HTTP_500_INTERNAL_SERVER_ERROR)
    TASK_LAYER_FAILED = (2007, "Layer execution failed", status.HTTP_500_INTERNAL_SERVER_ERROR)
    TASK_OUTPUT_NOT_FOUND = (2008, "Task output not found", status.HTTP_404_NOT_FOUND)
    
    # LLM & AI (3000-3099)
    LLM_PROVIDER_ERROR = (3000, "LLM provider returned an error", status.HTTP_502_BAD_GATEWAY)
    LLM_TIMEOUT = (3001, "LLM request timed out", status.HTTP_504_GATEWAY_TIMEOUT)
    LLM_INVALID_MODEL = (3002, "Invalid LLM model specified", status.HTTP_400_BAD_REQUEST)
    LLM_QUOTA_EXCEEDED = (3003, "LLM API quota exceeded", status.HTTP_429_TOO_MANY_REQUESTS)
    LLM_RATE_LIMIT = (3004, "LLM rate limit exceeded", status.HTTP_429_TOO_MANY_REQUESTS)
    LLM_CONTENT_FILTERED = (3005, "Content was filtered by LLM safety system", status.HTTP_400_BAD_REQUEST)
    LLM_INVALID_RESPONSE = (3006, "LLM returned an invalid response", status.HTTP_502_BAD_GATEWAY)
    LLM_CONFIGURATION_ERROR = (3007, "LLM configuration error", status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Code Processing (4000-4099)
    CODE_REPO_NOT_FOUND = (4000, "Code repository not found", status.HTTP_404_NOT_FOUND)
    CODE_REPO_ACCESS_DENIED = (4001, "Access to code repository denied", status.HTTP_403_FORBIDDEN)
    CODE_INVALID_BRANCH = (4002, "Invalid branch name", status.HTTP_400_BAD_REQUEST)
    CODE_CLONE_FAILED = (4003, "Failed to clone repository", status.HTTP_500_INTERNAL_SERVER_ERROR)
    CODE_PULL_FAILED = (4004, "Failed to pull latest changes", status.HTTP_500_INTERNAL_SERVER_ERROR)
    CODE_FILE_NOT_FOUND = (4005, "Code file not found", status.HTTP_404_NOT_FOUND)
    CODE_PARSE_ERROR = (4006, "Failed to parse code file", status.HTTP_422_UNPROCESSABLE_ENTITY)
    CODE_LANGUAGE_UNSUPPORTED = (4007, "Programming language not supported", status.HTTP_400_BAD_REQUEST)
    CODE_TOO_LARGE = (4008, "Code file exceeds maximum size", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    
    # Vector Store & Search (5000-5099)
    VECTOR_STORE_NOT_INITIALIZED = (5000, "Vector store is not initialized", status.HTTP_503_SERVICE_UNAVAILABLE)
    VECTOR_STORE_CONNECTION_ERROR = (5001, "Failed to connect to vector store", status.HTTP_503_SERVICE_UNAVAILABLE)
    VECTOR_EMBEDDING_FAILED = (5002, "Failed to generate embeddings", status.HTTP_500_INTERNAL_SERVER_ERROR)
    VECTOR_SEARCH_FAILED = (5003, "Vector search operation failed", status.HTTP_500_INTERNAL_SERVER_ERROR)
    VECTOR_COLLECTION_NOT_FOUND = (5004, "Vector collection not found", status.HTTP_404_NOT_FOUND)
    VECTOR_DEDUP_FAILED = (5005, "Vector deduplication failed", status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Memory & Storage (6000-6099)
    MEMORY_NOT_FOUND = (6000, "Memory entry not found", status.HTTP_404_NOT_FOUND)
    MEMORY_STORAGE_ERROR = (6001, "Failed to store in memory", status.HTTP_500_INTERNAL_SERVER_ERROR)
    MEMORY_RETRIEVAL_ERROR = (6002, "Failed to retrieve from memory", status.HTTP_500_INTERNAL_SERVER_ERROR)
    MEMORY_EXPIRED = (6003, "Memory entry has expired", status.HTTP_410_GONE)
    CACHE_CONNECTION_ERROR = (6004, "Failed to connect to cache", status.HTTP_503_SERVICE_UNAVAILABLE)
    CACHE_KEY_NOT_FOUND = (6005, "Cache key not found", status.HTTP_404_NOT_FOUND)
    
    # System & Infrastructure (7000-7099)
    SYSTEM_OVERLOADED = (7000, "System is overloaded, try again later", status.HTTP_503_SERVICE_UNAVAILABLE)
    SYSTEM_MAINTENANCE = (7001, "System is under maintenance", status.HTTP_503_SERVICE_UNAVAILABLE)
    SYSTEM_CONFIGURATION_ERROR = (7002, "System configuration error", status.HTTP_500_INTERNAL_SERVER_ERROR)
    SYSTEM_INTERNAL_ERROR = (7003, "Internal system error", status.HTTP_500_INTERNAL_SERVER_ERROR)
    DATABASE_CONNECTION_ERROR = (7004, "Failed to connect to database", status.HTTP_503_SERVICE_UNAVAILABLE)
    DATABASE_QUERY_ERROR = (7005, "Database query failed", status.HTTP_500_INTERNAL_SERVER_ERROR)
    REDIS_CONNECTION_ERROR = (7006, "Failed to connect to Redis", status.HTTP_503_SERVICE_UNAVAILABLE)
    EXTERNAL_SERVICE_ERROR = (7007, "External service error", status.HTTP_502_BAD_GATEWAY)
    
    # Validation & Input (8000-8099)
    VALIDATION_ERROR = (8000, "Input validation failed", status.HTTP_422_UNPROCESSABLE_ENTITY)
    INVALID_PARAMETER = (8001, "Invalid parameter provided", status.HTTP_400_BAD_REQUEST)
    MISSING_PARAMETER = (8002, "Required parameter is missing", status.HTTP_400_BAD_REQUEST)
    PARAMETER_OUT_OF_RANGE = (8003, "Parameter value is out of range", status.HTTP_400_BAD_REQUEST)
    INVALID_FORMAT = (8004, "Input format is invalid", status.HTTP_400_BAD_REQUEST)
    SCHEMA_VALIDATION_ERROR = (8005, "JSON schema validation failed", status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    # Rate Limiting (9000-9099)
    RATE_LIMIT_EXCEEDED = (9000, "Rate limit exceeded", status.HTTP_429_TOO_MANY_REQUESTS)
    QUOTA_EXCEEDED = (9001, "API quota exceeded", status.HTTP_429_TOO_MANY_REQUESTS)
    CONCURRENT_LIMIT_EXCEEDED = (9002, "Concurrent request limit exceeded", status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Agent & Orchestration (10000-10099)
    AGENT_NOT_FOUND = (10000, "Agent not found", status.HTTP_404_NOT_FOUND)
    AGENT_INITIALIZATION_ERROR = (10001, "Failed to initialize agent", status.HTTP_500_INTERNAL_SERVER_ERROR)
    AGENT_COMMUNICATION_ERROR = (10002, "Agent communication failed", status.HTTP_500_INTERNAL_SERVER_ERROR)
    ORCHESTRATION_FAILED = (10003, "Task orchestration failed", status.HTTP_500_INTERNAL_SERVER_ERROR)
    TRUST_MATRIX_ERROR = (10004, "Trust matrix computation error", status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @property
    def code(self) -> int:
        """Get the error code number."""
        return self.value[0]
    
    @property
    def message(self) -> str:
        """Get the error message."""
        return self.value[1]
    
    @property
    def http_status(self) -> int:
        """Get the HTTP status code."""
        return self.value[2]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "code": self.code,
            "message": self.message,
            "http_status": self.http_status
        }


class NeuralAgentException(Exception):
    """Base exception for NeuralAgent system."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.error_code = error_code
        self.message = message or error_code.message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "error": {
                "code": self.error_code.code,
                "message": self.message,
                "http_status": self.error_code.http_status
            }
        }
        if self.details:
            result["error"]["details"] = self.details
        if self.cause:
            result["error"]["cause"] = str(self.cause)
        return result
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.error_code.http_status,
            detail=self.to_dict()
        )


class AuthenticationError(NeuralAgentException):
    """Authentication related errors."""
    pass


class AuthorizationError(NeuralAgentException):
    """Authorization related errors."""
    pass


class TaskError(NeuralAgentException):
    """Task related errors."""
    pass


class LLMError(NeuralAgentException):
    """LLM related errors."""
    pass


class CodeProcessingError(NeuralAgentException):
    """Code processing related errors."""
    pass


class VectorStoreError(NeuralAgentException):
    """Vector store related errors."""
    pass


class ValidationError(NeuralAgentException):
    """Validation related errors."""
    pass


class RateLimitError(NeuralAgentException):
    """Rate limiting related errors."""
    pass


class SystemError(NeuralAgentException):
    """System related errors."""
    pass


def get_error_message(error_code: ErrorCode, locale: str = "en") -> str:
    """Get localized error message.
    
    Args:
        error_code: The error code
        locale: Language code (en, zh, etc.)
        
    Returns:
        Localized error message
    """
    translations = {
        "en": {},
        "zh": {
            ErrorCode.AUTH_INVALID_CREDENTIALS: "用户名或密码无效",
            ErrorCode.AUTH_TOKEN_EXPIRED: "访问令牌已过期",
            ErrorCode.AUTH_PERMISSION_DENIED: "此操作权限不足",
            ErrorCode.TASK_NOT_FOUND: "任务未找到",
            ErrorCode.LLM_PROVIDER_ERROR: "LLM服务提供商错误",
            ErrorCode.VALIDATION_ERROR: "输入验证失败",
            ErrorCode.RATE_LIMIT_EXCEEDED: "请求频率超限",
        }
    }
    
    return translations.get(locale, {}).get(error_code, error_code.message)


def is_retryable_error(error_code: ErrorCode) -> bool:
    """Check if an error is retryable.
    
    Args:
        error_code: The error code to check
        
    Returns:
        True if the error is temporary and retry might succeed
    """
    retryable_codes = {
        ErrorCode.LLM_TIMEOUT,
        ErrorCode.LLM_PROVIDER_ERROR,
        ErrorCode.VECTOR_STORE_CONNECTION_ERROR,
        ErrorCode.MEMORY_STORAGE_ERROR,
        ErrorCode.MEMORY_RETRIEVAL_ERROR,
        ErrorCode.DATABASE_CONNECTION_ERROR,
        ErrorCode.DATABASE_QUERY_ERROR,
        ErrorCode.REDIS_CONNECTION_ERROR,
        ErrorCode.EXTERNAL_SERVICE_ERROR,
        ErrorCode.SYSTEM_OVERLOADED,
        ErrorCode.RATE_LIMIT_EXCEEDED,
        ErrorCode.LLM_RATE_LIMIT,
    }
    
    return error_code in retryable_codes


def get_retry_after(error_code: ErrorCode) -> Optional[int]:
    """Get recommended retry delay in seconds.
    
    Args:
        error_code: The error code
        
    Returns:
        Retry delay in seconds or None
    """
    retry_delays = {
        ErrorCode.LLM_TIMEOUT: 5,
        ErrorCode.LLM_RATE_LIMIT: 60,
        ErrorCode.RATE_LIMIT_EXCEEDED: 60,
        ErrorCode.QUOTA_EXCEEDED: 300,
        ErrorCode.SYSTEM_OVERLOADED: 30,
        ErrorCode.EXTERNAL_SERVICE_ERROR: 10,
    }
    
    return retry_delays.get(error_code)
