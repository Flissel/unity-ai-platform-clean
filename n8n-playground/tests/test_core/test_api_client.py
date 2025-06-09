#!/usr/bin/env python3
"""Tests for core.api_client module."""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientResponse
from aioresponses import aioresponses

from core.api_client import (
    N8nApiClient,
    N8nApiConfig,
    N8nApiResponse,
    N8nApiError,
    N8nConnectionError,
    N8nAuthenticationError,
    N8nValidationError
)


class TestN8nApiConfig:
    """Test N8nApiConfig model."""
    
    def test_valid_config(self):
        """Test creating valid configuration."""
        config = N8nApiConfig(
            base_url="https://n8n.example.com",
            api_key="test-api-key"
        )
        
        assert config.base_url == "https://n8n.example.com"
        assert config.api_key == "test-api-key"
        assert config.timeout == 30
        assert config.max_retries == 3
    
    def test_base_url_validation(self):
        """Test base URL validation."""
        # Valid URLs
        valid_urls = [
            "http://localhost:5678",
            "https://n8n.example.com",
            "http://192.168.1.100:5678"
        ]
        
        for url in valid_urls:
            config = N8nApiConfig(base_url=url, api_key="test")
            assert config.base_url == url
    
    def test_invalid_base_url(self):
        """Test invalid base URL raises error."""
        with pytest.raises(ValueError, match="base_url must start with http"):
            N8nApiConfig(base_url="invalid-url", api_key="test")
    
    def test_base_url_trailing_slash_removal(self):
        """Test trailing slash is removed from base URL."""
        config = N8nApiConfig(
            base_url="https://n8n.example.com/",
            api_key="test"
        )
        assert config.base_url == "https://n8n.example.com"


class TestN8nApiResponse:
    """Test N8nApiResponse model."""
    
    def test_successful_response(self):
        """Test creating successful response."""
        response = N8nApiResponse(
            success=True,
            data={"id": "123", "name": "test"},
            status_code=200,
            execution_time=0.5
        )
        
        assert response.success is True
        assert response.data == {"id": "123", "name": "test"}
        assert response.error is None
        assert response.status_code == 200
        assert response.execution_time == 0.5
        assert isinstance(response.timestamp, datetime)
    
    def test_error_response(self):
        """Test creating error response."""
        response = N8nApiResponse(
            success=False,
            error="API Error",
            status_code=400
        )
        
        assert response.success is False
        assert response.data is None
        assert response.error == "API Error"
        assert response.status_code == 400


