"""Tests for health endpoints."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_basic_health_check(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    def test_detailed_health_check(self, client: TestClient):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "system" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_async_health_check(self, async_client: AsyncClient):
        """Test health check with async client."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy", "degraded"]

    def test_service_health_status(self, client: TestClient):
        """Test individual service health status."""
        response = client.get("/health/services/database")
        assert response.status_code in [200, 503]  # Healthy or unhealthy
        
        response = client.get("/health/services/redis")
        assert response.status_code in [200, 503]
        
        response = client.get("/health/services/n8n")
        assert response.status_code in [200, 503]

    def test_metrics_endpoint(self, client: TestClient):
        """Test metrics endpoint."""
        response = client.get("/health/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "application" in data

    def test_invalid_service_health(self, client: TestClient):
        """Test health check for non-existent service."""
        response = client.get("/health/services/nonexistent")
        assert response.status_code == 404

    def test_health_check_response_format(self, client: TestClient):
        """Test that health check response has correct format."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check status values
        assert data["status"] in ["healthy", "unhealthy", "degraded"]
        
        # Check timestamp format (ISO 8601)
        import datetime
        try:
            datetime.datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Invalid timestamp format")

    def test_health_check_headers(self, client: TestClient):
        """Test health check response headers."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.integration
    def test_health_check_with_dependencies(self, client: TestClient):
        """Test health check when dependencies are available."""
        # This test would require actual services running
        # Mark as integration test
        response = client.get("/health/detailed")
        data = response.json()
        
        if response.status_code == 200:
            assert "services" in data
            services = data["services"]
            
            # Check that service statuses are reported
            for service_name, service_data in services.items():
                assert "status" in service_data
                assert "response_time" in service_data
                assert service_data["status"] in ["healthy", "unhealthy", "unknown"]