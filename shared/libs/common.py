#!/usr/bin/env python3
"""
Common utilities for shared Python scripts in UnityAI.
This module provides shared functionality for all n8n-executable scripts.
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def setup_logging(level: str = "INFO", format_type: str = "json") -> logging.Logger:
    """Setup logging for scripts."""
    
    logger = logging.getLogger("unityai_script")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = logging.StreamHandler(sys.stderr)
    
    if format_type == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


def handle_errors(func):
    """Decorator for consistent error handling in scripts."""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            error_result = {
                "error": "Script execution interrupted",
                "error_type": "KeyboardInterrupt",
                "success": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            print(json.dumps(error_result), file=sys.stderr)
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            error_result = {
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "success": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            print(json.dumps(error_result), file=sys.stderr)
            sys.exit(1)
    
    return wrapper


def validate_input(data: Any, schema: Dict[str, Any]) -> bool:
    """Simple input validation based on schema."""
    
    if not isinstance(data, dict):
        return False
    
    for field, field_schema in schema.items():
        if field_schema.get("required", False) and field not in data:
            raise ValueError(f"Required field '{field}' is missing")
        
        if field in data:
            field_type = field_schema.get("type")
            field_value = data[field]
            
            if field_type == "string" and not isinstance(field_value, str):
                raise ValueError(f"Field '{field}' must be a string")
            elif field_type == "number" and not isinstance(field_value, (int, float)):
                raise ValueError(f"Field '{field}' must be a number")
            elif field_type == "array" and not isinstance(field_value, list):
                raise ValueError(f"Field '{field}' must be an array")
            elif field_type == "object" and not isinstance(field_value, dict):
                raise ValueError(f"Field '{field}' must be an object")
    
    return True


def safe_json_loads(json_str: str) -> Dict[str, Any]:
    """Safely parse JSON string with error handling."""
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON input: {e}")


def safe_json_dumps(data: Any, **kwargs) -> str:
    """Safely serialize data to JSON with default options."""
    
    default_kwargs = {
        "ensure_ascii": False,
        "indent": None,
        "separators": (',', ':')
    }
    default_kwargs.update(kwargs)
    
    try:
        return json.dumps(data, **default_kwargs)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot serialize data to JSON: {e}")


def create_success_response(data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create standardized success response."""
    
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def create_error_response(error: str, error_type: str = "Error", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create standardized error response."""
    
    response = {
        "success": False,
        "error": error,
        "error_type": error_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response


def read_file_safe(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Safely read file content with error handling."""
    
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return path.read_text(encoding=encoding)
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def write_file_safe(file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
    """Safely write content to file with error handling."""
    
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
    except Exception as e:
        raise IOError(f"Error writing file {file_path}: {e}")


def get_script_info() -> Dict[str, str]:
    """Get information about the current script."""
    
    script_path = Path(sys.argv[0])
    
    return {
        "script_name": script_path.name,
        "script_path": str(script_path.absolute()),
        "script_dir": str(script_path.parent.absolute()),
        "working_dir": str(Path.cwd())
    }


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    
    import re
    
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary."""
    
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def measure_execution_time(func):
    """Decorator to measure function execution time."""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        result = func(*args, **kwargs)
        end_time = datetime.utcnow()
        
        execution_time = (end_time - start_time).total_seconds()
        
        # Add execution time to result if it's a dict
        if isinstance(result, dict):
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["execution_time_seconds"] = execution_time
        
        return result
    
    return wrapper