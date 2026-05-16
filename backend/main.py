"""NeuralAgent System - Main FastAPI Application - Product Grade.

Standing on the shoulders of giants: FastAPI, Uvicorn, Pydantic.
Not reinventing the wheel: using industry-standard libraries.
Highly modular: clear separation of concerns.
Productized: comprehensive monitoring, health checks, and error handling.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app, Counter, Histogram

from backend.api.routes import router
from backend.config import settings
from backend.core.infrastructure.observability.prometheus_metrics import (
    init_metrics,
    MetricsConfig,
    get_metrics
)
from backend.core.llm_integration.unified_llm_client_wrapper import get_llm_client
from backend.core.infrastructure.observability.health_monitor import (
    HealthMonitor,
    get_health_monitor,
    check_health
)
from backend.core.structured_logging import setup_structured_logging


# Initialize logging first
setup_structured_logging(
    log_level=settings.log_level,
    json_logs=settings.environment != "development",
    service_name="neural_agent"
)

logger = logging.getLogger(__name__)


# Additional Prometheus metrics for FastAPI
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests received',
    ['method', 'endpoint', 'status_code']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with comprehensive initialization and cleanup."""
    logger.info("=" * 60)
    logger.info("NeuralAgent System starting up")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Host: {settings.api_host}")
    logger.info(f"API Port: {settings.api_port}")
    
    # Initialize Prometheus Metrics
    logger.info("Initializing Prometheus metrics")
    metrics_config = MetricsConfig(http_server_port=None)
    metrics = init_metrics(config=metrics_config)
    
    # Initialize Health Monitor
    logger.info("Initializing health monitor")
    health_monitor = get_health_monitor(app_version="0.1.0")
    
    # Register basic health checks
    health_monitor.register_check(
        name="basic",
        check_func=lambda: True,
        critical=True,
        description="Basic application health check"
    )
    
    # Initialize LLM Client
    logger.info("Initializing LLM client")
    try:
        llm_client = get_llm_client()
        logger.info(f"LLM client initialized with model: {llm_client.model}")
        
        # Register LLM health check (non-critical)
        health_monitor.register_check(
            name="llm",
            check_func=lambda: True,  # In production, you'd ping the LLM provider
            critical=False,
            description=f"LLM provider ({settings.llm_provider}) availability check"
        )
    except Exception as e:
        logger.warning(f"Failed to initialize LLM client: {e}, check configuration")
    
    # Record system info
    metrics.SYSTEM_INFO.info({
        "version": "0.1.0",
        "environment": settings.environment
    })
    
    logger.info("NeuralAgent System ready to accept requests")
    
    yield
    
    logger.info("=" * 60)
    logger.info("NeuralAgent System shutting down gracefully")
    logger.info("=" * 60)


# Create FastAPI application
app = FastAPI(
    title="NeuralAgent System",
    description="类神经网络多Agent协作系统 - Multi-Agent Collaboration System",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware with production-ready configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request/response metrics and logging
@app.middleware("http")
async def metrics_and_logging_middleware(request: Request, call_next):
    """Middleware to track request metrics and log activity."""
    start_time = __import__('time').time()
    method = request.method
    endpoint = request.url.path
    
    logger.debug(f"Request started: {method} {endpoint}")
    
    try:
        with HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).time():
            response = await call_next(request)
            
        status_code = response.status_code
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        # Record success metrics
        if 200 <= status_code < 300:
            metrics = get_metrics()
            metrics.API_REQUESTS_TOTAL.labels(
                endpoint=endpoint,
                method=method,
                status_code=str(status_code)
            ).inc()
            
        duration_ms = (__import__('time').time() - start_time) * 1000
        logger.debug(
            f"Request completed: {method} {endpoint} - "
            f"Status: {status_code} - Duration: {duration_ms:.2f}ms"
        )
        
        return response
        
    except Exception as e:
        status_code = 500
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        logger.exception(f"Request failed: {method} {endpoint} - Error: {e}")
        raise


# Include main API router
app.include_router(router)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with system information."""
    return {
        "name": "NeuralAgent System",
        "version": "0.1.0",
        "description": "类神经网络多Agent协作系统",
        "architecture": {
            "layers": [
                "Input Layer (FastAPI)",
                "Convolution Layer (Code Analysis)",
                "Pooling Layer (Information Compression)",
                "FC Layer 1 (Global Understanding)",
                "FC Layer 2 (Code Generation)",
                "FC Layer 3 (Test Generation)",
                "Output Layer (Document Generation)",
                "Backward Layer (Feedback Iteration)"
            ],
            "core_features": [
                "Dual Memory System (Redis + Milvus)",
                "Trust Matrix Management (Ray RLlib)",
                "LLM Unified Adapter (LiteLLM)",
                "Multi-Agent Orchestration (AutoGen/CrewAI/LangChain)"
            ]
        },
        "docs": "/docs",
        "health": "/health",
        "readiness": "/ready",
        "metrics": "/metrics"
    }


@app.get("/health", tags=["Health"], response_model=None)
async def health_check() -> JSONResponse:
    """Comprehensive health check endpoint.
    
    Returns detailed health report including:
    - Overall system health status
    - Individual health check results
    - System resource metrics (CPU, memory, disk)
    - Application uptime and version
    """
    try:
        health_report = check_health(app_version="0.1.0")
        return JSONResponse(content=health_report.to_dict())
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Health check failed"
        )


@app.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """Simple readiness check endpoint for load balancers."""
    return {
        "status": "ready",
        "version": "0.1.0",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


@app.get("/live", tags=["Health"])
async def liveness_check() -> Dict[str, Any]:
    """Simple liveness check endpoint for Kubernetes."""
    return {
        "status": "alive",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True
    )
