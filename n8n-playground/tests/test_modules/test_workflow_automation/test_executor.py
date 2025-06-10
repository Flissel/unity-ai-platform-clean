#!/usr/bin/env python3
"""
Tests for Workflow Executor.

Comprehensive test suite for the workflow executor that handles
workflow execution, monitoring, and result processing.

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from modules.workflow_automation.executor import (
    WorkflowExecutor,
    WorkflowExecutorConfig,
    ExecutionContext,
    ExecutionMonitor
)
from modules.workflow_automation.models import (
    Workflow,
    WorkflowExecution,
    ExecutionStatus,
    ExecutionResult,
    WorkflowStatus
)
from core.api_client import N8nApiClient, N8nApiResponse


class TestWorkflowExecutorConfig:
    """Test WorkflowExecutorConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = WorkflowExecutorConfig()
        
        assert config.max_concurrent_executions == 10
        assert config.execution_timeout == 300
        assert config.retry_attempts == 3
        assert config.retry_delay == 5
        assert config.enable_monitoring is True
        assert config.monitor_interval == 10
        assert config.cleanup_completed_after == 3600
        assert config.max_execution_history == 1000
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = WorkflowExecutorConfig(
            max_concurrent_executions=5,
            execution_timeout=600,
            retry_attempts=5,
            retry_delay=10,
            enable_monitoring=False,
            monitor_interval=30,
            cleanup_completed_after=7200,
            max_execution_history=500
        )
        
        assert config.max_concurrent_executions == 5
        assert config.execution_timeout == 600
        assert config.retry_attempts == 5
        assert config.retry_delay == 10
        assert config.enable_monitoring is False
        assert config.monitor_interval == 30
        assert config.cleanup_completed_after == 7200
        assert config.max_execution_history == 500


class TestExecutionContext:
    """Test ExecutionContext model."""
    
    def test_creation(self):
        """Test ExecutionContext creation."""
        workflow_id = str(uuid4())
        execution_id = str(uuid4())
        
        context = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            parameters={"key": "value"},
            metadata={"source": "test"}
        )
        
        assert context.workflow_id == workflow_id
        assert context.execution_id == execution_id
        assert context.parameters == {"key": "value"}
        assert context.metadata == {"source": "test"}
        assert isinstance(context.created_at, datetime)
        assert context.timeout is None
        assert context.retry_count == 0
    
    def test_with_timeout(self):
        """Test ExecutionContext with timeout."""
        context = ExecutionContext(
            workflow_id=str(uuid4()),
            execution_id=str(uuid4()),
            timeout=300
        )
        
        assert context.timeout == 300
    
    def test_increment_retry(self):
        """Test retry count increment."""
        context = ExecutionContext(
            workflow_id=str(uuid4()),
            execution_id=str(uuid4())
        )
        
        assert context.retry_count == 0
        context.retry_count += 1
        assert context.retry_count == 1


