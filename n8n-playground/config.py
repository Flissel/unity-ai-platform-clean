#!/usr/bin/env python3
"""
n8n API Playground - Configuration Management

This module provides centralized configuration management for the n8n API Playground.
It handles environment variables, configuration validation, and provides typed configuration objects.

Author: UnityAI Team
Version: 1.0.0
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource
import structlog

logger = structlog.get_logger(__name__)


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseType(str, Enum):
    """Database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class CacheType(str, Enum):
    """Cache types."""
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 1
    reload: bool = False
    access_log: bool = True
    use_colors: bool = True
    loop: str = "asyncio"
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create server config from environment variables."""
        return cls(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "8080")),
            workers=int(os.getenv("SERVER_WORKERS", "1")),
            reload=os.getenv("SERVER_RELOAD", "false").lower() == "true",
            access_log=os.getenv("SERVER_ACCESS_LOG", "true").lower() == "true",
            use_colors=os.getenv("SERVER_USE_COLORS", "true").lower() == "true",
            loop=os.getenv("SERVER_LOOP", "asyncio")
        )


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: DatabaseType = DatabaseType.SQLITE
    host: str = "localhost"
    port: int = 5432
    name: str = "n8n_playground"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    @property
    def url(self) -> str:
        """Get database URL."""
        if self.type == DatabaseType.SQLITE:
            return f"sqlite:///./data/{self.name}.db"
        elif self.type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
        elif self.type == DatabaseType.MYSQL:
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create database config from environment variables."""
        return cls(
            type=DatabaseType(os.getenv("DB_TYPE", "sqlite")),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "n8n_playground"),
            username=os.getenv("DB_USERNAME", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )


class CacheConfig(BaseModel):
    """Cache configuration."""
    type: CacheType = CacheType.MEMORY
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    max_connections: int = 10
    timeout: int = 5
    default_ttl: int = 3600
    
    @property
    def url(self) -> str:
        """Get cache URL."""
        if self.type == CacheType.REDIS:
            if self.password:
                return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
            else:
                return f"redis://{self.host}:{self.port}/{self.db}"
        else:
            return "memory://"
    
    @classmethod
    def from_env(cls) -> "CacheConfig":
        """Create cache config from environment variables."""
        return cls(
            type=CacheType(os.getenv("CACHE_TYPE", "memory")),
            host=os.getenv("CACHE_HOST", "localhost"),
            port=int(os.getenv("CACHE_PORT", "6379")),
            password=os.getenv("CACHE_PASSWORD", ""),
            db=int(os.getenv("CACHE_DB", "0")),
            max_connections=int(os.getenv("CACHE_MAX_CONNECTIONS", "10")),
            timeout=int(os.getenv("CACHE_TIMEOUT", "5")),
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "3600"))
        )


