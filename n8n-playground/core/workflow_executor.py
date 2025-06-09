#!/usr/bin/env python3
"""
Workflow Executor for n8n API Playground

Handles the execution of n8n workflows with parameter injection,
status monitoring, and result collection.

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel, Field

from .api_client import N8nApiClient, N8nApiResponse

# Setup structured logging
logger = structlog.get_logger(__name__)


class WorkflowExecution(BaseModel):
    """Represents a workflow execution."""
    
    execution_id: Optional[str] = None
    workflow_id: str
    session_id: str
    status: str = "pending"  # pending, running, success, error, timeout
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class WorkflowTemplate(BaseModel):
    """Represents a workflow template."""
    
    name: str
    description: Optional[str] = None
    nodes: List[Dict[str, Any]]
    connections: Dict[str, Any]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class WorkflowExecutor:
    """Main workflow executor class."""
    
    def __init__(self, api_client: N8nApiClient):
        self.api_client = api_client
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[WorkflowExecution] = []
        
        # Configuration
        self.max_execution_time = 300  # 5 minutes
        self.polling_interval = 2  # 2 seconds
        self.max_retries = 3
    
    async def execute(
        self,
        template: Dict[str, Any],
        parameters: Dict[str, Any],
        session_id: str,
        wait_for_completion: bool = True,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute workflow from template with parameters."""
        
        try:
            # Prepare workflow
            workflow_data = await self._prepare_workflow(template, parameters)
            
            # Create or update workflow
            workflow_response = await self._create_or_update_workflow(workflow_data)
            if not workflow_response.success:
                raise RuntimeError(f"Failed to create workflow: {workflow_response.error}")
            
            workflow_id = workflow_response.data.get('id')
            if not workflow_id:
                raise RuntimeError("No workflow ID returned from creation")
            
            # Create execution record
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                session_id=session_id,
                parameters=parameters
            )
            
            self.active_executions[session_id] = execution
            
            logger.info(
                "Starting workflow execution",
                session_id=session_id,
                workflow_id=workflow_id,
                template_name=template.get('name', 'unknown')
            )
            
            # Execute workflow
            execution_response = await self._trigger_workflow(workflow_id, parameters)
            if not execution_response.success:
                execution.status = "error"
                execution.error = execution_response.error
                raise RuntimeError(f"Failed to trigger workflow: {execution_response.error}")
            
            execution.execution_id = execution_response.data.get('id')
            execution.status = "running"
            
            # Wait for completion if requested
            if wait_for_completion:
                result = await self._wait_for_completion(
                    execution,
                    timeout or self.max_execution_time
                )
                return result
            else:
                return {
                    "execution_id": execution.execution_id,
                    "status": "running",
                    "session_id": session_id,
                    "started_at": execution.started_at.isoformat()
                }
        
        except Exception as e:
            logger.error(
                "Workflow execution failed",
                session_id=session_id,
                error=str(e)
            )
            
            if session_id in self.active_executions:
                execution = self.active_executions[session_id]
                execution.status = "error"
                execution.error = str(e)
                execution.completed_at = datetime.utcnow()
                self._archive_execution(execution)
            
            raise
    
    async def get_execution_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of workflow execution."""
        
        if session_id not in self.active_executions:
            raise ValueError(f"No active execution found for session {session_id}")
        
        execution = self.active_executions[session_id]
        
        # Update status if execution is running
        if execution.status == "running" and execution.execution_id:
            await self._update_execution_status(execution)
        
        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "session_id": execution.session_id,
            "status": execution.status,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "execution_time": execution.execution_time,
            "error": execution.error,
            "has_result": execution.result is not None
        }
    
    async def get_execution_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get result of workflow execution."""
        
        if session_id not in self.active_executions:
            # Check execution history
            for execution in self.execution_history:
                if execution.session_id == session_id:
                    return execution.result
            return None
        
        execution = self.active_executions[session_id]
        return execution.result
    
    async def cancel_execution(self, session_id: str) -> bool:
        """Cancel running workflow execution."""
        
        if session_id not in self.active_executions:
            return False
        
        execution = self.active_executions[session_id]
        
        if execution.execution_id:
            # Try to stop the execution via API
            try:
                stop_response = await self.api_client._make_request(
                    'POST',
                    f'executions/{execution.execution_id}/stop'
                )
                
                if stop_response.success:
                    logger.info(
                        "Workflow execution stopped",
                        session_id=session_id,
                        execution_id=execution.execution_id
                    )
            except Exception as e:
                logger.warning(
                    "Failed to stop execution via API",
                    session_id=session_id,
                    error=str(e)
                )
        
        # Update execution status
        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        execution.execution_time = (
            execution.completed_at - execution.started_at
        ).total_seconds()
        
        self._archive_execution(execution)
        
        return True
    
    # Private methods
    async def _prepare_workflow(
        self,
        template: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare workflow data with parameter injection."""
        
        workflow_data = template.copy()
        
        # Inject parameters into workflow nodes
        if 'nodes' in workflow_data:
            for node in workflow_data['nodes']:
                await self._inject_parameters_into_node(node, parameters)
        
        # Set workflow metadata
        workflow_data['name'] = f"{template.get('name', 'playground')}_exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        workflow_data['active'] = True
        
        return workflow_data
    
    async def _inject_parameters_into_node(
        self,
        node: Dict[str, Any],
        parameters: Dict[str, Any]
    ):
        """Inject parameters into workflow node."""
        
        if 'parameters' not in node:
            return
        
        node_params = node['parameters']
        
        # Replace parameter placeholders
        for key, value in node_params.items():
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                param_name = value[2:-2].strip()
                if param_name in parameters:
                    node_params[key] = parameters[param_name]
                    logger.debug(
                        "Parameter injected",
                        node_name=node.get('name', 'unknown'),
                        parameter=param_name,
                        value=parameters[param_name]
                    )
    
    async def _create_or_update_workflow(self, workflow_data: Dict[str, Any]) -> N8nApiResponse:
        """Create or update workflow in n8n."""
        
        # Try to create new workflow
        response = await self.api_client.create_workflow(workflow_data)
        
        if response.success:
            logger.debug("Workflow created", workflow_id=response.data.get('id'))
            return response
        
        # If creation failed, try to find existing workflow and update
        workflows_response = await self.api_client.get_workflows()
        if workflows_response.success:
            for workflow in workflows_response.data.get('data', []):
                if workflow.get('name') == workflow_data.get('name'):
                    # Update existing workflow
                    update_response = await self.api_client.update_workflow(
                        workflow['id'],
                        workflow_data
                    )
                    if update_response.success:
                        logger.debug(
                            "Workflow updated",
                            workflow_id=workflow['id']
                        )
                        return update_response
        
        return response  # Return original error
    
    async def _trigger_workflow(
        self,
        workflow_id: str,
        parameters: Dict[str, Any]
    ) -> N8nApiResponse:
        """Trigger workflow execution."""
        
        # First activate the workflow
        activate_response = await self.api_client.activate_workflow(workflow_id)
        if not activate_response.success:
            logger.warning(
                "Failed to activate workflow",
                workflow_id=workflow_id,
                error=activate_response.error
            )
        
        # Trigger execution via webhook or manual trigger
        trigger_data = {
            "workflowId": workflow_id,
            "data": parameters
        }
        
        return await self.api_client._make_request(
            'POST',
            f'workflows/{workflow_id}/execute',
            data=trigger_data
        )
    
    async def _wait_for_completion(
        self,
        execution: WorkflowExecution,
        timeout: int
    ) -> Dict[str, Any]:
        """Wait for workflow execution to complete."""
        
        start_time = datetime.utcnow()
        timeout_time = start_time + timedelta(seconds=timeout)
        
        while datetime.utcnow() < timeout_time:
            await self._update_execution_status(execution)
            
            if execution.status in ['success', 'error', 'cancelled']:
                break
            
            await asyncio.sleep(self.polling_interval)
        
        # Handle timeout
        if execution.status == 'running':
            execution.status = 'timeout'
            execution.error = f"Execution timed out after {timeout} seconds"
        
        # Calculate execution time
        execution.completed_at = datetime.utcnow()
        execution.execution_time = (
            execution.completed_at - execution.started_at
        ).total_seconds()
        
        # Archive execution
        self._archive_execution(execution)
        
        # Return result
        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "session_id": execution.session_id,
            "status": execution.status,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat(),
            "execution_time": execution.execution_time,
            "result": execution.result,
            "error": execution.error
        }
    
    async def _update_execution_status(self, execution: WorkflowExecution):
        """Update execution status from n8n API."""
        
        if not execution.execution_id:
            return
        
        try:
            response = await self.api_client.get_execution(execution.execution_id)
            
            if response.success and response.data:
                execution_data = response.data
                
                # Update status
                if execution_data.get('finished'):
                    if execution_data.get('success'):
                        execution.status = 'success'
                        execution.result = execution_data.get('data', {})
                    else:
                        execution.status = 'error'
                        execution.error = execution_data.get('error', 'Unknown error')
                elif execution_data.get('running'):
                    execution.status = 'running'
                
                logger.debug(
                    "Execution status updated",
                    execution_id=execution.execution_id,
                    status=execution.status
                )
        
        except Exception as e:
            logger.warning(
                "Failed to update execution status",
                execution_id=execution.execution_id,
                error=str(e)
            )
    
    def _archive_execution(self, execution: WorkflowExecution):
        """Archive completed execution."""
        
        # Move from active to history
        if execution.session_id in self.active_executions:
            del self.active_executions[execution.session_id]
        
        self.execution_history.append(execution)
        
        # Keep only last 100 executions in memory
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        logger.debug(
            "Execution archived",
            session_id=execution.session_id,
            status=execution.status,
            execution_time=execution.execution_time
        )