"""n8n integration endpoints for workflow automation and management."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Request
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.logging import get_logger, log_execution_time
from ...core.models import (
    WorkflowDefinition, WorkflowExecution, ExecutionStatus,
    Priority, BaseResponse
)
from ...core.exceptions import (
    ValidationException, N8nException, TimeoutException,
    NotFoundException
)
from ...services.n8n_service import get_n8n_service
from ..dependencies import (
    RequireApiKey, get_current_user, User, get_pagination_params,
    PaginationParams, validate_request_size
)

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


class N8nWorkflowResponse(BaseModel):
    """Response model for n8n workflow."""
    id: str
    name: str
    active: bool
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    nodes: int = 0
    connections: int = 0
    executions_count: int = 0


class N8nExecutionResponse(BaseModel):
    """Response model for n8n execution."""
    id: str
    workflow_id: str
    status: str
    mode: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class N8nWorkflowListResponse(BaseModel):
    """Response model for listing n8n workflows."""
    workflows: List[N8nWorkflowResponse]
    total: int
    page: int
    size: int
    has_next: bool


class N8nExecutionListResponse(BaseModel):
    """Response model for listing n8n executions."""
    executions: List[N8nExecutionResponse]
    total: int
    page: int
    size: int
    has_next: bool


class N8nStatsResponse(BaseModel):
    """Response model for n8n statistics."""
    total_workflows: int
    active_workflows: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    executions_by_status: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    top_workflows: List[Dict[str, Any]]


class WorkflowExecuteRequest(BaseModel):
    """Request model for workflow execution."""
    data: Dict[str, Any] = Field(default_factory=dict, description="Input data for workflow")
    wait_till_done: bool = Field(default=False, description="Wait for execution to complete")
    timeout: int = Field(default=300, description="Execution timeout in seconds")


class WebhookTriggerRequest(BaseModel):
    """Request model for webhook trigger."""
    workflow_id: str = Field(..., description="Workflow ID to trigger")
    data: Dict[str, Any] = Field(default_factory=dict, description="Webhook payload")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")


@router.get("/n8n/workflows", response_model=N8nWorkflowListResponse)
async def list_n8n_workflows(
    pagination: PaginationParams = Depends(get_pagination_params),
    active_only: bool = Query(False, description="Show only active workflows"),
    search: Optional[str] = Query(None, description="Search in workflow names"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    _: bool = Depends(RequireApiKey)
):
    """List n8n workflows with filtering and pagination."""
    try:
        n8n_service = await get_n8n_service()
        
        # Build filters
        filters = {}
        if active_only:
            filters['active'] = True
        if search:
            filters['search'] = search
        if tags:
            filters['tags'] = [tag.strip() for tag in tags.split(',')]
        
        # Get workflows
        workflows_data = await n8n_service.list_workflows(
            offset=pagination.offset,
            limit=pagination.size,
            filters=filters
        )
        
        workflows = workflows_data.get('data', [])
        total = workflows_data.get('total', len(workflows))
        
        # Convert to response format
        workflow_responses = [
            N8nWorkflowResponse(
                id=workflow['id'],
                name=workflow['name'],
                active=workflow.get('active', False),
                tags=workflow.get('tags', []),
                created_at=datetime.fromisoformat(workflow['createdAt'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(workflow['updatedAt'].replace('Z', '+00:00')),
                nodes=len(workflow.get('nodes', [])),
                connections=len(workflow.get('connections', {})),
                executions_count=workflow.get('executionsCount', 0)
            )
            for workflow in workflows
        ]
        
        has_next = (pagination.offset + pagination.size) < total
        
        logger.info(
            f"Listed {len(workflow_responses)} n8n workflows",
            extra={
                'total': total,
                'page': pagination.page,
                'filters': filters
            }
        )
        
        return N8nWorkflowListResponse(
            workflows=workflow_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            has_next=has_next
        )
        
    except N8nException as e:
        logger.error(f"n8n service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"n8n service error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error listing n8n workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list n8n workflows"
        )


@router.get("/n8n/workflows/{workflow_id}", response_model=N8nWorkflowResponse)
async def get_n8n_workflow(
    workflow_id: str,
    _: bool = Depends(RequireApiKey)
):
    """Get a specific n8n workflow."""
    try:
        n8n_service = await get_n8n_service()
        
        workflow = await n8n_service.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"n8n workflow {workflow_id} not found"
            )
        
        return N8nWorkflowResponse(
            id=workflow['id'],
            name=workflow['name'],
            active=workflow.get('active', False),
            tags=workflow.get('tags', []),
            created_at=datetime.fromisoformat(workflow['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(workflow['updatedAt'].replace('Z', '+00:00')),
            nodes=len(workflow.get('nodes', [])),
            connections=len(workflow.get('connections', {})),
            executions_count=workflow.get('executionsCount', 0)
        )
        
    except HTTPException:
        raise
    except N8nException as e:
        logger.error(f"n8n service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"n8n service error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error getting n8n workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get n8n workflow"
        )


@router.post("/n8n/workflows/{workflow_id}/execute", response_model=N8nExecutionResponse)
@log_execution_time
async def execute_n8n_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey),
    __: bool = Depends(validate_request_size)
):
    """Execute an n8n workflow."""
    try:
        logger.info(
            f"n8n workflow execution requested: {workflow_id}",
            extra={
                'user': current_user.username if current_user else 'anonymous',
                'workflow_id': workflow_id,
                'wait_till_done': request.wait_till_done
            }
        )
        
        n8n_service = await get_n8n_service()
        
        # Execute workflow
        execution = await n8n_service.execute_workflow(
            workflow_id=workflow_id,
            data=request.data,
            wait_till_done=request.wait_till_done,
            timeout=request.timeout
        )
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to execute n8n workflow"
            )
        
        # Add background monitoring if not waiting
        if not request.wait_till_done and execution.get('status') in ['running', 'waiting']:
            background_tasks.add_task(
                _monitor_n8n_execution,
                n8n_service,
                execution['id']
            )
        
        logger.info(
            f"n8n workflow execution started: {execution['id']}",
            extra={
                'execution_id': execution['id'],
                'workflow_id': workflow_id,
                'status': execution.get('status')
            }
        )
        
        return N8nExecutionResponse(
            id=execution['id'],
            workflow_id=workflow_id,
            status=execution.get('status', 'unknown'),
            mode=execution.get('mode', 'manual'),
            started_at=datetime.fromisoformat(execution['startedAt'].replace('Z', '+00:00')),
            finished_at=(
                datetime.fromisoformat(execution['finishedAt'].replace('Z', '+00:00'))
                if execution.get('finishedAt') else None
            ),
            duration=execution.get('duration'),
            data=execution.get('data'),
            error=execution.get('error')
        )
        
    except ValidationException as e:
        logger.warning(f"n8n workflow execution validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except N8nException as e:
        logger.error(f"n8n workflow execution failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except TimeoutException as e:
        logger.warning(f"n8n workflow execution timeout: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in n8n workflow execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during n8n workflow execution"
        )


@router.get("/n8n/executions/{execution_id}", response_model=N8nExecutionResponse)
async def get_n8n_execution(
    execution_id: str,
    _: bool = Depends(RequireApiKey)
):
    """Get the status and result of an n8n execution."""
    try:
        n8n_service = await get_n8n_service()
        
        execution = await n8n_service.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"n8n execution {execution_id} not found"
            )
        
        return N8nExecutionResponse(
            id=execution['id'],
            workflow_id=execution['workflowId'],
            status=execution.get('status', 'unknown'),
            mode=execution.get('mode', 'manual'),
            started_at=datetime.fromisoformat(execution['startedAt'].replace('Z', '+00:00')),
            finished_at=(
                datetime.fromisoformat(execution['finishedAt'].replace('Z', '+00:00'))
                if execution.get('finishedAt') else None
            ),
            duration=execution.get('duration'),
            data=execution.get('data'),
            error=execution.get('error')
        )
        
    except HTTPException:
        raise
    except N8nException as e:
        logger.error(f"n8n service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"n8n service error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error getting n8n execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get n8n execution"
        )


@router.get("/n8n/executions", response_model=N8nExecutionListResponse)
async def list_n8n_executions(
    pagination: PaginationParams = Depends(get_pagination_params),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    status_filter: Optional[str] = Query(None, description="Filter by execution status"),
    _: bool = Depends(RequireApiKey)
):
    """List n8n executions with filtering and pagination."""
    try:
        n8n_service = await get_n8n_service()
        
        # Build filters
        filters = {}
        if workflow_id:
            filters['workflowId'] = workflow_id
        if status_filter:
            filters['status'] = status_filter
        
        # Get executions
        executions_data = await n8n_service.list_executions(
            offset=pagination.offset,
            limit=pagination.size,
            filters=filters
        )
        
        executions = executions_data.get('data', [])
        total = executions_data.get('total', len(executions))
        
        # Convert to response format
        execution_responses = [
            N8nExecutionResponse(
                id=execution['id'],
                workflow_id=execution['workflowId'],
                status=execution.get('status', 'unknown'),
                mode=execution.get('mode', 'manual'),
                started_at=datetime.fromisoformat(execution['startedAt'].replace('Z', '+00:00')),
                finished_at=(
                    datetime.fromisoformat(execution['finishedAt'].replace('Z', '+00:00'))
                    if execution.get('finishedAt') else None
                ),
                duration=execution.get('duration'),
                data=execution.get('data'),
                error=execution.get('error')
            )
            for execution in executions
        ]
        
        has_next = (pagination.offset + pagination.size) < total
        
        return N8nExecutionListResponse(
            executions=execution_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            has_next=has_next
        )
        
    except N8nException as e:
        logger.error(f"n8n service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"n8n service error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error listing n8n executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list n8n executions"
        )


@router.post("/n8n/webhook/{workflow_id}")
async def trigger_n8n_webhook(
    workflow_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
) -> Dict[str, Any]:
    """Trigger an n8n workflow via webhook."""
    try:
        # Get request data
        content_type = request.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            data = await request.json()
        elif 'application/x-www-form-urlencoded' in content_type:
            form_data = await request.form()
            data = dict(form_data)
        else:
            data = await request.body()
            if isinstance(data, bytes):
                try:
                    data = data.decode('utf-8')
                except UnicodeDecodeError:
                    data = str(data)
        
        logger.info(
            f"n8n webhook triggered: {workflow_id}",
            extra={
                'user': current_user.username if current_user else 'anonymous',
                'workflow_id': workflow_id,
                'content_type': content_type
            }
        )
        
        n8n_service = await get_n8n_service()
        
        # Trigger webhook
        result = await n8n_service.trigger_webhook(
            workflow_id=workflow_id,
            data=data,
            headers=dict(request.headers),
            method=request.method
        )
        
        logger.info(
            f"n8n webhook completed: {workflow_id}",
            extra={
                'workflow_id': workflow_id,
                'success': result.get('success', False)
            }
        )
        
        return result
        
    except N8nException as e:
        logger.error(f"n8n webhook failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error triggering n8n webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger n8n webhook"
        )


@router.get("/n8n/stats", response_model=N8nStatsResponse)
async def get_n8n_stats(
    days: int = Query(7, description="Number of days to include in stats"),
    _: bool = Depends(RequireApiKey)
):
    """Get n8n workflow and execution statistics."""
    try:
        n8n_service = await get_n8n_service()
        
        # Get usage statistics
        stats = await n8n_service.get_usage_stats(days=days)
        
        return N8nStatsResponse(
            total_workflows=stats.get('total_workflows', 0),
            active_workflows=stats.get('active_workflows', 0),
            total_executions=stats.get('total_executions', 0),
            successful_executions=stats.get('successful_executions', 0),
            failed_executions=stats.get('failed_executions', 0),
            average_execution_time=stats.get('average_execution_time', 0.0),
            executions_by_status=stats.get('executions_by_status', {}),
            recent_activity=stats.get('recent_activity', []),
            top_workflows=stats.get('top_workflows', [])
        )
        
    except N8nException as e:
        logger.error(f"n8n service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"n8n service error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error getting n8n stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get n8n statistics"
        )


# Background task for monitoring n8n executions
async def _monitor_n8n_execution(n8n_service, execution_id: str):
    """Monitor a long-running n8n execution."""
    try:
        # Wait for execution to complete
        result = await n8n_service.wait_for_execution_completion(
            execution_id,
            timeout=600  # 10 minutes max monitoring
        )
        
        if result:
            logger.info(
                f"Monitored n8n execution completed: {execution_id}",
                extra={
                    'execution_id': execution_id,
                    'final_status': result.get('status'),
                    'duration': result.get('duration')
                }
            )
        else:
            logger.warning(
                f"Monitored n8n execution timeout: {execution_id}",
                extra={'execution_id': execution_id}
            )
            
    except Exception as e:
        logger.error(
            f"Error monitoring n8n execution {execution_id}: {e}",
            extra={'execution_id': execution_id}
        )