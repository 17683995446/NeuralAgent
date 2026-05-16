"""
API Usage Examples - Product Grade

This file demonstrates how to use all the product-grade modules
following the 5 architecture principles:
- Standing on the shoulders of giants
- Using open-source tools
- Not reinventing the wheel
- Highly modular
- Productized modules
"""

# =============================================================================
# Example 1: Rate Limiting
# =============================================================================

from backend.core.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    rate_limit,
    rate_limit_by_ip,
    rate_limit_by_user
)

# Basic rate limiter usage
config = RateLimitConfig(
    max_requests=100,
    window_seconds=60
)
limiter = RateLimiter(config)

# Check if request is allowed
result = limiter.check("user:123")
print(f"Allowed: {result.allowed}")
print(f"Remaining: {result.remaining}")

# Using decorator for rate limiting
@rate_limit(max_requests=10, window_seconds=60)
def api_endpoint():
    return {"status": "success"}

# Rate limit by IP
@rate_limit_by_ip(max_requests=100, window_seconds=60)
def protected_api(request):
    return {"data": "protected"}


# =============================================================================
# Example 2: Caching
# =============================================================================

from backend.core.cache_manager import (
    get_cache_manager,
    cache_result
)

# Get cache manager
cache = get_cache_manager()

# Set and get values
cache.set("user:123:profile", {"name": "John", "age": 30}, ttl=3600)
profile = cache.get("user:123:profile")
print(f"Profile: {profile}")

# Using cache decorator
@cache_result(key_prefix="expensive_op", ttl=600)
def expensive_computation(x):
    return x * x

result = expensive_computation(5)  # First call computes
result = expensive_computation(5)  # Second call returns cached


# =============================================================================
# Example 3: Error Handling
# =============================================================================

from backend.core.error_resilience import (
    retry_llm,
    retry_api,
    with_circuit_breaker,
    llm_circuit_breaker
)
from backend.core.error_codes import (
    ErrorCode,
    NeuralAgentException,
    TaskError
)

# Using retry decorator
@retry_llm(max_attempts=3)
def call_llm(prompt):
    # Your LLM call here
    return "response"

# Using circuit breaker
@with_circuit_breaker()
def external_api_call():
    # Your API call here
    return {"data": "response"}

# Using error codes
try:
    raise TaskError(
        ErrorCode.TASK_NOT_FOUND,
        message="Task 123 not found",
        details={"task_id": "123"}
    )
except NeuralAgentException as e:
    print(f"Error code: {e.error_code.code}")
    print(f"HTTP status: {e.error_code.http_status}")


# =============================================================================
# Example 4: Health Monitoring
# =============================================================================

from backend.core.health_monitor import (
    check_health,
    get_health_monitor
)

# Quick health check
health_report = check_health(app_version="1.0.0")
print(f"Overall status: {health_report.overall_status}")

# Using health monitor
monitor = get_health_monitor()
monitor.register_check("database", lambda: True)
monitor.register_check("redis", lambda: True)


# =============================================================================
# Example 5: Prometheus Metrics
# =============================================================================

from backend.core.prometheus_metrics import (
    get_metrics,
    track_api_request,
    track_llm_call
)

# Get metrics instance
metrics = get_metrics()

# Record API request
metrics.record_api_request(
    endpoint="/api/v1/tasks",
    method="POST",
    status_code=201
)

# Using decorator
@track_api_request("/api/v1/tasks")
def create_task():
    return {"task_id": "123"}


# =============================================================================
# Example 6: Configuration Management
# =============================================================================

from backend.config import settings
from backend.core.config_validator import (
    create_neuralagent_validator,
    validate_config_and_raise
)

# Access settings
print(f"API Port: {settings.api_port}")
print(f"Environment: {settings.environment}")
print(f"LLM Provider: {settings.llm_provider}")

# Get safe config (without secrets)
safe_config = settings.get_safe_config()
print(f"Safe config: {safe_config}")

# Validate configuration
validator = create_neuralagent_validator()
result = validator.validate(settings.model_dump())
print(f"Config valid: {result.is_valid}")


# =============================================================================
# Example 7: Structured Logging
# =============================================================================

from backend.core.structured_logging import (
    setup_structured_logging,
    get_logger,
    bind_context
)

# Setup logging
setup_structured_logging(log_level="INFO")

# Get logger
logger = get_logger(__name__)

# Log with context
bind_context(user_id="123", request_id="abc")
logger.info("Processing request")
logger.info("Request completed", extra={"duration_ms": 150})


# =============================================================================
# Example 8: Security
# =============================================================================

from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

# Hash and verify password
password = "secure_password_123"
hashed = hash_password(password)
is_valid = verify_password(password, hashed)
print(f"Password valid: {is_valid}")

# Create and decode JWT token
token = create_access_token(
    data={"sub": "user123", "role": "admin"}
)
print(f"Token: {token}")

decoded = decode_access_token(token)
print(f"Decoded: {decoded}")


# =============================================================================
# Example 9: Quality Scoring
# =============================================================================

from backend.core.product_quality_scoring import (
    generate_quality_report,
    QualityScoringSystem
)

# Generate quality report
report = generate_quality_report(print_report=False)
print(f"Overall score: {report.overall_percentage:.1f}%")
print(f"Level: {report.overall_level.name}")

# Get detailed category scores
for cat in report.category_scores:
    print(f"{cat.category.value}: {cat.percentage:.1f}%")


# =============================================================================
# Example 10: Full Integration Workflow
# =============================================================================

def process_request(user_id: str, request_data: dict):
    """Complete request processing with all product features."""
    
    # 1. Rate limiting
    limiter = get_rate_limiter()
    rate_result = limiter.check(f"user:{user_id}")
    if not rate_result.allowed:
        raise NeuralAgentException(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Rate limit exceeded",
            details=rate_result.to_dict()
        )
    
    # 2. Check cache
    cache = get_cache_manager()
    cache_key = f"request:{user_id}:{hash(str(request_data))}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # 3. Process with error handling
    @retry_api(max_attempts=2)
    def process():
        # Your business logic here
        return {"result": "processed", "user_id": user_id}
    
    result = process()
    
    # 4. Cache result
    cache.set(cache_key, result, ttl=300)
    
    # 5. Record metrics
    metrics = get_metrics()
    metrics.record_api_request(
        endpoint="/api/v1/process",
        method="POST",
        status_code=200
    )
    
    # 6. Log
    logger = get_logger(__name__)
    logger.info("Request processed", extra={
        "user_id": user_id,
        "duration_ms": 100
    })
    
    return result


if __name__ == "__main__":
    print("=" * 80)
    print("NeuralAgent API Usage Examples")
    print("=" * 80)
    print("\nAll modules follow the 5 architecture principles:")
    print("1. Standing on the shoulders of giants")
    print("2. Using open-source tools")
    print("3. Not reinventing the wheel")
    print("4. Highly modular")
    print("5. Productized modules")
    print("=" * 80)
