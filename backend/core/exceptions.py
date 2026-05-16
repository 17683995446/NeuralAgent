"""
NeuralAgent 异常处理系统 - 简化版
提供统一的异常处理和错误管理
"""

from typing import Dict, Optional, Any
from enum import Enum
from datetime import datetime


class ErrorCode(Enum):
    """错误码枚举"""
    # 通用错误 (1xxx)
    UNKNOWN = "1000"
    INVALID_INPUT = "1001"
    UNAUTHORIZED = "1002"
    FORBIDDEN = "1003"
    NOT_FOUND = "1004"
    CONFLICT = "1005"
    RATE_LIMITED = "1006"
    INTERNAL_ERROR = "1007"
    
    # 认证错误 (2xxx)
    AUTH_FAILED = "2000"
    INVALID_TOKEN = "2001"
    TOKEN_EXPIRED = "2002"
    INVALID_CREDENTIALS = "2003"
    USER_NOT_FOUND = "2004"
    USER_ALREADY_EXISTS = "2005"
    
    # API密钥错误 (3xxx)
    API_KEY_INVALID = "3000"
    API_KEY_EXPIRED = "3001"
    API_KEY_REVOKED = "3002"
    
    # 记忆系统错误 (4xxx)
    MEMORY_STORE_ERROR = "4000"
    MEMORY_RETRIEVE_ERROR = "4001"
    MEMORY_DELETE_ERROR = "4002"
    MEMORY_NOT_FOUND = "4003"
    
    # 工作流错误 (5xxx)
    WORKFLOW_EXECUTION_ERROR = "5000"
    WORKFLOW_NOT_FOUND = "5001"
    WORKFLOW_INVALID = "5002"
    WORKFLOW_TIMEOUT = "5003"
    
    # LLM错误 (6xxx)
    LLM_REQUEST_FAILED = "6000"
    LLM_TIMEOUT = "6001"
    LLM_RATE_LIMITED = "6002"
    
    # 缓存错误 (7xxx)
    CACHE_ERROR = "7000"
    CACHE_NOT_FOUND = "7001"
    
    # 配置错误 (8xxx)
    CONFIG_ERROR = "8000"
    CONFIG_INVALID = "8001"


class NeuralAgentException(Exception):
    """NeuralAgent 基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        error_data = {
            "code": self.code.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }
        if self.field:
            error_data["field"] = self.field
        if self.details:
            error_data["details"] = self.details
        
        return {
            "success": False,
            "error": error_data,
            "status_code": self.status_code
        }


# 具体异常类

class ValidationException(NeuralAgentException):
    """验证异常"""
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_INPUT,
            field=field,
            details=details,
            status_code=400
        )


class AuthenticationException(NeuralAgentException):
    """认证异常"""
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.AUTH_FAILED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
            status_code=401
        )


class AuthorizationException(NeuralAgentException):
    """授权异常"""
    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            details=details,
            status_code=403
        )


class NotFoundException(NeuralAgentException):
    """未找到异常"""
    def __init__(
        self,
        message: str = "Resource not found",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            field=field,
            details=details,
            status_code=404
        )


class RateLimitException(NeuralAgentException):
    """限流异常"""
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after_seconds: Optional[int] = 60,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMITED,
            details=details,
            status_code=429
        )
        if retry_after_seconds:
            self.details["retry_after_seconds"] = retry_after_seconds


class ConflictException(NeuralAgentException):
    """冲突异常"""
    def __init__(
        self,
        message: str = "Resource conflict",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            field=field,
            details=details,
            status_code=409
        )


class InternalException(NeuralAgentException):
    """内部错误异常"""
    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INTERNAL_ERROR,
            details=details,
            status_code=500
        )


# Helper functions

def create_validation_error(
    message: str,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ValidationException:
    """创建验证错误"""
    return ValidationException(message, field, details)


def create_auth_error(
    message: str,
    code: ErrorCode = ErrorCode.AUTH_FAILED,
    details: Optional[Dict[str, Any]] = None
) -> AuthenticationException:
    """创建认证错误"""
    return AuthenticationException(message, code, details)


def create_not_found_error(
    message: str,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> NotFoundException:
    """创建未找到错误"""
    return NotFoundException(message, field, details)


def create_rate_limit_error(
    message: str = "Rate limit exceeded",
    retry_after_seconds: Optional[int] = 60
) -> RateLimitException:
    """创建限流错误"""
    return RateLimitException(message, retry_after_seconds)


def wrap_exception(
    e: Exception,
    message: str = "An error occurred",
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
) -> NeuralAgentException:
    """包装其他异常为NeuralAgent异常"""
    if isinstance(e, NeuralAgentException):
        return e
    return InternalException(
        message=f"{message}: {str(e)}",
        details={"original_exception": str(e), "type": type(e).__name__}
    )
