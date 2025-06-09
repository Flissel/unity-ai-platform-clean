#!/usr/bin/env python3
"""
Core Module for n8n API Playground

Provides core functionality including API client, workflow execution,
response handling, and configuration management.

Author: UnityAI Team
Version: 1.0.0
"""

from .api_client import (
    N8nApiClient,
    N8nApiResponse
)

from .config import (
    Config,
    ConfigManager,
    N8nApiConfig,
    DatabaseConfig,
    RedisConfig,
    SecurityConfig,
    LoggingConfig,
    PlaygroundConfig as CorePlaygroundConfig,
    ModuleConfig,
    get_config,
    reload_config,
    update_config
)

from .playground_manager import (
    PlaygroundManager,
    PlaygroundSession,
    PlaygroundConfig
)

from .response_handler import (
    ResponseHandler,
    ProcessedResponse,
    DataExtractor,
    ResponseValidator
)

from .workflow_executor import (
    WorkflowExecutor,
    WorkflowExecution,
    WorkflowTemplate
)

__version__ = "1.0.0"
__author__ = "UnityAI Team"

__all__ = [
    # API Client
    "N8nApiClient",
    "N8nApiResponse",
    "N8nApiError",
    
    # Configuration
    "Config",
    "ConfigManager",
    "N8nApiConfig",
    "DatabaseConfig",
    "RedisConfig",
    "SecurityConfig",
    "LoggingConfig",
    "PlaygroundConfig",
    "ModuleConfig",
    "get_config",
    "reload_config",
    "update_config",
    
    # Playground Manager
    "PlaygroundManager",
    "SessionManager",
    "Session",
    "ModuleLoader",
    "TemplateManager",
    
    # Response Handler
    "ResponseHandler",
    "ProcessedResponse",
    "DataExtractor",
    "ResponseValidator",
    
    # Workflow Executor
    "WorkflowExecutor",
    "WorkflowExecution",
    "WorkflowTemplate"
]