"""Tests for Config Validator - Product Grade."""

import pytest
from backend.core.configuration.configuration_validator import (
    ConfigValidator,
    ConfigValidationResult,
    ValidationLevel,
    create_neuralagent_validator,
    validate_config_and_raise,
    validate_url,
    validate_port,
    validate_positive_number,
    validate_log_level,
    validate_llm_temperature,
    validate_enum_value
)
from backend.core.infrastructure.error_handling.error_codes import SystemError


class TestValidationHelpers:
    """Tests for validation helper functions."""

    def test_validate_url_valid(self):
        """Test valid URL validation."""
        validate_url("test", "http://example.com")
        validate_url("test", "https://example.com")
        validate_url("test", "redis://localhost:6379/0")
        validate_url("test", "postgresql://localhost:5432/db")

    def test_validate_url_invalid(self):
        """Test invalid URL validation."""
        with pytest.raises(ValueError):
            validate_url("test", "not-a-url")

    def test_validate_port_valid(self):
        """Test valid port validation."""
        validate_port("test", 80)
        validate_port("test", 8080)
        validate_port("test", 65535)

    def test_validate_port_invalid(self):
        """Test invalid port validation."""
        with pytest.raises(ValueError):
            validate_port("test", 0)
        with pytest.raises(ValueError):
            validate_port("test", 65536)

    def test_validate_positive_number(self):
        """Test positive number validation."""
        validate_positive_number("test", 1)
        validate_positive_number("test", 100)

        with pytest.raises(ValueError):
            validate_positive_number("test", 0)
        with pytest.raises(ValueError):
            validate_positive_number("test", -1)

    def test_validate_log_level_valid(self):
        """Test valid log level validation."""
        validate_log_level("test", "DEBUG")
        validate_log_level("test", "INFO")
        validate_log_level("test", "WARNING")
        validate_log_level("test", "ERROR")
        validate_log_level("test", "CRITICAL")

    def test_validate_log_level_invalid(self):
        """Test invalid log level validation."""
        with pytest.raises(ValueError):
            validate_log_level("test", "NOT_A_LEVEL")

    def test_validate_llm_temperature_valid(self):
        """Test valid LLM temperature validation."""
        validate_llm_temperature("test", 0)
        validate_llm_temperature("test", 1)
        validate_llm_temperature("test", 2)
        validate_llm_temperature("test", 0.7)

    def test_validate_llm_temperature_invalid(self):
        """Test invalid LLM temperature validation."""
        with pytest.raises(ValueError):
            validate_llm_temperature("test", -1)
        with pytest.raises(ValueError):
            validate_llm_temperature("test", 2.1)

    def test_validate_enum_value(self):
        """Test enum value validation."""
        validate_enum_value("test", "a", ["a", "b", "c"])
        validate_enum_value("test", "b", ["a", "b", "c"])

        with pytest.raises(ValueError):
            validate_enum_value("test", "d", ["a", "b", "c"])


class TestValidationResult:
    """Tests for ConfigValidationResult."""

    def test_result_initialization(self):
        """Test result initialization."""
        result = ConfigValidationResult()
        assert result.is_valid is True
        assert result.has_warnings is False
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.infos) == 0

    def test_add_error(self):
        """Test adding errors."""
        result = ConfigValidationResult()
        result.add_error("field1", "test error")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0][0] == ValidationLevel.ERROR
        assert result.errors[0][1] == "field1"
        assert result.errors[0][2] == "test error"

    def test_add_warning(self):
        """Test adding warnings."""
        result = ConfigValidationResult()
        result.add_warning("field1", "test warning")

        assert result.is_valid is True
        assert result.has_warnings is True
        assert len(result.warnings) == 1

    def test_add_info(self):
        """Test adding info."""
        result = ConfigValidationResult()
        result.add_info("field1", "test info")

        assert result.is_valid is True
        assert len(result.infos) == 1

    def test_to_dict(self):
        """Test converting result to dict."""
        result = ConfigValidationResult()
        result.add_error("field1", "error1")
        result.add_warning("field2", "warning1")
        result.add_info("field3", "info1")

        result_dict = result.to_dict()

        assert result_dict["is_valid"] is False
        assert result_dict["error_count"] == 1
        assert result_dict["warning_count"] == 1
        assert len(result_dict["errors"]) == 1
        assert len(result_dict["warnings"]) == 1
        assert len(result_dict["infos"]) == 1


class TestConfigValidator:
    """Tests for ConfigValidator."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = ConfigValidator()
        assert len(validator.validators) == 0
        assert len(validator.mandatory_fields) == 0

    def test_register_validator(self):
        """Test registering validator."""
        validator = ConfigValidator()
        validator.register_validator(
            "test_field",
            lambda f, v: None,
            mandatory=True,
            description="Test field"
        )

        assert len(validator.validators) == 1
        assert "test_field" in validator.mandatory_fields
        assert validator.get_field_doc("test_field") == "Test field"

    def test_validate_mandatory_field_missing(self):
        """Test validation with missing mandatory field."""
        validator = ConfigValidator()
        validator.register_validator(
            "required",
            lambda f, v: None,
            mandatory=True
        )

        result = validator.validate({})
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_validate_mandatory_field_present(self):
        """Test validation with present mandatory field."""
        validator = ConfigValidator()
        validator.register_validator(
            "required",
            lambda f, v: None,
            mandatory=True
        )

        result = validator.validate({"required": "value"})
        assert result.is_valid is True

    def test_validate_field_validator_error(self):
        """Test validation with field validator error."""
        validator = ConfigValidator()
        validator.register_validator(
            "test",
            lambda f, v: raise_value_error("test error")
        )

        result = validator.validate({"test": "value"})
        assert result.is_valid is False


def raise_value_error(msg: str) -> None:
    """Helper function to raise ValueError."""
    raise ValueError(msg)


class TestNeuralAgentValidator:
    """Tests for NeuralAgent specific validator."""

    def test_create_neuralagent_validator(self):
        """Test creating the default validator."""
        validator = create_neuralagent_validator()
        assert validator is not None
        assert len(validator.validators) > 0

    def test_validate_valid_config(self):
        """Test validating valid configuration."""
        validator = create_neuralagent_validator()
        config = {
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "llm_provider": "mock",
            "llm_model": "gpt-4",
            "postgres_url": "sqlite:///./test.db",
            "redis_url": "redis://localhost:6379/0"
        }

        result = validator.validate(config)
        # Should be valid - no errors for these fields
        assert result.is_valid is True or len(result.errors) == 0

    def test_validate_config_and_raise_valid(self):
        """Test validate_config_and_raise with valid config."""
        config = {
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "llm_provider": "mock",
            "llm_model": "gpt-4",
            "postgres_url": "sqlite:///./test.db",
            "redis_url": "redis://localhost:6379/0"
        }

        try:
            validate_config_and_raise(config)
        except SystemError:
            pytest.fail("Should not have raised an exception")


class TestSettingsValidation:
    """Tests for Settings validation integration."""

    def test_load_settings(self):
        """Test loading settings from defaults."""
        from backend.config import settings

        assert settings is not None
        assert settings.api_port == 8000
        assert settings.llm_provider == "mock"
        assert settings.vector_store_type in ["milvus", "chroma"]

    def test_get_safe_config(self):
        """Test getting safe config without sensitive info."""
        from backend.config import settings

        safe_config = settings.get_safe_config()
        assert "jwt_secret_key" in safe_config
        assert safe_config["jwt_secret_key"] == "***"
        assert "llm_api_key" in safe_config
        assert safe_config["llm_api_key"] == "***"
