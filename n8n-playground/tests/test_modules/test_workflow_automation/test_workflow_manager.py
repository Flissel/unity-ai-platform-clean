#!/usr/bin/env python3
"""
Tests for WorkflowManager class.

Comprehensive test suite covering workflow lifecycle management,
template processing, execution coordination, and error handling.

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from modules.workflow_automation.workflow_manager import (
    WorkflowManager,
    WorkflowManagerConfig
)
from modules.workflow_automation.models import (
    Workflow,
    WorkflowTemplate,
    WorkflowExecution,
    WorkflowStatus,
    ExecutionStatus,
    WorkflowParameter,
    ParameterType
)


class TestWorkflowManagerConfig:
    """Test WorkflowManagerConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = WorkflowManagerConfig()
        
        assert config.max_concurrent_workflows == 10
        assert config.execution_timeout == 300
        assert config.retry_attempts == 3
        assert config.retry_delay == 5.0
        assert config.enable_scheduling is True
        assert config.template_path == Path("templates")
        assert config.auto_cleanup_interval == 3600
        assert config.max_workflow_history == 1000
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = WorkflowManagerConfig(
            max_concurrent_workflows=20,
            execution_timeout=600,
            retry_attempts=5,
            retry_delay=10.0,
            enable_scheduling=False,
            template_path=Path("/custom/templates"),
            auto_cleanup_interval=7200,
            max_workflow_history=2000
        )
        
        assert config.max_concurrent_workflows == 20
        assert config.execution_timeout == 600
        assert config.retry_attempts == 5
        assert config.retry_delay == 10.0
        assert config.enable_scheduling is False
        assert config.template_path == Path("/custom/templates")
        assert config.auto_cleanup_interval == 7200
        assert config.max_workflow_history == 2000