class TestWorkflowExecutor:
    """Test WorkflowExecutor class."""
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock N8nApiClient."""
        client = AsyncMock(spec=N8nApiClient)
        return client
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return WorkflowExecutorConfig(
            max_concurrent_executions=5,
            execution_timeout=60,
            retry_attempts=2,
            retry_delay=1
        )
    
    @pytest.fixture
    def executor(self, mock_api_client, config):
        """Create WorkflowExecutor instance."""
        return WorkflowExecutor(mock_api_client, config)
    
    @pytest.fixture
    def sample_workflow(self):
        """Sample workflow for testing."""
        return Workflow(
            id=str(uuid4()),
            name="test_workflow",
            description="Test workflow",
            workflow_data={
                "nodes": [
                    {
                        "id": "start",
                        "type": "n8n-nodes-base.start",
                        "position": [100, 100]
                    }
                ],
                "connections": {}
            },
            parameters={"param1": "value1"}
        )
    
    @pytest.fixture
    def sample_execution(self, sample_workflow):
        """Sample execution for testing."""
        return WorkflowExecution(
            id=str(uuid4()),
            workflow_id=sample_workflow.id,
            status=ExecutionStatus.PENDING,
            parameters={"param1": "test_value"}
        )
    
    def test_initialization(self, mock_api_client, config):
        """Test WorkflowExecutor initialization."""
        executor = WorkflowExecutor(mock_api_client, config)
        
        assert executor.api_client == mock_api_client
        assert executor.config == config
        assert executor._active_executions == {}
        assert executor._execution_semaphore._value == config.max_concurrent_executions
        assert executor._monitor_task is None
        assert executor._running is False
    
    @pytest.mark.asyncio
    async def test_start_stop(self, executor):
        """Test executor start and stop."""
        # Start executor
        await executor.start()
        assert executor._running is True
        assert executor._monitor_task is not None
        
        # Stop executor
        await executor.stop()
        assert executor._running is False
        assert executor._monitor_task is None
    
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, executor, sample_workflow, sample_execution):
        """Test successful workflow execution."""
        # Mock API response
        executor.api_client.execute_workflow.return_value = N8nApiResponse(
            success=True,
            data={"id": "exec_123", "status": "running"},
            status_code=200
        )
        
        executor.api_client.get_execution.return_value = N8nApiResponse(
            success=True,
            data={
                "id": "exec_123",
                "status": "success",
                "data": {"result": "success"},
                "finished": True,
                "startedAt": datetime.now().isoformat(),
                "stoppedAt": datetime.now().isoformat()
            },
            status_code=200
        )
        
        # Execute workflow
        result = await executor.execute_workflow(sample_workflow, sample_execution.parameters)
        
        assert result is not None
        assert result.success is True
        assert result.execution_id == "exec_123"
        assert result.status == ExecutionStatus.SUCCESS
        
        # Verify API calls
        executor.api_client.execute_workflow.assert_called_once()
        executor.api_client.get_execution.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_workflow_failure(self, executor, sample_workflow):
        """Test workflow execution failure."""
        # Mock API error response
        executor.api_client.execute_workflow.return_value = N8nApiResponse(
            success=False,
            error="Execution failed",
            status_code=500
        )
        
        # Execute workflow
        result = await executor.execute_workflow(sample_workflow, {})
        
        assert result is not None
        assert result.success is False
        assert "Execution failed" in result.error
        assert result.status == ExecutionStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_execute_workflow_timeout(self, executor, sample_workflow):
        """Test workflow execution timeout."""
        # Mock API response that never completes
        executor.api_client.execute_workflow.return_value = N8nApiResponse(
            success=True,
            data={"id": "exec_123", "status": "running"},
            status_code=200
        )
        
        # Mock get_execution to always return running status
        executor.api_client.get_execution.return_value = N8nApiResponse(
            success=True,
            data={
                "id": "exec_123",
                "status": "running",
                "finished": False
            },
            status_code=200
        )
        
        # Set very short timeout
        executor.config.execution_timeout = 0.1
        
        # Execute workflow
        result = await executor.execute_workflow(sample_workflow, {})
        
        assert result is not None
        assert result.success is False
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_retry(self, executor, sample_workflow):
        """Test workflow execution with retry on failure."""
        # Mock API to fail first time, succeed second time
        call_count = 0
        
        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return N8nApiResponse(
                    success=False,
                    error="Temporary failure",
                    status_code=500
                )
            else:
                return N8nApiResponse(
                    success=True,
                    data={"id": "exec_123", "status": "running"},
                    status_code=200
                )
        
        executor.api_client.execute_workflow.side_effect = mock_execute
        
        executor.api_client.get_execution.return_value = N8nApiResponse(
            success=True,
            data={
                "id": "exec_123",
                "status": "success",
                "finished": True,
                "data": {"result": "success"}
            },
            status_code=200
        )
        
        # Execute workflow
        result = await executor.execute_workflow(sample_workflow, {})
        
        assert result is not None
        assert result.success is True
        assert call_count == 2  # Should have retried once
    
    @pytest.mark.asyncio
    async def test_execute_workflow_max_retries_exceeded(self, executor, sample_workflow):
        """Test workflow execution when max retries exceeded."""
        # Mock API to always fail
        executor.api_client.execute_workflow.return_value = N8nApiResponse(
            success=False,
            error="Persistent failure",
            status_code=500
        )
        
        # Execute workflow
        result = await executor.execute_workflow(sample_workflow, {})
        
        assert result is not None
        assert result.success is False
        assert result.status == ExecutionStatus.FAILED
        
        # Should have tried max_retry_attempts + 1 times
        expected_calls = executor.config.retry_attempts + 1
        assert executor.api_client.execute_workflow.call_count == expected_calls
    
    @pytest.mark.asyncio
    async def test_execute_workflow_concurrent_limit(self, executor, sample_workflow):
        """Test concurrent execution limit."""
        # Mock API to simulate long-running execution
        async def mock_execute(*args, **kwargs):
            await asyncio.sleep(0.1)
            return N8nApiResponse(
                success=True,
                data={"id": f"exec_{uuid4()}", "status": "running"},
                status_code=200
            )
        
        async def mock_get_execution(*args, **kwargs):
            await asyncio.sleep(0.1)
            return N8nApiResponse(
                success=True,
                data={
                    "id": "exec_123",
                    "status": "success",
                    "finished": True,
                    "data": {"result": "success"}
                },
                status_code=200
            )
        
        executor.api_client.execute_workflow.side_effect = mock_execute
        executor.api_client.get_execution.side_effect = mock_get_execution
        
        # Start more executions than the limit
        max_concurrent = executor.config.max_concurrent_executions
        tasks = []
        
        for i in range(max_concurrent + 2):
            task = asyncio.create_task(
                executor.execute_workflow(sample_workflow, {"param": f"value_{i}"})
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == max_concurrent + 2
        for result in results:
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_get_execution_status(self, executor):
        """Test getting execution status."""
        execution_id = "exec_123"
        
        # Mock API response
        executor.api_client.get_execution.return_value = N8nApiResponse(
            success=True,
            data={
                "id": execution_id,
                "status": "running",
                "finished": False,
                "startedAt": datetime.now().isoformat()
            },
            status_code=200
        )
        
        status = await executor.get_execution_status(execution_id)
        
        assert status == ExecutionStatus.RUNNING
        executor.api_client.get_execution.assert_called_once_with(execution_id)
    
    @pytest.mark.asyncio
    async def test_get_execution_status_not_found(self, executor):
        """Test getting status for non-existent execution."""
        execution_id = "non_existent"
        
        # Mock API error response
        executor.api_client.get_execution.return_value = N8nApiResponse(
            success=False,
            error="Execution not found",
            status_code=404
        )
        
        status = await executor.get_execution_status(execution_id)
        
        assert status is None
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self, executor):
        """Test canceling execution."""
        execution_id = "exec_123"
        
        # Mock API response
        executor.api_client.stop_execution.return_value = N8nApiResponse(
            success=True,
            data={"message": "Execution stopped"},
            status_code=200
        )
        
        result = await executor.cancel_execution(execution_id)
        
        assert result is True
        executor.api_client.stop_execution.assert_called_once_with(execution_id)
    
    @pytest.mark.asyncio
    async def test_cancel_execution_failure(self, executor):
        """Test canceling execution failure."""
        execution_id = "exec_123"
        
        # Mock API error response
        executor.api_client.stop_execution.return_value = N8nApiResponse(
            success=False,
            error="Cannot stop execution",
            status_code=400
        )
        
        result = await executor.cancel_execution(execution_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_active_executions(self, executor):
        """Test getting active executions."""
        # Add some mock active executions
        context1 = ExecutionContext(
            workflow_id=str(uuid4()),
            execution_id="exec_1"
        )
        context2 = ExecutionContext(
            workflow_id=str(uuid4()),
            execution_id="exec_2"
        )
        
        executor._active_executions["exec_1"] = context1
        executor._active_executions["exec_2"] = context2
        
        active = executor.get_active_executions()
        
        assert len(active) == 2
        assert "exec_1" in active
        assert "exec_2" in active
        assert active["exec_1"] == context1
        assert active["exec_2"] == context2
    
    def test_get_execution_statistics(self, executor):
        """Test getting execution statistics."""
        # Add some mock active executions
        for i in range(3):
            context = ExecutionContext(
                workflow_id=str(uuid4()),
                execution_id=f"exec_{i}"
            )
            executor._active_executions[f"exec_{i}"] = context
        
        stats = executor.get_execution_statistics()
        
        assert stats["active_executions"] == 3
        assert stats["max_concurrent_executions"] == executor.config.max_concurrent_executions
        assert stats["available_slots"] == executor.config.max_concurrent_executions - 3
        assert "uptime" in stats
    
    @pytest.mark.asyncio
    async def test_health_check(self, executor):
        """Test executor health check."""
        # Mock API health check
        executor.api_client.health_check.return_value = N8nApiResponse(
            success=True,
            data={"status": "ok"},
            status_code=200
        )
        
        health = await executor.health_check()
        
        assert health["status"] == "healthy"
        assert health["api_connection"] is True
        assert "active_executions" in health
        assert "uptime" in health
    
    @pytest.mark.asyncio
    async def test_health_check_api_failure(self, executor):
        """Test health check with API failure."""
        # Mock API health check failure
        executor.api_client.health_check.return_value = N8nApiResponse(
            success=False,
            error="API unavailable",
            status_code=503
        )
        
        health = await executor.health_check()
        
        assert health["status"] == "unhealthy"
        assert health["api_connection"] is False
        assert "error" in health


class TestExecutionMonitor:
    """Test ExecutionMonitor class."""
    
    @pytest.fixture
    def mock_executor(self):
        """Mock WorkflowExecutor."""
        executor = MagicMock(spec=WorkflowExecutor)
        executor.config = WorkflowExecutorConfig()
        executor._active_executions = {}
        executor._running = True
        return executor
    
    @pytest.fixture
    def monitor(self, mock_executor):
        """Create ExecutionMonitor instance."""
        return ExecutionMonitor(mock_executor)
    
    def test_initialization(self, mock_executor):
        """Test ExecutionMonitor initialization."""
        monitor = ExecutionMonitor(mock_executor)
        
        assert monitor.executor == mock_executor
        assert monitor._monitoring_task is None
        assert monitor._running is False
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring."""
        # Start monitoring
        await monitor.start()
        assert monitor._running is True
        assert monitor._monitoring_task is not None
        
        # Stop monitoring
        await monitor.stop()
        assert monitor._running is False
        assert monitor._monitoring_task is None
    
    @pytest.mark.asyncio
    async def test_monitor_executions(self, monitor, mock_executor):
        """Test monitoring executions."""
        # Mock active execution
        context = ExecutionContext(
            workflow_id=str(uuid4()),
            execution_id="exec_123",
            created_at=datetime.now() - timedelta(seconds=30)
        )
        mock_executor._active_executions = {"exec_123": context}
        
        # Mock API response for execution status
        mock_executor.api_client.get_execution.return_value = N8nApiResponse(
            success=True,
            data={
                "id": "exec_123",
                "status": "success",
                "finished": True
            },
            status_code=200
        )
        
        # Run one monitoring cycle
        await monitor._monitor_cycle()
        
        # Verify execution was checked
        mock_executor.api_client.get_execution.assert_called_with("exec_123")
    
    @pytest.mark.asyncio
    async def test_cleanup_completed_executions(self, monitor, mock_executor):
        """Test cleanup of completed executions."""
        # Mock old completed execution
        old_context = ExecutionContext(
            workflow_id=str(uuid4()),
            execution_id="exec_old",
            created_at=datetime.now() - timedelta(hours=2)
        )
        
        # Mock recent execution
        recent_context = ExecutionContext(
            workflow_id=str(uuid4()),
            execution_id="exec_recent",
            created_at=datetime.now() - timedelta(minutes=5)
        )
        
        mock_executor._active_executions = {
            "exec_old": old_context,
            "exec_recent": recent_context
        }
        
        # Set short cleanup interval
        mock_executor.config.cleanup_completed_after = 3600  # 1 hour
        
        # Mock API responses
        def mock_get_execution(execution_id):
            return N8nApiResponse(
                success=True,
                data={
                    "id": execution_id,
                    "status": "success",
                    "finished": True
                },
                status_code=200
            )
        
        mock_executor.api_client.get_execution.side_effect = mock_get_execution
        
        # Run monitoring cycle
        await monitor._monitor_cycle()
        
        # Old execution should be cleaned up, recent should remain
        assert "exec_old" not in mock_executor._active_executions
        assert "exec_recent" in mock_executor._active_executions


