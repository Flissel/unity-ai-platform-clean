"""Custom middleware for the FastAPI application."""

import time
import json
from typing import Callable, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.cache import get_cache_manager
from ..core.exceptions import RateLimitExceededException, SecurityException

settings = get_settings()
logger = get_logger(__name__)

# Prometheus metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

rate_limit_hits = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['client_ip', 'endpoint']
)

security_violations = Counter(
    'security_violations_total',
    'Total security violations',
    ['violation_type', 'client_ip']
)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and protection."""
    
    SUSPICIOUS_PATTERNS = [
        # SQL Injection patterns
        r"(?i)(union|select|insert|update|delete|drop|create|alter)\s+",
        r"(?i)(or|and)\s+\d+\s*=\s*\d+",
        r"(?i)'\s*(or|and)\s*'\w+'",
        
        # XSS patterns
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        
        # Path traversal
        r"\.\./",
        r"%2e%2e%2f",
        
        # Command injection
        r"[;&|`$(){}\[\]]",
    ]
    
    def __init__(self, app):
        super().__init__(app)
        import re
        self.patterns = [re.compile(pattern) for pattern in self.SUSPICIOUS_PATTERNS]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process security checks on incoming requests."""
        try:
            # Check request size
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > settings.security.max_request_size:
                security_violations.labels(
                    violation_type='request_too_large',
                    client_ip=self._get_client_ip(request)
                ).inc()
                raise SecurityException(
                    "Request too large",
                    details={"max_size": settings.security.max_request_size}
                )
            
            # Check for suspicious patterns in URL
            url_path = str(request.url.path)
            query_params = str(request.url.query)
            
            for pattern in self.patterns:
                if pattern.search(url_path) or pattern.search(query_params):
                    security_violations.labels(
                        violation_type='suspicious_pattern',
                        client_ip=self._get_client_ip(request)
                    ).inc()
                    logger.warning(
                        f"Suspicious pattern detected in request: {url_path}",
                        extra={
                            'client_ip': self._get_client_ip(request),
                            'user_agent': request.headers.get('user-agent'),
                            'pattern_matched': True
                        }
                    )
                    raise SecurityException("Suspicious request pattern detected")
            
            # Check request body for suspicious patterns (if applicable)
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body = await request.body()
                    if body:
                        body_str = body.decode('utf-8', errors='ignore')
                        for pattern in self.patterns:
                            if pattern.search(body_str):
                                security_violations.labels(
                                    violation_type='suspicious_body',
                                    client_ip=self._get_client_ip(request)
                                ).inc()
                                raise SecurityException("Suspicious content in request body")
                        
                        # Recreate request with body for downstream processing
                        request._body = body
                except Exception as e:
                    logger.warning(f"Could not parse request body for security check: {e}")
            
            # Add security headers to response
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            
            if settings.api.environment == "production":
                response.headers["Server"] = "Unity-AI"
            
            return response
            
        except SecurityException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'client_ip': self._get_client_ip(request),
                'user_agent': request.headers.get('user-agent'),
                'content_type': request.headers.get('content-type')
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} in {duration:.3f}s",
            extra={
                'status_code': response.status_code,
                'duration': duration,
                'response_size': response.headers.get('content-length')
            }
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.client.host if request.client else 'unknown'


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for requests."""
        if not settings.monitoring.enabled:
            return await call_next(request)
        
        # Skip metrics collection for metrics endpoint
        if request.url.path == '/metrics':
            return await call_next(request)
        
        start_time = time.time()
        active_requests.inc()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            endpoint = self._normalize_endpoint(request.url.path)
            
            request_count.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
            request_duration.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        finally:
            active_requests.dec()
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics."""
        # Replace dynamic segments with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{uuid}',
            path
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    def __init__(self, app):
        super().__init__(app)
        self.cache_manager = None
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 10, 'window': 60},      # 10 auth requests per minute
            'upload': {'requests': 5, 'window': 60},     # 5 uploads per minute
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP and endpoint."""
        if not settings.security.rate_limiting_enabled:
            return await call_next(request)
        
        # Initialize cache manager if not done
        if self.cache_manager is None:
            self.cache_manager = get_cache_manager()
        
        client_ip = self._get_client_ip(request)
        endpoint_type = self._get_endpoint_type(request.url.path)
        
        # Check rate limit
        is_allowed, remaining = await self._check_rate_limit(
            client_ip, endpoint_type
        )
        
        if not is_allowed:
            rate_limit_hits.labels(
                client_ip=client_ip,
                endpoint=endpoint_type
            ).inc()
            
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {endpoint_type}",
                extra={
                    'client_ip': client_ip,
                    'endpoint_type': endpoint_type,
                    'remaining': remaining
                }
            )
            
            raise RateLimitExceededException(
                "Rate limit exceeded",
                details={
                    'limit': self.rate_limits[endpoint_type]['requests'],
                    'window': self.rate_limits[endpoint_type]['window'],
                    'remaining': remaining
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        limit_info = self.rate_limits[endpoint_type]
        response.headers['X-RateLimit-Limit'] = str(limit_info['requests'])
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Reset'] = str(
            int(time.time()) + limit_info['window']
        )
        
        return response
    
    async def _check_rate_limit(self, client_ip: str, endpoint_type: str) -> tuple[bool, int]:
        """Check if request is within rate limit."""
        limit_info = self.rate_limits[endpoint_type]
        key = f"rate_limit:{endpoint_type}:{client_ip}"
        
        try:
            # Get current count
            current = await self.cache_manager.get(key)
            current = int(current) if current else 0
            
            if current >= limit_info['requests']:
                return False, 0
            
            # Increment counter
            new_count = await self.cache_manager.incr(key)
            
            # Set expiration on first request
            if new_count == 1:
                await self.cache_manager.expire(key, limit_info['window'])
            
            remaining = max(0, limit_info['requests'] - new_count)
            return True, remaining
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiting fails
            return True, limit_info['requests']
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.client.host if request.client else 'unknown'
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for rate limiting."""
        if '/auth' in path or '/login' in path:
            return 'auth'
        elif '/upload' in path or '/file' in path:
            return 'upload'
        else:
            return 'default'


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors and format responses consistently."""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException:
            # Let FastAPI handle HTTP exceptions
            raise
            
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unhandled error in request {request.method} {request.url.path}: {e}",
                exc_info=True,
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'client_ip': self._get_client_ip(request),
                    'error_type': type(e).__name__
                }
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An internal server error occurred",
                        "details": str(e) if settings.api.debug else None
                    }
                }
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.client.host if request.client else 'unknown'


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware for response compression."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Compress responses when appropriate."""
        response = await call_next(request)
        
        # Check if client accepts compression
        accept_encoding = request.headers.get('accept-encoding', '')
        
        if 'gzip' in accept_encoding and self._should_compress(response):
            # Add compression header
            response.headers['content-encoding'] = 'gzip'
            response.headers['vary'] = 'Accept-Encoding'
        
        return response
    
    def _should_compress(self, response: Response) -> bool:
        """Determine if response should be compressed."""
        # Don't compress small responses
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) < 1024:
            return False
        
        # Don't compress already compressed content
        content_type = response.headers.get('content-type', '')
        if any(ct in content_type for ct in ['image/', 'video/', 'audio/', 'application/zip']):
            return False
        
        return True