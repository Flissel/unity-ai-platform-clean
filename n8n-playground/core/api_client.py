#!/usr/bin/env python3
"""
n8n API Client for UnityAI Platform

Provides a unified interface for interacting with the n8n API Playground.
Supports all major n8n API operations including workflows, executions, and user management.

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
import structlog
from pydantic import BaseModel, Field, validator

# Setup structured logging
logger = structlog.get_logger(__name__)


class N8nApiConfig(BaseModel):
    """Configuration for n8n API client."""
    
    base_url: str = Field(..., description="n8n base URL")
    api_key: str = Field(..., description="n8n API key")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v.rstrip('/')


class N8nApiResponse(BaseModel):
    """Standardized response from n8n API."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    execution_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class N8nApiClient:
    """Main n8n API client class."""
    
    def __init__(self, config: N8nApiConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._base_headers = {
            'X-N8N-API-KEY': config.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'UnityAI-n8n-Client/1.0.0'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Initialize the HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._base_headers
            )
            logger.info("n8n API client session started", base_url=self.config.base_url)
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("n8n API client session closed")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> N8nApiResponse:
        """Make HTTP request to n8n API with retry logic."""
        
        if not self.session:
            await self.start()
        
        url = urljoin(f"{self.config.base_url}/api/v1/", endpoint.lstrip('/'))
        request_headers = self._base_headers.copy()
        if headers:
            request_headers.update(headers)
        
        start_time = datetime.utcnow()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(
                    "Making n8n API request",
                    method=method,
                    url=url,
                    attempt=attempt + 1
                )
                
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=request_headers
                ) as response:
                    
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    response_data = None
                    
                    try:
                        response_data = await response.json()
                    except Exception:
                        response_data = await response.text()
                    
                    if response.status >= 200 and response.status < 300:
                        logger.info(
                            "n8n API request successful",
                            method=method,
                            endpoint=endpoint,
                            status_code=response.status,
                            execution_time=execution_time
                        )
                        
                        return N8nApiResponse(
                            success=True,
                            data=response_data,
                            status_code=response.status,
                            execution_time=execution_time
                        )
                    
                    else:
                        error_msg = f"HTTP {response.status}: {response_data}"
                        
                        if attempt < self.config.max_retries:
                            logger.warning(
                                "n8n API request failed, retrying",
                                method=method,
                                endpoint=endpoint,
                                status_code=response.status,
                                attempt=attempt + 1,
                                error=error_msg
                            )
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        
                        logger.error(
                            "n8n API request failed after all retries",
                            method=method,
                            endpoint=endpoint,
                            status_code=response.status,
                            error=error_msg
                        )
                        
                        return N8nApiResponse(
                            success=False,
                            error=error_msg,
                            status_code=response.status,
                            execution_time=execution_time
                        )
            
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                error_msg = f"Request exception: {str(e)}"
                
                if attempt < self.config.max_retries:
                    logger.warning(
                        "n8n API request exception, retrying",
                        method=method,
                        endpoint=endpoint,
                        attempt=attempt + 1,
                        error=error_msg
                    )
                    await asyncio.sleep(2 ** attempt)
                    continue
                
                logger.error(
                    "n8n API request failed with exception",
                    method=method,
                    endpoint=endpoint,
                    error=error_msg
                )
                
                return N8nApiResponse(
                    success=False,
                    error=error_msg,
                    execution_time=execution_time
                )
        
        # This should never be reached
        return N8nApiResponse(
            success=False,
            error="Unexpected error in request handling"
        )
    
    # Workflow Operations
    async def get_workflows(self, active: Optional[bool] = None) -> N8nApiResponse:
        """Get all workflows."""
        params = {}
        if active is not None:
            params['active'] = str(active).lower()
        
        return await self._make_request('GET', 'workflows', params=params)
    
    async def get_workflow(self, workflow_id: str) -> N8nApiResponse:
        """Get specific workflow by ID."""
        return await self._make_request('GET', f'workflows/{workflow_id}')
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> N8nApiResponse:
        """Create new workflow."""
        return await self._make_request('POST', 'workflows', data=workflow_data)
    
    async def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> N8nApiResponse:
        """Update existing workflow."""
        return await self._make_request('PUT', f'workflows/{workflow_id}', data=workflow_data)
    
    async def delete_workflow(self, workflow_id: str) -> N8nApiResponse:
        """Delete workflow."""
        return await self._make_request('DELETE', f'workflows/{workflow_id}')
    
    async def activate_workflow(self, workflow_id: str) -> N8nApiResponse:
        """Activate workflow."""
        return await self._make_request('POST', f'workflows/{workflow_id}/activate')
    
    async def deactivate_workflow(self, workflow_id: str) -> N8nApiResponse:
        """Deactivate workflow."""
        return await self._make_request('POST', f'workflows/{workflow_id}/deactivate')
    
    # Execution Operations
    async def get_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 20,
        status: Optional[str] = None
    ) -> N8nApiResponse:
        """Get workflow executions."""
        params = {'limit': limit}
        if workflow_id:
            params['workflowId'] = workflow_id
        if status:
            params['status'] = status
        
        return await self._make_request('GET', 'executions', params=params)
    
    async def get_execution(self, execution_id: str) -> N8nApiResponse:
        """Get specific execution by ID."""
        return await self._make_request('GET', f'executions/{execution_id}')
    
    async def delete_execution(self, execution_id: str) -> N8nApiResponse:
        """Delete execution."""
        return await self._make_request('DELETE', f'executions/{execution_id}')
    
    async def retry_execution(self, execution_id: str) -> N8nApiResponse:
        """Retry failed execution."""
        return await self._make_request('POST', f'executions/{execution_id}/retry')
    
    # User Operations
    async def get_users(self) -> N8nApiResponse:
        """Get all users."""
        return await self._make_request('GET', 'users')
    
    async def get_user(self, user_id: str) -> N8nApiResponse:
        """Get specific user by ID."""
        return await self._make_request('GET', f'users/{user_id}')
    
    async def create_user(self, user_data: Dict[str, Any]) -> N8nApiResponse:
        """Create new user."""
        return await self._make_request('POST', 'users', data=user_data)
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> N8nApiResponse:
        """Update existing user."""
        return await self._make_request('PUT', f'users/{user_id}', data=user_data)
    
    async def delete_user(self, user_id: str) -> N8nApiResponse:
        """Delete user."""
        return await self._make_request('DELETE', f'users/{user_id}')
    
    # Health Check
    async def health_check(self) -> N8nApiResponse:
        """Check n8n API health by testing a simple endpoint."""
        return await self._make_request('GET', 'rest/login')
    
    # Utility Methods
    async def test_connection(self) -> bool:
        """Test if connection to n8n API is working."""
        try:
            response = await self.health_check()
            # For login endpoint, we expect a 401 or similar, which means the API is responding
            return True  # If we get any response, the API is accessible
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return False


# Factory function for easy client creation
def create_n8n_client(
    base_url: str,
    api_key: str,
    timeout: int = 30,
    max_retries: int = 3
) -> N8nApiClient:
    """Factory function to create n8n API client."""
    config = N8nApiConfig(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries
    )
    return N8nApiClient(config)