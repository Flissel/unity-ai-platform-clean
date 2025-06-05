"""Redis cache utilities for Unity AI platform."""

import json
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio

import redis.asyncio as redis
from redis.asyncio import Redis

from .config import get_settings
from .logging import get_logger
from .exceptions import CacheError

logger = get_logger(__name__)


class CacheManager:
    """Redis cache manager with async support."""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._initialized:
            return
        
        try:
            settings = get_settings()
            
            self._redis = redis.from_url(
                settings.redis.url,
                db=settings.redis.db,
                max_connections=settings.redis.max_connections,
                decode_responses=settings.redis.decode_responses,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            await self._redis.ping()
            
            self._initialized = True
            logger.info("Redis cache connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise CacheError(f"Cache initialization failed: {e}")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._initialized = False
            logger.info("Redis cache connection closed")
    
    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is established."""
        if not self._initialized:
            await self.initialize()
        
        if not self._redis:
            raise CacheError("Redis not initialized")
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serializer: str = "json"
    ) -> bool:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            serializer: Serialization method (json or pickle)
            
        Returns:
            True if successful
        """
        await self._ensure_connected()
        
        try:
            # Serialize value
            if serializer == "json":
                serialized_value = json.dumps(value, default=str)
            elif serializer == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                raise ValueError(f"Unsupported serializer: {serializer}")
            
            # Set value with optional TTL
            if ttl:
                result = await self._redis.setex(key, ttl, serialized_value)
            else:
                result = await self._redis.set(key, serialized_value)
            
            logger.debug(f"Cache set: {key} (TTL: {ttl})")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            raise CacheError(f"Cache set operation failed: {e}")
    
    async def get(
        self,
        key: str,
        serializer: str = "json",
        default: Any = None
    ) -> Any:
        """Get a value from cache.
        
        Args:
            key: Cache key
            serializer: Serialization method (json or pickle)
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        await self._ensure_connected()
        
        try:
            value = await self._redis.get(key)
            
            if value is None:
                logger.debug(f"Cache miss: {key}")
                return default
            
            # Deserialize value
            if serializer == "json":
                result = json.loads(value)
            elif serializer == "pickle":
                result = pickle.loads(value)
            else:
                raise ValueError(f"Unsupported serializer: {serializer}")
            
            logger.debug(f"Cache hit: {key}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            # Return default on error to prevent cache failures from breaking the app
            return default
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted
        """
        await self._ensure_connected()
        
        try:
            result = await self._redis.delete(key)
            logger.debug(f"Cache delete: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            raise CacheError(f"Cache delete operation failed: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists
        """
        await self._ensure_connected()
        
        try:
            result = await self._redis.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to check cache key existence {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if expiration was set
        """
        await self._ensure_connected()
        
        try:
            result = await self._redis.expire(key, ttl)
            logger.debug(f"Cache expire: {key} (TTL: {ttl})")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            raise CacheError(f"Cache expire operation failed: {e}")
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        await self._ensure_connected()
        
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                result = await self._redis.delete(*keys)
                logger.info(f"Cache clear pattern: {pattern} ({result} keys deleted)")
                return result
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")
            raise CacheError(f"Cache clear pattern operation failed: {e}")
    
    async def health_check(self) -> bool:
        """Check cache health.
        
        Returns:
            True if cache is healthy
        """
        try:
            await self._ensure_connected()
            await self._redis.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server information.
        
        Returns:
            Redis server info
        """
        await self._ensure_connected()
        
        try:
            info = await self._redis.info()
            return {
                "version": info.get("redis_version"),
                "uptime": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            raise CacheError(f"Cache info operation failed: {e}")


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
async def init_cache() -> None:
    """Initialize cache connection."""
    await cache_manager.initialize()


async def close_cache() -> None:
    """Close cache connection."""
    await cache_manager.close()


# Decorators
def cached(
    ttl: int = 300,
    key_prefix: str = "",
    serializer: str = "json",
    skip_cache: Optional[Callable] = None
):
    """Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        serializer: Serialization method
        skip_cache: Function to determine if cache should be skipped
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip cache if condition is met
            if skip_cache and skip_cache(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = ":".join(filter(None, key_parts))
            
            try:
                # Try to get from cache
                cached_result = await cache_manager.get(
                    cache_key,
                    serializer=serializer
                )
                
                if cached_result is not None:
                    logger.debug(f"Cache hit for function {func.__name__}")
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                
                await cache_manager.set(
                    cache_key,
                    result,
                    ttl=ttl,
                    serializer=serializer
                )
                
                logger.debug(f"Cache miss for function {func.__name__}, result cached")
                return result
                
            except Exception as e:
                logger.warning(f"Cache operation failed for {func.__name__}: {e}")
                # Execute function without cache on error
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def cache_invalidate(key_pattern: str):
    """Decorator to invalidate cache after function execution.
    
    Args:
        key_pattern: Pattern of cache keys to invalidate
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            try:
                await cache_manager.clear_pattern(key_pattern)
                logger.debug(f"Cache invalidated: {key_pattern}")
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")
            
            return result
        
        return wrapper
    return decorator


# Session cache for temporary data
class SessionCache:
    """Session-based cache for temporary data storage."""
    
    def __init__(self, session_id: str, ttl: int = 3600):
        self.session_id = session_id
        self.ttl = ttl
        self.key_prefix = f"session:{session_id}"
    
    async def set(self, key: str, value: Any) -> bool:
        """Set session value."""
        full_key = f"{self.key_prefix}:{key}"
        return await cache_manager.set(full_key, value, ttl=self.ttl)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get session value."""
        full_key = f"{self.key_prefix}:{key}"
        return await cache_manager.get(full_key, default=default)
    
    async def delete(self, key: str) -> bool:
        """Delete session value."""
        full_key = f"{self.key_prefix}:{key}"
        return await cache_manager.delete(full_key)
    
    async def clear(self) -> int:
        """Clear all session data."""
        pattern = f"{self.key_prefix}:*"
        return await cache_manager.clear_pattern(pattern)
    
    async def extend_ttl(self, additional_seconds: int = 3600) -> None:
        """Extend TTL for all session keys."""
        pattern = f"{self.key_prefix}:*"
        try:
            keys = await cache_manager._redis.keys(pattern)
            for key in keys:
                await cache_manager.expire(key, self.ttl + additional_seconds)
        except Exception as e:
            logger.warning(f"Failed to extend session TTL: {e}")