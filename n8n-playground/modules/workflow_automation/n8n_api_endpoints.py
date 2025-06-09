#!/usr/bin/env python3
"""
n8n API Endpoints for Workflow Automation

This module provides FastAPI endpoints for integrating with n8n workflows,
allowing users to execute, monitor, and manage n8n workflows through a REST API.

Author: UnityAI Team
Version: 1.0.0
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import structlog

from .n8n_integration import (
    N8nIntegrationManager,
    N8nExecutionRequest,
    N8nExecutionResponse,
    N8nWorkflowInfo
)

# Setup structured logging
logger = structlog.get_logger(__name__)

# Create router with prefix
n8n_router = APIRouter(
    prefix="/n8n",
    tags=["n8n Integration"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Global n8n manager instance
_n8n_manager: Optional[N8nIntegrationManager] = None


def get_n8n_manager() -> N8nIntegrationManager:
    """Dependency to get n8n integration manager."""
    global _n8n_manager
    
    if _n8n_manager is None:
        api_key = os.getenv("N8N_API_KEY")
        base_url = os.getenv("N8N_API_BASE_URL", "https://n8n.unit-y-ai.io")
        
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="N8N_API_KEY environment variable is required"
            )
        
        _n8n_manager = N8nIntegrationManager(api_key=api_key, base_url=base_url)
        logger.info("n8n integration manager initialized", base_url=base_url)
    
    return _n8n_manager


@n8n_router.get("/health", response_model=Dict[str, Any])
async def check_n8n_health(manager: N8nIntegrationManager = Depends(get_n8n_manager)):
    """
    Check n8n API health and connectivity.
    
    Returns:
        Dict containing health status, API accessibility, and timestamp.
    """
    try:
        health_status = await manager.health_check()
        return health_status
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@n8n_router.get("/workflows", response_model=List[N8nWorkflowInfo])
async def list_workflows(
    active_only: bool = Query(False, description="Filter to only active workflows"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of workflows to return"),
    manager: N8nIntegrationManager = Depends(get_n8n_manager)
):
    """
    List all available workflows from n8n.
    
    Args:
        active_only: If True, only return active workflows
        limit: Maximum number of workflows to return (1-1000)
        
    Returns:
        List of workflow information including ID, name, status, and metadata.
    """
    try:
        workflows = await manager.list_workflows(active_only=active_only, limit=limit)
        logger.info("Listed workflows", count=len(workflows), active_only=active_only)
        return workflows
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@n8n_router.get("/workflows/{workflow_id}", response_model=N8nWorkflowInfo)
async def get_workflow(
    workflow_id: str,
    manager: N8nIntegrationManager = Depends(get_n8n_manager)
):
    """
    Get detailed information about a specific workflow.
    
    Args:
        workflow_id: The n8n workflow ID
        
    Returns:
        Detailed workflow information including nodes and connections.
    """
    try:
        workflow = await manager.get_workflow(workflow_id)
        logger.info("Retrieved workflow", workflow_id=workflow_id, name=workflow.name)
        return workflow
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")


@n8n_router.post("/workflows/{workflow_id}/execute", response_model=N8nExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: N8nExecutionRequest,
    background_tasks: BackgroundTasks,
    manager: N8nIntegrationManager = Depends(get_n8n_manager)
):
    """
    Execute a workflow in n8n.
    
    Args:
        workflow_id: The n8n workflow ID to execute
        request: Execution request containing input data and options
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        Execution response with status, results, and metadata.
    """
    try:
        # Override workflow_id from URL parameter
        request.workflow_id = workflow_id
        
        logger.info(
            "Executing workflow",
            workflow_id=workflow_id,
            wait_for_completion=request.wait_for_completion,
            timeout=request.timeout
        )
        
        execution_response = await manager.execute_workflow(request)
        
        logger.info(
            "Workflow execution completed",
            workflow_id=workflow_id,
            execution_id=execution_response.execution_id,
            status=execution_response.status
        )
        
        return execution_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@n8n_router.get("/executions/{execution_id}", response_model=N8nExecutionResponse)
async def get_execution_status(
    execution_id: str,
    manager: N8nIntegrationManager = Depends(get_n8n_manager)
):
    """
    Get the status and results of a workflow execution.
    
    Args:
        execution_id: The n8n execution ID
        
    Returns:
        Execution status, results, and metadata.
    """
    try:
        execution = await manager.get_execution_status(execution_id)
        logger.info(
            "Retrieved execution status",
            execution_id=execution_id,
            status=execution.status
        )
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get execution status", execution_id=execution_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")


@n8n_router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    manager: N8nIntegrationManager = Depends(get_n8n_manager)
):
    """
    Cancel a running workflow execution.
    
    Args:
        execution_id: The n8n execution ID to cancel
        
    Returns:
        Cancellation confirmation with timestamp.
    """
    try:
        result = await manager.cancel_execution(execution_id)
        logger.info("Execution cancelled", execution_id=execution_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel execution", execution_id=execution_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")


@n8n_router.get("/executions", response_model=List[N8nExecutionResponse])
async def list_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of executions to return"),
    manager: N8nIntegrationManager = Depends(get_n8n_manager)
):
    """
    List workflow executions.
    
    Args:
        workflow_id: Optional workflow ID to filter executions
        limit: Maximum number of executions to return (1-500)
        
    Returns:
        List of execution information with status and results.
    """
    try:
        executions = await manager.list_executions(workflow_id=workflow_id, limit=limit)
        logger.info(
            "Listed executions",
            count=len(executions),
            workflow_id=workflow_id
        )
        return executions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list executions",
            workflow_id=workflow_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@n8n_router.post("/workflows/batch-execute")
async def batch_execute_workflows(
    requests: List[N8nExecutionRequest],
    background_tasks: BackgroundTasks,
    manager: N8nIntegrationManager = Depends(get_n8n_manager)
):
    """
    Execute multiple workflows in batch.
    
    Args:
        requests: List of execution requests
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        List of execution responses for each workflow.
    """
    if len(requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 workflows can be executed in a single batch"
        )
    
    try:
        results = []
        for request in requests:
            try:
                execution_response = await manager.execute_workflow(request)
                results.append({
                    "workflow_id": request.workflow_id,
                    "status": "success",
                    "execution": execution_response
                })
            except Exception as e:
                logger.error(
                    "Failed to execute workflow in batch",
                    workflow_id=request.workflow_id,
                    error=str(e)
                )
                results.append({
                    "workflow_id": request.workflow_id,
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info("Batch execution completed", total=len(requests), successful=len([r for r in results if r["status"] == "success"]))
        return {"results": results}
        
    except Exception as e:
        logger.error("Batch execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch execution failed: {str(e)}")


@n8n_router.get("/workflows/{workflow_id}/stats")
async def get_workflow_stats(
    workflow_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    manager: N8nIntegrationManager = Depends(get_n8n_manager)
):
    """
    Get workflow execution statistics.
    
    Args:
        workflow_id: The n8n workflow ID
        days: Number of days to analyze (1-365)
        
    Returns:
        Workflow execution statistics including success rate, average duration, etc.
    """
    try:
        # Get recent executions for the workflow
        executions = await manager.list_executions(workflow_id=workflow_id, limit=1000)
        
        # Filter executions by date range
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
        
        recent_executions = [
            exec for exec in executions
            if exec.started_at and exec.started_at >= cutoff_date
        ]
        
        # Calculate statistics
        total_executions = len(recent_executions)
        successful_executions = len([e for e in recent_executions if e.status == 'success'])
        failed_executions = len([e for e in recent_executions if e.status == 'error'])
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        # Calculate average duration for completed executions
        completed_executions = [e for e in recent_executions if e.duration is not None]
        avg_duration = sum(e.duration for e in completed_executions) / len(completed_executions) if completed_executions else 0
        
        stats = {
            "workflow_id": workflow_id,
            "period_days": days,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate_percent": round(success_rate, 2),
            "average_duration_seconds": round(avg_duration, 2),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Generated workflow stats",
            workflow_id=workflow_id,
            total_executions=total_executions,
            success_rate=success_rate
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow stats", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get workflow stats: {str(e)}")


# Error handlers
@n8n_router.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@n8n_router.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions with structured logging."""
    logger.error(
        "Unexpected exception occurred",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )