"""Workflow orchestration endpoints for managing automation workflows."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.logging import get_logger, log_execution_time
from ...core.models import (
    WorkflowDefinition, WorkflowExecution, ExecutionStatus,
    Priority, BaseResponse
)
from ...core.exceptions import (
    ValidationException, WorkflowExecutionException, TimeoutException,
    NotFoundException
)
from ...services.workflow_service import get_workflow_service, WorkflowType
from ..dependencies import (
    RequireApiKey, get_current_user, User, get_pagination_params,
    PaginationParams, validate_request_size
)

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution."""
    workflow_id: str = Field(..., description="Workflow ID to execute")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters")
    priority: Priority = Field(default=Priority.MEDIUM, description="Execution priority")
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    steps_completed: int = 0
    total_steps: int = 0


class WorkflowListResponse(BaseModel):
    """Response model for listing workflows."""
    workflows: List[WorkflowDefinition]
    total: int
    page: int
    size: int
    has_next: bool


class WorkflowExecutionListResponse(BaseModel):
    """Response model for listing workflow executions."""
    executions: List[WorkflowExecutionResponse]
    total: int
    page: int
    size: int
    has_next: bool


class WorkflowStatsResponse(BaseModel):
    """Response model for workflow statistics."""
    total_workflows: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    workflows_by_type: Dict[str, int]
    executions_by_status: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    top_workflows: List[Dict[str, Any]]


class WorkflowValidationRequest(BaseModel):
    """Request model for workflow validation."""
    definition: WorkflowDefinition
    strict: bool = Field(default=False, description="Enable strict validation")


class WorkflowValidationResponse(BaseModel):
    """Response model for workflow validation."""
    is_valid: bool
    issues: List[Dict[str, Any]]
    warnings: List[str]
    suggestions: List[str]
    estimated_duration: Optional[float] = None


