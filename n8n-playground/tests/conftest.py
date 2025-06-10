#!/usr/bin/env python3
"""Pytest configuration and shared fixtures."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DB_TYPE"] = "sqlite"
os.environ["DB_NAME"] = ":memory:"
os.environ["CACHE_TYPE"] = "memory"
os.environ["N8N_API_BASE_URL"] = "http://localhost:5678"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return {
        "server": {
            "host": "localhost",
            "port": 8080,
            "debug": True
        },
        "database": {
            "type": "sqlite",
            "name": ":memory:",
            "host": "localhost",
            "port": 5432,
            "username": "test",
            "password": "test"
        },
        "cache": {
            "type": "memory",
            "host": "localhost",
            "port": 6379,
            "db": 0
        },
        "n8n_api": {
            "base_url": "http://localhost:5678",
            "api_key": "test-api-key",
            "timeout": 30,
            "max_retries": 3
        },
        "security": {
            "secret_key": "test-secret-key",
            "algorithm": "HS256",
            "access_token_expire_minutes": 30
        }
    }


@pytest.fixture
def mock_n8n_client():
    """Mock n8n API client."""
    client = AsyncMock()
    
    # Mock workflow responses
    client.get_workflows.return_value = {
        "data": [
            {
                "id": "1",
                "name": "Test Workflow",
                "active": True,
                "nodes": [],
                "connections": {},
                "settings": {}
            }
        ]
    }
    
    client.create_workflow.return_value = {
        "id": "1",
        "name": "Test Workflow",
        "active": True,
        "nodes": [],
        "connections": {},
        "settings": {}
    }
    
    client.execute_workflow.return_value = {
        "id": "exec_1",
        "workflowId": "1",
        "mode": "manual",
        "status": "success",
        "data": {"resultData": {"runData": {}}}
    }
    
    return client


@pytest.fixture
def mock_database():
    """Mock database session."""
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def mock_async_database():
    """Mock async database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def mock_cache():
    """Mock cache client."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.exists = AsyncMock(return_value=False)
    return cache


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for tests."""
    return {
        "name": "Test Workflow",
        "nodes": [
            {
                "id": "node1",
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {}
            },
            {
                "id": "node2",
                "name": "HTTP Request",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 1,
                "position": [450, 300],
                "parameters": {
                    "url": "https://api.example.com/data",
                    "method": "GET"
                }
            }
        ],
        "connections": {
            "Start": {
                "main": [
                    [
                        {
                            "node": "HTTP Request",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        },
        "settings": {
            "executionOrder": "v1"
        }
    }


@pytest.fixture
def sample_template_data():
    """Sample template data for tests."""
    return {
        "name": "HTTP Request Template",
        "description": "Basic HTTP request template",
        "version": "1.0.0",
        "parameters": {
            "url": {
                "type": "string",
                "required": True,
                "description": "Target URL"
            },
            "method": {
                "type": "string",
                "default": "GET",
                "allowed_values": ["GET", "POST", "PUT", "DELETE"]
            }
        },
        "workflow": {
            "nodes": [
                {
                    "id": "start",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "parameters": {}
                },
                {
                    "id": "http",
                    "name": "HTTP Request",
                    "type": "n8n-nodes-base.httpRequest",
                    "parameters": {
                        "url": "{{ url }}",
                        "method": "{{ method }}"
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_execution_data():
    """Sample execution data for tests."""
    return {
        "id": "exec_123",
        "workflowId": "workflow_123",
        "mode": "manual",
        "status": "success",
        "startedAt": "2024-01-01T10:00:00Z",
        "finishedAt": "2024-01-01T10:01:00Z",
        "data": {
            "resultData": {
                "runData": {
                    "Start": [
                        {
                            "hints": [],
                            "startTime": 1704103200000,
                            "executionTime": 1,
                            "source": [],
                            "executionStatus": "success",
                            "data": {
                                "main": [
                                    [
                                        {
                                            "json": {},
                                            "pairedItem": {"item": 0}
                                        }
                                    ]
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_workflow_manager():
    """Mock workflow manager."""
    manager = AsyncMock()
    manager.create_workflow.return_value = MagicMock(id="workflow_123")
    manager.get_workflow.return_value = MagicMock(id="workflow_123")
    manager.execute_workflow.return_value = MagicMock(id="exec_123")
    manager.list_workflows.return_value = []
    return manager


@pytest.fixture
def mock_template_engine():
    """Mock template engine."""
    engine = MagicMock()
    engine.load_template.return_value = {"name": "test", "workflow": {}}
    engine.render_template.return_value = {"nodes": [], "connections": {}}
    engine.validate_template.return_value = True
    return engine


@pytest.fixture
def mock_validator():
    """Mock validator."""
    validator = MagicMock()
    validator.validate_workflow.return_value = True
    validator.validate_parameters.return_value = True
    validator.validate_template.return_value = True
    return validator


# Async test configuration
pytest_asyncio.fixture(scope="session")
async def async_test_client():
    """Async test client for FastAPI."""
    from main import create_app
    
    app = create_app()
    
    # Use async test client when available
    # For now, use regular TestClient
    with TestClient(app) as client:
        yield client