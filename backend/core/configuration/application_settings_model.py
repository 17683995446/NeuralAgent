"""Configuration management for NeuralAgent System - Product Grade.

Standing on the shoulders of giants: using pydantic-settings.
Not reinventing the wheel: using industry-standard config patterns.
Highly modular: clear separation of concerns.
Productized: comprehensive validation and documentation.
"""

import os
from typing import Optional, Callable, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    log_level: str = Field(default="INFO", description="Log level")
    environment: str = Field(default="development", description="Environment")
    
    # JWT Authentication Settings
    jwt_secret_key: Optional[str] = Field(default=None, description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=60, description="JWT token expiration in minutes")
    
    # LLM Settings
    llm_provider: str = Field(default="mock", description="LLM provider (openai, anthropic, ollama, mock)")
    llm_model: str = Field(default="gpt-4", description="LLM model name")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API key")
    llm_base_url: Optional[str] = Field(default=None, description="LLM base URL (for proxies)")
    llm_temperature: float = Field(default=0.7, description="LLM temperature")
    llm_max_tokens: int = Field(default=2048, description="LLM max tokens")
    llm_embedding_model: str = Field(default="text-embedding-ada-002", description="Embedding model")
    llm_timeout: float = Field(default=30.0, description="LLM timeout in seconds")
    
    # Database Settings
    postgres_url: str = Field(
        default="sqlite:///./neural_agent.db",
        description="PostgreSQL connection URL"
    )
    
    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Milvus Settings
    milvus_host: str = Field(default="localhost", description="Milvus host")
    milvus_port: int = Field(default=19530, description="Milvus port")
    
    # Vector Store Settings
    vector_store_type: str = Field(default="chroma", description="Vector store type (milvus, chroma)")
    chroma_persist_dir: str = Field(default="./chroma_db", description="Chroma persist directory")
    
    # Code Repository Settings
    code_repos_dir: str = Field(default="./code_repos", description="Code repositories directory")
    task_output_dir: str = Field(default="./task_outputs", description="Task outputs directory")
    
    # Parallel Processing Settings
    max_workers: int = Field(default=10, description="Max parallel workers")
    use_ray: bool = Field(default=False, description="Use Ray for distributed processing")
    
    # Cache Settings
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=1000, description="Cache max size")
    
    # Hot Reload Settings
    hot_reload_enabled: bool = Field(default=True, description="Enable hot reload")
    hot_reload_interval: int = Field(default=30, description="Hot reload check interval in seconds")
    
    # Security Settings
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_max_requests: int = Field(default=100, description="Max requests per window")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window in seconds")
    
    # Additional optional fields from .env.example
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    litellm_api_key: Optional[str] = Field(default=None, description="LiteLLM API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    rabbitmq_url: Optional[str] = Field(default=None, description="RabbitMQ URL")
    milvus_url: Optional[str] = Field(default=None, description="Milvus URL")
    celery_broker_url: Optional[str] = Field(default=None, description="Celery broker URL")
    celery_result_backend: Optional[str] = Field(default=None, description="Celery result backend")
    trust_update_lr: float = Field(default=0.1, description="Trust update learning rate")
    max_iteration: int = Field(default=5, description="Max iterations")
    default_confidence_threshold: float = Field(default=0.8, description="Default confidence threshold")
    trust_filter_threshold: float = Field(default=0.6, description="Trust filter threshold")
    vector_dimension: int = Field(default=1536, description="Vector dimension")
    embedding_model: str = Field(default="text-embedding-3-large", description="Embedding model")

    # ==================== Field Validators ====================
    @field_validator("api_port")
    @classmethod
    def validate_api_port(cls, v: int) -> int:
        if v < 1 or v > 65535:
            raise ValueError("API port must be between 1 and 65535")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        allowed_providers = ["openai", "anthropic", "ollama", "mock"]
        if v not in allowed_providers:
            raise ValueError(f"LLM provider must be one of {allowed_providers}")
        return v

    @field_validator("llm_temperature")
    @classmethod
    def validate_llm_temperature(cls, v: float) -> float:
        if v < 0 or v > 2:
            raise ValueError("LLM temperature must be between 0 and 2")
        return v

    @field_validator("vector_store_type")
    @classmethod
    def validate_vector_store_type(cls, v: str) -> str:
        allowed_types = ["milvus", "chroma"]
        if v not in allowed_types:
            raise ValueError(f"Vector store type must be one of {allowed_types}")
        return v

    @field_validator("max_workers")
    @classmethod
    def validate_max_workers(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Max workers must be positive")
        return v

    @field_validator("cache_ttl_seconds")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Cache TTL must be positive")
        return v

    @field_validator("milvus_port")
    @classmethod
    def validate_milvus_port(cls, v: int) -> int:
        if v < 1 or v > 65535:
            raise ValueError("Milvus port must be between 1 and 65535")
        return v

    # ==================== Model Validator ====================
    @model_validator(mode="after")
    def validate_model(self) -> "Settings":
        """Validate model after initialization."""
        from backend.core.configuration.configuration_validator import create_neuralagent_validator, ConfigValidationResult
        import logging

        logger.info("Validating configuration...")

        # Create validator and validate
        validator = create_neuralagent_validator()
        result = validator.validate(self.model_dump())
        result.log_results(logger)

        if not result.is_valid:
            raise ValueError(f"Configuration validation failed: {result.to_dict()}")

        # Production environment warnings
        if self.environment == "production" and self.jwt_secret_key is None:
            logger.warning("⚠️  JWT secret key is not set in production environment")

        if self.environment == "production" and self.llm_provider == "mock":
            logger.warning("⚠️  Using mock LLM provider in production environment")

        if self.hot_reload_enabled and self.environment == "production":
            logger.warning("⚠️  Hot reload should be disabled in production for better security")

        return self

    # ==================== Helpers ====================
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return self.model_dump()

    def get_safe_config(self) -> dict:
        """Get safe config without sensitive information."""
        safe = self.model_dump()
        # Mask sensitive fields
        if "jwt_secret_key" in safe:
            safe["jwt_secret_key"] = "***"
        if "llm_api_key" in safe:
            safe["llm_api_key"] = "***"
        return safe

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }


try:
    settings = Settings()
    logger.info("Configuration loaded and validated successfully")
except Exception as e:
    logger.critical(f"Failed to load configuration: {e}")
    raise
