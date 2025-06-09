#!/usr/bin/env python3
"""
n8n API Playground - Main Application Entry Point

This module serves as the main entry point for the n8n API Playground FastAPI application.
It initializes all modules, configures middleware, sets up routing, and handles application lifecycle.

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge
from fastapi import Request, Response
import time
import structlog
import uvicorn

# Core imports
from core import (
    PlaygroundManager,
    N8nApiClient,
    WorkflowExecutor,
    ResponseHandler
)
from core.playground_manager import PlaygroundConfig

# Module imports
from modules.workflow_automation import workflow_automation_router as workflow_router
# from modules.fastapi_integration import fastapi_integration_router  # Module not implemented yet
# from modules.monitoring import monitoring_router  # Module not implemented yet
# from modules.user_management import user_management_router  # Module not implemented yet

# Middleware imports
# from modules.user_management.middleware import AuthenticationMiddleware  # Module not implemented yet
# from modules.monitoring.middleware import MetricsMiddleware  # Module not implemented yet

# Exception imports
# from core.exceptions import PlaygroundException  # Module not implemented yet
# from modules.workflow_automation.exceptions import WorkflowException  # Module not implemented yet
# from modules.fastapi_integration.exceptions import IntegrationException  # Module not implemented yet
# from modules.monitoring.exceptions import MonitoringException  # Module not implemented yet
# from modules.user_management.exceptions import UserManagementException  # Module not implemented yet

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting n8n API Playground application")
    
    try:
        # Load configuration
        from config import PlaygroundConfig as Config
        app_config = Config()
        
        # Create playground config with n8n configuration
        # Convert dataclass N8nApiConfig to Pydantic model
        from core.config import N8nApiConfig as CoreN8nApiConfig
        core_n8n_config = CoreN8nApiConfig(
            base_url=app_config.n8n_api.base_url,
            api_key=app_config.n8n_api.api_key,
            timeout=app_config.n8n_api.timeout,
            max_retries=app_config.n8n_api.max_retries,
            retry_delay=app_config.n8n_api.retry_delay,
            verify_ssl=app_config.n8n_api.verify_ssl
        )
        from core.playground_manager import PlaygroundConfig as CorePlaygroundConfig
        playground_config = CorePlaygroundConfig(n8n_config=core_n8n_config)
        app_state["config"] = playground_config
        
        # Initialize core components
        api_client = N8nApiClient(app_config.n8n_api)
        app_state["api_client"] = api_client
        
        workflow_executor = WorkflowExecutor(api_client)
        app_state["workflow_executor"] = workflow_executor
        
        response_handler = ResponseHandler()
        app_state["response_handler"] = response_handler
        
        # Initialize playground manager
        playground_manager = PlaygroundManager(
            config=playground_config
        )
        app_state["playground_manager"] = playground_manager
        
        # Start playground manager
        await playground_manager.start()
        
        # Initialize modules
        if app_config.modules.workflow_automation.enabled:
            logger.info("Initializing Workflow Automation module")
            # Module-specific initialization would go here
        
        if app_config.modules.fastapi_integration.enabled:
            logger.info("Initializing FastAPI Integration module")
            # Module-specific initialization would go here
        
        if app_config.modules.monitoring.enabled:
            logger.info("Initializing Monitoring module")
            # Module-specific initialization would go here
        
        if app_config.modules.user_management.enabled:
            logger.info("Initializing User Management module")
            # Module-specific initialization would go here
        
        logger.info("n8n API Playground application started successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e), exc_info=True)
        raise
    
    # Shutdown
    logger.info("Shutting down n8n API Playground application")
    
    try:
        # Stop playground manager
        if "playground_manager" in app_state:
            await app_state["playground_manager"].stop()
        
        # Cleanup resources
        app_state.clear()
        
        logger.info("n8n API Playground application shut down successfully")
        
    except Exception as e:
        logger.error("Error during application shutdown", error=str(e), exc_info=True)


def patched_build_middleware_stack(self):
    """
    Patched version of build_middleware_stack that handles Middleware objects correctly.
    
    This fixes the "too many values to unpack (expected 2)" error by properly
    extracting cls and options from Middleware objects.
    """
    debug = self.debug
    error_handler = None
    exception_handlers = {}

    for key, value in self.exception_handlers.items():
        if key in (500, Exception):
            error_handler = value
        else:
            exception_handlers[key] = value

    from starlette.middleware.errors import ServerErrorMiddleware
    from starlette.middleware.exceptions import ExceptionMiddleware
    from starlette.middleware import Middleware
    
    middleware = (
        [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]
        + self.user_middleware
        + [
            Middleware(
                ExceptionMiddleware, handlers=exception_handlers, debug=debug
            )
        ]
    )

    app = self.router
    
    # Fix: Properly handle Middleware objects by extracting cls and combining args/kwargs
    for middleware_item in reversed(middleware):
        if hasattr(middleware_item, 'cls'):
            # This is a Middleware object, extract the class and options
            cls = middleware_item.cls
            # Get options from the middleware object
            options = getattr(middleware_item, 'options', {})
            if hasattr(middleware_item, 'kwargs'):
                options.update(middleware_item.kwargs)
            app = cls(app=app, **options)
        else:
            # This might be a tuple (cls, options) - handle legacy format
            cls, options = middleware_item
            app = cls(app=app, **options)
    
    return app


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Load configuration
    from config import PlaygroundConfig
    app_config = PlaygroundConfig()
    config = app_config  # Use the main config directly
    
    # Create FastAPI app
    app = FastAPI(
        title="n8n API Playground",
        description="Comprehensive n8n API integration and workflow automation platform",
        version="1.0.0",
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None,
        openapi_url="/openapi.json" if config.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app, config)
    
    # Apply middleware fix - monkey patch the build_middleware_stack method
    import types
    app.build_middleware_stack = types.MethodType(patched_build_middleware_stack, app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Setup routes
    setup_routes(app, config, app_config)
    
    # Setup monitoring
    if config.modules.monitoring.enabled:
        setup_monitoring(app)
    
    return app


def setup_middleware(app: FastAPI, config) -> None:
    """
    Setup application middleware.
    
    Args:
        app: FastAPI application instance
        config: Application configuration
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # GZip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup global exception handlers.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Exception occurred",
            error=str(exc),
            path=request.url.path,
            method=request.method
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An internal server error occurred",
                "details": str(exc)
            }
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred"
            }
        )


