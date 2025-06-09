#!/usr/bin/env python3
"""
Configuration Management for n8n API Playground

Centralized configuration handling with environment variable support,
validation, and dynamic configuration updates.

Author: UnityAI Team
Version: 1.0.0
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel, Field, validator, root_validator

# Setup structured logging
logger = structlog.get_logger(__name__)


class N8nApiConfig(BaseModel):
    """n8n API configuration."""
    
    base_url: str = Field(..., description="n8n instance base URL")
    api_key: str = Field(..., description="n8n API key")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v.rstrip('/')
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    url: Optional[str] = Field(default=None, description="Database URL")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="n8n_playground", description="Database name")
    username: str = Field(default="postgres", description="Database username")
    password: str = Field(..., description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Maximum pool overflow")
    
    @root_validator(skip_on_failure=True)
    def build_url(cls, values):
        if not values.get('url'):
            values['url'] = (
                f"postgresql://{values['username']}:{values['password']}"
                f"@{values['host']}:{values['port']}/{values['name']}"
            )
        return values


class RedisConfig(BaseModel):
    """Redis configuration."""
    
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")
    max_connections: int = Field(default=20, description="Maximum connections")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    
    @property
    def url(self) -> str:
        """Build Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class ServerConfig(BaseModel):
    """Server configuration."""
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    reload: bool = Field(default=False, description="Auto-reload on changes")
    access_log: bool = Field(default=True, description="Enable access logging")
    use_colors: bool = Field(default=True, description="Use colored output")
    loop: str = Field(default="asyncio", description="Event loop type")
    
    @validator('port')
    def validate_port(cls, v):
        if v <= 0 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class SecurityConfig(BaseModel):
    """Security configuration."""
    
    secret_key: str = Field(..., description="Application secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration: int = Field(default=3600, description="JWT expiration in seconds")
    cors_origins: List[str] = Field(default_factory=list, description="CORS allowed origins")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json, text)")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(default=10485760, description="Max log file size in bytes (10MB)")
    backup_count: int = Field(default=5, description="Number of backup log files")
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


