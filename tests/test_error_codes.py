"""Tests for Error Codes Module."""

import pytest
from backend.core.infrastructure.error_handling.error_codes import (
    ErrorCode,
    NeuralAgentException,
    AuthenticationError,
    TaskError,
    LLMError,
    ValidationError,
    SystemError,
    get_error_message,
    is_retryable_error,
    get_retry_after
)


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_error_code_properties(self):
        """Test error code properties."""
        error = ErrorCode.AUTH_INVALID_CREDENTIALS
        assert error.code == 1000
        assert error.message == "Invalid username or password"
        assert error.http_status == 401

    def test_error_code_to_dict(self):
        """Test converting error code to dictionary."""
        error = ErrorCode.TASK_NOT_FOUND
        result = error.to_dict()
        assert result["code"] == 2000
        assert result["message"] == "Task not found"
        assert result["http_status"] == 404

    def test_all_error_codes_have_unique_codes(self):
        """Test that all error codes are unique."""
        codes = [e.code for e in ErrorCode]
        assert len(codes) == len(set(codes))

    def test_authentication_errors(self):
        """Test authentication error codes."""
        assert ErrorCode.AUTH_INVALID_CREDENTIALS.http_status == 401
        assert ErrorCode.AUTH_TOKEN_EXPIRED.http_status == 401
        assert ErrorCode.AUTH_PERMISSION_DENIED.http_status == 403

    def test_task_errors(self):
        """Test task error codes."""
        assert ErrorCode.TASK_NOT_FOUND.http_status == 404
        assert ErrorCode.TASK_ALREADY_EXISTS.http_status == 409
        assert ErrorCode.TASK_INVALID_INPUT.http_status == 400

    def test_llm_errors(self):
        """Test LLM error codes."""
        assert ErrorCode.LLM_PROVIDER_ERROR.http_status == 502
        assert ErrorCode.LLM_TIMEOUT.http_status == 504
        assert ErrorCode.LLM_QUOTA_EXCEEDED.http_status == 429

    def test_validation_errors(self):
        """Test validation error codes."""
        assert ErrorCode.VALIDATION_ERROR.http_status == 422
        assert ErrorCode.INVALID_PARAMETER.http_status == 400
        assert ErrorCode.MISSING_PARAMETER.http_status == 400


class TestNeuralAgentException:
    """Tests for NeuralAgentException class."""

    def test_exception_creation(self):
        """Test creating a NeuralAgentException."""
        error = NeuralAgentException(
            error_code=ErrorCode.TASK_NOT_FOUND,
            message="Custom message",
            details={"task_id": "123"}
        )
        assert error.error_code == ErrorCode.TASK_NOT_FOUND
        assert error.message == "Custom message"
        assert error.details == {"task_id": "123"}

    def test_exception_to_dict(self):
        """Test converting exception to dictionary."""
        error = NeuralAgentException(
            error_code=ErrorCode.AUTH_INVALID_CREDENTIALS
        )
        result = error.to_dict()
        assert "error" in result
        assert result["error"]["code"] == 1000
        assert result["error"]["http_status"] == 401

    def test_exception_to_http_exception(self):
        """Test converting to FastAPI HTTPException."""
        error = NeuralAgentException(
            error_code=ErrorCode.TASK_NOT_FOUND
        )
        http_exc = error.to_http_exception()
        assert http_exc.status_code == 404

    def test_exception_with_cause(self):
        """Test exception with cause."""
        cause = ValueError("Original error")
        error = NeuralAgentException(
            error_code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            cause=cause
        )
        result = error.to_dict()
        assert result["error"]["cause"] == "Original error"


class TestSpecificExceptions:
    """Tests for specific exception types."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError(ErrorCode.AUTH_TOKEN_EXPIRED)
        assert error.error_code == ErrorCode.AUTH_TOKEN_EXPIRED

    def test_task_error(self):
        """Test TaskError."""
        error = TaskError(ErrorCode.TASK_NOT_FOUND)
        assert error.error_code == ErrorCode.TASK_NOT_FOUND

    def test_llm_error(self):
        """Test LLMError."""
        error = LLMError(ErrorCode.LLM_PROVIDER_ERROR)
        assert error.error_code == ErrorCode.LLM_PROVIDER_ERROR

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError(ErrorCode.VALIDATION_ERROR)
        assert error.error_code == ErrorCode.VALIDATION_ERROR

    def test_system_error(self):
        """Test SystemError."""
        error = SystemError(ErrorCode.SYSTEM_OVERLOADED)
        assert error.error_code == ErrorCode.SYSTEM_OVERLOADED


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_error_message_default(self):
        """Test getting default error message."""
        msg = get_error_message(ErrorCode.AUTH_INVALID_CREDENTIALS)
        assert msg == "Invalid username or password"

    def test_get_error_message_localized(self):
        """Test getting localized error message."""
        msg = get_error_message(ErrorCode.AUTH_INVALID_CREDENTIALS, locale="zh")
        assert msg == "用户名或密码无效"

    def test_is_retryable_error_retryable(self):
        """Test identifying retryable errors."""
        assert is_retryable_error(ErrorCode.LLM_TIMEOUT) is True
        assert is_retryable_error(ErrorCode.LLM_PROVIDER_ERROR) is True
        assert is_retryable_error(ErrorCode.RATE_LIMIT_EXCEEDED) is True

    def test_is_retryable_error_not_retryable(self):
        """Test identifying non-retryable errors."""
        assert is_retryable_error(ErrorCode.AUTH_INVALID_CREDENTIALS) is False
        assert is_retryable_error(ErrorCode.TASK_NOT_FOUND) is False
        assert is_retryable_error(ErrorCode.INVALID_PARAMETER) is False

    def test_get_retry_after(self):
        """Test getting retry delay."""
        delay = get_retry_after(ErrorCode.LLM_TIMEOUT)
        assert delay == 5

        delay = get_retry_after(ErrorCode.RATE_LIMIT_EXCEEDED)
        assert delay == 60

        delay = get_retry_after(ErrorCode.AUTH_INVALID_CREDENTIALS)
        assert delay is None