class N8nApiConfig(BaseModel):
    """n8n API configuration."""
    base_url: str = "http://localhost:5678"
    api_key: str = ""
    username: str = ""
    password: str = ""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True
    
    @classmethod
    def from_env(cls) -> "N8nApiConfig":
        """Create n8n API config from environment variables."""
        return cls(
            base_url=os.getenv("N8N_API_BASE_URL", "http://localhost:5678"),
            api_key=os.getenv("N8N_API_KEY", ""),
            username=os.getenv("N8N_USERNAME", ""),
            password=os.getenv("N8N_PASSWORD", ""),
            timeout=int(os.getenv("N8N_API_TIMEOUT", "30")),
            max_retries=int(os.getenv("N8N_API_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("N8N_API_RETRY_DELAY", "1.0")),
            verify_ssl=os.getenv("N8N_API_VERIFY_SSL", "true").lower() == "true"
        )


class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    trusted_hosts: List[str] = Field(default_factory=list)
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Create security config from environment variables."""
        cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
        trusted_hosts = os.getenv("TRUSTED_HOSTS", "").split(",") if os.getenv("TRUSTED_HOSTS") else []
        
        return cls(
            secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
            algorithm=os.getenv("ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
            cors_origins=cors_origins,
            trusted_hosts=trusted_hosts
        )


class ModuleConfig(BaseModel):
    """Module configuration."""
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class ModulesConfig(BaseModel):
    """All modules configuration."""
    workflow_automation: ModuleConfig = Field(default_factory=ModuleConfig)
    fastapi_integration: ModuleConfig = Field(default_factory=ModuleConfig)
    monitoring: ModuleConfig = Field(default_factory=ModuleConfig)
    user_management: ModuleConfig = Field(default_factory=ModuleConfig)
    
    @classmethod
    def from_env(cls) -> "ModulesConfig":
        """Create modules config from environment variables."""
        return cls(
            workflow_automation=ModuleConfig(
                enabled=os.getenv("MODULE_WORKFLOW_AUTOMATION_ENABLED", "true").lower() == "true"
            ),
            fastapi_integration=ModuleConfig(
                enabled=os.getenv("MODULE_FASTAPI_INTEGRATION_ENABLED", "true").lower() == "true"
            ),
            monitoring=ModuleConfig(
                enabled=os.getenv("MODULE_MONITORING_ENABLED", "true").lower() == "true"
            ),
            user_management=ModuleConfig(
                enabled=os.getenv("MODULE_USER_MANAGEMENT_ENABLED", "true").lower() == "true"
            )
        )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    format: str = "json"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Create logging config from environment variables."""
        return cls(
            level=LogLevel(os.getenv("LOG_LEVEL", "INFO")),
            format=os.getenv("LOG_FORMAT", "json"),
            file_path=os.getenv("LOG_FILE_PATH"),
            max_file_size=int(os.getenv("LOG_MAX_FILE_SIZE", str(10 * 1024 * 1024))),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
        )


class PlaygroundConfig(BaseSettings):
    """
    Main configuration class for the n8n API Playground.
    
    This class aggregates all configuration sections and provides
    a single point of access for application configuration.
    """
    
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    testing: bool = False
    
    # Project info
    project_name: str = "n8n API Playground"
    version: str = "1.0.0"
    description: str = "Comprehensive n8n API integration and workflow automation platform"
    
    # Configuration sections
    server: ServerConfig = Field(default_factory=ServerConfig.from_env)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig.from_env)
    cache: CacheConfig = Field(default_factory=CacheConfig.from_env)
    n8n_api: N8nApiConfig = Field(default_factory=N8nApiConfig.from_env)
    security: SecurityConfig = Field(default_factory=SecurityConfig.from_env)
    modules: ModulesConfig = Field(default_factory=ModulesConfig.from_env)
    logging: LoggingConfig = Field(default_factory=LoggingConfig.from_env)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
        
        @classmethod
        def customise_sources(
            cls,
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load configuration from environment
        self.environment = Environment(os.getenv("ENVIRONMENT", "development"))
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.testing = os.getenv("TESTING", "false").lower() == "true"
        
        # Override debug based on environment
        if self.environment == Environment.PRODUCTION:
            self.debug = False
        
        # Load section configurations
        self.server = ServerConfig.from_env()
        self.database = DatabaseConfig.from_env()
        self.cache = CacheConfig.from_env()
        self.n8n_api = N8nApiConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.modules = ModulesConfig.from_env()
        self.logging = LoggingConfig.from_env()
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration settings."""
        # Validate required settings for production
        if self.environment == Environment.PRODUCTION:
            if self.security.secret_key == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            
            if not self.n8n_api.api_key and not (self.n8n_api.username and self.n8n_api.password):
                raise ValueError("n8n API credentials must be set in production")
        
        # Validate database configuration
        if self.database.type != DatabaseType.SQLITE and not self.database.password:
            logger.warning("Database password not set for non-SQLite database")
        
        # Validate cache configuration
        if self.cache.type == CacheType.REDIS and not self.cache.host:
            raise ValueError("Redis host must be set when using Redis cache")
        
        # Create data directory for SQLite
        if self.database.type == DatabaseType.SQLITE:
            data_dir = Path("./data")
            data_dir.mkdir(exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING or self.testing
    
    def get_database_url(self) -> str:
        """Get database URL."""
        return self.database.url
    
    def get_cache_url(self) -> str:
        """Get cache URL."""
        return self.cache.url
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "testing": self.testing,
            "project_name": self.project_name,
            "version": self.version,
            "description": self.description,
            "server": self.server.__dict__,
            "database": {
                **self.database.__dict__,
                "password": "***" if self.database.password else ""
            },
            "cache": {
                **self.cache.__dict__,
                "password": "***" if self.cache.password else ""
            },
            "n8n_api": {
                **self.n8n_api.__dict__,
                "api_key": "***" if self.n8n_api.api_key else "",
                "password": "***" if self.n8n_api.password else ""
            },
            "security": {
                **self.security.__dict__,
                "secret_key": "***"
            },
            "modules": {
                "workflow_automation": self.modules.workflow_automation.__dict__,
                "fastapi_integration": self.modules.fastapi_integration.__dict__,
                "monitoring": self.modules.monitoring.__dict__,
                "user_management": self.modules.user_management.__dict__
            },
            "logging": self.logging.__dict__
        }


# Global configuration instance
config = PlaygroundConfig()


def get_config() -> PlaygroundConfig:
    """Get the global configuration instance."""
    return config


def reload_config() -> PlaygroundConfig:
    """Reload configuration from environment."""
    global config
    config = PlaygroundConfig()
    return config