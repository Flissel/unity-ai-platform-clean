#!/usr/bin/env python3
"""
API Endpoints for Workflow Automation Module

Provides FastAPI endpoints for workflow management, execution,
and monitoring within the n8n API Playground.

Author: UnityAI Team
Version: 1.0.0
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core import PlaygroundManager
from .workflow_manager import WorkflowManager
from .models import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    ExecuteWorkflowRequest,
    WorkflowListResponse,
    Workflow,
    WorkflowExecution,
    ExecutionListResponse,
    WorkflowStatsResponse,
    WorkflowStatus,
    ExecutionStatus
)
from .validators import WorkflowValidator
from .n8n_api_endpoints import n8n_router

# Setup structured logging
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter(
    prefix="/workflow-automation",
    tags=["Workflow Automation"],
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)

# Include n8n integration endpoints
router.include_router(n8n_router, prefix="", tags=["n8n Integration"])


# Dependency injection
async def get_workflow_manager() -> WorkflowManager:
    """Get workflow manager instance."""
    # This would be injected from the main application
    # For now, we'll create a new instance
    manager = WorkflowManager()
    await manager.start()
    return manager


async def get_playground_manager() -> PlaygroundManager:
    """Get playground manager instance."""
    # This would be injected from the main application
    from ...config import Config
    from ...core.config import PlaygroundConfig
    app_config = Config()
    config = PlaygroundConfig(n8n_config=app_config.n8n_api)
    manager = PlaygroundManager(config)
    await manager.start()
    return manager


# Error response models
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str
    validation_errors: List[str]
    timestamp: datetime = datetime.utcnow()


# Workflow Management Endpoints
@router.post(
    "/workflows",
    response_model=Workflow,
    status_code=201,
    summary="Create a new workflow",
    description="Create a new workflow from a template with custom parameters."
)
async def create_workflow(
    request: CreateWorkflowRequest,
    background_tasks: BackgroundTasks,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Workflow:
    """Create a new workflow."""
    
    try:
        logger.info(
            "Creating workflow",
            name=request.name,
            template_name=request.template_name
        )
        
        # Create workflow
        workflow = await workflow_manager.create_workflow(
            name=request.name,
            template_name=request.template_name,
            parameters=request.parameters or {},
            description=request.description,
            tags=request.tags or [],
            schedule=request.schedule
        )
        
        # Schedule background validation if needed
        if request.validate_on_create:
            background_tasks.add_task(
                _validate_workflow_background,
                workflow_manager,
                workflow.id
            )
        
        logger.info(
            "Workflow created successfully",
            workflow_id=workflow.id,
            name=workflow.name
        )
        
        return workflow
    
    except ValueError as e:
        logger.error("Workflow creation validation error", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
    
    except Exception as e:
        logger.error("Workflow creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create workflow")


@router.get(
    "/workflows",
    response_model=WorkflowListResponse,
    summary="List workflows",
    description="Get a paginated list of workflows with optional filtering."
)
async def list_workflows(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    template_name: Optional[str] = Query(None, description="Filter by template name"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowListResponse:
    """List workflows with filtering and pagination."""
    
    try:
        logger.debug(
            "Listing workflows",
            page=page,
            page_size=page_size,
            status=status,
            template_name=template_name
        )
        
        # Build filters
        filters = {}
        if status:
            filters['status'] = status
        if template_name:
            filters['template_name'] = template_name
        if tags:
            filters['tags'] = tags
        if search:
            filters['search'] = search
        
        # Get workflows
        workflows, total = await workflow_manager.list_workflows(
            page=page,
            page_size=page_size,
            filters=filters
        )
        
        return WorkflowListResponse(
            workflows=[WorkflowResponse.from_workflow(w) for w in workflows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    
    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list workflows")


@router.get(
    "/workflows/{workflow_id}",
    response_model=Workflow,
    summary="Get workflow details",
    description="Get detailed information about a specific workflow."
)
async def get_workflow(
    workflow_id: UUID,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Workflow:
    """Get workflow by ID."""
    
    try:
        workflow = await workflow_manager.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return workflow
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get workflow")


@router.put(
    "/workflows/{workflow_id}",
    response_model=Workflow,
    summary="Update workflow",
    description="Update workflow configuration and parameters."
)
async def update_workflow(
    workflow_id: UUID,
    request: UpdateWorkflowRequest,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Workflow:
    """Update workflow."""
    
    try:
        logger.info("Updating workflow", workflow_id=workflow_id)
        
        # Check if workflow exists
        existing_workflow = await workflow_manager.get_workflow(workflow_id)
        if not existing_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update workflow
        workflow = await workflow_manager.update_workflow(
            workflow_id=workflow_id,
            name=request.name,
            description=request.description,
            parameters=request.parameters,
            tags=request.tags,
            schedule=request.schedule,
            status=request.status
        )
        
        logger.info("Workflow updated successfully", workflow_id=workflow_id)
        
        return workflow
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Workflow update validation error", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Failed to update workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update workflow")


@router.delete(
    "/workflows/{workflow_id}",
    status_code=204,
    summary="Delete workflow",
    description="Delete a workflow and all its executions."
)
async def delete_workflow(
    workflow_id: UUID,
    force: bool = Query(False, description="Force delete even if executions are running"),
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
):
    """Delete workflow."""
    
    try:
        logger.info("Deleting workflow", workflow_id=workflow_id, force=force)
        
        # Check if workflow exists
        existing_workflow = await workflow_manager.get_workflow(workflow_id)
        if not existing_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Delete workflow
        await workflow_manager.delete_workflow(workflow_id, force=force)
        
        logger.info("Workflow deleted successfully", workflow_id=workflow_id)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Workflow deletion validation error", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete workflow")


# Workflow Execution Endpoints
@router.post(
    "/workflows/{workflow_id}/execute",
    response_model=WorkflowExecution,
    status_code=202,
    summary="Execute workflow",
    description="Start execution of a workflow with optional parameter overrides."
)
async def execute_workflow(
    workflow_id: UUID,
    request: ExecuteWorkflowRequest,
    background_tasks: BackgroundTasks,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowExecution:
    """Execute workflow."""
    
    try:
        logger.info(
            "Executing workflow",
            workflow_id=workflow_id,
            async_execution=request.async_execution
        )
        
        # Check if workflow exists
        workflow = await workflow_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Execute workflow
        execution = await workflow_manager.execute_workflow(
            workflow_id=workflow_id,
            parameters=request.parameters or {},
            async_execution=request.async_execution,
            webhook_url=request.webhook_url
        )
        
        # If synchronous execution, wait for completion
        if not request.async_execution:
            execution = await workflow_manager.wait_for_execution(
                execution.id,
                timeout=request.timeout or 300
            )
        
        logger.info(
            "Workflow execution started",
            workflow_id=workflow_id,
            execution_id=execution.id
        )
        
        return WorkflowExecutionResponse.from_execution(execution)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Workflow execution validation error", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to execute workflow",
            workflow_id=workflow_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to execute workflow")


@router.get(
    "/workflows/{workflow_id}/executions",
    response_model=ExecutionListResponse,
    summary="List workflow executions",
    description="Get a paginated list of executions for a specific workflow."
)
async def list_workflow_executions(
    workflow_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[ExecutionStatus] = Query(None, description="Filter by status"),
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> ExecutionListResponse:
    """List executions for a workflow."""
    
    try:
        # Check if workflow exists
        workflow = await workflow_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Build filters
        filters = {'workflow_id': workflow_id}
        if status:
            filters['status'] = status
        
        # Get executions
        executions, total = await workflow_manager.list_executions(
            page=page,
            page_size=page_size,
            filters=filters
        )
        
        return WorkflowExecutionListResponse(
            executions=[WorkflowExecutionResponse.from_execution(e) for e in executions],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list workflow executions",
            workflow_id=workflow_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to list executions")


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecution,
    summary="Get execution details",
    description="Get detailed information about a specific execution."
)
async def get_execution(
    execution_id: UUID,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowExecution:
    """Get execution by ID."""
    
    try:
        execution = await workflow_manager.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return WorkflowExecutionResponse.from_execution(execution)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get execution", execution_id=execution_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get execution")


@router.post(
    "/executions/{execution_id}/cancel",
    response_model=WorkflowExecution,
    summary="Cancel execution",
    description="Cancel a running workflow execution."
)
async def cancel_execution(
    execution_id: UUID,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowExecution:
    """Cancel execution."""
    
    try:
        logger.info("Cancelling execution", execution_id=execution_id)
        
        # Check if execution exists
        execution = await workflow_manager.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Cancel execution
        execution = await workflow_manager.cancel_execution(execution_id)
        
        logger.info("Execution cancelled", execution_id=execution_id)
        
        return WorkflowExecutionResponse.from_execution(execution)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Execution cancellation validation error", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Failed to cancel execution", execution_id=execution_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to cancel execution")


# Statistics and Monitoring Endpoints
@router.get(
    "/workflows/{workflow_id}/stats",
    response_model=WorkflowStatsResponse,
    summary="Get workflow statistics",
    description="Get execution statistics and metrics for a workflow."
)
async def get_workflow_stats(
    workflow_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> WorkflowStatsResponse:
    """Get workflow statistics."""
    
    try:
        # Check if workflow exists
        workflow = await workflow_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get statistics
        stats = await workflow_manager.get_workflow_stats(workflow_id, days=days)
        
        return WorkflowStatsResponse.from_stats(stats)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get workflow stats",
            workflow_id=workflow_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get workflow statistics")


@router.get(
    "/health",
    summary="Health check",
    description="Check the health status of the workflow automation module."
)
async def health_check(
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """Health check endpoint."""
    
    try:
        # Check workflow manager health
        manager_health = await workflow_manager.health_check()
        
        return {
            "status": "healthy" if manager_health else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "module": "workflow_automation",
            "version": "1.0.0",
            "manager_health": manager_health
        }
    
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "module": "workflow_automation",
            "version": "1.0.0",
            "error": str(e)
        }


# Template Management Endpoints
@router.get(
    "/templates",
    summary="List workflow templates",
    description="Get a list of available workflow templates."
)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """List available workflow templates."""
    
    try:
        templates = await workflow_manager.list_templates(category=category)
        
        return {
            "templates": [
                {
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "version": template.version,
                    "parameters": [
                        {
                            "name": param.name,
                            "type": param.type.value,
                            "required": param.required,
                            "description": param.description
                        }
                        for param in template.parameters
                    ]
                }
                for template in templates
            ],
            "total": len(templates)
        }
    
    except Exception as e:
        logger.error("Failed to list templates", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list templates")


@router.get(
    "/templates/{template_name}",
    summary="Get template details",
    description="Get detailed information about a specific template."
)
async def get_template(
    template_name: str,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """Get template by name."""
    
    try:
        template = await workflow_manager.get_template(template_name)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "version": template.version,
            "author": template.author,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type.value,
                    "required": param.required,
                    "description": param.description,
                    "default": param.default,
                    "validation": param.validation.dict() if param.validation else None
                }
                for param in template.parameters
            ],
            "tags": template.tags,
            "template_data": template.template_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get template", template_name=template_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get template")


# Background tasks
async def _validate_workflow_background(
    workflow_manager: WorkflowManager,
    workflow_id: UUID
):
    """Background task to validate workflow."""
    
    try:
        logger.info("Starting background workflow validation", workflow_id=workflow_id)
        
        workflow = await workflow_manager.get_workflow(workflow_id)
        if not workflow:
            logger.warning("Workflow not found for validation", workflow_id=workflow_id)
            return
        
        # Validate workflow
        validator = WorkflowValidator()
        result = await validator.validate_workflow(workflow)
        
        if not result.valid:
            logger.warning(
                "Workflow validation failed",
                workflow_id=workflow_id,
                errors=result.errors
            )
            # Could update workflow status or send notification
        else:
            logger.info("Workflow validation passed", workflow_id=workflow_id)
    
    except Exception as e:
        logger.error(
            "Background workflow validation failed",
            workflow_id=workflow_id,
            error=str(e)
        )


# Error handlers
# Note: Exception handlers should be added at the app level, not router level