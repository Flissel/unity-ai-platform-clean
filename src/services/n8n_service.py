"""n8n service for workflow management and execution."""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import UUID, uuid4

import httpx
from httpx import AsyncClient, Response

from ..core.config import get_settings
from ..core.logging import get_logger, log_execution_time
from ..core.exceptions import N8nServiceError, TimeoutError, ValidationError
from ..core.models import (
    WorkflowDefinition,
    WorkflowExecution,
    ExecutionStatus,
    BaseResponse
)
from ..core.cache import cached, cache_manager

logger = get_logger(__name__)


class N8nService:
    """Service for interacting with n8n workflows."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[AsyncClient] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize n8n service."""
        if self._initialized:
            return
        
        try:
            self.client = AsyncClient(
                base_url=self.settings.n8n.api_url,
                headers={
                    "X-N8N-API-KEY": self.settings.n8n.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=httpx.Timeout(
                    timeout=self.settings.n8n.timeout,
                    connect=10.0
                ),
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20
                )
            )
            
            # Test connection
            await self.health_check()
            
            self._initialized = True
            logger.info("n8n service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize n8n service: {e}")
            raise N8nServiceError(f"n8n service initialization failed: {e}")
    
    async def close(self) -> None:
        """Close n8n service."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self._initialized = False
            logger.info("n8n service closed")
    
    async def _ensure_initialized(self) -> None:
        """Ensure service is initialized."""
        if not self._initialized:
            await self.initialize()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 3
    ) -> Response:
        """Make HTTP request to n8n API with retry logic."""
        await self._ensure_initialized()
        
        if not self.client:
            raise N8nServiceError("n8n client not initialized")
        
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    json=data,
                    params=params
                )
                
                # Check for HTTP errors
                if response.status_code >= 400:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("message", error_detail)
                    except:
                        pass
                    
                    raise N8nServiceError(
                        f"n8n API error {response.status_code}: {error_detail}",
                        error_code=str(response.status_code)
                    )
                
                return response
                
            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"n8n API timeout: {e}")
                logger.warning(f"n8n API timeout (attempt {attempt + 1}/{retries + 1}): {e}")
                
            except httpx.ConnectError as e:
                last_exception = N8nServiceError(f"n8n API connection error: {e}")
                logger.warning(f"n8n API connection error (attempt {attempt + 1}/{retries + 1}): {e}")
                
            except Exception as e:
                last_exception = N8nServiceError(f"n8n API request failed: {e}")
                logger.error(f"n8n API request failed (attempt {attempt + 1}/{retries + 1}): {e}")
            
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_exception
    
    @log_execution_time(logger, "n8n health check")
    async def health_check(self) -> bool:
        """Check n8n service health."""
        try:
            response = await self._make_request("GET", "/healthz", retries=1)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"n8n health check failed: {e}")
            return False
    
    @cached(ttl=300, key_prefix="n8n:workflows")
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows."""
        try:
            response = await self._make_request("GET", "/workflows")
            workflows = response.json().get("data", [])
            
            logger.info(f"Retrieved {len(workflows)} workflows from n8n")
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise N8nServiceError(f"Failed to list workflows: {e}")
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        try:
            response = await self._make_request("GET", f"/workflows/{workflow_id}")
            workflow = response.json()
            
            logger.debug(f"Retrieved workflow {workflow_id}")
            return workflow
            
        except N8nServiceError as e:
            if "404" in str(e):
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            raise N8nServiceError(f"Failed to get workflow: {e}")
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        try:
            # Validate required fields
            if "name" not in workflow_data:
                raise ValidationError("Workflow name is required")
            
            response = await self._make_request("POST", "/workflows", data=workflow_data)
            workflow = response.json()
            
            logger.info(f"Created workflow: {workflow.get('name')} (ID: {workflow.get('id')})")
            
            # Invalidate cache
            await cache_manager.clear_pattern("n8n:workflows:*")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise N8nServiceError(f"Failed to create workflow: {e}")
    
    async def update_workflow(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing workflow."""
        try:
            response = await self._make_request(
                "PUT",
                f"/workflows/{workflow_id}",
                data=workflow_data
            )
            workflow = response.json()
            
            logger.info(f"Updated workflow {workflow_id}")
            
            # Invalidate cache
            await cache_manager.clear_pattern("n8n:workflows:*")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_id}: {e}")
            raise N8nServiceError(f"Failed to update workflow: {e}")
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        try:
            await self._make_request("DELETE", f"/workflows/{workflow_id}")
            
            logger.info(f"Deleted workflow {workflow_id}")
            
            # Invalidate cache
            await cache_manager.clear_pattern("n8n:workflows:*")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            raise N8nServiceError(f"Failed to delete workflow: {e}")
    
    @log_execution_time(logger, "n8n workflow execution")
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = True,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a workflow.
        
        Args:
            workflow_id: Workflow ID to execute
            input_data: Input data for the workflow
            wait_for_completion: Whether to wait for completion
            timeout: Execution timeout in seconds
            
        Returns:
            Execution result
        """
        try:
            execution_data = {
                "workflowData": input_data or {}
            }
            
            response = await self._make_request(
                "POST",
                f"/workflows/{workflow_id}/execute",
                data=execution_data
            )
            
            execution = response.json()
            execution_id = execution.get("data", {}).get("executionId")
            
            logger.info(f"Started workflow execution {execution_id} for workflow {workflow_id}")
            
            if wait_for_completion and execution_id:
                return await self._wait_for_execution(
                    execution_id,
                    timeout or self.settings.n8n.timeout
                )
            
            return execution
            
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            raise N8nServiceError(f"Failed to execute workflow: {e}")
    
    async def trigger_webhook(
        self,
        webhook_path: str,
        data: Optional[Dict[str, Any]] = None,
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Trigger a webhook.
        
        Args:
            webhook_path: Webhook path
            data: Data to send
            method: HTTP method
            
        Returns:
            Webhook response
        """
        try:
            webhook_url = f"{self.settings.n8n.webhook_url}/{webhook_path}"
            
            async with AsyncClient(timeout=self.settings.n8n.timeout) as client:
                response = await client.request(
                    method=method,
                    url=webhook_url,
                    json=data or {}
                )
                
                if response.status_code >= 400:
                    raise N8nServiceError(
                        f"Webhook error {response.status_code}: {response.text}"
                    )
                
                result = response.json() if response.content else {}
                
                logger.info(f"Triggered webhook: {webhook_path}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to trigger webhook {webhook_path}: {e}")
            raise N8nServiceError(f"Failed to trigger webhook: {e}")
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution details."""
        try:
            response = await self._make_request("GET", f"/executions/{execution_id}")
            execution = response.json()
            
            logger.debug(f"Retrieved execution {execution_id}")
            return execution
            
        except N8nServiceError as e:
            if "404" in str(e):
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
            raise N8nServiceError(f"Failed to get execution: {e}")
    
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List executions."""
        try:
            params = {"limit": limit}
            if workflow_id:
                params["workflowId"] = workflow_id
            
            response = await self._make_request("GET", "/executions", params=params)
            executions = response.json().get("data", [])
            
            logger.debug(f"Retrieved {len(executions)} executions")
            return executions
            
        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            raise N8nServiceError(f"Failed to list executions: {e}")
    
    async def _wait_for_execution(
        self,
        execution_id: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Wait for execution to complete."""
        start_time = datetime.utcnow()
        
        while True:
            execution = await self.get_execution(execution_id)
            
            if not execution:
                raise N8nServiceError(f"Execution {execution_id} not found")
            
            status = execution.get("finished", False)
            
            if status:
                logger.info(f"Execution {execution_id} completed")
                return execution
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout:
                raise TimeoutError(f"Execution {execution_id} timed out after {timeout}s")
            
            # Wait before next check
            await asyncio.sleep(2)
    
    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        try:
            workflows = await self.list_workflows()
            executions = await self.list_executions(limit=100)
            
            # Calculate statistics
            total_workflows = len(workflows)
            active_workflows = len([w for w in workflows if w.get("active", False)])
            
            execution_stats = {
                "total": len(executions),
                "success": len([e for e in executions if e.get("finished") and not e.get("stoppedAt")]),
                "failed": len([e for e in executions if e.get("stoppedAt")]),
                "running": len([e for e in executions if not e.get("finished")])
            }
            
            return {
                "workflows": {
                    "total": total_workflows,
                    "active": active_workflows,
                    "inactive": total_workflows - active_workflows
                },
                "executions": execution_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow statistics: {e}")
            raise N8nServiceError(f"Failed to get workflow statistics: {e}")


# Global service instance
n8n_service = N8nService()


# Convenience functions
async def init_n8n_service() -> None:
    """Initialize n8n service."""
    await n8n_service.initialize()


async def close_n8n_service() -> None:
    """Close n8n service."""
    await n8n_service.close()