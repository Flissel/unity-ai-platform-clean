#!/usr/bin/env python3
"""
Unity AI Platform - FastAPI Application
Main application entry point with comprehensive API endpoints
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import redis.asyncio as redis
import asyncpg
import httpx
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "Unity AI Platform")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Database
        self.database_url = os.getenv("DATABASE_URL", "postgresql://n8n_user:password@db:5432/n8n")
        
        # Redis
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        # n8n Integration
        self.n8n_base_url = os.getenv("N8N_BASE_URL", "http://n8n:5678")
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678")
        
        # Security
        self.secret_key = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
        self.api_keys = os.getenv("API_KEYS", "dev-key-1,dev-key-2,dev-key-3").split(",")
        
        # CORS
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        
        # External APIs
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

settings = Settings()

# Global connections
redis_client = None
db_pool = None
httpx_client = None

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    global redis_client, db_pool, httpx_client
    
    try:
        # Initialize Redis
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Initialize Database Pool
        db_pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
        logger.info("Database pool created")
        
        # Initialize HTTP client
        httpx_client = httpx.AsyncClient(timeout=30.0)
        logger.info("HTTP client initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Unity AI Platform")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
    
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")
    
    if httpx_client:
        await httpx_client.aclose()
        logger.info("HTTP client closed")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Unity AI Platform - Automated workflow and AI processing system",
    lifespan=lifespan,
    docs_url="/api/v1/docs" if settings.debug else None,
    redoc_url="/api/v1/redoc" if settings.debug else None,
)

# Security
security = HTTPBearer()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["api.unit-y-ai.io", "localhost"]
)

# Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app, endpoint="/metrics")

# Models
class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = settings.app_version
    environment: str = settings.environment
    services: Dict[str, str] = {}

class WorkflowTriggerRequest(BaseModel):
    workflow_id: str = Field(..., description="n8n workflow ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="Input data for workflow")
    webhook_url: str = Field(None, description="Optional webhook URL for results")

class WorkflowTriggerResponse(BaseModel):
    execution_id: str
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TaskRequest(BaseModel):
    task_type: str = Field(..., description="Type of task to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)

class TaskResponse(BaseModel):
    task_id: str
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Authentication
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key authentication."""
    if credentials.credentials not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# Dependency functions
async def get_redis():
    """Get Redis client."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    return redis_client

async def get_db():
    """Get database connection."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    async with db_pool.acquire() as connection:
        yield connection

# Health check endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    services = {}
    
    # Check Redis
    try:
        await redis_client.ping()
        services["redis"] = "healthy"
    except Exception:
        services["redis"] = "unhealthy"
    
    # Check Database
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        services["database"] = "healthy"
    except Exception:
        services["database"] = "unhealthy"
    
    # Check n8n
    try:
        async with httpx_client.get(f"{settings.n8n_base_url}/healthz") as response:
            if response.status_code == 200:
                services["n8n"] = "healthy"
            else:
                services["n8n"] = "unhealthy"
    except Exception:
        services["n8n"] = "unhealthy"
    
    return HealthResponse(services=services)

@app.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    try:
        await redis_client.ping()
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")

@app.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {"status": "alive"}

# API Routes
@app.get("/api/v1/info")
async def get_info():
    """Get application information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.post("/api/v1/workflows/trigger", response_model=WorkflowTriggerResponse)
async def trigger_workflow(
    request: WorkflowTriggerRequest,
    api_key: str = Depends(verify_api_key),
    redis_conn = Depends(get_redis)
):
    """Trigger an n8n workflow."""
    execution_id = str(uuid.uuid4())
    
    try:
        # Prepare webhook URL for n8n
        webhook_url = f"{settings.n8n_webhook_url}/webhook/{request.workflow_id}"
        
        # Send request to n8n
        payload = {
            "executionId": execution_id,
            "data": request.data,
            "webhookUrl": request.webhook_url
        }
        
        async with httpx_client.post(webhook_url, json=payload) as response:
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to trigger workflow: {response.text}"
                )
            
            result = response.json()
        
        # Store execution info in Redis
        execution_data = {
            "workflow_id": request.workflow_id,
            "status": "triggered",
            "created_at": datetime.utcnow().isoformat(),
            "api_key": api_key,
            "data": request.data
        }
        
        await redis_conn.setex(
            f"execution:{execution_id}",
            3600,  # 1 hour TTL
            json.dumps(execution_data)
        )
        
        return WorkflowTriggerResponse(
            execution_id=execution_id,
            status="triggered",
            message="Workflow triggered successfully"
        )
        
    except httpx.RequestError as e:
        logger.error(f"Failed to trigger workflow {request.workflow_id}: {e}")
        raise HTTPException(status_code=503, detail="n8n service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error triggering workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/workflows/execution/{execution_id}")
async def get_execution_status(
    execution_id: str,
    api_key: str = Depends(verify_api_key),
    redis_conn = Depends(get_redis)
):
    """Get workflow execution status."""
    try:
        execution_data = await redis_conn.get(f"execution:{execution_id}")
        if not execution_data:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return json.loads(execution_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid execution data")
    except Exception as e:
        logger.error(f"Error retrieving execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/tasks/queue", response_model=TaskResponse)
async def queue_task(
    request: TaskRequest,
    api_key: str = Depends(verify_api_key),
    redis_conn = Depends(get_redis)
):
    """Queue a task for processing."""
    task_id = str(uuid.uuid4())
    
    try:
        task_data = {
            "task_id": task_id,
            "task_type": request.task_type,
            "parameters": request.parameters,
            "priority": request.priority,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "api_key": api_key
        }
        
        # Add to Redis queue
        await redis_conn.lpush("task_queue", json.dumps(task_data))
        
        # Store task info
        await redis_conn.setex(
            f"task:{task_id}",
            3600,  # 1 hour TTL
            json.dumps(task_data)
        )
        
        return TaskResponse(
            task_id=task_id,
            status="queued"
        )
        
    except Exception as e:
        logger.error(f"Error queuing task: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue task")

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key),
    redis_conn = Depends(get_redis)
):
    """Get task status."""
    try:
        task_data = await redis_conn.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return json.loads(task_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid task data")
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/stats")
async def get_stats(
    api_key: str = Depends(verify_api_key),
    redis_conn = Depends(get_redis)
):
    """Get system statistics."""
    try:
        # Get queue length
        queue_length = await redis_conn.llen("task_queue")
        
        # Get Redis info
        redis_info = await redis_conn.info()
        
        return {
            "queue_length": queue_length,
            "redis_memory_used": redis_info.get("used_memory_human", "unknown"),
            "redis_connected_clients": redis_info.get("connected_clients", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )