#!/usr/bin/env python3
"""
Tests for Workflow Automation Models.

Comprehensive test suite for all data models used in the workflow
automation system including validation, serialization, and relationships.

Author: UnityAI Team
Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import uuid4

from pydantic import ValidationError

from modules.workflow_automation.models import (
    WorkflowStatus,
    ExecutionStatus,
    ParameterType,
    ValidationRule,
    WorkflowParameter,
    WorkflowTemplate,
    Workflow,
    WorkflowExecution,
    ExecutionResult,
    WorkflowMetrics,
    ValidationResult
)


class TestEnums:
    """Test enumeration classes."""
    
    def test_workflow_status_values(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.CREATED == "created"
        assert WorkflowStatus.ACTIVE == "active"
        assert WorkflowStatus.INACTIVE == "inactive"
        assert WorkflowStatus.ARCHIVED == "archived"
        assert WorkflowStatus.ERROR == "error"
    
    def test_execution_status_values(self):
        """Test ExecutionStatus enum values."""
        assert ExecutionStatus.PENDING == "pending"
        assert ExecutionStatus.RUNNING == "running"
        assert ExecutionStatus.SUCCESS == "success"
        assert ExecutionStatus.FAILED == "failed"
        assert ExecutionStatus.CANCELLED == "cancelled"
        assert ExecutionStatus.TIMEOUT == "timeout"
    
    def test_parameter_type_values(self):
        """Test ParameterType enum values."""
        assert ParameterType.STRING == "string"
        assert ParameterType.INTEGER == "integer"
        assert ParameterType.FLOAT == "float"
        assert ParameterType.BOOLEAN == "boolean"
        assert ParameterType.ARRAY == "array"
        assert ParameterType.OBJECT == "object"
        assert ParameterType.FILE == "file"
        assert ParameterType.URL == "url"
        assert ParameterType.EMAIL == "email"
        assert ParameterType.DATE == "date"
        assert ParameterType.DATETIME == "datetime"


class TestValidationRule:
    """Test ValidationRule model."""
    
    def test_basic_validation_rule(self):
        """Test basic validation rule creation."""
        rule = ValidationRule(
            type=ParameterType.STRING,
            required=True,
            min_length=5,
            max_length=100
        )
        
        assert rule.type == ParameterType.STRING
        assert rule.required is True
        assert rule.min_length == 5
        assert rule.max_length == 100
        assert rule.default is None
    
    def test_validation_rule_with_default(self):
        """Test validation rule with default value."""
        rule = ValidationRule(
            type=ParameterType.INTEGER,
            default=42,
            min_value=0,
            max_value=100
        )
        
        assert rule.type == ParameterType.INTEGER
        assert rule.default == 42
        assert rule.min_value == 0
        assert rule.max_value == 100
    
    def test_validation_rule_with_allowed_values(self):
        """Test validation rule with allowed values."""
        rule = ValidationRule(
            type=ParameterType.STRING,
            allowed_values=["option1", "option2", "option3"]
        )
        
        assert rule.allowed_values == ["option1", "option2", "option3"]
    
    def test_validation_rule_with_pattern(self):
        """Test validation rule with regex pattern."""
        rule = ValidationRule(
            type=ParameterType.STRING,
            pattern=r"^[a-zA-Z0-9]+$"
        )
        
        assert rule.pattern == r"^[a-zA-Z0-9]+$"


class TestWorkflowParameter:
    """Test WorkflowParameter model."""
    
    def test_basic_parameter(self):
        """Test basic parameter creation."""
        param = WorkflowParameter(
            name="test_param",
            type=ParameterType.STRING,
            description="Test parameter"
        )
        
        assert param.name == "test_param"
        assert param.type == ParameterType.STRING
        assert param.description == "Test parameter"
        assert param.required is False
        assert param.default is None
        assert param.validation is None
        assert param.group is None
        assert param.order == 0
        assert param.sensitive is False
    
    def test_required_parameter(self):
        """Test required parameter."""
        param = WorkflowParameter(
            name="required_param",
            type=ParameterType.STRING,
            required=True
        )
        
        assert param.required is True
    
    def test_parameter_with_validation(self):
        """Test parameter with validation rule."""
        validation = ValidationRule(
            type=ParameterType.STRING,
            min_length=5,
            max_length=50
        )
        
        param = WorkflowParameter(
            name="validated_param",
            type=ParameterType.STRING,
            validation=validation
        )
        
        assert param.validation == validation
        assert param.validation.min_length == 5
        assert param.validation.max_length == 50
    
    def test_sensitive_parameter(self):
        """Test sensitive parameter (e.g., password)."""
        param = WorkflowParameter(
            name="api_key",
            type=ParameterType.STRING,
            sensitive=True,
            description="API key for authentication"
        )
        
        assert param.sensitive is True
    
    def test_parameter_with_group_and_order(self):
        """Test parameter with group and order."""
        param = WorkflowParameter(
            name="grouped_param",
            type=ParameterType.STRING,
            group="authentication",
            order=10
        )
        
        assert param.group == "authentication"
        assert param.order == 10


class TestWorkflowTemplate:
    """Test WorkflowTemplate model."""
    
    def test_basic_template(self):
        """Test basic template creation."""
        template_data = {
            "nodes": [
                {
                    "id": "start",
                    "type": "n8n-nodes-base.start",
                    "position": [100, 100]
                }
            ],
            "connections": {}
        }
        
        template = WorkflowTemplate(
            name="test_template",
            description="Test template",
            template_data=template_data
        )
        
        assert template.name == "test_template"
        assert template.description == "Test template"
        assert template.version == "1.0.0"  # default
        assert template.category == "general"  # default
        assert template.template_data == template_data
        assert template.tags == []
        assert template.parameters == []
        assert template.id is not None  # auto-generated UUID
    
    def test_template_with_parameters(self):
        """Test template with parameters."""
        param1 = WorkflowParameter(
            name="param1",
            type=ParameterType.STRING,
            required=True
        )
        param2 = WorkflowParameter(
            name="param2",
            type=ParameterType.INTEGER,
            default=42
        )
        
        template = WorkflowTemplate(
            name="parameterized_template",
            template_data={"nodes": [], "connections": {}},
            parameters=[param1, param2]
        )
        
        assert len(template.parameters) == 2
        assert template.parameters[0] == param1
        assert template.parameters[1] == param2
    
    def test_template_with_metadata(self):
        """Test template with full metadata."""
        template = WorkflowTemplate(
            name="full_template",
            description="Full template with metadata",
            version="2.1.0",
            category="data_processing",
            tags=["etl", "data", "processing"],
            template_data={"nodes": [], "connections": {}},
            author="Test Author",
            documentation_url="https://docs.example.com",
            icon="data-icon"
        )
        
        assert template.version == "2.1.0"
        assert template.category == "data_processing"
        assert template.tags == ["etl", "data", "processing"]
        assert template.author == "Test Author"
        assert template.documentation_url == "https://docs.example.com"
        assert template.icon == "data-icon"
    
    def test_template_validation_empty_name(self):
        """Test template validation with empty name."""
        with pytest.raises(ValidationError):
            WorkflowTemplate(
                name="",  # Empty name should fail
                template_data={"nodes": [], "connections": {}}
            )
    
    def test_template_validation_missing_template_data(self):
        """Test template validation with missing template data."""
        with pytest.raises(ValidationError):
            WorkflowTemplate(
                name="test_template"
                # Missing template_data should fail
            )


class TestWorkflow:
    """Test Workflow model."""
    
    def test_basic_workflow(self):
        """Test basic workflow creation."""
        workflow_data = {
            "nodes": [
                {
                    "id": "start",
                    "type": "n8n-nodes-base.start",
                    "position": [100, 100]
                }
            ],
            "connections": {}
        }
        
        workflow = Workflow(
            name="test_workflow",
            template_name="test_template",
            template_version="1.0.0",
            parameters={"param1": "value1"},
            workflow_data=workflow_data
        )
        
        assert workflow.name == "test_workflow"
        assert workflow.template_name == "test_template"
        assert workflow.template_version == "1.0.0"
        assert workflow.parameters == {"param1": "value1"}
        assert workflow.workflow_data == workflow_data
        assert workflow.status == WorkflowStatus.CREATED  # default
        assert workflow.id is not None  # auto-generated UUID
        assert workflow.created_at is not None
        assert workflow.updated_at is None
    
    def test_workflow_with_metadata(self):
        """Test workflow with full metadata."""
        workflow = Workflow(
            name="full_workflow",
            description="Full workflow with metadata",
            template_name="test_template",
            template_version="1.0.0",
            parameters={},
            workflow_data={"nodes": [], "connections": {}},
            tags=["test", "automation"],
            status=WorkflowStatus.ACTIVE,
            n8n_workflow_id="n8n_123"
        )
        
        assert workflow.description == "Full workflow with metadata"
        assert workflow.tags == ["test", "automation"]
        assert workflow.status == WorkflowStatus.ACTIVE
        assert workflow.n8n_workflow_id == "n8n_123"
    
    def test_workflow_update_timestamp(self):
        """Test workflow timestamp updates."""
        workflow = Workflow(
            name="test_workflow",
            template_name="test_template",
            template_version="1.0.0",
            parameters={},
            workflow_data={"nodes": [], "connections": {}}
        )
        
        original_created = workflow.created_at
        assert workflow.updated_at is None
        
        # Simulate update
        workflow.updated_at = datetime.utcnow()
        
        assert workflow.created_at == original_created
        assert workflow.updated_at is not None
        assert workflow.updated_at > workflow.created_at
    
    def test_workflow_validation_empty_name(self):
        """Test workflow validation with empty name."""
        with pytest.raises(ValidationError):
            Workflow(
                name="",  # Empty name should fail
                template_name="test_template",
                template_version="1.0.0",
                parameters={},
                workflow_data={"nodes": [], "connections": {}}
            )


class TestWorkflowExecution:
    """Test WorkflowExecution model."""
    
    def test_basic_execution(self):
        """Test basic execution creation."""
        execution = WorkflowExecution(
            workflow_id="workflow_123",
            input_data={"test": "data"}
        )
        
        assert execution.workflow_id == "workflow_123"
        assert execution.input_data == {"test": "data"}
        assert execution.status == ExecutionStatus.PENDING  # default
        assert execution.id is not None  # auto-generated UUID
        assert execution.created_at is not None
        assert execution.started_at is None
        assert execution.finished_at is None
        assert execution.output_data is None
        assert execution.error_message is None
    
    def test_execution_lifecycle(self):
        """Test execution status lifecycle."""
        execution = WorkflowExecution(
            workflow_id="workflow_123",
            input_data={}
        )
        
        # Start execution
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.started_at is not None
        
        # Complete execution
        execution.status = ExecutionStatus.SUCCESS
        execution.finished_at = datetime.utcnow()
        execution.output_data = {"result": "success"}
        
        assert execution.status == ExecutionStatus.SUCCESS
        assert execution.finished_at is not None
        assert execution.output_data == {"result": "success"}
        assert execution.finished_at > execution.started_at
    
    def test_execution_with_error(self):
        """Test execution with error."""
        execution = WorkflowExecution(
            workflow_id="workflow_123",
            input_data={}
        )
        
        # Fail execution
        execution.status = ExecutionStatus.FAILED
        execution.finished_at = datetime.utcnow()
        execution.error_message = "Test error message"
        
        assert execution.status == ExecutionStatus.FAILED
        assert execution.error_message == "Test error message"
    
    def test_execution_duration_property(self):
        """Test execution duration calculation."""
        execution = WorkflowExecution(
            workflow_id="workflow_123",
            input_data={}
        )
        
        # No duration when not started
        assert execution.duration is None
        
        # Duration when started but not finished
        execution.started_at = datetime.utcnow()
        duration = execution.duration
        assert duration is not None
        assert duration >= timedelta(0)
        
        # Duration when finished
        execution.finished_at = execution.started_at + timedelta(seconds=30)
        assert execution.duration == timedelta(seconds=30)
    
    def test_execution_with_metadata(self):
        """Test execution with metadata."""
        execution = WorkflowExecution(
            workflow_id="workflow_123",
            input_data={},
            n8n_execution_id="n8n_exec_456",
            trigger_mode="manual",
            user_id="user_789"
        )
        
        assert execution.n8n_execution_id == "n8n_exec_456"
        assert execution.trigger_mode == "manual"
        assert execution.user_id == "user_789"


class TestExecutionResult:
    """Test ExecutionResult model."""
    
    def test_successful_result(self):
        """Test successful execution result."""
        result = ExecutionResult(
            success=True,
            execution_id="exec_123",
            output_data={"result": "success"},
            duration=timedelta(seconds=30)
        )
        
        assert result.success is True
        assert result.execution_id == "exec_123"
        assert result.output_data == {"result": "success"}
        assert result.duration == timedelta(seconds=30)
        assert result.error_message is None
    
    def test_failed_result(self):
        """Test failed execution result."""
        result = ExecutionResult(
            success=False,
            execution_id="exec_123",
            error_message="Execution failed",
            duration=timedelta(seconds=15)
        )
        
        assert result.success is False
        assert result.error_message == "Execution failed"
        assert result.output_data is None


class TestWorkflowMetrics:
    """Test WorkflowMetrics model."""
    
    def test_basic_metrics(self):
        """Test basic metrics creation."""
        metrics = WorkflowMetrics(
            workflow_id="workflow_123",
            total_executions=100,
            successful_executions=85,
            failed_executions=15,
            average_duration=timedelta(seconds=45)
        )
        
        assert metrics.workflow_id == "workflow_123"
        assert metrics.total_executions == 100
        assert metrics.successful_executions == 85
        assert metrics.failed_executions == 15
        assert metrics.average_duration == timedelta(seconds=45)
    
    def test_metrics_success_rate_property(self):
        """Test success rate calculation."""
        metrics = WorkflowMetrics(
            workflow_id="workflow_123",
            total_executions=100,
            successful_executions=85,
            failed_executions=15
        )
        
        assert metrics.success_rate == 0.85
        
        # Test with zero executions
        metrics_zero = WorkflowMetrics(
            workflow_id="workflow_456",
            total_executions=0,
            successful_executions=0,
            failed_executions=0
        )
        
        assert metrics_zero.success_rate == 0.0


class TestValidationResult:
    """Test ValidationResult model."""
    
    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult(
            valid=True,
            errors=[]
        )
        
        assert result.valid is True
        assert result.errors == []
    
    def test_invalid_result(self):
        """Test invalid validation result."""
        errors = [
            "Parameter 'name' is required",
            "Parameter 'age' must be a positive integer"
        ]
        
        result = ValidationResult(
            valid=False,
            errors=errors
        )
        
        assert result.valid is False
        assert result.errors == errors
    
    def test_validation_result_with_warnings(self):
        """Test validation result with warnings."""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=["Parameter 'timeout' not specified, using default"]
        )
        
        assert result.valid is True
        assert result.warnings == ["Parameter 'timeout' not specified, using default"]


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_workflow_json_serialization(self):
        """Test workflow JSON serialization."""
        workflow = Workflow(
            name="test_workflow",
            template_name="test_template",
            template_version="1.0.0",
            parameters={"param1": "value1"},
            workflow_data={"nodes": [], "connections": {}}
        )
        
        # Serialize to JSON
        json_data = workflow.json()
        assert isinstance(json_data, str)
        
        # Deserialize from JSON
        workflow_copy = Workflow.parse_raw(json_data)
        assert workflow_copy.name == workflow.name
        assert workflow_copy.template_name == workflow.template_name
        assert workflow_copy.parameters == workflow.parameters
    
    def test_workflow_dict_serialization(self):
        """Test workflow dict serialization."""
        workflow = Workflow(
            name="test_workflow",
            template_name="test_template",
            template_version="1.0.0",
            parameters={"param1": "value1"},
            workflow_data={"nodes": [], "connections": {}}
        )
        
        # Serialize to dict
        dict_data = workflow.dict()
        assert isinstance(dict_data, dict)
        assert dict_data['name'] == "test_workflow"
        assert dict_data['template_name'] == "test_template"
        
        # Deserialize from dict
        workflow_copy = Workflow(**dict_data)
        assert workflow_copy.name == workflow.name
    
    def test_execution_json_serialization(self):
        """Test execution JSON serialization."""
        execution = WorkflowExecution(
            workflow_id="workflow_123",
            input_data={"test": "data"},
            status=ExecutionStatus.SUCCESS,
            output_data={"result": "success"}
        )
        
        # Serialize to JSON
        json_data = execution.json()
        assert isinstance(json_data, str)
        
        # Deserialize from JSON
        execution_copy = WorkflowExecution.parse_raw(json_data)
        assert execution_copy.workflow_id == execution.workflow_id
        assert execution_copy.status == execution.status
        assert execution_copy.input_data == execution.input_data
        assert execution_copy.output_data == execution.output_data