class PlaygroundConfig(BaseModel):
    """Playground-specific configuration."""
    
    max_concurrent_executions: int = Field(default=10, description="Maximum concurrent workflow executions")
    execution_timeout: int = Field(default=300, description="Workflow execution timeout in seconds")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    max_session_history: int = Field(default=100, description="Maximum session history entries")
    auto_cleanup_interval: int = Field(default=3600, description="Auto cleanup interval in seconds")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_webhooks: bool = Field(default=True, description="Enable webhook support")
    webhook_timeout: int = Field(default=30, description="Webhook timeout in seconds")
    
    @validator('max_concurrent_executions')
    def validate_max_executions(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Max concurrent executions must be between 1 and 100')
        return v


class ModuleConfig(BaseModel):
    """Module configuration."""
    
    enabled_modules: List[str] = Field(
        default=["workflow_automation", "fastapi_integration", "monitoring", "user_management"],
        description="List of enabled modules"
    )
    module_timeout: int = Field(default=60, description="Module operation timeout in seconds")
    auto_reload: bool = Field(default=False, description="Auto-reload modules on changes")
    
    @validator('enabled_modules')
    def validate_modules(cls, v):
        valid_modules = [
            "workflow_automation",
            "fastapi_integration", 
            "monitoring",
            "user_management"
        ]
        for module in v:
            if module not in valid_modules:
                raise ValueError(f'Invalid module: {module}. Valid modules: {valid_modules}')
        return v


class Config(BaseModel):
    """Main configuration class."""
    
    # Environment
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Component configurations
    server: ServerConfig
    n8n_api: N8nApiConfig
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    logging: LoggingConfig
    playground: PlaygroundConfig
    modules: ModuleConfig
    
    # Paths
    base_path: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    templates_path: Path = Field(default=None)
    logs_path: Path = Field(default=None)
    
    @root_validator(skip_on_failure=True)
    def set_default_paths(cls, values):
        base_path = values.get('base_path', Path(__file__).parent.parent)
        
        if not values.get('templates_path'):
            values['templates_path'] = base_path / 'templates'
        
        if not values.get('logs_path'):
            values['logs_path'] = base_path / 'logs'
        
        return values
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v
    
    class Config:
        env_prefix = "N8N_PLAYGROUND_"
        case_sensitive = False
        validate_assignment = True


class ConfigManager:
    """Configuration manager with environment variable support."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._config: Optional[Config] = None
        self._env_overrides: Dict[str, Any] = {}
    
    def load_config(self) -> Config:
        """Load configuration from environment and file."""
        
        try:
            # Load from environment variables
            config_data = self._load_from_env()
            
            # Load from file if specified
            if self.config_file and os.path.exists(self.config_file):
                file_data = self._load_from_file()
                config_data.update(file_data)
            
            # Create configuration
            self._config = Config(**config_data)
            
            logger.info(
                "Configuration loaded successfully",
                environment=self._config.environment,
                debug=self._config.debug,
                modules=len(self._config.modules.enabled_modules)
            )
            
            return self._config
        
        except Exception as e:
            logger.error(
                "Failed to load configuration",
                error=str(e)
            )
            raise
    
    def get_config(self) -> Config:
        """Get current configuration."""
        
        if self._config is None:
            self._config = self.load_config()
        
        return self._config
    
    def reload_config(self) -> Config:
        """Reload configuration."""
        
        self._config = None
        return self.load_config()
    
    def update_config(self, updates: Dict[str, Any]) -> Config:
        """Update configuration with new values."""
        
        if self._config is None:
            self._config = self.load_config()
        
        # Apply updates
        config_dict = self._config.dict()
        self._deep_update(config_dict, updates)
        
        # Recreate configuration
        self._config = Config(**config_dict)
        
        logger.info(
            "Configuration updated",
            updates=list(updates.keys())
        )
        
        return self._config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        
        config_data = {
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            
            'server': ServerConfig(
                host=os.getenv('SERVER_HOST', '0.0.0.0'),
                port=int(os.getenv('SERVER_PORT', '8080')),
                workers=int(os.getenv('SERVER_WORKERS', '1')),
                reload=os.getenv('SERVER_RELOAD', 'false').lower() == 'true',
                access_log=os.getenv('SERVER_ACCESS_LOG', 'true').lower() == 'true',
                use_colors=os.getenv('SERVER_USE_COLORS', 'true').lower() == 'true',
                loop=os.getenv('SERVER_LOOP', 'asyncio')
            ),
            
            'n8n_api': N8nApiConfig(
                base_url=os.getenv('N8N_BASE_URL', 'http://localhost:5678'),
                api_key=os.getenv('N8N_API_KEY', ''),
                timeout=int(os.getenv('N8N_API_TIMEOUT', '30')),
                max_retries=int(os.getenv('N8N_API_MAX_RETRIES', '3')),
                retry_delay=float(os.getenv('N8N_API_RETRY_DELAY', '1.0')),
                verify_ssl=os.getenv('N8N_API_VERIFY_SSL', 'true').lower() == 'true'
            ),
            
            'database': DatabaseConfig(
                url=os.getenv('DATABASE_URL'),
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
                name=os.getenv('DB_NAME', 'n8n_playground'),
                username=os.getenv('DB_USERNAME', 'postgres'),
                password=os.getenv('DB_PASSWORD', '')
            ),
            
            'redis': RedisConfig(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                password=os.getenv('REDIS_PASSWORD'),
                db=int(os.getenv('REDIS_DB', '0'))
            ),
            
            'security': SecurityConfig(
                secret_key=os.getenv('SECRET_KEY', self._generate_secret_key()),
                cors_origins=os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
            ),
            
            'logging': LoggingConfig(
                level=os.getenv('LOG_LEVEL', 'INFO'),
                format=os.getenv('LOG_FORMAT', 'json'),
                file_path=os.getenv('LOG_FILE_PATH')
            ),
            
            'playground': PlaygroundConfig(
                max_concurrent_executions=int(os.getenv('MAX_CONCURRENT_EXECUTIONS', '10')),
                execution_timeout=int(os.getenv('EXECUTION_TIMEOUT', '300')),
                enable_metrics=os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
                enable_webhooks=os.getenv('ENABLE_WEBHOOKS', 'true').lower() == 'true'
            ),
            
            'modules': ModuleConfig(
                enabled_modules=os.getenv('ENABLED_MODULES', 'workflow_automation,fastapi_integration,monitoring,user_management').split(','),
                auto_reload=os.getenv('MODULE_AUTO_RELOAD', 'false').lower() == 'true'
            )
        }
        
        return config_data
    
    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from file."""
        
        import json
        import yaml
        
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.endswith('.json'):
                    return json.load(f)
                elif self.config_file.endswith(('.yml', '.yaml')):
                    return yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {self.config_file}")
        
        except Exception as e:
            logger.warning(
                "Failed to load config file",
                file=self.config_file,
                error=str(e)
            )
            return {}
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Deep update dictionary."""
        
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _generate_secret_key(self) -> str:
        """Generate a random secret key."""
        
        import secrets
        return secrets.token_urlsafe(32)


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get global configuration instance."""
    return config_manager.get_config()


def reload_config() -> Config:
    """Reload global configuration."""
    return config_manager.reload_config()


def update_config(updates: Dict[str, Any]) -> Config:
    """Update global configuration."""
    return config_manager.update_config(updates)