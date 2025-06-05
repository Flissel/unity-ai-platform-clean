"""Pytest configuration and fixtures for UnityAI tests."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ENVIRONMENT"] = "test"

from src.api.main import app
from src.core.database import Base, get_db
from src.core.config import get_settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client."""
    mock_redis = mocker.MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    return mock_redis


@pytest.fixture
def mock_n8n_service(mocker):
    """Mock n8n service."""
    mock_service = mocker.MagicMock()
    mock_service.list_workflows.return_value = []
    mock_service.get_workflow.return_value = None
    mock_service.execute_workflow.return_value = {"id": "test-execution"}
    mock_service.get_execution.return_value = None
    mock_service.list_executions.return_value = []
    mock_service.get_statistics.return_value = {}
    return mock_service


@pytest.fixture
def mock_autogen_service(mocker):
    """Mock AutoGen service."""
    mock_service = mocker.MagicMock()
    mock_service.execute_agent.return_value = {"id": "test-execution"}
    mock_service.get_execution.return_value = None
    mock_service.start_conversation.return_value = {"id": "test-conversation"}
    mock_service.get_conversation.return_value = None
    mock_service.analyze_code.return_value = {"analysis": "test"}
    mock_service.list_executions.return_value = []
    mock_service.get_capabilities.return_value = {}
    mock_service.get_statistics.return_value = {}
    return mock_service


@pytest.fixture
def mock_code_execution_service(mocker):
    """Mock code execution service."""
    mock_service = mocker.MagicMock()
    mock_service.execute_code.return_value = {"id": "test-execution"}
    mock_service.get_execution.return_value = None
    mock_service.cancel_execution.return_value = True
    mock_service.list_executions.return_value = []
    mock_service.validate_code.return_value = {"valid": True}
    mock_service.get_capabilities.return_value = {}
    mock_service.get_statistics.return_value = {}
    mock_service.list_active_executions.return_value = []
    return mock_service


@pytest.fixture
def mock_workflow_service(mocker):
    """Mock workflow service."""
    mock_service = mocker.MagicMock()
    mock_service.execute_workflow.return_value = {"id": "test-execution"}
    mock_service.get_execution.return_value = None
    mock_service.cancel_execution.return_value = True
    mock_service.list_executions.return_value = []
    mock_service.list_definitions.return_value = []
    mock_service.get_definition.return_value = None
    mock_service.validate_workflow.return_value = {"valid": True}
    mock_service.get_templates.return_value = []
    mock_service.get_statistics.return_value = {}
    mock_service.list_active_workflows.return_value = []
    return mock_service


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "roles": ["user"],
        "permissions": ["read"],
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing."""
    return {
        "name": "Test Workflow",
        "description": "A test workflow",
        "type": "sequential",
        "steps": [
            {
                "name": "step1",
                "type": "code_execution",
                "config": {"code": "print('Hello, World!')", "language": "python"},
            }
        ],
        "config": {"timeout": 300, "retry_count": 3},
    }


@pytest.fixture
def sample_code_data():
    """Sample code data for testing."""
    return {
        "code": "print('Hello, World!')",
        "language": "python",
        "timeout": 30,
        "environment": "default",
    }


@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing."""
    return {
        "agent_type": "assistant",
        "task": "Help with coding",
        "config": {"model": "gpt-4", "temperature": 0.7},
        "timeout": 300,
    }


# Pytest markers
pytestmark = pytest.mark.asyncio