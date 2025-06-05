"""Custom exceptions for Unity AI platform."""

from typing import Optional, Dict, Any


class UnityAIException(Exception):
    """Base exception for Unity AI platform."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ValidationError(UnityAIException):
    """Input validation failed."""
    pass


class AuthenticationError(UnityAIException):
    """Authentication failed."""
    pass


class AuthorizationError(UnityAIException):
    """Authorization failed."""
    pass


class ServiceUnavailableError(UnityAIException):
    """External service is temporarily unavailable."""
    pass


class ConfigurationError(UnityAIException):
    """Configuration error."""
    pass


class WorkflowExecutionError(UnityAIException):
    """Workflow execution failed."""
    pass


class CodeExecutionError(UnityAIException):
    """Code execution failed."""
    pass


class AutoGenError(UnityAIException):
    """AutoGen agent error."""
    pass


class N8nServiceError(UnityAIException):
    """n8n service error."""
    pass


class DatabaseError(UnityAIException):
    """Database operation error."""
    pass


class CacheError(UnityAIException):
    """Cache operation error."""
    pass


class RateLimitError(UnityAIException):
    """Rate limit exceeded."""
    pass


class TimeoutError(UnityAIException):
    """Operation timed out."""
    pass


class NotFoundError(UnityAIException):
    """Resource not found."""
    pass


class ConflictError(UnityAIException):
    """Resource conflict."""
    pass