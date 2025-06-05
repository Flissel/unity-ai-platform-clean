"""Centralized configuration management for Unity AI platform."""

from functools import lru_cache
from typing import List, Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
from enum import Enum


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max pool overflow")
    echo: bool = Field(default=False, description="Echo SQL queries")
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration."""
    url: str = Field(default="redis://redis:6379", description="Redis connection URL")
    db: int = Field(default=0, description="Redis database number")
    max_connections: int = Field(default=10, description="Max connections in pool")
    decode_responses: bool = Field(default=True, description="Decode responses to strings")
    
    class Config:
        env_prefix = "REDIS_"


class N8nSettings(BaseSettings):
    """n8n service configuration."""
    api_url: str = Field(default="http://n8n:5678/api/v1", description="n8n API base URL")
    api_key: str = Field(..., description="n8n API key")
    webhook_url: str = Field(default="http://n8n:5678/webhook", description="n8n webhook URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    class Config:
        env_prefix = "N8N_"


class AutoGenSettings(BaseSettings):
    """AutoGen configuration."""
    enabled: bool = Field(default=True, description="Enable AutoGen functionality")
    model: str = Field(default="gpt-4o", description="Default model for AutoGen")
    temperature: float = Field(default=0.7, description="Model temperature")
    max_tokens: int = Field(default=1000, description="Maximum tokens per response")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    
    class Config:
        env_prefix = "AUTOGEN_"


class SecuritySettings(BaseSettings):
    """Security configuration."""
    secret_key: str = Field(..., description="Application secret key")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"], description="CORS allowed methods")
    cors_headers: List[str] = Field(default=["*"], description="CORS allowed headers")
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_prefix = "SECURITY_"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration."""
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    logging_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    class Config:
        env_prefix = "MONITORING_"


class APISettings(BaseSettings):
    """API server configuration."""
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, description="API server port")
    prefix: str = Field(default="/api/v1", description="API prefix")
    title: str = Field(default="Unity AI Platform", description="API title")
    description: str = Field(default="Event-driven automation platform", description="API description")
    version: str = Field(default="1.0.0", description="API version")
    docs_url: str = Field(default="/docs", description="Swagger UI URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")
    workers: int = Field(default=1, description="Number of worker processes")
    
    class Config:
        env_prefix = "API_"


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    app_name: str = Field(default="Unity AI Platform", description="Application name")
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # External API Keys
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # Service configurations
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    n8n: N8nSettings = N8nSettings()
    autogen: AutoGenSettings = AutoGenSettings()
    security: SecuritySettings = SecuritySettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    api: APISettings = APISettings()
    
    @validator('debug', pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow nested models to be configured via environment variables
        env_nested_delimiter = "__"


@lru_cache()
def get_settings(environment: Optional[str] = None) -> Settings:
    """Get application settings with caching.
    
    Args:
        environment: Override environment (for testing)
        
    Returns:
        Settings instance
    """
    if environment:
        # For testing, create settings with specific environment
        import os
        original_env = os.environ.get('ENVIRONMENT')
        os.environ['ENVIRONMENT'] = environment
        try:
            settings = Settings()
        finally:
            if original_env:
                os.environ['ENVIRONMENT'] = original_env
            else:
                os.environ.pop('ENVIRONMENT', None)
        return settings
    
    return Settings()


def get_database_url() -> str:
    """Get database URL from settings."""
    settings = get_settings()
    return settings.database.url


def get_redis_url() -> str:
    """Get Redis URL from settings."""
    settings = get_settings()
    return settings.redis.url


def is_development() -> bool:
    """Check if running in development mode."""
    settings = get_settings()
    return settings.environment == Environment.DEVELOPMENT


def is_production() -> bool:
    """Check if running in production mode."""
    settings = get_settings()
    return settings.environment == Environment.PRODUCTION