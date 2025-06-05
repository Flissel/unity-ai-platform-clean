"""Code execution endpoints for testing and running code safely."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.logging import get_logger, log_execution_time
from ...core.models import (
    CodeExecutionRequest, CodeExecutionResult, ExecutionStatus,
    Priority, BaseResponse
)
from ...core.exceptions import (
    ValidationException, CodeExecutionException, TimeoutException
)
from ...services.code_execution_service import get_code_execution_service
from ..dependencies import (
    RequireApiKey, get_current_user, User, get_pagination_params,
    PaginationParams, validate_request_size
)

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


class CodeExecutionResponse(BaseModel):
    """Response model for code execution."""
    execution_id: str
    status: ExecutionStatus
    result: Optional[CodeExecutionResult] = None
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class ExecutionListResponse(BaseModel):
    """Response model for listing executions."""
    executions: List[CodeExecutionResponse]
    total: int
    page: int
    size: int
    has_next: bool


class ExecutionStatsResponse(BaseModel):
    """Response model for execution statistics."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    languages_used: Dict[str, int]
    executions_by_status: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class CodeValidationRequest(BaseModel):
    """Request model for code validation."""
    code: str = Field(..., description="Code to validate")
    language: str = Field(..., description="Programming language")
    strict: bool = Field(default=False, description="Enable strict validation")


class CodeValidationResponse(BaseModel):
    """Response model for code validation."""
    is_valid: bool
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    security_warnings: List[str]


