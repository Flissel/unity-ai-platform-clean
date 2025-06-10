#!/usr/bin/env python3
"""
Workflow Automation Module

This module provides comprehensive workflow automation capabilities
for the n8n API Playground, including template management, workflow
execution, and monitoring.

Author: UnityAI Team
Version: 1.0.0
"""

from .workflow_manager import WorkflowManager
from .template_engine import TemplateEngine
from .validators import WorkflowValidator, N8nWorkflowValidator
from .api import router as workflow_automation_router
from .models import (
    # Core models
    WorkflowTemplate,
    Workflow,
    WorkflowExecution,
    WorkflowParameter,
    WorkflowSchedule,
    WorkflowMetrics,
    WorkflowEvent,
    WorkflowCategory,
    WorkflowTag,
    
    # Enums
    WorkflowStatus,
    ExecutionStatus,
    ParameterType,
    
    # Validation
    ValidationRule,
    ValidationResult,
    
    # API models
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    ExecuteWorkflowRequest,
    WorkflowListResponse,
    ExecutionListResponse,
    WorkflowStatsResponse,
    
    # Import/Export
    WorkflowImportResult,
    WorkflowExportResult
)

__version__ = "1.0.0"
__author__ = "UnityAI Team"

# Module metadata
__all__ = [
    # Core classes
    "WorkflowManager",
    "TemplateEngine",
    "WorkflowValidator",
    "N8nWorkflowValidator",
    
    # API router
    "workflow_automation_router",
    
    # Core models
    "WorkflowTemplate",
    "Workflow",
    "WorkflowExecution",
    "WorkflowParameter",
    "WorkflowSchedule",
    "WorkflowMetrics",
    "WorkflowEvent",
    "WorkflowCategory",
    "WorkflowTag",
    
    # Enums
    "WorkflowStatus",
    "ExecutionStatus",
    "ParameterType",
    
    # Validation
    "ValidationRule",
    "ValidationResult",
    
    # API models
    "WorkflowCreateRequest",
    "WorkflowUpdateRequest",
    "WorkflowExecuteRequest",
    "WorkflowResponse",
    "WorkflowListResponse",
    "WorkflowExecutionResponse",
    "WorkflowExecutionListResponse",
    "WorkflowStatsResponse",
    
    # Import/Export
    "WorkflowImportResult",
    "WorkflowExportResult"
]


# Module configuration
MODULE_CONFIG = {
    "name": "workflow_automation",
    "version": __version__,
    "description": "Workflow automation and template management for n8n API Playground",
    "author": __author__,
    "dependencies": [
        "fastapi",
        "pydantic",
        "structlog",
        "jinja2",
        "pyyaml",
        "aiofiles",
        "asyncio"
    ],
    "api_prefix": "/workflow-automation",
    "api_tags": ["Workflow Automation"],
    "features": [
        "Template Management",
        "Workflow Creation",
        "Workflow Execution",
        "Parameter Validation",
        "Execution Monitoring",
        "Statistics and Metrics",
        "Scheduled Execution",
        "Import/Export"
    ]
}


def get_module_info():
    """Get module information."""
    return MODULE_CONFIG


def get_version():
    """Get module version."""
    return __version__


def get_api_router():
    """Get the FastAPI router for this module."""
    return workflow_automation_router