@pytest.mark.integration
class TestWorkflowExecutorIntegration:
    """Integration tests for WorkflowExecutor."""
    
    @pytest.mark.requires_n8n
    @pytest.mark.asyncio
    async def test_real_workflow_execution(self):
        """Test execution with real n8n instance."""
        # This test requires a real n8n instance
        # Skip if not available
        pytest.skip("Requires real n8n instance")
        
        # Real integration test would go here
        # - Connect to real n8n API
        # - Create a simple workflow
        # - Execute it
        # - Monitor execution
        # - Verify results
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_stress_test_concurrent_executions(self):
        """Stress test with many concurrent executions."""
        # Mock setup for stress testing
        mock_api_client = AsyncMock(spec=N8nApiClient)
        
        config = WorkflowExecutorConfig(
            max_concurrent_executions=50,
            execution_timeout=30
        )
        
        executor = WorkflowExecutor(mock_api_client, config)
        
        # Mock successful execution
        mock_api_client.execute_workflow.return_value = N8nApiResponse(
            success=True,
            data={"id": "exec_123", "status": "running"},
            status_code=200
        )
        
        mock_api_client.get_execution.return_value = N8nApiResponse(
            success=True,
            data={
                "id": "exec_123",
                "status": "success",
                "finished": True,
                "data": {"result": "success"}
            },
            status_code=200
        )
        
        # Create sample workflow
        workflow = Workflow(
            id=str(uuid4()),
            name="stress_test_workflow",
            workflow_data={"nodes": [], "connections": {}}
        )
        
        # Execute many workflows concurrently
        tasks = []
        for i in range(100):
            task = asyncio.create_task(
                executor.execute_workflow(workflow, {"iteration": i})
            )
            tasks.append(task)
        
        # Wait for all executions to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify results
        successful_results = [r for r in results if isinstance(r, ExecutionResult) and r.success]
        assert len(successful_results) == 100
        
        # Verify no active executions remain
        assert len(executor._active_executions) == 0