@pytest.mark.asyncio
class TestN8nApiClient:
    """Test N8nApiClient class."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return N8nApiConfig(
            base_url="https://n8n.example.com",
            api_key="test-api-key",
            timeout=10,
            max_retries=2
        )
    
    @pytest.fixture
    def client(self, config):
        """Test client instance."""
        return N8nApiClient(config)
    
    async def test_client_initialization(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client.session is None
        assert client._base_headers['X-N8N-API-KEY'] == "test-api-key"
        assert client._base_headers['Content-Type'] == "application/json"
    
    async def test_context_manager(self, client):
        """Test client as async context manager."""
        async with client as c:
            assert c.session is not None
            assert isinstance(c.session, ClientSession)
        
        assert client.session is None
    
    async def test_start_and_close(self, client):
        """Test manual start and close."""
        await client.start()
        assert client.session is not None
        
        await client.close()
        assert client.session is None
    
    async def test_make_request_success(self, client):
        """Test successful API request."""
        with aioresponses() as m:
            m.get(
                "https://n8n.example.com/api/v1/workflows",
                payload={"data": [{"id": "1", "name": "test"}]},
                status=200
            )
            
            async with client:
                response = await client._make_request("GET", "workflows")
            
            assert response.success is True
            assert response.status_code == 200
            assert response.data == {"data": [{"id": "1", "name": "test"}]}
            assert response.execution_time is not None
    
    async def test_make_request_error(self, client):
        """Test API request with error response."""
        with aioresponses() as m:
            m.get(
                "https://n8n.example.com/api/v1/workflows",
                payload={"message": "Not found"},
                status=404
            )
            
            async with client:
                response = await client._make_request("GET", "workflows")
            
            assert response.success is False
            assert response.status_code == 404
            assert "Not found" in str(response.error)
    
    async def test_make_request_with_retry(self, client):
        """Test request retry on failure."""
        with aioresponses() as m:
            # First two requests fail, third succeeds
            m.get(
                "https://n8n.example.com/api/v1/workflows",
                status=500,
                repeat=True
            )
            m.get(
                "https://n8n.example.com/api/v1/workflows",
                payload={"data": []},
                status=200
            )
            
            async with client:
                response = await client._make_request("GET", "workflows")
            
            # Should eventually succeed after retries
            assert response.success is False  # Will fail after max retries
            assert response.status_code == 500
    
    async def test_get_workflows(self, client):
        """Test get workflows method."""
        with aioresponses() as m:
            m.get(
                "https://n8n.example.com/api/v1/workflows",
                payload={
                    "data": [
                        {"id": "1", "name": "Workflow 1", "active": True},
                        {"id": "2", "name": "Workflow 2", "active": False}
                    ]
                },
                status=200
            )
            
            async with client:
                workflows = await client.get_workflows()
            
            assert len(workflows) == 2
            assert workflows[0]["id"] == "1"
            assert workflows[1]["name"] == "Workflow 2"
    
    async def test_get_workflow_by_id(self, client):
        """Test get workflow by ID method."""
        workflow_data = {
            "id": "123",
            "name": "Test Workflow",
            "active": True,
            "nodes": [],
            "connections": {}
        }
        
        with aioresponses() as m:
            m.get(
                "https://n8n.example.com/api/v1/workflows/123",
                payload=workflow_data,
                status=200
            )
            
            async with client:
                workflow = await client.get_workflow("123")
            
            assert workflow["id"] == "123"
            assert workflow["name"] == "Test Workflow"
    
    async def test_create_workflow(self, client, sample_workflow_data):
        """Test create workflow method."""
        created_workflow = {**sample_workflow_data, "id": "new_123"}
        
        with aioresponses() as m:
            m.post(
                "https://n8n.example.com/api/v1/workflows",
                payload=created_workflow,
                status=201
            )
            
            async with client:
                workflow = await client.create_workflow(sample_workflow_data)
            
            assert workflow["id"] == "new_123"
            assert workflow["name"] == sample_workflow_data["name"]
    
    async def test_update_workflow(self, client, sample_workflow_data):
        """Test update workflow method."""
        updated_data = {**sample_workflow_data, "name": "Updated Workflow"}
        
        with aioresponses() as m:
            m.put(
                "https://n8n.example.com/api/v1/workflows/123",
                payload=updated_data,
                status=200
            )
            
            async with client:
                workflow = await client.update_workflow("123", updated_data)
            
            assert workflow["name"] == "Updated Workflow"
    
    async def test_delete_workflow(self, client):
        """Test delete workflow method."""
        with aioresponses() as m:
            m.delete(
                "https://n8n.example.com/api/v1/workflows/123",
                status=204
            )
            
            async with client:
                result = await client.delete_workflow("123")
            
            assert result is True
    
    async def test_execute_workflow(self, client):
        """Test execute workflow method."""
        execution_data = {
            "id": "exec_123",
            "workflowId": "123",
            "mode": "manual",
            "status": "running"
        }
        
        with aioresponses() as m:
            m.post(
                "https://n8n.example.com/api/v1/workflows/123/execute",
                payload=execution_data,
                status=200
            )
            
            async with client:
                execution = await client.execute_workflow(
                    "123",
                    {"data": {"test": "value"}}
                )
            
            assert execution["id"] == "exec_123"
            assert execution["workflowId"] == "123"
    
    async def test_get_executions(self, client):
        """Test get executions method."""
        executions_data = {
            "data": [
                {"id": "exec_1", "status": "success"},
                {"id": "exec_2", "status": "error"}
            ],
            "nextCursor": None
        }
        
        with aioresponses() as m:
            m.get(
                "https://n8n.example.com/api/v1/executions",
                payload=executions_data,
                status=200
            )
            
            async with client:
                executions = await client.get_executions()
            
            assert len(executions["data"]) == 2
            assert executions["data"][0]["id"] == "exec_1"
    
    async def test_get_execution_by_id(self, client, sample_execution_data):
        """Test get execution by ID method."""
        with aioresponses() as m:
            m.get(
                "https://n8n.example.com/api/v1/executions/exec_123",
                payload=sample_execution_data,
                status=200
            )
            
            async with client:
                execution = await client.get_execution("exec_123")
            
            assert execution["id"] == "exec_123"
            assert execution["status"] == "success"
    
    async def test_health_check(self, client):
        """Test health check method."""
        with aioresponses() as m:
            m.get(
                "https://n8n.example.com/healthz",
                payload={"status": "ok"},
                status=200
            )
            
            async with client:
                health = await client.health_check()
            
            assert health["status"] == "ok"
    
    async def test_authentication_error(self, client):
        """Test authentication error handling."""
        with aioresponses() as m:
            m.get(
                "https://n8n.example.com/api/v1/workflows",
                status=401
            )
            
            async with client:
                with pytest.raises(N8nAuthenticationError):
                    await client.get_workflows()
    
    async def test_connection_error(self, client):
        """Test connection error handling."""
        # Mock aiohttp to raise connection error
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = N8nConnectionError("Connection failed")
            
            async with client:
                with pytest.raises(N8nConnectionError):
                    await client.get_workflows()
    
    async def test_validation_error(self, client):
        """Test validation error handling."""
        with aioresponses() as m:
            m.post(
                "https://n8n.example.com/api/v1/workflows",
                payload={"message": "Validation failed"},
                status=422
            )
            
            async with client:
                with pytest.raises(N8nValidationError):
                    await client.create_workflow({"invalid": "data"})


@pytest.mark.integration
class TestN8nApiClientIntegration:
    """Integration tests for N8nApiClient."""
    
    @pytest.mark.requires_n8n
    async def test_real_n8n_connection(self):
        """Test connection to real n8n instance."""
        # This test requires a real n8n instance
        # Skip if N8N_TEST_URL is not set
        import os
        
        test_url = os.getenv("N8N_TEST_URL")
        test_key = os.getenv("N8N_TEST_API_KEY")
        
        if not test_url or not test_key:
            pytest.skip("N8N_TEST_URL and N8N_TEST_API_KEY required")
        
        config = N8nApiConfig(
            base_url=test_url,
            api_key=test_key
        )
        
        async with N8nApiClient(config) as client:
            # Test health check
            health = await client.health_check()
            assert "status" in health
            
            # Test get workflows
            workflows = await client.get_workflows()
            assert isinstance(workflows, list)