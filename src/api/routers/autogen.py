"""AutoGen AI agent endpoints for multi-agent conversations and automation."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.logging import get_logger, log_execution_time
from ...core.models import (
    AgentRequest, AgentResponse, ExecutionStatus,
    Priority, BaseResponse
)
from ...core.exceptions import (
    ValidationException, AutoGenException, TimeoutException,
    NotFoundException
)
from ...services.autogen_service import get_autogen_service
from ..dependencies import (
    RequireApiKey, get_current_user, User, get_pagination_params,
    PaginationParams, validate_request_size
)

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


class AgentExecutionRequest(BaseModel):
    """Request model for agent execution."""
    agent_type: str = Field(..., description="Type of agent to execute")
    task: str = Field(..., description="Task description for the agent")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    priority: Priority = Field(default=Priority.MEDIUM, description="Execution priority")
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    max_iterations: int = Field(default=10, description="Maximum conversation iterations")
    temperature: float = Field(default=0.7, description="LLM temperature setting")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentExecutionResponse(BaseModel):
    """Response model for agent execution."""
    execution_id: str
    agent_type: str
    status: ExecutionStatus
    result: Optional[AgentResponse] = None
    error: Optional[str] = None
    message: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    iterations_completed: int = 0
    max_iterations: int = 0


class ConversationRequest(BaseModel):
    """Request model for multi-agent conversation."""
    agents: List[str] = Field(..., description="List of agent types to include")
    initial_message: str = Field(..., description="Initial message to start conversation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")
    max_rounds: int = Field(default=5, description="Maximum conversation rounds")
    timeout: int = Field(default=600, description="Total conversation timeout")
    temperature: float = Field(default=0.7, description="LLM temperature setting")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConversationResponse(BaseModel):
    """Response model for multi-agent conversation."""
    conversation_id: str
    status: ExecutionStatus
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    rounds_completed: int = 0
    max_rounds: int = 0


class AgentListResponse(BaseModel):
    """Response model for listing agent executions."""
    executions: List[AgentExecutionResponse]
    total: int
    page: int
    size: int
    has_next: bool


class AgentStatsResponse(BaseModel):
    """Response model for agent statistics."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    agents_by_type: Dict[str, int]
    executions_by_status: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    top_agents: List[Dict[str, Any]]


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    code: str = Field(..., description="Code to analyze")
    language: str = Field(..., description="Programming language")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")
    include_suggestions: bool = Field(default=True, description="Include improvement suggestions")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis."""
    analysis_id: str
    status: ExecutionStatus
    analysis: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    completed_at: Optional[datetime] = None


@router.post("/agents/execute", response_model=AgentExecutionResponse)
@log_execution_time
async def execute_agent(
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey),
    __: bool = Depends(validate_request_size)
):
    """Execute an AI agent with the given task."""
    try:
        logger.info(
            f"Agent execution requested: {request.agent_type}",
            extra={
                'user': current_user.username if current_user else 'anonymous',
                'agent_type': request.agent_type,
                'priority': request.priority,
                'timeout': request.timeout
            }
        )
        
        # Get AutoGen service
        autogen_service = await get_autogen_service()
        
        # Create agent request
        agent_request = AgentRequest(
            agent_type=request.agent_type,
            task=request.task,
            context=request.context,
            priority=request.priority,
            timeout=request.timeout,
            max_iterations=request.max_iterations,
            temperature=request.temperature,
            metadata={
                **request.metadata,
                'user': current_user.username if current_user else 'anonymous'
            }
        )
        
        # Execute agent
        execution_id, response = await autogen_service.execute_agent(agent_request)
        
        # Log execution result
        logger.info(
            f"Agent execution started: {execution_id}",
            extra={
                'execution_id': execution_id,
                'agent_type': request.agent_type,
                'status': response.status if response else 'pending'
            }
        )
        
        # Add background task to monitor long-running executions
        if response is None or response.status == ExecutionStatus.RUNNING:
            background_tasks.add_task(
                _monitor_agent_execution,
                autogen_service,
                execution_id
            )
        
        return AgentExecutionResponse(
            execution_id=execution_id,
            agent_type=request.agent_type,
            status=response.status if response else ExecutionStatus.PENDING,
            result=response,
            message="Agent execution started" if not response else "Agent execution completed",
            created_at=datetime.utcnow(),
            started_at=response.created_at if response else None,
            completed_at=response.completed_at if response else None,
            duration=response.duration if response else None,
            iterations_completed=response.iterations_completed if response else 0,
            max_iterations=request.max_iterations
        )
        
    except ValidationException as e:
        logger.warning(f"Agent execution validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except AutoGenException as e:
        logger.error(f"Agent execution failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except TimeoutException as e:
        logger.warning(f"Agent execution timeout: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in agent execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during agent execution"
        )


@router.get("/agents/executions/{execution_id}", response_model=AgentExecutionResponse)
async def get_agent_execution(
    execution_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """Get the status and result of an agent execution."""
    try:
        autogen_service = await get_autogen_service()
        
        execution = await autogen_service.get_execution_result(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent execution {execution_id} not found"
            )
        
        # Check access permissions
        if (current_user and 
            not current_user.has_role('admin') and 
            execution.get('metadata', {}).get('user') != current_user.username):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this agent execution"
            )
        
        return AgentExecutionResponse(
            execution_id=execution_id,
            agent_type=execution.get('agent_type', ''),
            status=execution.get('status', ExecutionStatus.UNKNOWN),
            result=execution.get('result'),
            error=execution.get('error'),
            message=f"Execution {execution.get('status', 'unknown')}",
            created_at=execution.get('created_at', datetime.utcnow()),
            started_at=execution.get('started_at'),
            completed_at=execution.get('completed_at'),
            duration=execution.get('duration'),
            iterations_completed=execution.get('iterations_completed', 0),
            max_iterations=execution.get('max_iterations', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent execution"
        )


@router.post("/agents/conversation", response_model=ConversationResponse)
@log_execution_time
async def start_conversation(
    request: ConversationRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey),
    __: bool = Depends(validate_request_size)
):
    """Start a multi-agent conversation."""
    try:
        logger.info(
            f"Multi-agent conversation requested: {request.agents}",
            extra={
                'user': current_user.username if current_user else 'anonymous',
                'agents': request.agents,
                'max_rounds': request.max_rounds
            }
        )
        
        autogen_service = await get_autogen_service()
        
        # Start conversation
        conversation_id = await autogen_service.start_conversation(
            agents=request.agents,
            initial_message=request.initial_message,
            context=request.context,
            max_rounds=request.max_rounds,
            timeout=request.timeout,
            temperature=request.temperature,
            metadata={
                **request.metadata,
                'user': current_user.username if current_user else 'anonymous'
            }
        )
        
        # Add background task to monitor conversation
        background_tasks.add_task(
            _monitor_conversation,
            autogen_service,
            conversation_id
        )
        
        logger.info(
            f"Multi-agent conversation started: {conversation_id}",
            extra={
                'conversation_id': conversation_id,
                'agents': request.agents
            }
        )
        
        return ConversationResponse(
            conversation_id=conversation_id,
            status=ExecutionStatus.RUNNING,
            created_at=datetime.utcnow(),
            max_rounds=request.max_rounds
        )
        
    except ValidationException as e:
        logger.warning(f"Conversation validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except AutoGenException as e:
        logger.error(f"Conversation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during conversation"
        )


@router.get("/agents/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """Get the status and messages of a conversation."""
    try:
        autogen_service = await get_autogen_service()
        
        conversation = await autogen_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Check access permissions
        if (current_user and 
            not current_user.has_role('admin') and 
            conversation.get('metadata', {}).get('user') != current_user.username):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )
        
        return ConversationResponse(
            conversation_id=conversation_id,
            status=conversation.get('status', ExecutionStatus.UNKNOWN),
            messages=conversation.get('messages', []),
            summary=conversation.get('summary'),
            decisions=conversation.get('decisions', []),
            created_at=conversation.get('created_at', datetime.utcnow()),
            completed_at=conversation.get('completed_at'),
            duration=conversation.get('duration'),
            rounds_completed=conversation.get('rounds_completed', 0),
            max_rounds=conversation.get('max_rounds', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )


@router.post("/agents/analyze-code", response_model=CodeAnalysisResponse)
@log_execution_time
async def analyze_code(
    request: CodeAnalysisRequest,
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey),
    __: bool = Depends(validate_request_size)
):
    """Analyze code using AI agents."""
    try:
        logger.info(
            f"Code analysis requested: {request.language}",
            extra={
                'user': current_user.username if current_user else 'anonymous',
                'language': request.language,
                'analysis_type': request.analysis_type
            }
        )
        
        autogen_service = await get_autogen_service()
        
        # Analyze code
        analysis_id, result = await autogen_service.analyze_code(
            code=request.code,
            language=request.language,
            analysis_type=request.analysis_type,
            include_suggestions=request.include_suggestions,
            context=request.context
        )
        
        logger.info(
            f"Code analysis completed: {analysis_id}",
            extra={
                'analysis_id': analysis_id,
                'language': request.language,
                'status': result.get('status', 'completed')
            }
        )
        
        return CodeAnalysisResponse(
            analysis_id=analysis_id,
            status=result.get('status', ExecutionStatus.COMPLETED),
            analysis=result.get('analysis'),
            suggestions=result.get('suggestions', []),
            issues=result.get('issues', []),
            metrics=result.get('metrics', {}),
            created_at=datetime.utcnow(),
            completed_at=result.get('completed_at', datetime.utcnow())
        )
        
    except ValidationException as e:
        logger.warning(f"Code analysis validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except AutoGenException as e:
        logger.error(f"Code analysis failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in code analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during code analysis"
        )


@router.get("/agents/executions", response_model=AgentListResponse)
async def list_agent_executions(
    pagination: PaginationParams = Depends(get_pagination_params),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status_filter: Optional[ExecutionStatus] = Query(None, description="Filter by execution status"),
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """List agent executions with filtering and pagination."""
    try:
        autogen_service = await get_autogen_service()
        
        # Build filters
        filters = {}
        if agent_type:
            filters['agent_type'] = agent_type
        if status_filter:
            filters['status'] = status_filter
        if current_user and not current_user.has_role('admin'):
            filters['user'] = current_user.username
        
        # Get executions
        executions, total = await autogen_service.list_executions(
            offset=pagination.offset,
            limit=pagination.size,
            filters=filters,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order
        )
        
        # Convert to response format
        execution_responses = [
            AgentExecutionResponse(
                execution_id=exec_data['id'],
                agent_type=exec_data.get('agent_type', ''),
                status=exec_data.get('status', ExecutionStatus.UNKNOWN),
                result=exec_data.get('result'),
                error=exec_data.get('error'),
                message=f"Execution {exec_data.get('status', 'unknown')}",
                created_at=exec_data.get('created_at', datetime.utcnow()),
                started_at=exec_data.get('started_at'),
                completed_at=exec_data.get('completed_at'),
                duration=exec_data.get('duration'),
                iterations_completed=exec_data.get('iterations_completed', 0),
                max_iterations=exec_data.get('max_iterations', 0)
            )
            for exec_data in executions
        ]
        
        has_next = (pagination.offset + pagination.size) < total
        
        return AgentListResponse(
            executions=execution_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Error listing agent executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agent executions"
        )


@router.get("/agents/capabilities")
async def get_agent_capabilities(
    _: bool = Depends(RequireApiKey)
) -> Dict[str, Any]:
    """Get available agent types and their capabilities."""
    try:
        autogen_service = await get_autogen_service()
        capabilities = await autogen_service.get_capabilities()
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent capabilities"
        )


@router.get("/agents/stats", response_model=AgentStatsResponse)
async def get_agent_stats(
    days: int = Query(7, description="Number of days to include in stats"),
    current_user: Optional[User] = Depends(get_current_user),
    _: bool = Depends(RequireApiKey)
):
    """Get agent execution statistics."""
    try:
        autogen_service = await get_autogen_service()
        
        # Get usage statistics
        stats = await autogen_service.get_usage_stats(days=days)
        
        return AgentStatsResponse(
            total_executions=stats.get('total_executions', 0),
            successful_executions=stats.get('successful_executions', 0),
            failed_executions=stats.get('failed_executions', 0),
            average_execution_time=stats.get('average_execution_time', 0.0),
            agents_by_type=stats.get('agents_by_type', {}),
            executions_by_status=stats.get('executions_by_status', {}),
            recent_activity=stats.get('recent_activity', []),
            top_agents=stats.get('top_agents', [])
        )
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent statistics"
        )


# Background tasks for monitoring
async def _monitor_agent_execution(autogen_service, execution_id: str):
    """Monitor a long-running agent execution."""
    try:
        result = await autogen_service.wait_for_completion(
            execution_id,
            timeout=300  # 5 minutes max monitoring
        )
        
        if result:
            logger.info(
                f"Monitored agent execution completed: {execution_id}",
                extra={
                    'execution_id': execution_id,
                    'final_status': result.get('status')
                }
            )
        else:
            logger.warning(
                f"Monitored agent execution timeout: {execution_id}",
                extra={'execution_id': execution_id}
            )
            
    except Exception as e:
        logger.error(
            f"Error monitoring agent execution {execution_id}: {e}",
            extra={'execution_id': execution_id}
        )


async def _monitor_conversation(autogen_service, conversation_id: str):
    """Monitor a multi-agent conversation."""
    try:
        result = await autogen_service.wait_for_conversation_completion(
            conversation_id,
            timeout=600  # 10 minutes max monitoring
        )
        
        if result:
            logger.info(
                f"Monitored conversation completed: {conversation_id}",
                extra={
                    'conversation_id': conversation_id,
                    'final_status': result.get('status'),
                    'rounds_completed': result.get('rounds_completed', 0)
                }
            )
        else:
            logger.warning(
                f"Monitored conversation timeout: {conversation_id}",
                extra={'conversation_id': conversation_id}
            )
            
    except Exception as e:
        logger.error(
            f"Error monitoring conversation {conversation_id}: {e}",
            extra={'conversation_id': conversation_id}
        )