"""Base models and schemas for Unity AI platform."""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = Field(description="Operation success status")
    message: Optional[str] = Field(default=None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")


class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = Field(default=False, description="Always false for errors")
    error_code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ServiceHealth(BaseModel):
    """Service health information."""
    name: str = Field(description="Service name")
    status: HealthStatus = Field(description="Service status")
    version: Optional[str] = Field(default=None, description="Service version")
    uptime: Optional[float] = Field(default=None, description="Uptime in seconds")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last health check")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional health details")


class HealthResponse(BaseResponse):
    """Health check response."""
    status: HealthStatus = Field(description="Overall system status")
    services: List[ServiceHealth] = Field(description="Individual service health")
    version: str = Field(description="Application version")
    uptime: float = Field(description="System uptime in seconds")


class ExecutionStatus(str, Enum):
    """Execution status for workflows and code."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class BaseTask(BaseModel):
    """Base task model."""
    id: UUID = Field(default_factory=uuid4, description="Task unique identifier")
    name: str = Field(description="Task name")
    description: Optional[str] = Field(default=None, description="Task description")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Task status")
    priority: Priority = Field(default=Priority.NORMAL, description="Task priority")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    class Config:
        use_enum_values = True


class CodeExecutionRequest(BaseModel):
    """Code execution request model."""
    code: str = Field(description="Code to execute")
    language: str = Field(default="python", description="Programming language")
    timeout: Optional[int] = Field(default=30, description="Execution timeout in seconds")
    environment: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    requirements: Optional[List[str]] = Field(default=None, description="Package requirements")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Execution context")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v is not None and (v <= 0 or v > 300):
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v


class CodeExecutionResult(BaseModel):
    """Code execution result model."""
    success: bool = Field(description="Execution success status")
    output: Optional[str] = Field(default=None, description="Execution output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    exit_code: Optional[int] = Field(default=None, description="Process exit code")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class WorkflowTrigger(BaseModel):
    """Workflow trigger configuration."""
    type: str = Field(description="Trigger type (webhook, api, schedule)")
    config: Dict[str, Any] = Field(description="Trigger configuration")
    enabled: bool = Field(default=True, description="Trigger enabled status")


class WorkflowDefinition(BaseModel):
    """Workflow definition model."""
    id: UUID = Field(default_factory=uuid4, description="Workflow unique identifier")
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    version: str = Field(default="1.0.0", description="Workflow version")
    triggers: List[WorkflowTrigger] = Field(description="Workflow triggers")
    nodes: List[Dict[str, Any]] = Field(description="Workflow nodes")
    connections: List[Dict[str, Any]] = Field(description="Node connections")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Workflow settings")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        use_enum_values = True


class WorkflowExecution(BaseTask):
    """Workflow execution model."""
    workflow_id: UUID = Field(description="Workflow definition ID")
    trigger_data: Optional[Dict[str, Any]] = Field(default=None, description="Trigger input data")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Execution result")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Error details if failed")
    execution_log: Optional[List[Dict[str, Any]]] = Field(default=None, description="Execution log")


class AgentRequest(BaseModel):
    """AutoGen agent request model."""
    agent_type: str = Field(description="Type of agent to use")
    task: str = Field(description="Task description")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Task context")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Agent parameters")
    timeout: Optional[int] = Field(default=60, description="Request timeout in seconds")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v is not None and (v <= 0 or v > 600):
            raise ValueError('Timeout must be between 1 and 600 seconds')
        return v


class AgentResponse(BaseModel):
    """AutoGen agent response model."""
    success: bool = Field(description="Agent execution success")
    result: Optional[Any] = Field(default=None, description="Agent result")
    reasoning: Optional[str] = Field(default=None, description="Agent reasoning")
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Confidence must be between 0 and 1')
        return v


class MetricsData(BaseModel):
    """Metrics data model."""
    name: str = Field(description="Metric name")
    value: Union[int, float] = Field(description="Metric value")
    labels: Optional[Dict[str, str]] = Field(default=None, description="Metric labels")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metric timestamp")
    unit: Optional[str] = Field(default=None, description="Metric unit")


class LogEntry(BaseModel):
    """Log entry model."""
    level: str = Field(description="Log level")
    message: str = Field(description="Log message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    logger: Optional[str] = Field(default=None, description="Logger name")
    module: Optional[str] = Field(default=None, description="Module name")
    function: Optional[str] = Field(default=None, description="Function name")
    line: Optional[int] = Field(default=None, description="Line number")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Extra log data")