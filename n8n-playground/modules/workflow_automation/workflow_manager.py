#!/usr/bin/env python3
"""
Workflow Manager for n8n API Playground

Main workflow management component that handles workflow lifecycle,
template management, and execution coordination.

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

from core import (
    N8nApiClient,
    WorkflowExecutor,
    ResponseHandler,
    get_config
)
from .models import (
    Workflow,
    WorkflowTemplate,
    WorkflowExecution,
    WorkflowStatus,
    ExecutionStatus
)
from .template_engine import TemplateEngine
from .validators import WorkflowValidator

# Setup structured logging
logger = structlog.get_logger(__name__)


class WorkflowManagerConfig(BaseModel):
    """Configuration for workflow manager."""
    
    max_concurrent_workflows: int = Field(default=10)
    execution_timeout: int = Field(default=300)
    retry_attempts: int = Field(default=3)
    retry_delay: float = Field(default=5.0)
    enable_scheduling: bool = Field(default=True)
    template_path: Path = Field(default=Path("templates"))
    auto_cleanup_interval: int = Field(default=3600)
    max_workflow_history: int = Field(default=1000)


class WorkflowManager:
    """Main workflow manager class."""
    
    def __init__(
        self,
        api_client: N8nApiClient,
        config: Optional[WorkflowManagerConfig] = None
    ):
        self.api_client = api_client
        self.config = config or WorkflowManagerConfig()
        
        # Initialize components
        self.executor = WorkflowExecutor(api_client)
        self.response_handler = ResponseHandler()
        self.template_engine = TemplateEngine(self.config.template_path)
        self.validator = WorkflowValidator()
        
        # Storage
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self.stats = {
            'total_workflows': 0,
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'active_workflows': 0
        }
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the workflow manager."""
        
        if self._running:
            return
        
        self._running = True
        
        # Load existing workflows
        await self._load_workflows()
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(
            "Workflow manager started",
            workflows=len(self.workflows),
            config=self.config.dict()
        )
    
    async def stop(self):
        """Stop the workflow manager."""
        
        if not self._running:
            return
        
        self._running = False
        
        # Cancel active executions
        for execution_id, task in self.active_executions.items():
            if not task.done():
                task.cancel()
                logger.info("Cancelled active execution", execution_id=execution_id)
        
        # Stop background tasks
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        logger.info("Workflow manager stopped")
    
    async def create_workflow(
        self,
        template_name: str,
        name: str,
        parameters: Dict[str, Any],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Workflow:
        """Create a new workflow from template."""
        
        try:
            # Load template
            template = await self.template_engine.load_template(template_name)
            if not template:
                raise ValueError(f"Template not found: {template_name}")
            
            # Validate parameters
            validation_result = await self.validator.validate_parameters(
                parameters,
                template.parameters
            )
            
            if not validation_result.valid:
                raise ValueError(f"Parameter validation failed: {validation_result.errors}")
            
            # Generate workflow
            workflow_data = await self.template_engine.generate_workflow(
                template,
                parameters
            )
            
            # Create workflow object
            workflow = Workflow(
                id=str(uuid4()),
                name=name,
                description=description or template.description,
                template_name=template_name,
                template_version=template.version,
                parameters=parameters,
                workflow_data=workflow_data,
                tags=tags or [],
                status=WorkflowStatus.CREATED,
                created_at=datetime.utcnow()
            )
            
            # Store workflow
            self.workflows[workflow.id] = workflow
            self.stats['total_workflows'] += 1
            
            logger.info(
                "Workflow created",
                workflow_id=workflow.id,
                name=workflow.name,
                template=template_name
            )
            
            return workflow
        
        except Exception as e:
            logger.error(
                "Failed to create workflow",
                template_name=template_name,
                name=name,
                error=str(e)
            )
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        
        return self.workflows.get(workflow_id)
    
    async def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
        template_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Workflow]:
        """List workflows with filtering."""
        
        workflows = list(self.workflows.values())
        
        # Apply filters
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        if template_name:
            workflows = [w for w in workflows if w.template_name == template_name]
        
        if tags:
            workflows = [
                w for w in workflows
                if any(tag in w.tags for tag in tags)
            ]
        
        # Sort by creation date (newest first)
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        
        # Apply pagination
        return workflows[offset:offset + limit]
    
    async def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Workflow]:
        """Update workflow."""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        # Update allowed fields
        allowed_fields = ['name', 'description', 'tags', 'parameters']
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(workflow, field, value)
        
        workflow.updated_at = datetime.utcnow()
        
        # Regenerate workflow data if parameters changed
        if 'parameters' in updates:
            template = await self.template_engine.load_template(workflow.template_name)
            if template:
                workflow.workflow_data = await self.template_engine.generate_workflow(
                    template,
                    workflow.parameters
                )
        
        logger.info(
            "Workflow updated",
            workflow_id=workflow_id,
            fields=list(updates.keys())
        )
        
        return workflow
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow."""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        # Check if workflow has active executions
        active_executions = [
            e for e in self.executions.values()
            if e.workflow_id == workflow_id and e.status == ExecutionStatus.RUNNING
        ]
        
        if active_executions:
            raise ValueError("Cannot delete workflow with active executions")
        
        # Delete workflow
        del self.workflows[workflow_id]
        
        logger.info("Workflow deleted", workflow_id=workflow_id)
        
        return True
    
    async def execute_workflow(
        self,
        workflow_id: str,
        execution_parameters: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = False,
        timeout: Optional[int] = None
    ) -> WorkflowExecution:
        """Execute workflow."""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Check concurrent execution limit
        active_count = len([
            e for e in self.executions.values()
            if e.status == ExecutionStatus.RUNNING
        ])
        
        if active_count >= self.config.max_concurrent_workflows:
            raise ValueError("Maximum concurrent workflows exceeded")
        
        # Merge parameters
        final_parameters = workflow.parameters.copy()
        if execution_parameters:
            final_parameters.update(execution_parameters)
        
        # Create execution record
        execution = WorkflowExecution(
            id=str(uuid4()),
            workflow_id=workflow_id,
            parameters=final_parameters,
            status=ExecutionStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.executions[execution.id] = execution
        self.stats['total_executions'] += 1
        
        # Start execution
        execution_task = asyncio.create_task(
            self._execute_workflow_async(
                execution,
                workflow,
                timeout or self.config.execution_timeout
            )
        )
        
        self.active_executions[execution.id] = execution_task
        
        logger.info(
            "Workflow execution started",
            execution_id=execution.id,
            workflow_id=workflow_id
        )
        
        # Wait for completion if requested
        if wait_for_completion:
            await execution_task
        
        return execution
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID."""
        
        return self.executions.get(execution_id)
    
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List executions with filtering."""
        
        executions = list(self.executions.values())
        
        # Apply filters
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        if status:
            executions = [e for e in executions if e.status == status]
        
        # Sort by creation date (newest first)
        executions.sort(key=lambda e: e.created_at, reverse=True)
        
        # Apply pagination
        return executions[offset:offset + limit]
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel workflow execution."""
        
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        if execution.status != ExecutionStatus.RUNNING:
            return False
        
        # Cancel execution task
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            if not task.done():
                task.cancel()
        
        # Update execution status
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        execution.error = "Execution cancelled by user"
        
        logger.info("Workflow execution cancelled", execution_id=execution_id)
        
        return True
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get workflow manager statistics."""
        
        # Update active workflows count
        self.stats['active_workflows'] = len([
            e for e in self.executions.values()
            if e.status == ExecutionStatus.RUNNING
        ])
        
        return {
            **self.stats,
            'templates_loaded': len(await self.template_engine.list_templates()),
            'workflows_by_status': {
                status.value: len([
                    w for w in self.workflows.values()
                    if w.status == status
                ])
                for status in WorkflowStatus
            },
            'executions_by_status': {
                status.value: len([
                    e for e in self.executions.values()
                    if e.status == status
                ])
                for status in ExecutionStatus
            }
        }
    
    # Private methods
    async def _execute_workflow_async(
        self,
        execution: WorkflowExecution,
        workflow: Workflow,
        timeout: int
    ):
        """Execute workflow asynchronously."""
        
        try:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()
            
            # Execute workflow using executor
            result = await self.executor.execute(
                workflow.workflow_data,
                execution.parameters,
                execution.id,
                wait_for_completion=True,
                timeout=timeout
            )
            
            # Process result
            if result.get('status') == 'success':
                execution.status = ExecutionStatus.SUCCESS
                execution.result = result.get('result')
                self.stats['successful_executions'] += 1
            else:
                execution.status = ExecutionStatus.FAILED
                execution.error = result.get('error', 'Unknown error')
                self.stats['failed_executions'] += 1
            
            execution.completed_at = datetime.utcnow()
            execution.execution_time = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            logger.info(
                "Workflow execution completed",
                execution_id=execution.id,
                status=execution.status.value,
                execution_time=execution.execution_time
            )
        
        except asyncio.CancelledError:
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            execution.error = "Execution cancelled"
            
            logger.info(
                "Workflow execution cancelled",
                execution_id=execution.id
            )
        
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error = str(e)
            self.stats['failed_executions'] += 1
            
            logger.error(
                "Workflow execution failed",
                execution_id=execution.id,
                error=str(e)
            )
        
        finally:
            # Remove from active executions
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]
    
    async def _load_workflows(self):
        """Load existing workflows from storage."""
        
        # This would typically load from database
        # For now, we start with empty state
        logger.info("Workflows loaded", count=len(self.workflows))
    
    async def _cleanup_loop(self):
        """Background cleanup task."""
        
        while self._running:
            try:
                await self._cleanup_old_executions()
                await asyncio.sleep(self.config.auto_cleanup_interval)
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error("Cleanup task error", error=str(e))
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _cleanup_old_executions(self):
        """Clean up old execution records."""
        
        if len(self.executions) <= self.config.max_workflow_history:
            return
        
        # Sort executions by completion date
        completed_executions = [
            e for e in self.executions.values()
            if e.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]
        ]
        
        completed_executions.sort(key=lambda e: e.completed_at or e.created_at)
        
        # Remove oldest executions
        to_remove = len(completed_executions) - self.config.max_workflow_history
        if to_remove > 0:
            for execution in completed_executions[:to_remove]:
                del self.executions[execution.id]
            
            logger.info("Old executions cleaned up", count=to_remove)