@router.post("/code/execute", response_model=CodeExecutionResponse)
@log_execution_time
async def execute_code(
    request: CodeExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey),
    __: bool = Depends(validate_request_size)
):
    """Execute code in a secure sandbox environment."""
    try:
        logger.info(
            f"Code execution requested: {request.language}",
            extra={
                'user': current_user.username if current_user else 'anonymous',
                'language': request.language,
                'timeout': request.timeout,
                'priority': request.priority
            }
        )
        
        # Get code execution service
        code_service = await get_code_execution_service()
        
        # Execute code
        execution_id, result = await code_service.execute_code(request)
        
        # Log execution result
        logger.info(
            f"Code execution completed: {execution_id}",
            extra={
                'execution_id': execution_id,
                'status': result.status if result else 'pending',
                'language': request.language
            }
        )
        
        # If execution is async, add background task to monitor
        if result is None or result.status == ExecutionStatus.RUNNING:
            background_tasks.add_task(
                _monitor_execution,
                code_service,
                execution_id
            )
        
        return CodeExecutionResponse(
            execution_id=execution_id,
            status=result.status if result else ExecutionStatus.PENDING,
            result=result,
            message="Code execution started" if not result else "Code execution completed",
            created_at=datetime.utcnow(),
            completed_at=result.completed_at if result and result.completed_at else None
        )
        
    except ValidationException as e:
        logger.warning(f"Code execution validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except CodeExecutionException as e:
        logger.error(f"Code execution failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except TimeoutException as e:
        logger.warning(f"Code execution timeout: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in code execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during code execution"
        )


@router.get("/code/execute/{execution_id}", response_model=CodeExecutionResponse)
async def get_execution_status(
    execution_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """Get the status and result of a code execution."""
    try:
        code_service = await get_code_execution_service()
        
        # Get execution result
        result = await code_service.get_execution_result(execution_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found"
            )
        
        return CodeExecutionResponse(
            execution_id=execution_id,
            status=result.status,
            result=result,
            message=f"Execution {result.status.value}",
            created_at=result.created_at,
            completed_at=result.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution status"
        )


@router.delete("/code/execute/{execution_id}")
async def cancel_execution(
    execution_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
) -> BaseResponse:
    """Cancel a running code execution."""
    try:
        code_service = await get_code_execution_service()
        
        success = await code_service.cancel_execution(execution_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found or cannot be cancelled"
            )
        
        logger.info(
            f"Code execution cancelled: {execution_id}",
            extra={
                'execution_id': execution_id,
                'user': current_user.username if current_user else 'anonymous'
            }
        )
        
        return BaseResponse(
            success=True,
            message=f"Execution {execution_id} cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel execution"
        )


@router.get("/code/executions", response_model=ExecutionListResponse)
async def list_executions(
    pagination: PaginationParams = Depends(get_pagination_params),
    status_filter: Optional[ExecutionStatus] = Query(None, description="Filter by execution status"),
    language_filter: Optional[str] = Query(None, description="Filter by programming language"),
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """List code executions with filtering and pagination."""
    try:
        code_service = await get_code_execution_service()
        
        # Build filters
        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if language_filter:
            filters['language'] = language_filter
        if current_user:
            filters['user'] = current_user.username
        
        # Get executions
        executions, total = await code_service.list_executions(
            offset=pagination.offset,
            limit=pagination.size,
            filters=filters,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order
        )
        
        # Convert to response format
        execution_responses = [
            CodeExecutionResponse(
                execution_id=exec_data['id'],
                status=exec_data['status'],
                result=exec_data.get('result'),
                message=exec_data.get('message', ''),
                created_at=exec_data['created_at'],
                completed_at=exec_data.get('completed_at')
            )
            for exec_data in executions
        ]
        
        has_next = (pagination.offset + pagination.size) < total
        
        return ExecutionListResponse(
            executions=execution_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list executions"
        )


@router.post("/code/validate", response_model=CodeValidationResponse)
async def validate_code(
    request: CodeValidationRequest,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """Validate code without executing it."""
    try:
        code_service = await get_code_execution_service()
        
        # Validate code
        validation_result = await code_service.validate_code(
            code=request.code,
            language=request.language,
            strict=request.strict
        )
        
        logger.info(
            f"Code validation completed: {request.language}",
            extra={
                'user': current_user.username if current_user else 'anonymous',
                'language': request.language,
                'is_valid': validation_result['is_valid'],
                'issues_count': len(validation_result.get('issues', []))
            }
        )
        
        return CodeValidationResponse(
            is_valid=validation_result['is_valid'],
            issues=validation_result.get('issues', []),
            suggestions=validation_result.get('suggestions', []),
            security_warnings=validation_result.get('security_warnings', [])
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Error validating code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate code"
        )


@router.get("/code/capabilities")
async def get_code_capabilities(
    _: bool = Depends(RequireApiKey)
) -> Dict[str, Any]:
    """Get supported languages and execution capabilities."""
    try:
        code_service = await get_code_execution_service()
        capabilities = await code_service.get_capabilities()
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get capabilities"
        )


@router.get("/code/stats", response_model=ExecutionStatsResponse)
async def get_execution_stats(
    days: int = Query(7, description="Number of days to include in stats"),
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """Get code execution statistics."""
    try:
        code_service = await get_code_execution_service()
        
        # Get usage statistics
        stats = await code_service.get_usage_stats(days=days)
        
        return ExecutionStatsResponse(
            total_executions=stats.get('total_executions', 0),
            successful_executions=stats.get('successful_executions', 0),
            failed_executions=stats.get('failed_executions', 0),
            average_execution_time=stats.get('average_execution_time', 0.0),
            languages_used=stats.get('languages_used', {}),
            executions_by_status=stats.get('executions_by_status', {}),
            recent_activity=stats.get('recent_activity', [])
        )
        
    except Exception as e:
        logger.error(f"Error getting execution stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution statistics"
        )


@router.get("/code/active")
async def get_active_executions(
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
) -> List[Dict[str, Any]]:
    """Get currently running code executions."""
    try:
        code_service = await get_code_execution_service()
        
        # Get active executions
        active_executions = await code_service.get_active_executions()
        
        # Filter by user if not admin
        if current_user and not current_user.has_role('admin'):
            active_executions = [
                exec_data for exec_data in active_executions
                if exec_data.get('user') == current_user.username
            ]
        
        return active_executions
        
    except Exception as e:
        logger.error(f"Error getting active executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active executions"
        )


# Background task for monitoring long-running executions
async def _monitor_execution(code_service, execution_id: str):
    """Monitor a long-running execution and update status."""
    try:
        # Wait for execution to complete
        result = await code_service.wait_for_completion(
            execution_id,
            timeout=300  # 5 minutes max monitoring
        )
        
        if result:
            logger.info(
                f"Monitored execution completed: {execution_id}",
                extra={
                    'execution_id': execution_id,
                    'final_status': result.status
                }
            )
        else:
            logger.warning(
                f"Monitored execution timeout: {execution_id}",
                extra={'execution_id': execution_id}
            )
            
    except Exception as e:
        logger.error(
            f"Error monitoring execution {execution_id}: {e}",
            extra={'execution_id': execution_id}
        )