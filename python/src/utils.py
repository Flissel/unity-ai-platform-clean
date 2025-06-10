#!/usr/bin/env python3
"""
Utility functions for UnityAI Python Worker Service.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from .config import settings


def setup_logging():
    """Setup structured logging configuration."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def sanitize_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize parameters for logging (remove sensitive data)."""
    sensitive_keys = {
        'password', 'token', 'key', 'secret', 'api_key', 
        'auth', 'credential', 'private', 'confidential'
    }
    
    sanitized = {}
    for key, value in parameters.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_parameters(value)
        else:
            sanitized[key] = value
    
    return sanitized


def format_task_result(task_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Format task result for API response."""
    return {
        "task_id": task_id,
        "timestamp": result.get("completed_at"),
        "status": result.get("status"),
        "data": result.get("result"),
        "error": result.get("error"),
        "execution_time": calculate_execution_time(result)
    }


def calculate_execution_time(task_info: Dict[str, Any]) -> float:
    """Calculate task execution time in seconds."""
    try:
        from datetime import datetime
        
        started_at = task_info.get("started_at")
        completed_at = task_info.get("completed_at")
        
        if started_at and completed_at:
            start_time = datetime.fromisoformat(started_at)
            end_time = datetime.fromisoformat(completed_at)
            return (end_time - start_time).total_seconds()
    except Exception:
        pass
    
    return 0.0


def validate_task_parameters(task_type: str, parameters: Dict[str, Any]) -> bool:
    """Validate task parameters based on task type."""
    
    required_params = {
        "data_processing": ["operation", "data"],
        "ml_inference": ["model_type", "input_data"],
        "web_scraping": ["url"],
        "document_processing": ["document_type", "content"],
        "image_processing": ["image_path", "operation"],
        "custom_script": ["script"]
    }
    
    if task_type not in required_params:
        return False
    
    required = required_params[task_type]
    return all(param in parameters for param in required)


def get_task_schema(task_type: str) -> Dict[str, Any]:
    """Get parameter schema for a task type."""
    
    schemas = {
        "data_processing": {
            "operation": {"type": "string", "enum": ["sum", "average", "count"]},
            "data": {"type": "array", "items": {"type": "number"}}
        },
        "ml_inference": {
            "model_type": {"type": "string", "enum": ["sentiment", "classification"]},
            "input_data": {"type": "string"}
        },
        "web_scraping": {
            "url": {"type": "string", "format": "uri"},
            "selector": {"type": "string", "default": ""}
        },
        "document_processing": {
            "document_type": {"type": "string", "enum": ["pdf", "docx", "txt"]},
            "content": {"type": "string"}
        },
        "image_processing": {
            "image_path": {"type": "string"},
            "operation": {"type": "string", "enum": ["resize", "crop", "filter"]}
        },
        "custom_script": {
            "script": {"type": "string"},
            "args": {"type": "object", "default": {}}
        }
    }
    
    return schemas.get(task_type, {})