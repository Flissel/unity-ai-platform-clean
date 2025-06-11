#!/usr/bin/env python3
"""
Data Models for Workflow Automation Module

Defines all data structures used in the workflow automation system,
including workflows, executions, templates, and validation models.

Author: UnityAI Team
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""
    
    CREATED = "created"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    ERROR = "error"


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ParameterType(str, Enum):
    """Parameter type enumeration."""
    
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"
    URL = "url"
    EMAIL = "email"
    DATE = "date"
    DATETIME = "datetime"


class ValidationRule(BaseModel):
    """Parameter validation rule."""
    
    type: ParameterType
    required: bool = False
    default: Optional[Any] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    description: Optional[str] = None


class WorkflowParameter(BaseModel):
    """Workflow parameter definition."""
    
    name: str
    type: ParameterType
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None
    validation: Optional[ValidationRule] = None
    group: Optional[str] = None
    order: int = 0
    sensitive: bool = False  # For passwords, API keys, etc.


class WorkflowTemplate(BaseModel):
    """Workflow template model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    
    # Template definition
    template_data: Dict[str, Any]
    parameters: List[WorkflowParameter] = Field(default_factory=list)
    
    # Metadata
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Usage statistics
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Workflow(BaseModel):
    """Workflow model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    
    # Template information
    template_name: str
    template_version: str
    
    # Configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)
    workflow_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.CREATED
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_executed: Optional[datetime] = None
    
    # Statistics
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    # n8n specific
    n8n_workflow_id: Optional[str] = None
    n8n_workflow_url: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowExecution(BaseModel):
    """Workflow execution model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    
    # Execution parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Status and timing
    status: ExecutionStatus = ExecutionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None  # in seconds
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    
    # n8n specific
    n8n_execution_id: Optional[str] = None
    n8n_execution_url: Optional[str] = None
    
    # Metadata
    triggered_by: Optional[str] = None  # user, schedule, webhook, etc.
    trigger_data: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return self.status in [
            ExecutionStatus.SUCCESS,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT
        ]
    
    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS


class WorkflowSchedule(BaseModel):
    """Workflow schedule model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    name: str
    description: Optional[str] = None
    
    # Schedule configuration
    cron_expression: str
    timezone: str = "UTC"
    enabled: bool = True
    
    # Parameters for scheduled execution
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    # Statistics
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationResult(BaseModel):
    """Validation result model."""
    
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkflowMetrics(BaseModel):
    """Workflow execution metrics."""
    
    workflow_id: str
    
    # Execution statistics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    
    # Timing statistics
    average_execution_time: Optional[float] = None
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    
    # Recent activity
    last_execution: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    # Performance indicators
    success_rate: float = 0.0
    reliability_score: float = 0.0
    
    # Time period for metrics
    period_start: datetime
    period_end: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('success_rate', 'reliability_score')
    def validate_percentage(cls, v):
        """Validate percentage values."""
        if not 0.0 <= v <= 100.0:
            raise ValueError('Percentage must be between 0 and 100')
        return v


class WorkflowEvent(BaseModel):
    """Workflow event model for audit trail."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    execution_id: Optional[str] = None
    
    # Event details
    event_type: str  # created, updated, executed, failed, etc.
    event_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Context
    user_id: Optional[str] = None
    source: str = "system"  # system, user, api, webhook, etc.
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowCategory(BaseModel):
    """Workflow category model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    
    # Display properties
    icon: Optional[str] = None
    color: Optional[str] = None
    order: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowTag(BaseModel):
    """Workflow tag model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    
    # Usage statistics
    usage_count: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowImportResult(BaseModel):
    """Result of workflow import operation."""
    
    success: bool
    workflow_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Import statistics
    templates_imported: int = 0
    workflows_imported: int = 0
    parameters_mapped: int = 0
    
    # Details
    import_details: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExportResult(BaseModel):
    """Result of workflow export operation."""
    
    success: bool
    export_data: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    
    # Export statistics
    workflows_exported: int = 0
    templates_exported: int = 0
    
    # Metadata
    export_format: str = "json"
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request/Response models for API
class CreateWorkflowRequest(BaseModel):
    """Request model for creating workflow."""
    
    template_name: str
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class UpdateWorkflowRequest(BaseModel):
    """Request model for updating workflow."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    status: Optional[WorkflowStatus] = None


class ExecuteWorkflowRequest(BaseModel):
    """Request model for executing workflow."""
    
    parameters: Optional[Dict[str, Any]] = None
    wait_for_completion: bool = False
    timeout: Optional[int] = None


class WorkflowListResponse(BaseModel):
    """Response model for workflow list."""
    
    workflows: List[Workflow]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class ExecutionListResponse(BaseModel):
    """Response model for execution list."""
    
    executions: List[WorkflowExecution]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class WorkflowStatsResponse(BaseModel):
    """Response model for workflow statistics."""
    
    total_workflows: int
    active_workflows: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: Optional[float] = None
    
    # Breakdown by status
    workflows_by_status: Dict[str, int]
    executions_by_status: Dict[str, int]
    
    # Recent activity
    recent_executions: List[WorkflowExecution]
    top_workflows: List[Dict[str, Any]]


class ExecutionResult(BaseModel):
    """Execution result model for workflow executions."""
    success: bool
    execution_id: str
    output_data: Optional[Dict[str, Any]] = None
    duration: Optional[timedelta] = None
    error_message: Optional[str] = None