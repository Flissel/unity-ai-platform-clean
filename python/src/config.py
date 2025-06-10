#!/usr/bin/env python3
"""
Configuration settings for UnityAI Python Worker Service.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service configuration
    service_name: str = Field(default="python-worker", env="SERVICE_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Database configuration
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Redis configuration
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=1, env="REDIS_DB")  # Use DB 1 for Python worker
    
    # n8n integration
    n8n_base_url: str = Field(default="http://n8n:5678", env="N8N_BASE_URL")
    n8n_api_key: Optional[str] = Field(default=None, env="N8N_API_KEY")
    
    # FastAPI main app integration
    fastapi_base_url: str = Field(default="http://app:8000", env="FASTAPI_BASE_URL")
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Task execution settings
    max_concurrent_tasks: int = Field(default=10, env="MAX_CONCURRENT_TASKS")
    task_timeout: int = Field(default=300, env="TASK_TIMEOUT")  # 5 minutes
    
    # File storage
    data_dir: str = Field(default="/app/data", env="DATA_DIR")
    temp_dir: str = Field(default="/app/temp", env="TEMP_DIR")
    logs_dir: str = Field(default="/app/logs", env="LOGS_DIR")
    
    # AI/ML model settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    huggingface_token: Optional[str] = Field(default=None, env="HUGGINGFACE_TOKEN")
    
    # Security settings
    api_key: Optional[str] = Field(default=None, env="PYTHON_WORKER_API_KEY")
    allowed_hosts: list = Field(default=["*"], env="ALLOWED_HOSTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_redis_url(self) -> str:
        """Get Redis URL with authentication."""
        if self.redis_url:
            return self.redis_url
        
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def get_database_url(self) -> Optional[str]:
        """Get database URL."""
        return self.database_url


# Global settings instance
settings = Settings()