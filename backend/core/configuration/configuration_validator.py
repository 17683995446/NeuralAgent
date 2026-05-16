"""Configuration validation system - Product Grade.

Standing on the shoulders of giants: using Pydantic validation.
Not reinventing the wheel: using industry-standard patterns.
Highly modular: clear separation of validation concerns.
Productized: comprehensive validation with error reporting and docs.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Callable, Optional
from enum import Enum
from functools import wraps
# Remove pydantic dependencies for compatibility
# from pydantic import field_validator, model_validator
from backend.core.infrastructure.error_handling.error_codes import ErrorCode, SystemError, ValidationError

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConfigValidationResult:
    """Result of configuration validation."""

    def __init__(self):
        self.errors: List[Tuple[ValidationLevel, str, str]] = []
        self.warnings: List[Tuple[ValidationLevel, str, str]] = []
        self.infos: List[Tuple[ValidationLevel, str, str]] = []

    def add_error(self, field: str, message: str) -> None:
        """Add an error."""
        self.errors.append((ValidationLevel.ERROR, field, message))

    def add_warning(self, field: str, message: str) -> None:
        """Add a warning."""
        self.warnings.append((ValidationLevel.WARNING, field, message))

    def add_info(self, field: str, message: str) -> None:
        """Add an info."""
        self.infos.append((ValidationLevel.INFO, field, message))

    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": [{"field": f, "message": m} for (l, f, m) in self.errors],
            "warnings": [{"field": f, "message": m} for (l, f, m) in self.warnings],
            "infos": [{"field": f, "message": m} for (l, f, m) in self.infos],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }

    def log_results(self, logger: logging.Logger) -> None:
        """Log validation results."""
        if self.errors:
            logger.error(f"Configuration validation failed with {len(self.errors)} errors:")
            for (level, field, message) in self.errors:
                logger.error(f"  [{field}] {message}")

        if self.warnings:
            logger.warning(f"Configuration has {len(self.warnings)} warnings:")
            for (level, field, message) in self.warnings:
                logger.warning(f"  [{field}] {message}")

        if self.is_valid and not self.warnings:
            logger.info("Configuration validation passed successfully")


class ConfigValidator:
    """Product-grade configuration validator."""

    def __init__(self):
        self.validators: List[Tuple[str, Callable[[str, Any], None]]] = []
        self.mandatory_fields: List[str] = []
        self.field_descriptions: Dict[str, str] = {}

    def register_validator(
        self,
        field: str,
        validator_func: Callable[[str, Any], None],
        mandatory: bool = False,
        description: str = ""
    ) -> "ConfigValidator":
        """Register a validator for a field.

        Args:
            field: Field name
            validator_func: Validation function
            mandatory: Whether field is mandatory
            description: Field description

        Returns:
            Self for chaining
        """
        self.validators.append((field, validator_func))
        if mandatory:
            self.mandatory_fields.append(field)
        if description:
            self.field_descriptions[field] = description
        return self

    def validate(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """Validate configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Validation result
        """
        result = ConfigValidationResult()

        # Check mandatory fields
        for field in self.mandatory_fields:
            if field not in config or config[field] is None or config[field] == "":
                result.add_error(field, f"Mandatory field '{field}' is missing or empty")

        # Run field validators
        for field, validator in self.validators:
            if field in config:
                try:
                    validator(field, config[field])
                except ValueError as e:
                    result.add_error(field, str(e))
                except Warning as e:
                    result.add_warning(field, str(e))

        return result

    def get_field_doc(self, field: str) -> Optional[str]:
        """Get field documentation."""
        return self.field_descriptions.get(field)


# Common validators
def validate_url(field: str, value: str) -> None:
    """Validate URL format."""
    url_pattern = r'^(https?|redis|postgresql?|sqlite)://.*$'
    if not re.match(url_pattern, value):
        raise ValueError(f"Invalid URL format for {field}: {value}")


def validate_positive_number(field: str, value: int) -> None:
    """Validate positive number."""
    if value <= 0:
        raise ValueError(f"{field} must be positive, got: {value}")


def validate_port(field: str, value: int) -> None:
    """Validate port number."""
    if value < 1 or value > 65535:
        raise ValueError(f"{field} must be between 1 and 65535, got: {value}")


def validate_enum_value(field: str, value: str, allowed_values: List[str]) -> None:
    """Validate value is in allowed list."""
    if value not in allowed_values:
        raise ValueError(
            f"{field} must be one of {allowed_values}, got: '{value}'"
        )


def validate_log_level(field: str, value: str) -> None:
    """Validate log level."""
    allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    value = value.upper()
    if value not in allowed_levels:
        raise ValueError(
            f"{field} must be one of {allowed_levels}, got: '{value}'"
        )


def validate_email(field: str, value: str) -> None:
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValueError(f"Invalid email format for {field}: {value}")


def validate_percentage(field: str, value: float) -> None:
    """Validate percentage value."""
    if value < 0 or value > 1:
        raise ValueError(f"{field} must be between 0 and 1, got: {value}")


def validate_llm_temperature(field: str, value: float) -> None:
    """Validate LLM temperature."""
    if value < 0 or value > 2:
        raise ValueError(f"{field} must be between 0 and 2, got: {value}")


# Create NeuralAgent configuration validator
def create_neuralagent_validator() -> ConfigValidator:
    """Create the NeuralAgent configuration validator."""
    validator = ConfigValidator()

    # API Settings
    validator.register_validator(
        "api_host",
        lambda f, v: None,
        mandatory=True,
        description="API server host address"
    )

    validator.register_validator(
        "api_port",
        validate_port,
        mandatory=True,
        description="API server port (1-65535)"
    )

    validator.register_validator(
        "log_level",
        validate_log_level,
        mandatory=False,
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    validator.register_validator(
        "environment",
        lambda f, v: validate_enum_value(f, v, ["development", "staging", "production"]),
        mandatory=False,
        description="Environment (development, staging, production)"
    )

    # LLM Settings
    validator.register_validator(
        "llm_provider",
        lambda f, v: validate_enum_value(f, v, ["openai", "anthropic", "ollama", "mock"]),
        mandatory=True,
        description="LLM provider (openai, anthropic, ollama, mock)"
    )

    validator.register_validator(
        "llm_model",
        lambda f, v: None if len(v) > 0 else ValueError("LLM model name cannot be empty"),
        mandatory=True,
        description="LLM model name"
    )

    validator.register_validator(
        "llm_temperature",
        validate_llm_temperature,
        mandatory=False,
        description="LLM temperature (0-2)"
    )

    validator.register_validator(
        "llm_max_tokens",
        validate_positive_number,
        mandatory=False,
        description="LLM maximum tokens"
    )

    validator.register_validator(
        "llm_timeout",
        validate_positive_number,
        mandatory=False,
        description="LLM timeout in seconds"
    )

    # Database Settings
    validator.register_validator(
        "postgres_url",
        validate_url,
        mandatory=True,
        description="PostgreSQL connection URL"
    )

    # Redis Settings
    validator.register_validator(
        "redis_url",
        validate_url,
        mandatory=True,
        description="Redis connection URL"
    )

    # Vector Store Settings
    validator.register_validator(
        "vector_store_type",
        lambda f, v: validate_enum_value(f, v, ["milvus", "chroma"]),
        mandatory=False,
        description="Vector store type (milvus, chroma)"
    )

    # Parallel Processing Settings
    validator.register_validator(
        "max_workers",
        validate_positive_number,
        mandatory=False,
        description="Maximum parallel workers"
    )

    # Cache Settings
    validator.register_validator(
        "cache_ttl_seconds",
        validate_positive_number,
        mandatory=False,
        description="Cache TTL in seconds"
    )

    # Security Settings
    validator.register_validator(
        "rate_limit_max_requests",
        validate_positive_number,
        mandatory=False,
        description="Rate limit max requests"
    )

    return validator


def validate_config_and_raise(config: Dict[str, Any]) -> None:
    """Validate configuration and raise exception if invalid.

    Args:
        config: Configuration dictionary

    Raises:
        SystemError: If configuration is invalid
    """
    validator = create_neuralagent_validator()
    result = validator.validate(config)
    result.log_results(logger)

    if not result.is_valid:
        raise SystemError(
            error_code=ErrorCode.SYSTEM_CONFIGURATION_ERROR,
            message="Invalid configuration",
            details=result.to_dict()
        )


def with_config_validation(validator: Optional[ConfigValidator] = None):
    """Decorator to validate configuration before function execution.

    Args:
        validator: Configuration validator to use

    Returns:
        Decorated function
    """
    if validator is None:
        validator = create_neuralagent_validator()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract config from kwargs or first argument
            config = kwargs.get('config')
            if config is None and len(args) > 0:
                config = args[0]

            if config:
                result = validator.validate(config if isinstance(config, dict) else config.__dict__)
                if not result.is_valid:
                    raise SystemError(
                        error_code=ErrorCode.SYSTEM_CONFIGURATION_ERROR,
                        message=f"Configuration invalid for {func.__name__}",
                        details=result.to_dict()
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator
