#!/usr/bin/env python3
"""
UnityAI Python Worker Service
Main entry point for the Python container service.
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .config import settings
from .services import PythonWorkerService
from .utils import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class TaskRequest(BaseModel):
    task_type: str
    parameters: Dict[str, Any]
    task_id: str = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Dict[str, Any] = None
    error: str = None


# Global service instance
worker_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global worker_service
    
    # Startup
    logger.info("Starting UnityAI Python Worker Service")
    worker_service = PythonWorkerService()
    await worker_service.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down UnityAI Python Worker Service")
    if worker_service:
        await worker_service.stop()


# Create FastAPI app
app = FastAPI(
    title="UnityAI Python Worker",
    description="Python container service for UnityAI platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="python-worker",
        version="1.0.0"
    )


@app.post("/tasks", response_model=TaskResponse)
async def execute_task(task: TaskRequest):
    """Execute a Python task."""
    try:
        if not worker_service:
            raise HTTPException(status_code=503, detail="Service not available")
        
        result = await worker_service.execute_task(
            task.task_type,
            task.parameters,
            task.task_id
        )
        
        return TaskResponse(
            task_id=result["task_id"],
            status="completed",
            result=result["data"]
        )
    
    except Exception as e:
        logger.error("Task execution failed", error=str(e), task_type=task.task_type)
        return TaskResponse(
            task_id=task.task_id or "unknown",
            status="failed",
            error=str(e)
        )


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    if not worker_service:
        raise HTTPException(status_code=503, detail="Service not available")
    
    status = await worker_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal", signal=signum)
    sys.exit(0)


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        reload=False
    )