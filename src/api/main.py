"""Main FastAPI application with refactored architecture."""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from ..core.config import get_settings
from ..core.logging import setup_logging, get_logger
from ..core.exceptions import UnityAIException
from ..core.database import init_database, close_database
from ..core.cache import init_cache, close_cache
from ..services.n8n_service import n8n_service, init_n8n_service, close_n8n_service
from ..services.autogen_service import autogen_service, init_autogen_service, close_autogen_service
from ..services.code_execution_service import code_execution_service
from ..services.workflow_service import init_workflow_service, get_workflow_service
from .routers import health, code_execution, workflows, autogen, n8n
from .middleware import (
    SecurityMiddleware, LoggingMiddleware, MetricsMiddleware,
    RateLimitMiddleware, ErrorHandlingMiddleware
)
from .dependencies import get_current_user, verify_api_key

# Initialize settings and logging
settings = get_settings()
setup_logging(settings)
logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to logs."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        # Add request ID for tracing
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add to log context
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'client_ip': request.client.host if request.client else None
            }
        )
        
        response = await call_next(request)
        
        logger.info(
            f"Request completed: {response.status_code}",
            extra={
                'request_id': request_id,
                'status_code': response.status_code
            }
        )
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Unity AI application...")
    
    try:
        # Initialize core services
        await init_database()
        await init_cache()
        
        # Initialize external services
        await init_n8n_service()
        await init_autogen_service()
        
        # Initialize workflow service
        await init_workflow_service(
            n8n_service=n8n_service,
            autogen_service=autogen_service,
            code_execution_service=code_execution_service
        )
        
        logger.info("Unity AI application started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down Unity AI application...")
        
        try:
            await close_n8n_service()
            await close_autogen_service()
            await close_cache()
            await close_database()
            
            logger.info("Unity AI application shut down successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Unity AI",
    description="Hardened VPS-based automation platform using Autogen agents and n8n workflows",
    version="2.0.0",
    docs_url=None,  # Disable default docs for security
    redoc_url=None,  # Disable redoc for security
    openapi_url=None if settings.api.environment == "production" else "/openapi.json",
    lifespan=lifespan
)


# Add middleware (order matters - first added is outermost)
if settings.security.trusted_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.security.trusted_hosts
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RequestContextMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

if settings.security.rate_limiting_enabled:
    app.add_middleware(RateLimitMiddleware)


# Exception handlers
@app.exception_handler(UnityAIException)
async def unity_ai_exception_handler(request: Request, exc: UnityAIException):
    """Handle Unity AI custom exceptions."""
    logger.error(f"Unity AI exception: {exc.message}", extra={'error_code': exc.error_code})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": None
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "details": str(exc) if settings.api.debug else None
            }
        }
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(
    code_execution.router,
    prefix="/api/v1",
    tags=["Code Execution"],
    dependencies=[Depends(verify_api_key)] if settings.security.api_key_required else []
)
app.include_router(
    workflows.router,
    prefix="/api/v1",
    tags=["Workflows"],
    dependencies=[Depends(verify_api_key)] if settings.security.api_key_required else []
)
app.include_router(
    autogen.router,
    prefix="/api/v1",
    tags=["AutoGen"],
    dependencies=[Depends(verify_api_key)] if settings.security.api_key_required else []
)
app.include_router(
    n8n.router,
    prefix="/api/v1",
    tags=["n8n"],
    dependencies=[Depends(verify_api_key)] if settings.security.api_key_required else []
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Unity AI",
        "version": "2.0.0",
        "description": "Hardened VPS-based automation platform",
        "status": "running",
        "docs_url": "/docs" if settings.api.environment != "production" else None
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.monitoring.enabled:
        raise HTTPException(status_code=404, detail="Metrics not enabled")
    
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Custom docs endpoint (protected)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    """Custom Swagger UI with authentication."""
    if settings.api.environment == "production":
        raise HTTPException(status_code=404, detail="Documentation not available in production")
    
    # In production, you might want to add authentication here
    # For now, just check if docs are enabled
    if not settings.api.debug:
        raise HTTPException(status_code=404, detail="Documentation not available")
    
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    """Custom OpenAPI endpoint."""
    if settings.api.environment == "production":
        raise HTTPException(status_code=404, detail="OpenAPI spec not available in production")
    
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


# Webhook endpoints for n8n integration
@app.post("/webhooks/n8n/{webhook_path:path}")
async def n8n_webhook_handler(
    webhook_path: str,
    request: Request,
    data: Dict[str, Any] = None
):
    """Handle n8n webhooks."""
    try:
        # Get request body
        if data is None:
            data = await request.json()
        
        logger.info(f"Received n8n webhook: {webhook_path}")
        
        # Forward to n8n service
        result = await n8n_service.trigger_webhook(
            webhook_path=webhook_path,
            data=data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Webhook handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check for load balancers
@app.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    try:
        # Check if all services are ready
        workflow_service = await get_workflow_service()
        is_ready = await workflow_service.health_check()
        
        if is_ready:
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "src.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level="info",
        access_log=True
    )