@router.post("/workflows/execute", response_model=WorkflowExecutionResponse)
@log_execution_time
async def execute_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey),
    __: bool = Depends(validate_request_size)
):
    """Execute a workflow with the given parameters."""
    try:
        logger.info(
            f"Workflow execution requested: {request.workflow_id}",
            extra={
                'user': current_user.username if current_user else 'anonymous',
                'workflow_id': request.workflow_id,
                'priority': request.priority,
                'timeout': request.timeout
            }
        )
        
        # Get workflow service
        workflow_service = await get_workflow_service()
        
        # Execute workflow
        execution_id = await workflow_service.execute_workflow(
            workflow_id=request.workflow_id,
            inputs=request.inputs,
            priority=request.priority,
            timeout=request.timeout,
            metadata={
                **request.metadata,
                'user': current_user.username if current_user else 'anonymous'
            }
        )
        
        # Get initial execution status
        execution = await workflow_service.get_workflow_execution(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create workflow execution"
            )
        
        # Add background task to monitor long-running workflows
        if execution.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            background_tasks.add_task(
                _monitor_workflow_execution,
                workflow_service,
                execution_id
            )
        
        logger.info(
            f"Workflow execution started: {execution_id}",
            extra={
                'execution_id': execution_id,
                'workflow_id': request.workflow_id,
                'status': execution.status
            }
        )
        
        return WorkflowExecutionResponse(
            execution_id=execution_id,
            workflow_id=request.workflow_id,
            status=execution.status,
            result=execution.result,
            error=execution.error,
            message="Workflow execution started",
            created_at=execution.created_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration=execution.duration,
            steps_completed=execution.steps_completed or 0,
            total_steps=execution.total_steps or 0
        )
        
    except ValidationException as e:
        logger.warning(f"Workflow execution validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except NotFoundException as e:
        logger.warning(f"Workflow not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except WorkflowExecutionException as e:
        logger.error(f"Workflow execution failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in workflow execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during workflow execution"
        )


@router.get("/workflows/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_workflow_execution(
    execution_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """Get the status and result of a workflow execution."""
    try:
        workflow_service = await get_workflow_service()
        
        execution = await workflow_service.get_workflow_execution(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow execution {execution_id} not found"
            )
        
        # Check access permissions
        if (current_user and 
            not current_user.has_role('admin') and 
            execution.metadata.get('user') != current_user.username):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workflow execution"
            )
        
        return WorkflowExecutionResponse(
            execution_id=execution_id,
            workflow_id=execution.workflow_id,
            status=execution.status,
            result=execution.result,
            error=execution.error,
            message=f"Execution {execution.status.value}",
            created_at=execution.created_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration=execution.duration,
            steps_completed=execution.steps_completed or 0,
            total_steps=execution.total_steps or 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow execution"
        )


@router.delete("/workflows/executions/{execution_id}")
async def cancel_workflow_execution(
    execution_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
) -> BaseResponse:
    """Cancel a running workflow execution."""
    try:
        workflow_service = await get_workflow_service()
        
        # Check if execution exists and user has permission
        execution = await workflow_service.get_workflow_execution(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow execution {execution_id} not found"
            )
        
        if (current_user and 
            not current_user.has_role('admin') and 
            execution.metadata.get('user') != current_user.username):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to cancel this workflow execution"
            )
        
        success = await workflow_service.cancel_workflow_execution(execution_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow execution {execution_id} cannot be cancelled"
            )
        
        logger.info(
            f"Workflow execution cancelled: {execution_id}",
            extra={
                'execution_id': execution_id,
                'user': current_user.username if current_user else 'anonymous'
            }
        )
        
        return BaseResponse(
            success=True,
            message=f"Workflow execution {execution_id} cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling workflow execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel workflow execution"
        )


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    pagination: PaginationParams = Depends(get_pagination_params),
    workflow_type: Optional[WorkflowType] = Query(None, description="Filter by workflow type"),
    search: Optional[str] = Query(None, description="Search in workflow names and descriptions"),
    _: bool = Depends(RequireApiKey)
):
    """List available workflows with filtering and pagination."""
    try:
        workflow_service = await get_workflow_service()
        
        # Build filters
        filters = {}
        if workflow_type:
            filters['type'] = workflow_type
        if search:
            filters['search'] = search
        
        # Get workflows
        workflows, total = await workflow_service.list_workflows(
            offset=pagination.offset,
            limit=pagination.size,
            filters=filters,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order
        )
        
        has_next = (pagination.offset + pagination.size) < total
        
        return WorkflowListResponse(
            workflows=workflows,
            total=total,
            page=pagination.page,
            size=pagination.size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list workflows"
        )


@router.get("/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(
    workflow_id: str,
    _: bool = Depends(RequireApiKey)
):
    """Get a specific workflow definition."""
    try:
        workflow_service = await get_workflow_service()
        
        workflow = await workflow_service.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return workflow
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow"
        )


