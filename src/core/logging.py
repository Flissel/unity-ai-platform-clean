"""Centralized logging configuration for Unity AI platform."""

import logging
import logging.config
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from .config import get_settings, LogLevel


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "getMessage", "exc_info",
                "exc_text", "stack_info"
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ContextFilter(logging.Filter):
    """Add context information to log records."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Setup application logging configuration.
    
    Args:
        log_level: Logging level override
        log_format: Log format override (json or text)
        log_file: Log file path
        context: Additional context to add to all logs
    """
    settings = get_settings()
    
    # Use provided values or fall back to settings
    level = log_level or settings.monitoring.logging_level.value
    format_type = log_format or settings.monitoring.log_format
    
    # Create logs directory if logging to file
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure formatters
    formatters = {
        "json": {
            "()": "src.core.logging.JSONFormatter"
        },
        "text": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    }
    
    # Configure handlers
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": format_type,
            "stream": "ext://sys.stdout"
        }
    }
    
    # Add file handler if specified
    if log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": format_type,
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    
    # Configure filters
    filters = {}
    if context:
        filters["context"] = {
            "()": "src.core.logging.ContextFilter",
            "context": context
        }
    
    # Configure loggers
    loggers = {
        "src": {
            "level": level,
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": list(handlers.keys()),
            "propagate": False
        }
    }
    
    # Add filters to handlers if context is provided
    if context:
        for handler_config in handlers.values():
            handler_config["filters"] = ["context"]
    
    # Build logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "filters": filters,
        "handlers": handlers,
        "loggers": loggers,
        "root": {
            "level": level,
            "handlers": list(handlers.keys())
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Get a logger with optional context.
    
    Args:
        name: Logger name
        context: Additional context for this logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if context:
        # Add context filter to this specific logger
        context_filter = ContextFilter(context)
        logger.addFilter(context_filter)
    
    return logger


def log_execution_time(logger: logging.Logger, operation: str):
    """Decorator to log execution time of functions.
    
    Args:
        logger: Logger instance
        operation: Operation description
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"{operation} completed successfully",
                    extra={
                        "operation": operation,
                        "execution_time": execution_time,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{operation} failed: {str(e)}",
                    extra={
                        "operation": operation,
                        "execution_time": execution_time,
                        "status": "error",
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def log_api_request(logger: logging.Logger):
    """Decorator to log API requests.
    
    Args:
        logger: Logger instance
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            # Extract request info (assuming FastAPI)
            request_info = {}
            if args and hasattr(args[0], 'method'):
                request = args[0]
                request_info = {
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent")
                }
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"API request completed",
                    extra={
                        **request_info,
                        "execution_time": execution_time,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"API request failed: {str(e)}",
                    extra={
                        **request_info,
                        "execution_time": execution_time,
                        "status": "error",
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


# Initialize logging on module import
def init_logging():
    """Initialize logging with default configuration."""
    try:
        setup_logging()
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logging.getLogger(__name__).warning(
            f"Failed to setup advanced logging, using basic configuration: {e}"
        )


# Auto-initialize logging
init_logging()