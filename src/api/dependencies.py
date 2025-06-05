"""FastAPI dependencies for authentication, authorization, and common utilities."""

from typing import Optional, Dict, Any, Annotated
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.cache import get_cache_manager
from ..core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ValidationException
)
from ..core.models import BaseResponse

settings = get_settings()
logger = get_logger(__name__)

# Security setup
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.security.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class User:
    """User model for authentication."""
    
    def __init__(self, username: str, email: str, roles: list[str] = None, is_active: bool = True):
        self.username = username
        self.email = email
        self.roles = roles or []
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.last_login = None
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise AuthenticationException("Invalid token")


async def get_current_user_from_token(token: str) -> User:
    """Get current user from JWT token."""
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        
        if username is None:
            raise AuthenticationException("Invalid token payload")
        
        # In a real application, you would fetch user from database
        # For now, we'll create a mock user based on token data
        user = User(
            username=username,
            email=payload.get("email", f"{username}@example.com"),
            roles=payload.get("roles", ["user"]),
            is_active=payload.get("is_active", True)
        )
        
        if not user.is_active:
            raise AuthenticationException("User account is disabled")
        
        return user
        
    except JWTError:
        raise AuthenticationException("Could not validate credentials")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user from Authorization header."""
    if not credentials:
        return None
    
    return await get_current_user_from_token(credentials.credentials)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (required authentication)."""
    if not current_user:
        raise AuthenticationException("Authentication required")
    
    if not current_user.is_active:
        raise AuthenticationException("User account is disabled")
    
    return current_user


def require_roles(required_roles: list[str]):
    """Dependency factory for role-based authorization."""
    
    async def check_roles(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.has_any_role(required_roles):
            raise AuthorizationException(
                f"Insufficient permissions. Required roles: {required_roles}"
            )
        return current_user
    
    return check_roles


def require_role(required_role: str):
    """Dependency factory for single role requirement."""
    return require_roles([required_role])


async def verify_api_key(
    x_api_key: Annotated[str, Header()] = None,
    request: Request = None
) -> bool:
    """Verify API key from header or query parameter."""
    if not settings.security.api_key_required:
        return True
    
    api_key = None
    
    # Check header first
    if x_api_key:
        api_key = x_api_key
    # Check query parameter as fallback
    elif request and "api_key" in request.query_params:
        api_key = request.query_params["api_key"]
    
    if not api_key:
        raise AuthenticationException(
            "API key required",
            details={"header": "X-API-Key", "query_param": "api_key"}
        )
    
    # Verify API key
    valid_api_keys = settings.security.api_keys
    if api_key not in valid_api_keys:
        logger.warning(
            f"Invalid API key used: {api_key[:8]}...",
            extra={
                'client_ip': request.client.host if request and request.client else 'unknown',
                'user_agent': request.headers.get('user-agent') if request else None
            }
        )
        raise AuthenticationException("Invalid API key")
    
    return True


async def get_rate_limit_key(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user)
) -> str:
    """Generate rate limit key based on user or IP."""
    if current_user:
        return f"user:{current_user.username}"
    
    # Use IP address for anonymous users
    client_ip = request.client.host if request.client else 'unknown'
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    
    return f"ip:{client_ip}"


async def validate_request_size(
    request: Request,
    max_size: int = None
) -> bool:
    """Validate request content size."""
    if max_size is None:
        max_size = settings.security.max_request_size
    
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > max_size:
        raise ValidationException(
            f"Request too large. Maximum size: {max_size} bytes",
            details={"max_size": max_size, "actual_size": int(content_length)}
        )
    
    return True


async def get_request_context(request: Request) -> Dict[str, Any]:
    """Extract request context for logging and monitoring."""
    return {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else 'unknown',
        "user_agent": request.headers.get('user-agent'),
        "content_type": request.headers.get('content-type'),
        "content_length": request.headers.get('content-length'),
        "request_id": getattr(request.state, 'request_id', None)
    }


class PaginationParams:
    """Pagination parameters for list endpoints."""
    
    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.page = max(1, page)
        self.size = min(max(1, size), 100)  # Limit to 100 items per page
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order.lower() in ["asc", "desc"] else "desc"
        self.offset = (self.page - 1) * self.size
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "page": self.page,
            "size": self.size,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "offset": self.offset
        }


def get_pagination_params(
    page: int = 1,
    size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> PaginationParams:
    """Dependency for pagination parameters."""
    return PaginationParams(page, size, sort_by, sort_order)


class FilterParams:
    """Base class for filter parameters."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


async def get_cache_dependency() -> Any:
    """Dependency to get cache manager."""
    return get_cache_manager()


async def validate_json_content_type(request: Request) -> bool:
    """Validate that request has JSON content type."""
    content_type = request.headers.get('content-type', '')
    if not content_type.startswith('application/json'):
        raise ValidationException(
            "Content-Type must be application/json",
            details={"received": content_type, "expected": "application/json"}
        )
    return True


async def get_user_permissions(
    current_user: User = Depends(get_current_active_user)
) -> list[str]:
    """Get user permissions based on roles."""
    # Define role-based permissions
    role_permissions = {
        "admin": [
            "read:all", "write:all", "delete:all",
            "manage:users", "manage:workflows", "manage:system"
        ],
        "operator": [
            "read:workflows", "write:workflows", "execute:workflows",
            "read:executions", "manage:executions"
        ],
        "developer": [
            "read:code", "write:code", "execute:code",
            "read:workflows", "write:workflows"
        ],
        "user": [
            "read:own", "execute:workflows"
        ]
    }
    
    permissions = set()
    for role in current_user.roles:
        if role in role_permissions:
            permissions.update(role_permissions[role])
    
    return list(permissions)


def require_permission(required_permission: str):
    """Dependency factory for permission-based authorization."""
    
    async def check_permission(
        permissions: list[str] = Depends(get_user_permissions)
    ) -> bool:
        if required_permission not in permissions and "write:all" not in permissions:
            raise AuthorizationException(
                f"Insufficient permissions. Required: {required_permission}"
            )
        return True
    
    return check_permission


# Common dependency combinations
RequireAuth = Depends(get_current_active_user)
RequireAdmin = Depends(require_role("admin"))
RequireOperator = Depends(require_roles(["admin", "operator"]))
RequireDeveloper = Depends(require_roles(["admin", "developer"]))
RequireApiKey = Depends(verify_api_key)