def setup_routes(app: FastAPI, config, app_config) -> None:
    """
    Setup application routes.
    
    Args:
        app: FastAPI application instance
        config: Application configuration
        app_config: Main application configuration with modules
    """
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        from datetime import datetime
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "n8n API Playground",
            "version": "1.0.0",
            "description": "Comprehensive n8n API integration and workflow automation platform",
            "docs_url": "/docs" if app_config.debug else None,
            "modules": {
                "workflow_automation": app_config.modules.workflow_automation.enabled,
                "fastapi_integration": app_config.modules.fastapi_integration.enabled,
                "monitoring": app_config.modules.monitoring.enabled,
                "user_management": app_config.modules.user_management.enabled
            }
        }
    
    # Include module routers
    if app_config.modules.workflow_automation.enabled:
        app.include_router(
            workflow_router,
            prefix="/workflow-automation",
            tags=["Workflow Automation"]
        )
    
    # TODO: Uncomment when modules are implemented
    # if "fastapi_integration" in config.modules.enabled_modules:
    #     app.include_router(
    #         fastapi_integration_router,
    #         prefix="/fastapi-integration",
    #         tags=["FastAPI Integration"]
    #     )
    # 
    # if "monitoring" in config.modules.enabled_modules:
    #     app.include_router(
    #         monitoring_router,
    #         prefix="/monitoring",
    #         tags=["Monitoring"]
    #     )
    # 
    # if "user_management" in config.modules.enabled_modules:
    #     app.include_router(
    #         user_management_router,
    #         prefix="/user-management",
    #         tags=["User Management"]
    #     )
    
    # Static files (if needed)
    static_dir = Path("static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")


# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
IN_PROGRESS = Gauge('http_requests_inprogress', 'HTTP requests in progress')

def setup_monitoring(app: FastAPI) -> None:
    """
    Setup Prometheus monitoring.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        IN_PROGRESS.inc()
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        endpoint = request.url.path
        method = request.method
        status = str(response.status_code)
        
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        IN_PROGRESS.dec()
        
        return response
    
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Create the application instance
app = create_app()


if __name__ == "__main__":
    # Development server
    from config import PlaygroundConfig
    config = PlaygroundConfig()
    
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.debug,
        log_level="debug" if config.debug else "info",
        access_log=True,
        use_colors=True,
        loop="asyncio"
    )