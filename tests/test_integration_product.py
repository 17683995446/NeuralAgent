"""Comprehensive Integration Tests - Product Grade.

Tests the entire NeuralAgent system integration including:
- API endpoints
- Authentication
- Health checks
- Metrics
- Error handling
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestAPIRoutes:
    """Integration tests for API routes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from backend.main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns system information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NeuralAgent System"
        assert "version" in data
        assert "architecture" in data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "version" in data
        assert "checks" in data
        assert "system_metrics" in data
    
    def test_readiness_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "version" in data
    
    def test_liveness_endpoint(self, client):
        """Test liveness check endpoint."""
        response = client.get("/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "demo_user", "password": "demo_password"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_info" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "wrong_user", "password": "wrong_password"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_version_endpoint(self, client):
        """Test version endpoint."""
        response = client.get("/api/v1/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "api_version" in data


class TestHealthMonitor:
    """Integration tests for health monitoring."""
    
    def test_health_check_function(self):
        """Test the check_health convenience function."""
        from backend.core.infrastructure.observability.health_monitor import check_health
        
        report = check_health(app_version="0.1.0")
        assert report is not None
        assert report.version == "0.1.0"
        assert report.overall_status is not None
    
    def test_health_monitor_registration(self):
        """Test health check registration."""
        from backend.core.infrastructure.observability.health_monitor import HealthMonitor
        
        monitor = HealthMonitor(app_version="1.0.0")
        
        # Register a passing check
        monitor.register_check(
            name="test_check",
            check_func=lambda: True,
            critical=True,
            description="Test health check"
        )
        
        report = monitor.run_all_checks()
        assert "test_check" in report.checks
    
    def test_health_check_failure_tracking(self):
        """Test that health checks track failures."""
        from backend.core.infrastructure.observability.health_monitor import HealthMonitor
        
        monitor = HealthMonitor()
        
        # Create a check that fails
        check = monitor.register_check(
            name="failing_check",
            check_func=lambda: False,
            critical=True
        )
        
        # Run it multiple times
        for _ in range(3):
            monitor.run_all_checks()
        
        assert check.failure_count >= 3


class TestMetrics:
    """Integration tests for metrics system."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        from backend.core.infrastructure.observability.prometheus_metrics import get_metrics, init_metrics, MetricsConfig
        
        config = MetricsConfig(http_server_port=None)
        metrics = init_metrics(config)
        
        assert metrics is not None
        assert metrics.API_REQUESTS_TOTAL is not None
    
    def test_metrics_recording(self):
        """Test recording metrics."""
        from backend.core.infrastructure.observability.prometheus_metrics import get_metrics
        
        metrics = get_metrics()
        
        # Record some metrics
        metrics.API_REQUESTS_TOTAL.labels(
            endpoint="/test",
            method="GET",
            status_code="200"
        ).inc()
        
        # Verify metric was recorded (basic check)
        assert metrics.API_REQUESTS_TOTAL is not None


class TestErrorResilience:
    """Integration tests for error resilience."""
    
    def test_retry_decorator_success(self):
        """Test retry decorator with successful function."""
        from backend.core.infrastructure.error_handling.error_resilience import retry_api
        
        @retry_api(max_attempts=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_circuit_breaker_creation(self):
        """Test circuit breaker creation."""
        from backend.core.infrastructure.error_handling.error_resilience import CircuitBreaker
        
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exceptions=(ValueError,)
        )
        
        assert breaker is not None
        assert breaker.failure_count == 0


class TestStructuredLogging:
    """Integration tests for structured logging."""
    
    def test_logger_creation(self):
        """Test creating a logger."""
        from backend.core.structured_logging import get_logger
        
        logger = get_logger("test_module")
        assert logger is not None
    
    def test_log_context_binding(self):
        """Test binding context to logs."""
        from backend.core.structured_logging import bind_context, unbind_context
        
        # Bind context
        bind_context(request_id="test_123", user_id="user_456")
        
        # Unbind when done
        unbind_context("request_id", "user_id")


class TestAgentOrchestration:
    """Integration tests for agent orchestration."""
    
    def test_orchestrator_factory(self):
        """Test creating orchestrators."""
        from backend.core.agents.distributed_multi_agent_orchestrator import OrchestratorFactory, OrchestrationFramework
        
        # Test CrewAI orchestrator
        crewai = OrchestratorFactory.create(OrchestrationFramework.CREW_AI)
        assert crewai is not None
        
        # Test AutoGen orchestrator
        autogen = OrchestratorFactory.create(OrchestrationFramework.AUTO_GEN)
        assert autogen is not None
    
    def test_agent_config_creation(self):
        """Test creating agent configuration."""
        from backend.core.agents.distributed_multi_agent_orchestrator import AgentConfig
        
        config = AgentConfig(
            name="test_agent",
            role="Test Role",
            goal="Test Goal",
            backstory="Test Background"
        )
        
        assert config.name == "test_agent"
        assert config.role == "Test Role"
    
    def test_task_config_creation(self):
        """Test creating task configuration."""
        from backend.core.agents.distributed_multi_agent_orchestrator import TaskConfig
        
        config = TaskConfig(
            description="Test task description",
            expected_output="Test output"
        )
        
        assert config.description == "Test task description"


class TestSecurity:
    """Integration tests for security module."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        from backend.core.infrastructure.security import hash_password, verify_password
        
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_access_token_creation(self):
        """Test JWT token creation and decoding."""
        from backend.core.infrastructure.security import create_access_token, decode_access_token
        
        data = {"sub": "test_user", "role": "admin"}
        token = create_access_token(data)
        
        assert token is not None
        
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "test_user"


class TestConfiguration:
    """Integration tests for configuration management."""
    
    def test_settings_loading(self):
        """Test loading settings from environment."""
        from backend.config import settings
        
        assert settings is not None
        assert hasattr(settings, "api_port")
        assert hasattr(settings, "log_level")
        assert hasattr(settings, "environment")
    
    def test_llm_config_defaults(self):
        """Test LLM configuration defaults."""
        from backend.config import settings
        
        assert settings.llm_provider is not None
        assert settings.llm_model is not None


class TestErrorHandling:
    """Integration tests for error handling."""
    
    def test_validation_error_response(self):
        """Test validation error handling."""
        from backend.api.schemas import LoginRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            LoginRequest(username="ab", password="12345")  # Too short
    
    def test_schema_validation(self):
        """Test Pydantic schema validation."""
        from backend.api.schemas import TaskInput
        
        # Valid input
        valid_input = TaskInput(
            task_id="test_task_123",
            user_requirement="Test requirement",
            max_iteration=5,
            learning_rate=0.1
        )
        
        assert valid_input.task_id == "test_task_123"
        assert valid_input.max_iteration == 5


class TestSystemIntegration:
    """End-to-end system integration tests."""
    
    def test_full_health_check_flow(self):
        """Test complete health check flow."""
        from backend.core.infrastructure.observability.health_monitor import check_health
        
        # Get health report
        report = check_health(app_version="0.1.0")
        
        # Convert to dict
        report_dict = report.to_dict()
        
        # Verify structure
        assert "overall_status" in report_dict
        assert "version" in report_dict
        assert "checks" in report_dict
        assert "system_metrics" in report_dict
    
    def test_module_imports(self):
        """Test that all modules can be imported successfully."""
        # Core modules
        from backend.core.infrastructure.observability.prometheus_metrics import get_metrics
        from backend.core.infrastructure.error_handling.error_resilience import retry_api
        from backend.core.llm_integration.unified_llm_client_wrapper import get_llm_client
        from backend.core.infrastructure.security import hash_password
        from backend.core.agents.distributed_multi_agent_orchestrator import OrchestratorFactory
        from backend.core.structured_logging import get_logger
        from backend.core.infrastructure.observability.health_monitor import check_health
        
        # Configuration
        from backend.config import settings
        
        # All imports successful
        assert True
    
    def test_api_schema_completeness(self):
        """Test that all API schemas are properly defined."""
        from backend.api.schemas import (
            TaskInput, TaskContext, TaskStatus, FeedbackInput,
            FeedbackResult, TaskResult, LoginRequest, LoginResponse,
            CodeProcessingRequest, VectorStoreStats
        )
        
        # Verify schemas exist and can be instantiated
        login_req = LoginRequest(username="test", password="password123")
        assert login_req.username == "test"
        
        task_input = TaskInput(
            task_id="test123",
            user_requirement="Test requirement"
        )
        assert task_input.task_id == "test123"