@router.get("/workflows/executions", response_model=WorkflowExecutionListResponse)
async def list_workflow_executions(
    pagination: PaginationParams = Depends(get_pagination_params),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    status_filter: Optional[ExecutionStatus] = Query(None, description="Filter by execution status"),
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """List workflow executions with filtering and pagination."""
    try:
        workflow_service = await get_workflow_service()
        
        # Build filters
        filters = {}
        if workflow_id:
            filters['workflow_id'] = workflow_id
        if status_filter:
            filters['status'] = status_filter
        if current_user and not current_user.has_role('admin'):
            filters['user'] = current_user.username
        
        # Get executions
        executions, total = await workflow_service.list_workflow_executions(
            offset=pagination.offset,
            limit=pagination.size,
            filters=filters,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order
        )
        
        # Convert to response format
        execution_responses = [
            WorkflowExecutionResponse(
                execution_id=exec_data.execution_id,
                workflow_id=exec_data.workflow_id,
                status=exec_data.status,
                result=exec_data.result,
                error=exec_data.error,
                message=f"Execution {exec_data.status.value}",
                created_at=exec_data.created_at,
                started_at=exec_data.started_at,
                completed_at=exec_data.completed_at,
                duration=exec_data.duration,
                steps_completed=exec_data.steps_completed or 0,
                total_steps=exec_data.total_steps or 0
            )
            for exec_data in executions
        ]
        
        has_next = (pagination.offset + pagination.size) < total
        
        return WorkflowExecutionListResponse(
            executions=execution_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Error listing workflow executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list workflow executions"
        )


@router.post("/workflows/validate", response_model=WorkflowValidationResponse)
async def validate_workflow(
    request: WorkflowValidationRequest,
    _: bool = Depends(RequireApiKey)
):
    """Validate a workflow definition without executing it."""
    try:
        workflow_service = await get_workflow_service()
        
        # Validate workflow
        validation_result = await workflow_service.validate_workflow(
            definition=request.definition,
            strict=request.strict
        )
        
        logger.info(
            f"Workflow validation completed: {request.definition.name}",
            extra={
                'workflow_name': request.definition.name,
                'is_valid': validation_result['is_valid'],
                'issues_count': len(validation_result.get('issues', []))
            }
        )
        
        return WorkflowValidationResponse(
            is_valid=validation_result['is_valid'],
            issues=validation_result.get('issues', []),
            warnings=validation_result.get('warnings', []),
            suggestions=validation_result.get('suggestions', []),
            estimated_duration=validation_result.get('estimated_duration')
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error validating workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate workflow"
        )


@router.get("/workflows/templates")
async def get_workflow_templates(
    workflow_type: Optional[WorkflowType] = Query(None, description="Filter by workflow type"),
    _: bool = Depends(RequireApiKey)
) -> List[Dict[str, Any]]:
    """Get available workflow templates."""
    try:
        workflow_service = await get_workflow_service()
        
        templates = await workflow_service.get_workflow_templates(
            workflow_type=workflow_type
        )
        
        return templates
        
    except Exception as e:
        logger.error(f"Error getting workflow templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow templates"
        )


@router.get("/workflows/stats", response_model=WorkflowStatsResponse)
async def get_workflow_stats(
    days: int = Query(7, description="Number of days to include in stats"),
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """Get workflow execution statistics."""
    try:
        workflow_service = await get_workflow_service()
        
        # Get usage statistics
        stats = await workflow_service.get_usage_stats(days=days)
        
        return WorkflowStatsResponse(
            total_workflows=stats.get('total_workflows', 0),
            total_executions=stats.get('total_executions', 0),
            successful_executions=stats.get('successful_executions', 0),
            failed_executions=stats.get('failed_executions', 0),
            average_execution_time=stats.get('average_execution_time', 0.0),
            workflows_by_type=stats.get('workflows_by_type', {}),
            executions_by_status=stats.get('executions_by_status', {}),
            recent_activity=stats.get('recent_activity', []),
            top_workflows=stats.get('top_workflows', [])
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow statistics"
        )


@router.get("/workflows/active")
async def get_active_workflows(
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
) -> List[Dict[str, Any]]:
    """Get currently running workflow executions."""
    try:
        workflow_service = await get_workflow_service()
        
        # Get active workflows
        active_workflows = await workflow_service.get_active_workflows()
        
        # Filter by user if not admin
        if current_user and not current_user.has_role('admin'):
            active_workflows = [
                workflow_data for workflow_data in active_workflows
                if workflow_data.get('metadata', {}).get('user') == current_user.username
            ]
        
        return active_workflows
        
    except Exception as e:
        logger.error(f"Error getting active workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active workflows"
        )


# Background task for monitoring long-running workflow executions
async def _monitor_workflow_execution(workflow_service, execution_id: str):
    """Monitor a long-running workflow execution and update status."""
    try:
        # Wait for execution to complete
        execution = await workflow_service.wait_for_completion(
            execution_id,
            timeout=600  # 10 minutes max monitoring
        )
        
        if execution:
            logger.info(
                f"Monitored workflow execution completed: {execution_id}",
                extra={
                    'execution_id': execution_id,
                    'final_status': execution.status,
                    'duration': execution.duration
                }
            )
        else:
            logger.warning(
                f"Monitored workflow execution timeout: {execution_id}",
                extra={'execution_id': execution_id}
            )
            
    except Exception as e:
        logger.error(
            f"Error monitoring workflow execution {execution_id}: {e}",
            extra={'execution_id': execution_id}
        )