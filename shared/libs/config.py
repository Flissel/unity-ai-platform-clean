#!/usr/bin/env python3
"""
Configuration management for shared Python scripts in UnityAI.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional


class ScriptConfig:
    """Configuration class for shared scripts."""
    
    def __init__(self):
        self.base_dir = Path("/shared")
        self.scripts_dir = self.base_dir / "scripts"
        self.libs_dir = self.base_dir / "libs"
        self.data_dir = Path("/app/data")
        self.logs_dir = Path("/app/logs")
        
        # Environment-based configuration
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")
        
        # Database configuration
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL")
        
        # API endpoints
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678")
        self.fastapi_url = os.getenv("FASTAPI_URL", "http://app:8000")
        
        # Script execution settings
        self.max_execution_time = int(os.getenv("MAX_SCRIPT_EXECUTION_TIME", "300"))  # 5 minutes
        self.max_memory_mb = int(os.getenv("MAX_SCRIPT_MEMORY_MB", "512"))
        self.temp_dir = Path(os.getenv("TEMP_DIR", "/tmp"))
        
        # Security settings
        self.allow_file_operations = os.getenv("ALLOW_FILE_OPERATIONS", "true").lower() == "true"
        self.allow_network_access = os.getenv("ALLOW_NETWORK_ACCESS", "true").lower() == "true"
        self.allowed_domains = os.getenv("ALLOWED_DOMAINS", "").split(",") if os.getenv("ALLOWED_DOMAINS") else []
        
        # External service configurations
        self.external_apis = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        }
    
    def get_script_path(self, category: str, script_name: str) -> Path:
        """Get full path to a script."""
        return self.scripts_dir / category / script_name
    
    def get_requirements_path(self, category: str) -> Path:
        """Get path to requirements.txt for a script category."""
        return self.scripts_dir / category / "requirements.txt"
    
    def get_temp_file_path(self, filename: str) -> Path:
        """Get path for temporary file."""
        return self.temp_dir / filename
    
    def get_data_file_path(self, filename: str) -> Path:
        """Get path for data file."""
        return self.data_dir / filename
    
    def get_log_file_path(self, filename: str) -> Path:
        """Get path for log file."""
        return self.logs_dir / filename
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for external service."""
        return self.external_apis.get(f"{service}_api_key")
    
    def validate_domain(self, url: str) -> bool:
        """Validate if URL domain is allowed."""
        if not self.allowed_domains:
            return True  # No restrictions if no domains specified
        
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return any(domain.endswith(allowed) for allowed in self.allowed_domains)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "base_dir": str(self.base_dir),
            "scripts_dir": str(self.scripts_dir),
            "libs_dir": str(self.libs_dir),
            "data_dir": str(self.data_dir),
            "logs_dir": str(self.logs_dir),
            "environment": self.environment,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "max_execution_time": self.max_execution_time,
            "max_memory_mb": self.max_memory_mb,
            "temp_dir": str(self.temp_dir),
            "allow_file_operations": self.allow_file_operations,
            "allow_network_access": self.allow_network_access,
            "allowed_domains": self.allowed_domains,
            "n8n_webhook_url": self.n8n_webhook_url,
            "fastapi_url": self.fastapi_url,
        }


# Global configuration instance
_config = None


def get_config() -> ScriptConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = ScriptConfig()
    return _config


def reload_config() -> ScriptConfig:
    """Reload configuration from environment."""
    global _config
    _config = ScriptConfig()
    return _config


# Script category configurations
SCRIPT_CATEGORIES = {
    "data_processing": {
        "description": "Data analysis, transformation, and aggregation scripts",
        "default_timeout": 300,
        "max_memory_mb": 1024,
        "required_packages": ["pandas", "numpy", "scipy"]
    },
    "web_scraping": {
        "description": "Web scraping and content extraction scripts",
        "default_timeout": 180,
        "max_memory_mb": 512,
        "required_packages": ["requests", "beautifulsoup4", "selenium"]
    },
    "ml_inference": {
        "description": "Machine learning inference and analysis scripts",
        "default_timeout": 600,
        "max_memory_mb": 2048,
        "required_packages": ["scikit-learn", "transformers", "torch"]
    },
    "document_processing": {
        "description": "Document parsing and text extraction scripts",
        "default_timeout": 240,
        "max_memory_mb": 512,
        "required_packages": ["PyPDF2", "python-docx", "openpyxl"]
    },
    "utilities": {
        "description": "General utility and helper scripts",
        "default_timeout": 120,
        "max_memory_mb": 256,
        "required_packages": ["requests", "python-dateutil"]
    }
}


def get_category_config(category: str) -> Dict[str, Any]:
    """Get configuration for a script category."""
    return SCRIPT_CATEGORIES.get(category, SCRIPT_CATEGORIES["utilities"])


def list_categories() -> list:
    """List all available script categories."""
    return list(SCRIPT_CATEGORIES.keys())