#!/usr/bin/env python3
"""
n8n Integration Module for Workflow Automation

This module provides direct integration with n8n API for executing workflows,
monitoring executions, and managing workflow lifecycle.

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4

import httpx
import structlog
from fastapi import HTTPException
from pydantic import BaseModel, Field

# Setup structured logging
logger = structlog.get_logger(__name__)


class N8nExecutionRequest(BaseModel):
    """Request model for executing n8n workflows."""
    workflow_id: str = Field(..., description="n8n workflow ID to execute")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data for the workflow")
    wait_for_completion: bool = Field(True, description="Whether to wait for execution completion")
    timeout: int = Field(300, description="Timeout in seconds for execution completion")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the execution")


class N8nExecutionResponse(BaseModel):
    """Response model for n8n workflow execution."""
    execution_id: str = Field(..., description="n8n execution ID")
    workflow_id: str = Field(..., description="n8n workflow ID")
    status: str = Field(..., description="Execution status")
    started_at: Optional[datetime] = Field(None, description="Execution start time")
    finished_at: Optional[datetime] = Field(None, description="Execution finish time")
    duration: Optional[float] = Field(None, description="Execution duration in seconds")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Execution result data")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class N8nWorkflowInfo(BaseModel):
    """Model for n8n workflow information."""
    id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    active: bool = Field(..., description="Whether workflow is active")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Workflow tags")
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="Workflow nodes")
    connections: Optional[Dict[str, Any]] = Field(None, description="Workflow connections")


class N8nIntegrationManager:
    """Manager class for n8n API integration."""
    
    def __init__(self, api_key: str, base_url: str = "https://n8n.unit-y-ai.io"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json",
            "User-Agent": "UnityAI-n8n-Integration/1.0.0"
        }
        self.active_executions: Dict[str, Dict[str, Any]] = {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check n8n API health and connectivity."""
        try:
            async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=10.0) as client:
                # Try to get workflows as a health check
                response = await client.get("/api/v1/workflows", params={"limit": 1})
                response.raise_for_status()
                
                return {
                    "status": "healthy",
                    "base_url": self.base_url,
                    "api_accessible": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error("n8n health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "base_url": self.base_url,
                "api_accessible": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def list_workflows(self, active_only: bool = False, limit: int = 100) -> List[N8nWorkflowInfo]:
        """List all available workflows from n8n."""
        try:
            params = {"limit": limit}
            if active_only:
                params["active"] = "true"
            
            async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
                response = await client.get("/api/v1/workflows", params=params)
                response.raise_for_status()
                
                data = response.json()
                workflows = data.get('data', []) if isinstance(data, dict) else data
                
                result = []
                for workflow in workflows:
                    workflow_info = N8nWorkflowInfo(
                        id=workflow['id'],
                        name=workflow.get('name', 'Unnamed'),
                        active=workflow.get('active', False),
                        created_at=self._parse_datetime(workflow.get('createdAt')),
                        updated_at=self._parse_datetime(workflow.get('updatedAt')),
                        tags=workflow.get('tags', []),
                        nodes=workflow.get('nodes'),
                        connections=workflow.get('connections')
                    )
                    result.append(workflow_info)
                
                logger.info("Listed workflows", count=len(result), active_only=active_only)
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error("Failed to list workflows", status_code=e.response.status_code, error=str(e))
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to list workflows: {e.response.text}"
            )
        except Exception as e:
            logger.error("Unexpected error listing workflows", error=str(e))
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    async def get_workflow(self, workflow_id: str) -> N8nWorkflowInfo:
        """Get detailed information about a specific workflow."""
        try:
            async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
                response = await client.get(f"/api/v1/workflows/{workflow_id}")
                response.raise_for_status()
                
                workflow = response.json()
                return N8nWorkflowInfo(
                    id=workflow['id'],
                    name=workflow.get('name', 'Unnamed'),
                    active=workflow.get('active', False),
                    created_at=self._parse_datetime(workflow.get('createdAt')),
                    updated_at=self._parse_datetime(workflow.get('updatedAt')),
                    tags=workflow.get('tags', []),
                    nodes=workflow.get('nodes'),
                    connections=workflow.get('connections')
                )
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
            logger.error("Failed to get workflow", workflow_id=workflow_id, status_code=e.response.status_code)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to get workflow: {e.response.text}"
            )
        except Exception as e:
            logger.error("Unexpected error getting workflow", workflow_id=workflow_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    async def execute_workflow(self, request: N8nExecutionRequest) -> N8nExecutionResponse:
        """Execute a workflow in n8n."""
        try:
            # Prepare execution payload
            payload = {}
            if request.input_data:
                payload["data"] = request.input_data
            
            # Start execution
            async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=60.0) as client:
                response = await client.post(
                    f"/api/v1/workflows/{request.workflow_id}/execute",
                    json=payload
                )
                response.raise_for_status()
                
                execution_result = response.json()
                execution_id = execution_result.get('data', {}).get('executionId')
                
                if not execution_id:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to get execution ID from n8n response"
                    )
                
                logger.info(
                    "Workflow execution started",
                    workflow_id=request.workflow_id,
                    execution_id=execution_id
                )
                
                # Store execution info
                self.active_executions[execution_id] = {
                    "workflow_id": request.workflow_id,
                    "started_at": datetime.utcnow(),
                    "metadata": request.metadata or {}
                }
                
                # If waiting for completion, poll for results
                if request.wait_for_completion:
                    return await self._wait_for_execution_completion(
                        execution_id,
                        request.workflow_id,
                        request.timeout,
                        request.metadata
                    )
                else:
                    # Return immediate response
                    return N8nExecutionResponse(
                        execution_id=execution_id,
                        workflow_id=request.workflow_id,
                        status="running",
                        started_at=datetime.utcnow(),
                        metadata=request.metadata
                    )
                    
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Workflow {request.workflow_id} not found")
            logger.error(
                "Failed to execute workflow",
                workflow_id=request.workflow_id,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to execute workflow: {e.response.text}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error executing workflow",
                workflow_id=request.workflow_id,
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    async def get_execution_status(self, execution_id: str) -> N8nExecutionResponse:
        """Get the status and results of a workflow execution."""
        try:
            async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
                response = await client.get(f"/api/v1/executions/{execution_id}")
                response.raise_for_status()
                
                execution = response.json()
                return self._parse_execution_response(execution)
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
            logger.error(
                "Failed to get execution status",
                execution_id=execution_id,
                status_code=e.response.status_code
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to get execution status: {e.response.text}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error getting execution status",
                execution_id=execution_id,
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    async def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """Cancel a running workflow execution."""
        try:
            async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
                response = await client.post(f"/api/v1/executions/{execution_id}/stop")
                response.raise_for_status()
                
                logger.info("Execution cancelled", execution_id=execution_id)
                
                # Clean up from active executions
                self.active_executions.pop(execution_id, None)
                
                return {
                    "execution_id": execution_id,
                    "status": "cancelled",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
            logger.error(
                "Failed to cancel execution",
                execution_id=execution_id,
                status_code=e.response.status_code
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to cancel execution: {e.response.text}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error cancelling execution",
                execution_id=execution_id,
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    async def list_executions(self, workflow_id: Optional[str] = None, limit: int = 50) -> List[N8nExecutionResponse]:
        """List workflow executions."""
        try:
            params = {"limit": limit}
            if workflow_id:
                params["workflowId"] = workflow_id
            
            async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
                response = await client.get("/api/v1/executions", params=params)
                response.raise_for_status()
                
                data = response.json()
                executions = data.get('data', []) if isinstance(data, dict) else data
                
                result = []
                for execution in executions:
                    result.append(self._parse_execution_response(execution))
                
                logger.info("Listed executions", count=len(result), workflow_id=workflow_id)
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to list executions",
                workflow_id=workflow_id,
                status_code=e.response.status_code
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to list executions: {e.response.text}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error listing executions",
                workflow_id=workflow_id,
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    async def _wait_for_execution_completion(
        self,
        execution_id: str,
        workflow_id: str,
        timeout: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> N8nExecutionResponse:
        """Wait for execution to complete and return results."""
        start_time = datetime.utcnow()
        poll_interval = 2  # seconds
        
        while True:
            try:
                execution_response = await self.get_execution_status(execution_id)
                
                # Check if execution is complete
                if execution_response.status in ['success', 'error', 'canceled', 'crashed']:
                    # Clean up from active executions
                    self.active_executions.pop(execution_id, None)
                    
                    # Add metadata if provided
                    if metadata:
                        execution_response.metadata = metadata
                    
                    logger.info(
                        "Execution completed",
                        execution_id=execution_id,
                        status=execution_response.status,
                        duration=execution_response.duration
                    )
                    
                    return execution_response
                
                # Check timeout
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed > timeout:
                    logger.warning(
                        "Execution timeout",
                        execution_id=execution_id,
                        timeout=timeout,
                        elapsed=elapsed
                    )
                    
                    # Try to cancel the execution
                    try:
                        await self.cancel_execution(execution_id)
                    except Exception as cancel_error:
                        logger.error(
                            "Failed to cancel timed out execution",
                            execution_id=execution_id,
                            error=str(cancel_error)
                        )
                    
                    raise HTTPException(
                        status_code=408,
                        detail=f"Execution timed out after {timeout} seconds"
                    )
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(
                    "Error while waiting for execution",
                    execution_id=execution_id,
                    error=str(e)
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error monitoring execution: {str(e)}"
                )
    
    def _parse_execution_response(self, execution: Dict[str, Any]) -> N8nExecutionResponse:
        """Parse n8n execution response into our model."""
        started_at = self._parse_datetime(execution.get('startedAt'))
        finished_at = self._parse_datetime(execution.get('stoppedAt'))
        
        duration = None
        if started_at and finished_at:
            duration = (finished_at - started_at).total_seconds()
        
        # Extract error message if present
        error_message = None
        result_data = execution.get('data', {})
        if execution.get('status') == 'error':
            error_data = result_data.get('resultData', {}).get('error', {})
            error_message = error_data.get('message', 'Unknown error')
        
        return N8nExecutionResponse(
            execution_id=execution['id'],
            workflow_id=execution.get('workflowId', ''),
            status=execution.get('status', 'unknown'),
            started_at=started_at,
            finished_at=finished_at,
            duration=duration,
            result_data=result_data,
            error_message=error_message
        )
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from n8n API."""
        if not date_str:
            return None
        try:
            # Handle ISO format with Z suffix
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None