class TestWorkflowManager:
    """Test WorkflowManager class."""
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock N8nApiClient."""
        client = AsyncMock()
        client.get_workflows.return_value = {"success": True, "data": []}
        return client
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return WorkflowManagerConfig(
            max_concurrent_workflows=5,
            execution_timeout=60,
            template_path=Path("/test/templates")
        )
    
    @pytest.fixture
    def workflow_manager(self, mock_api_client, config):
        """Create WorkflowManager instance."""
        return WorkflowManager(mock_api_client, config)
    
    @pytest.fixture
    def sample_template(self):
        """Sample workflow template."""
        return WorkflowTemplate(
            name="test_template",
            description="Test template",
            version="1.0.0",
            category="test",
            template_data={
                "nodes": [
                    {
                        "id": "start",
                        "type": "n8n-nodes-base.start",
                        "position": [100, 100]
                    }
                ],
                "connections": {}
            },
            parameters=[
                WorkflowParameter(
                    name="test_param",
                    type=ParameterType.STRING,
                    required=True,
                    description="Test parameter"
                )
            ]
        )
    
    @pytest.fixture
    def sample_workflow(self, sample_template):
        """Sample workflow."""
        return Workflow(
            id=str(uuid4()),
            name="test_workflow",
            description="Test workflow",
            template_name=sample_template.name,
            template_version=sample_template.version,
            parameters={"test_param": "test_value"},
            workflow_data=sample_template.template_data,
            status=WorkflowStatus.CREATED
        )
    
    def test_initialization(self, mock_api_client, config):
        """Test WorkflowManager initialization."""
        manager = WorkflowManager(mock_api_client, config)
        
        assert manager.api_client == mock_api_client
        assert manager.config == config
        assert manager.workflows == {}
        assert manager.executions == {}
        assert manager.active_executions == {}
        assert manager._running is False
        assert manager.stats['total_workflows'] == 0
        assert manager.stats['total_executions'] == 0
    
    def test_initialization_default_config(self, mock_api_client):
        """Test WorkflowManager initialization with default config."""
        manager = WorkflowManager(mock_api_client)
        
        assert isinstance(manager.config, WorkflowManagerConfig)
        assert manager.config.max_concurrent_workflows == 10
    
    @pytest.mark.asyncio
    async def test_start_stop(self, workflow_manager):
        """Test starting and stopping the workflow manager."""
        with patch.object(workflow_manager, '_load_workflows', new_callable=AsyncMock) as mock_load:
            with patch('asyncio.create_task') as mock_create_task:
                # Test start
                await workflow_manager.start()
                
                assert workflow_manager._running is True
                mock_load.assert_called_once()
                mock_create_task.assert_called_once()
                
                # Test stop
                workflow_manager._cleanup_task = AsyncMock()
                workflow_manager._cleanup_task.done.return_value = False
                
                await workflow_manager.stop()
                
                assert workflow_manager._running is False
                workflow_manager._cleanup_task.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_already_running(self, workflow_manager):
        """Test starting when already running."""
        workflow_manager._running = True
        
        with patch.object(workflow_manager, '_load_workflows', new_callable=AsyncMock) as mock_load:
            await workflow_manager.start()
            mock_load.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stop_not_running(self, workflow_manager):
        """Test stopping when not running."""
        workflow_manager._running = False
        
        await workflow_manager.stop()
        # Should not raise any errors
    
    @pytest.mark.asyncio
    async def test_create_workflow_success(self, workflow_manager, sample_template):
        """Test successful workflow creation."""
        with patch.object(workflow_manager.template_engine, 'load_template', new_callable=AsyncMock) as mock_load:
            with patch.object(workflow_manager.validator, 'validate_parameters', new_callable=AsyncMock) as mock_validate:
                with patch.object(workflow_manager.template_engine, 'generate_workflow', new_callable=AsyncMock) as mock_generate:
                    
                    # Setup mocks
                    mock_load.return_value = sample_template
                    mock_validate.return_value = MagicMock(valid=True, errors=[])
                    mock_generate.return_value = sample_template.template_data
                    
                    # Create workflow
                    workflow = await workflow_manager.create_workflow(
                        template_name="test_template",
                        name="test_workflow",
                        parameters={"test_param": "test_value"},
                        description="Test description",
                        tags=["test"]
                    )
                    
                    # Verify workflow
                    assert workflow.name == "test_workflow"
                    assert workflow.description == "Test description"
                    assert workflow.template_name == "test_template"
                    assert workflow.parameters == {"test_param": "test_value"}
                    assert workflow.tags == ["test"]
                    assert workflow.status == WorkflowStatus.CREATED
                    
                    # Verify storage
                    assert workflow.id in workflow_manager.workflows
                    assert workflow_manager.stats['total_workflows'] == 1
                    
                    # Verify mock calls
                    mock_load.assert_called_once_with("test_template")
                    mock_validate.assert_called_once()
                    mock_generate.assert_called_once_with(sample_template, {"test_param": "test_value"})
    
    @pytest.mark.asyncio
    async def test_create_workflow_template_not_found(self, workflow_manager):
        """Test workflow creation with missing template."""
        with patch.object(workflow_manager.template_engine, 'load_template', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = None
            
            with pytest.raises(ValueError, match="Template not found: missing_template"):
                await workflow_manager.create_workflow(
                    template_name="missing_template",
                    name="test_workflow",
                    parameters={}
                )
    
    @pytest.mark.asyncio
    async def test_create_workflow_validation_failed(self, workflow_manager, sample_template):
        """Test workflow creation with parameter validation failure."""
        with patch.object(workflow_manager.template_engine, 'load_template', new_callable=AsyncMock) as mock_load:
            with patch.object(workflow_manager.validator, 'validate_parameters', new_callable=AsyncMock) as mock_validate:
                
                # Setup mocks
                mock_load.return_value = sample_template
                mock_validate.return_value = MagicMock(
                    valid=False,
                    errors=["test_param is required"]
                )
                
                with pytest.raises(ValueError, match="Parameter validation failed"):
                    await workflow_manager.create_workflow(
                        template_name="test_template",
                        name="test_workflow",
                        parameters={}
                    )
    
    @pytest.mark.asyncio
    async def test_get_workflow(self, workflow_manager, sample_workflow):
        """Test getting workflow by ID."""
        # Store workflow
        workflow_manager.workflows[sample_workflow.id] = sample_workflow
        
        # Get workflow
        result = await workflow_manager.get_workflow(sample_workflow.id)
        assert result == sample_workflow
        
        # Get non-existent workflow
        result = await workflow_manager.get_workflow("non_existent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, workflow_manager, sample_workflow):
        """Test listing workflows."""
        # Store workflow
        workflow_manager.workflows[sample_workflow.id] = sample_workflow
        
        # List all workflows
        workflows = await workflow_manager.list_workflows()
        assert len(workflows) == 1
        assert workflows[0] == sample_workflow
        
        # List with status filter
        workflows = await workflow_manager.list_workflows(status=WorkflowStatus.CREATED)
        assert len(workflows) == 1
        
        workflows = await workflow_manager.list_workflows(status=WorkflowStatus.ACTIVE)
        assert len(workflows) == 0
        
        # List with tag filter
        sample_workflow.tags = ["test"]
        workflows = await workflow_manager.list_workflows(tags=["test"])
        assert len(workflows) == 1
        
        workflows = await workflow_manager.list_workflows(tags=["other"])
        assert len(workflows) == 0
    
    @pytest.mark.asyncio
    async def test_update_workflow(self, workflow_manager, sample_workflow):
        """Test updating workflow."""
        # Store workflow
        workflow_manager.workflows[sample_workflow.id] = sample_workflow
        
        # Update workflow
        updates = {
            "name": "updated_name",
            "description": "updated_description",
            "tags": ["updated"]
        }
        
        updated_workflow = await workflow_manager.update_workflow(
            sample_workflow.id,
            **updates
        )
        
        assert updated_workflow.name == "updated_name"
        assert updated_workflow.description == "updated_description"
        assert updated_workflow.tags == ["updated"]
        assert updated_workflow.updated_at is not None
        
        # Verify storage
        stored_workflow = workflow_manager.workflows[sample_workflow.id]
        assert stored_workflow.name == "updated_name"
    
    @pytest.mark.asyncio
    async def test_update_workflow_not_found(self, workflow_manager):
        """Test updating non-existent workflow."""
        result = await workflow_manager.update_workflow(
            "non_existent",
            name="new_name"
        )
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_workflow(self, workflow_manager, sample_workflow):
        """Test deleting workflow."""
        # Store workflow
        workflow_manager.workflows[sample_workflow.id] = sample_workflow
        
        # Delete workflow
        result = await workflow_manager.delete_workflow(sample_workflow.id)
        assert result is True
        
        # Verify removal
        assert sample_workflow.id not in workflow_manager.workflows
        
        # Delete non-existent workflow
        result = await workflow_manager.delete_workflow("non_existent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, workflow_manager, sample_workflow):
        """Test workflow execution."""
        # Store workflow
        workflow_manager.workflows[sample_workflow.id] = sample_workflow
        
        with patch.object(workflow_manager.executor, 'execute_workflow', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": {"execution_id": "exec_123"}
            }
            
            # Execute workflow
            execution = await workflow_manager.execute_workflow(
                sample_workflow.id,
                input_data={"test": "data"}
            )
            
            assert execution.workflow_id == sample_workflow.id
            assert execution.input_data == {"test": "data"}
            assert execution.status == ExecutionStatus.PENDING
            
            # Verify storage
            assert execution.id in workflow_manager.executions
            assert workflow_manager.stats['total_executions'] == 1
            
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, workflow_manager):
        """Test executing non-existent workflow."""
        with pytest.raises(ValueError, match="Workflow not found"):
            await workflow_manager.execute_workflow(
                "non_existent",
                input_data={}
            )
    
    @pytest.mark.asyncio
    async def test_get_execution(self, workflow_manager):
        """Test getting execution by ID."""
        execution = WorkflowExecution(
            id="exec_123",
            workflow_id="workflow_123",
            status=ExecutionStatus.SUCCESS
        )
        
        # Store execution
        workflow_manager.executions[execution.id] = execution
        
        # Get execution
        result = await workflow_manager.get_execution(execution.id)
        assert result == execution
        
        # Get non-existent execution
        result = await workflow_manager.get_execution("non_existent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_executions(self, workflow_manager):
        """Test listing executions."""
        execution1 = WorkflowExecution(
            id="exec_1",
            workflow_id="workflow_1",
            status=ExecutionStatus.SUCCESS
        )
        execution2 = WorkflowExecution(
            id="exec_2",
            workflow_id="workflow_1",
            status=ExecutionStatus.FAILED
        )
        
        # Store executions
        workflow_manager.executions[execution1.id] = execution1
        workflow_manager.executions[execution2.id] = execution2
        
        # List all executions
        executions = await workflow_manager.list_executions()
        assert len(executions) == 2
        
        # List by workflow
        executions = await workflow_manager.list_executions(workflow_id="workflow_1")
        assert len(executions) == 2
        
        executions = await workflow_manager.list_executions(workflow_id="workflow_2")
        assert len(executions) == 0
        
        # List by status
        executions = await workflow_manager.list_executions(status=ExecutionStatus.SUCCESS)
        assert len(executions) == 1
        assert executions[0] == execution1
    
    def test_get_stats(self, workflow_manager):
        """Test getting statistics."""
        stats = workflow_manager.get_stats()
        
        assert 'total_workflows' in stats
        assert 'total_executions' in stats
        assert 'successful_executions' in stats
        assert 'failed_executions' in stats
        assert 'active_workflows' in stats
    
    @pytest.mark.asyncio
    async def test_health_check(self, workflow_manager):
        """Test health check."""
        with patch.object(workflow_manager.api_client, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {"success": True, "data": {"status": "ok"}}
            
            health = await workflow_manager.health_check()
            
            assert health['status'] == 'healthy'
            assert 'api_client' in health
            assert 'stats' in health
            assert 'running' in health
            
            mock_health.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_api_error(self, workflow_manager):
        """Test health check with API error."""
        with patch.object(workflow_manager.api_client, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.side_effect = Exception("API error")
            
            health = await workflow_manager.health_check()
            
            assert health['status'] == 'unhealthy'
            assert 'error' in health


@pytest.mark.integration
class TestWorkflowManagerIntegration:
    """Integration tests for WorkflowManager."""
    
    @pytest.mark.requires_n8n
    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle(self, real_api_client):
        """Test complete workflow lifecycle with real n8n instance."""
        manager = WorkflowManager(real_api_client)
        
        try:
            await manager.start()
            
            # Create workflow from template
            workflow = await manager.create_workflow(
                template_name="simple_webhook",
                name="integration_test_workflow",
                parameters={"webhook_path": "/test"}
            )
            
            assert workflow.status == WorkflowStatus.CREATED
            
            # Execute workflow
            execution = await manager.execute_workflow(
                workflow.id,
                input_data={"test": "data"}
            )
            
            assert execution.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
            
            # Wait for completion (with timeout)
            timeout = 30
            while timeout > 0 and execution.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
                await asyncio.sleep(1)
                execution = await manager.get_execution(execution.id)
                timeout -= 1
            
            assert execution.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]
            
        finally:
            await manager.stop()