#!/usr/bin/env python3
"""
Tests for Workflow Validator.

Comprehensive test suite for the workflow validator that validates
workflow templates, parameters, and execution data.

Author: UnityAI Team
Version: 1.0.0
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from modules.workflow_automation.validator import (
    WorkflowValidator,
    ValidatorConfig,
    ParameterValidator,
    TemplateValidator,
    ExecutionValidator
)
from modules.workflow_automation.models import (
    WorkflowTemplate,
    WorkflowParameter,
    ValidationRule,
    ValidationResult,
    ParameterType,
    Workflow,
    WorkflowExecution
)


class TestValidatorConfig:
    """Test ValidatorConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ValidatorConfig()
        
        assert config.strict_validation is True
        assert config.allow_extra_parameters is False
        assert config.validate_node_connections is True
        assert config.validate_parameter_types is True
        assert config.validate_required_fields is True
        assert config.max_template_size == 1024 * 1024  # 1MB
        assert config.max_parameter_count == 100
        assert config.max_node_count == 50
        assert config.enable_custom_validators is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ValidatorConfig(
            strict_validation=False,
            allow_extra_parameters=True,
            validate_node_connections=False,
            validate_parameter_types=False,
            validate_required_fields=False,
            max_template_size=512 * 1024,
            max_parameter_count=50,
            max_node_count=25,
            enable_custom_validators=False
        )
        
        assert config.strict_validation is False
        assert config.allow_extra_parameters is True
        assert config.validate_node_connections is False
        assert config.validate_parameter_types is False
        assert config.validate_required_fields is False
        assert config.max_template_size == 512 * 1024
        assert config.max_parameter_count == 50
        assert config.max_node_count == 25
        assert config.enable_custom_validators is False


class TestParameterValidator:
    """Test ParameterValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create ParameterValidator instance."""
        return ParameterValidator()
    
    @pytest.fixture
    def string_parameter(self):
        """Sample string parameter with validation rules."""
        return WorkflowParameter(
            name="username",
            type=ParameterType.STRING,
            required=True,
            description="User name",
            validation=ValidationRule(
                min_length=3,
                max_length=20,
                pattern=r"^[a-zA-Z0-9_]+$"
            )
        )
    
    @pytest.fixture
    def number_parameter(self):
        """Sample number parameter with validation rules."""
        return WorkflowParameter(
            name="age",
            type=ParameterType.NUMBER,
            required=True,
            description="User age",
            validation=ValidationRule(
                min_value=0,
                max_value=120
            )
        )
    
    @pytest.fixture
    def array_parameter(self):
        """Sample array parameter with validation rules."""
        return WorkflowParameter(
            name="tags",
            type=ParameterType.ARRAY,
            required=False,
            description="Tags list",
            validation=ValidationRule(
                min_items=1,
                max_items=10
            )
        )
    
    def test_validate_string_parameter_valid(self, validator, string_parameter):
        """Test validating valid string parameter."""
        result = validator.validate_parameter(string_parameter, "john_doe")
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.parameter_name == "username"
    
    def test_validate_string_parameter_too_short(self, validator, string_parameter):
        """Test validating string parameter that's too short."""
        result = validator.validate_parameter(string_parameter, "jo")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "minimum length" in result.errors[0].lower()
    
    def test_validate_string_parameter_too_long(self, validator, string_parameter):
        """Test validating string parameter that's too long."""
        result = validator.validate_parameter(string_parameter, "a" * 25)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "maximum length" in result.errors[0].lower()
    
    def test_validate_string_parameter_invalid_pattern(self, validator, string_parameter):
        """Test validating string parameter with invalid pattern."""
        result = validator.validate_parameter(string_parameter, "john-doe!")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "pattern" in result.errors[0].lower()
    
    def test_validate_number_parameter_valid(self, validator, number_parameter):
        """Test validating valid number parameter."""
        result = validator.validate_parameter(number_parameter, 25)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_number_parameter_string_number(self, validator, number_parameter):
        """Test validating number parameter with string number."""
        result = validator.validate_parameter(number_parameter, "25")
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_number_parameter_too_small(self, validator, number_parameter):
        """Test validating number parameter that's too small."""
        result = validator.validate_parameter(number_parameter, -5)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "minimum value" in result.errors[0].lower()
    
    def test_validate_number_parameter_too_large(self, validator, number_parameter):
        """Test validating number parameter that's too large."""
        result = validator.validate_parameter(number_parameter, 150)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "maximum value" in result.errors[0].lower()
    
    def test_validate_number_parameter_invalid_type(self, validator, number_parameter):
        """Test validating number parameter with invalid type."""
        result = validator.validate_parameter(number_parameter, "not_a_number")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "number" in result.errors[0].lower()
    
    def test_validate_array_parameter_valid(self, validator, array_parameter):
        """Test validating valid array parameter."""
        result = validator.validate_parameter(array_parameter, ["tag1", "tag2", "tag3"])
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_array_parameter_empty(self, validator, array_parameter):
        """Test validating empty array parameter."""
        result = validator.validate_parameter(array_parameter, [])
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "minimum items" in result.errors[0].lower()
    
    def test_validate_array_parameter_too_many_items(self, validator, array_parameter):
        """Test validating array parameter with too many items."""
        large_array = [f"tag{i}" for i in range(15)]
        result = validator.validate_parameter(array_parameter, large_array)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "maximum items" in result.errors[0].lower()
    
    def test_validate_array_parameter_not_array(self, validator, array_parameter):
        """Test validating array parameter with non-array value."""
        result = validator.validate_parameter(array_parameter, "not_an_array")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "array" in result.errors[0].lower()
    
    def test_validate_boolean_parameter(self, validator):
        """Test validating boolean parameter."""
        bool_param = WorkflowParameter(
            name="enabled",
            type=ParameterType.BOOLEAN,
            required=True
        )
        
        # Test valid boolean values
        assert validator.validate_parameter(bool_param, True).is_valid
        assert validator.validate_parameter(bool_param, False).is_valid
        assert validator.validate_parameter(bool_param, "true").is_valid
        assert validator.validate_parameter(bool_param, "false").is_valid
        assert validator.validate_parameter(bool_param, 1).is_valid
        assert validator.validate_parameter(bool_param, 0).is_valid
        
        # Test invalid boolean value
        result = validator.validate_parameter(bool_param, "maybe")
        assert result.is_valid is False
        assert "boolean" in result.errors[0].lower()
    
    def test_validate_object_parameter(self, validator):
        """Test validating object parameter."""
        obj_param = WorkflowParameter(
            name="config",
            type=ParameterType.OBJECT,
            required=True
        )
        
        # Test valid object
        valid_obj = {"key1": "value1", "key2": 42}
        result = validator.validate_parameter(obj_param, valid_obj)
        assert result.is_valid is True
        
        # Test invalid object (string)
        result = validator.validate_parameter(obj_param, "not_an_object")
        assert result.is_valid is False
        assert "object" in result.errors[0].lower()
    
    def test_validate_required_parameter_missing(self, validator, string_parameter):
        """Test validating required parameter with None value."""
        result = validator.validate_parameter(string_parameter, None)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "required" in result.errors[0].lower()
    
    def test_validate_optional_parameter_missing(self, validator, array_parameter):
        """Test validating optional parameter with None value."""
        # array_parameter is not required
        result = validator.validate_parameter(array_parameter, None)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_parameter_with_default_value(self, validator):
        """Test validating parameter with default value."""
        param_with_default = WorkflowParameter(
            name="timeout",
            type=ParameterType.NUMBER,
            required=False,
            default_value=30
        )
        
        # Test with None value (should use default)
        result = validator.validate_parameter(param_with_default, None)
        assert result.is_valid is True
        
        # Test with explicit value
        result = validator.validate_parameter(param_with_default, 60)
        assert result.is_valid is True
    
    def test_validate_parameter_with_allowed_values(self, validator):
        """Test validating parameter with allowed values constraint."""
        enum_param = WorkflowParameter(
            name="priority",
            type=ParameterType.STRING,
            required=True,
            validation=ValidationRule(
                allowed_values=["low", "medium", "high"]
            )
        )
        
        # Test valid value
        result = validator.validate_parameter(enum_param, "medium")
        assert result.is_valid is True
        
        # Test invalid value
        result = validator.validate_parameter(enum_param, "urgent")
        assert result.is_valid is False
        assert "allowed values" in result.errors[0].lower()
    
    def test_validate_multiple_parameters(self, validator, string_parameter, number_parameter):
        """Test validating multiple parameters at once."""
        parameters = [string_parameter, number_parameter]
        values = {"username": "john_doe", "age": 25}
        
        results = validator.validate_parameters(parameters, values)
        
        assert len(results) == 2
        assert all(result.is_valid for result in results)
    
    def test_validate_multiple_parameters_with_errors(self, validator, string_parameter, number_parameter):
        """Test validating multiple parameters with some errors."""
        parameters = [string_parameter, number_parameter]
        values = {"username": "jo", "age": 150}  # Both invalid
        
        results = validator.validate_parameters(parameters, values)
        
        assert len(results) == 2
        assert all(not result.is_valid for result in results)
        assert len(results[0].errors) == 1  # username too short
        assert len(results[1].errors) == 1  # age too large
    
    def test_validate_parameters_missing_required(self, validator, string_parameter, number_parameter):
        """Test validating parameters with missing required values."""
        parameters = [string_parameter, number_parameter]
        values = {"username": "john_doe"}  # Missing age
        
        results = validator.validate_parameters(parameters, values)
        
        assert len(results) == 2
        assert results[0].is_valid is True  # username provided
        assert results[1].is_valid is False  # age missing
        assert "required" in results[1].errors[0].lower()


class TestTemplateValidator:
    """Test TemplateValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create TemplateValidator instance."""
        return TemplateValidator()
    
    @pytest.fixture
    def valid_template(self):
        """Sample valid workflow template."""
        return WorkflowTemplate(
            id="template_001",
            name="Test Template",
            description="A test template",
            version="1.0.0",
            category="test",
            tags=["test", "example"],
            template_data={
                "nodes": [
                    {
                        "id": "node1",
                        "name": "Start",
                        "type": "n8n-nodes-base.start",
                        "position": [100, 100],
                        "parameters": {}
                    },
                    {
                        "id": "node2",
                        "name": "HTTP Request",
                        "type": "n8n-nodes-base.httpRequest",
                        "position": [300, 100],
                        "parameters": {
                            "url": "{{$parameter.api_url}}",
                            "method": "GET"
                        }
                    }
                ],
                "connections": {
                    "Start": {
                        "main": [
                            [
                                {
                                    "node": "HTTP Request",
                                    "type": "main",
                                    "index": 0
                                }
                            ]
                        ]
                    }
                }
            },
            parameters=[
                WorkflowParameter(
                    name="api_url",
                    type=ParameterType.STRING,
                    required=True,
                    description="API URL to call"
                )
            ]
        )
    
    def test_validate_template_structure_valid(self, validator, valid_template):
        """Test validating valid template structure."""
        result = validator.validate_template_structure(valid_template)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_template_structure_missing_nodes(self, validator, valid_template):
        """Test validating template with missing nodes."""
        valid_template.template_data["nodes"] = []
        
        result = validator.validate_template_structure(valid_template)
        
        assert result.is_valid is False
        assert any("nodes" in error.lower() for error in result.errors)
    
    def test_validate_template_structure_invalid_node(self, validator, valid_template):
        """Test validating template with invalid node structure."""
        # Remove required field from node
        del valid_template.template_data["nodes"][0]["type"]
        
        result = validator.validate_template_structure(valid_template)
        
        assert result.is_valid is False
        assert any("type" in error.lower() for error in result.errors)
    
    def test_validate_template_structure_missing_connections(self, validator, valid_template):
        """Test validating template with missing connections."""
        del valid_template.template_data["connections"]
        
        result = validator.validate_template_structure(valid_template)
        
        assert result.is_valid is False
        assert any("connections" in error.lower() for error in result.errors)
    
    def test_validate_node_connections_valid(self, validator, valid_template):
        """Test validating valid node connections."""
        result = validator.validate_node_connections(valid_template)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_node_connections_invalid_reference(self, validator, valid_template):
        """Test validating connections with invalid node reference."""
        # Reference non-existent node
        valid_template.template_data["connections"]["Start"]["main"][0][0]["node"] = "NonExistent"
        
        result = validator.validate_node_connections(valid_template)
        
        assert result.is_valid is False
        assert any("nonexistent" in error.lower() for error in result.errors)
    
    def test_validate_node_connections_circular_dependency(self, validator, valid_template):
        """Test validating connections with circular dependency."""
        # Add circular connection
        valid_template.template_data["connections"]["HTTP Request"] = {
            "main": [
                [
                    {
                        "node": "Start",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }
        
        result = validator.validate_node_connections(valid_template)
        
        assert result.is_valid is False
        assert any("circular" in error.lower() for error in result.errors)
    
    def test_validate_template_parameters_valid(self, validator, valid_template):
        """Test validating valid template parameters."""
        result = validator.validate_template_parameters(valid_template)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_template_parameters_unused_parameter(self, validator, valid_template):
        """Test validating template with unused parameter."""
        # Add unused parameter
        unused_param = WorkflowParameter(
            name="unused_param",
            type=ParameterType.STRING,
            required=False
        )
        valid_template.parameters.append(unused_param)
        
        result = validator.validate_template_parameters(valid_template)
        
        assert result.is_valid is False
        assert any("unused" in error.lower() for error in result.errors)
    
    def test_validate_template_parameters_missing_parameter(self, validator, valid_template):
        """Test validating template with missing parameter definition."""
        # Use parameter in template but don't define it
        valid_template.template_data["nodes"][1]["parameters"]["headers"] = "{{$parameter.auth_token}}"
        
        result = validator.validate_template_parameters(valid_template)
        
        assert result.is_valid is False
        assert any("auth_token" in error.lower() for error in result.errors)
    
    def test_validate_template_size(self, validator, valid_template):
        """Test validating template size."""
        config = ValidatorConfig(max_template_size=1000)  # 1KB limit
        validator.config = config
        
        # Add large data to exceed limit
        valid_template.template_data["large_data"] = "x" * 2000
        
        result = validator.validate_template_size(valid_template)
        
        assert result.is_valid is False
        assert any("size" in error.lower() for error in result.errors)
    
    def test_validate_node_count(self, validator, valid_template):
        """Test validating node count limit."""
        config = ValidatorConfig(max_node_count=1)
        validator.config = config
        
        result = validator.validate_node_count(valid_template)
        
        assert result.is_valid is False
        assert any("node count" in error.lower() for error in result.errors)
    
    def test_validate_parameter_count(self, validator, valid_template):
        """Test validating parameter count limit."""
        config = ValidatorConfig(max_parameter_count=0)
        validator.config = config
        
        result = validator.validate_parameter_count(valid_template)
        
        assert result.is_valid is False
        assert any("parameter count" in error.lower() for error in result.errors)
    
    def test_validate_template_comprehensive(self, validator, valid_template):
        """Test comprehensive template validation."""
        result = validator.validate_template(valid_template)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.template_id == "template_001"
    
    def test_validate_template_comprehensive_with_errors(self, validator, valid_template):
        """Test comprehensive template validation with multiple errors."""
        # Introduce multiple errors
        del valid_template.template_data["nodes"][0]["type"]  # Missing node type
        valid_template.template_data["connections"]["Start"]["main"][0][0]["node"] = "NonExistent"  # Invalid connection
        
        result = validator.validate_template(valid_template)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2  # Should have multiple errors


class TestExecutionValidator:
    """Test ExecutionValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create ExecutionValidator instance."""
        return ExecutionValidator()
    
    @pytest.fixture
    def sample_workflow(self):
        """Sample workflow for testing."""
        return Workflow(
            id="workflow_001",
            name="Test Workflow",
            template_id="template_001",
            parameters={"api_url": "https://api.example.com"},
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_execution(self, sample_workflow):
        """Sample workflow execution for testing."""
        return WorkflowExecution(
            id="exec_001",
            workflow_id=sample_workflow.id,
            status="running",
            started_at=datetime.now()
        )
    
    def test_validate_execution_parameters_valid(self, validator, sample_workflow):
        """Test validating valid execution parameters."""
        parameters = {"api_url": "https://api.example.com"}
        
        result = validator.validate_execution_parameters(sample_workflow, parameters)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_execution_parameters_missing_required(self, validator, sample_workflow):
        """Test validating execution with missing required parameters."""
        parameters = {}  # Missing api_url
        
        result = validator.validate_execution_parameters(sample_workflow, parameters)
        
        assert result.is_valid is False
        assert any("required" in error.lower() for error in result.errors)
    
    def test_validate_execution_parameters_extra_parameters(self, validator, sample_workflow):
        """Test validating execution with extra parameters."""
        parameters = {
            "api_url": "https://api.example.com",
            "extra_param": "not_allowed"
        }
        
        # Test with strict validation (default)
        config = ValidatorConfig(allow_extra_parameters=False)
        validator.config = config
        
        result = validator.validate_execution_parameters(sample_workflow, parameters)
        
        assert result.is_valid is False
        assert any("extra" in error.lower() for error in result.errors)
        
        # Test with allowing extra parameters
        config.allow_extra_parameters = True
        validator.config = config
        
        result = validator.validate_execution_parameters(sample_workflow, parameters)
        
        assert result.is_valid is True
    
    def test_validate_execution_state_valid(self, validator, sample_execution):
        """Test validating valid execution state."""
        result = validator.validate_execution_state(sample_execution)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_execution_state_invalid_transition(self, validator, sample_execution):
        """Test validating invalid execution state transition."""
        # Set execution to completed but without end time
        sample_execution.status = "completed"
        sample_execution.finished_at = None
        
        result = validator.validate_execution_state(sample_execution)
        
        assert result.is_valid is False
        assert any("finished_at" in error.lower() for error in result.errors)
    
    def test_validate_execution_state_invalid_status(self, validator, sample_execution):
        """Test validating execution with invalid status."""
        sample_execution.status = "invalid_status"
        
        result = validator.validate_execution_state(sample_execution)
        
        assert result.is_valid is False
        assert any("status" in error.lower() for error in result.errors)
    
    def test_validate_execution_timeout(self, validator, sample_execution):
        """Test validating execution timeout."""
        # Set execution start time to long ago
        from datetime import timedelta
        sample_execution.started_at = datetime.now() - timedelta(hours=2)
        
        # Set timeout to 1 hour
        timeout_seconds = 3600
        
        result = validator.validate_execution_timeout(sample_execution, timeout_seconds)
        
        assert result.is_valid is False
        assert any("timeout" in error.lower() for error in result.errors)
    
    def test_validate_execution_timeout_not_exceeded(self, validator, sample_execution):
        """Test validating execution within timeout."""
        # Set timeout to 2 hours
        timeout_seconds = 7200
        
        result = validator.validate_execution_timeout(sample_execution, timeout_seconds)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_execution_data_structure(self, validator):
        """Test validating execution data structure."""
        valid_data = {
            "nodes": [
                {
                    "id": "node1",
                    "name": "Start",
                    "type": "n8n-nodes-base.start"
                }
            ],
            "connections": {}
        }
        
        result = validator.validate_execution_data_structure(valid_data)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_execution_data_structure_invalid(self, validator):
        """Test validating invalid execution data structure."""
        invalid_data = {
            "invalid_field": "value"
        }
        
        result = validator.validate_execution_data_structure(invalid_data)
        
        assert result.is_valid is False
        assert any("structure" in error.lower() for error in result.errors)


class TestWorkflowValidator:
    """Test main WorkflowValidator class."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return ValidatorConfig(
            strict_validation=True,
            validate_node_connections=True,
            validate_parameter_types=True
        )
    
    @pytest.fixture
    def validator(self, config):
        """Create WorkflowValidator instance."""
        return WorkflowValidator(config)
    
    @pytest.fixture
    def valid_template(self):
        """Sample valid workflow template."""
        return WorkflowTemplate(
            id="template_001",
            name="Test Template",
            description="A test template",
            version="1.0.0",
            category="test",
            template_data={
                "nodes": [
                    {
                        "id": "node1",
                        "name": "Start",
                        "type": "n8n-nodes-base.start",
                        "position": [100, 100],
                        "parameters": {}
                    }
                ],
                "connections": {}
            },
            parameters=[
                WorkflowParameter(
                    name="test_param",
                    type=ParameterType.STRING,
                    required=True
                )
            ]
        )
    
    def test_initialization(self, config):
        """Test WorkflowValidator initialization."""
        validator = WorkflowValidator(config)
        
        assert validator.config == config
        assert isinstance(validator.parameter_validator, ParameterValidator)
        assert isinstance(validator.template_validator, TemplateValidator)
        assert isinstance(validator.execution_validator, ExecutionValidator)
    
    def test_validate_template_success(self, validator, valid_template):
        """Test successful template validation."""
        result = validator.validate_template(valid_template)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.template_id == "template_001"
    
    def test_validate_template_failure(self, validator, valid_template):
        """Test failed template validation."""
        # Make template invalid
        valid_template.template_data["nodes"] = []
        
        result = validator.validate_template(valid_template)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_parameters_success(self, validator, valid_template):
        """Test successful parameter validation."""
        parameters = {"test_param": "valid_value"}
        
        results = validator.validate_parameters(valid_template.parameters, parameters)
        
        assert len(results) == 1
        assert results[0].is_valid is True
    
    def test_validate_parameters_failure(self, validator, valid_template):
        """Test failed parameter validation."""
        parameters = {}  # Missing required parameter
        
        results = validator.validate_parameters(valid_template.parameters, parameters)
        
        assert len(results) == 1
        assert results[0].is_valid is False
    
    def test_validate_workflow_execution_success(self, validator):
        """Test successful workflow execution validation."""
        workflow = Workflow(
            id="workflow_001",
            name="Test Workflow",
            template_id="template_001",
            parameters={"test_param": "value"},
            created_at=datetime.now()
        )
        
        execution = WorkflowExecution(
            id="exec_001",
            workflow_id=workflow.id,
            status="running",
            started_at=datetime.now()
        )
        
        result = validator.validate_workflow_execution(workflow, execution)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_workflow_execution_failure(self, validator):
        """Test failed workflow execution validation."""
        workflow = Workflow(
            id="workflow_001",
            name="Test Workflow",
            template_id="template_001",
            parameters={},  # Missing required parameters
            created_at=datetime.now()
        )
        
        execution = WorkflowExecution(
            id="exec_001",
            workflow_id=workflow.id,
            status="invalid_status",  # Invalid status
            started_at=datetime.now()
        )
        
        result = validator.validate_workflow_execution(workflow, execution)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_comprehensive(self, validator, valid_template):
        """Test comprehensive validation of template and parameters."""
        parameters = {"test_param": "valid_value"}
        
        template_result, param_results = validator.validate_comprehensive(
            valid_template,
            parameters
        )
        
        assert template_result.is_valid is True
        assert len(param_results) == 1
        assert param_results[0].is_valid is True
    
    def test_validate_comprehensive_with_errors(self, validator, valid_template):
        """Test comprehensive validation with errors."""
        # Make template invalid
        valid_template.template_data["nodes"] = []
        
        # Make parameters invalid
        parameters = {}  # Missing required parameter
        
        template_result, param_results = validator.validate_comprehensive(
            valid_template,
            parameters
        )
        
        assert template_result.is_valid is False
        assert len(param_results) == 1
        assert param_results[0].is_valid is False
    
    def test_custom_validator_registration(self, validator):
        """Test registering custom validators."""
        def custom_template_validator(template):
            if "custom" not in template.name.lower():
                return ValidationResult(
                    is_valid=False,
                    errors=["Template name must contain 'custom'"],
                    template_id=template.id
                )
            return ValidationResult(
                is_valid=True,
                errors=[],
                template_id=template.id
            )
        
        validator.register_custom_validator("template", custom_template_validator)
        
        # Test with template that doesn't meet custom requirement
        template = WorkflowTemplate(
            id="test_001",
            name="Regular Template",
            description="Test",
            template_data={"nodes": [], "connections": {}},
            parameters=[]
        )
        
        result = validator.validate_template(template)
        
        assert result.is_valid is False
        assert any("custom" in error.lower() for error in result.errors)
    
    def test_validation_with_disabled_checks(self, validator, valid_template):
        """Test validation with some checks disabled."""
        # Disable node connection validation
        validator.config.validate_node_connections = False
        
        # Add invalid connection that should be ignored
        valid_template.template_data["connections"] = {
            "NonExistent": {"main": [[{"node": "AlsoNonExistent"}]]}
        }
        
        result = validator.validate_template(valid_template)
        
        # Should pass because connection validation is disabled
        assert result.is_valid is True


@pytest.mark.integration
class TestValidatorIntegration:
    """Integration tests for the complete validation system."""
    
    def test_end_to_end_validation_workflow(self):
        """Test complete end-to-end validation workflow."""
        # Create comprehensive test scenario
        config = ValidatorConfig(
            strict_validation=True,
            validate_node_connections=True,
            validate_parameter_types=True,
            max_node_count=10,
            max_parameter_count=20
        )
        
        validator = WorkflowValidator(config)
        
        # Create complex template
        template = WorkflowTemplate(
            id="complex_template",
            name="Complex Workflow Template",
            description="A complex template for testing",
            version="2.0.0",
            category="integration",
            tags=["test", "complex", "integration"],
            template_data={
                "nodes": [
                    {
                        "id": "start",
                        "name": "Start",
                        "type": "n8n-nodes-base.start",
                        "position": [100, 100],
                        "parameters": {}
                    },
                    {
                        "id": "http1",
                        "name": "HTTP Request 1",
                        "type": "n8n-nodes-base.httpRequest",
                        "position": [300, 100],
                        "parameters": {
                            "url": "{{$parameter.api_url}}",
                            "method": "GET",
                            "headers": {
                                "Authorization": "Bearer {{$parameter.api_token}}"
                            }
                        }
                    },
                    {
                        "id": "transform",
                        "name": "Transform Data",
                        "type": "n8n-nodes-base.function",
                        "position": [500, 100],
                        "parameters": {
                            "functionCode": "return items.map(item => ({ ...item.json, processed: true }));"
                        }
                    },
                    {
                        "id": "condition",
                        "name": "Condition",
                        "type": "n8n-nodes-base.if",
                        "position": [700, 100],
                        "parameters": {
                            "conditions": {
                                "boolean": [
                                    {
                                        "value1": "={{$parameter.enable_processing}}",
                                        "value2": true
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "id": "webhook",
                        "name": "Webhook",
                        "type": "n8n-nodes-base.webhook",
                        "position": [900, 100],
                        "parameters": {
                            "path": "{{$parameter.webhook_path}}",
                            "httpMethod": "POST"
                        }
                    }
                ],
                "connections": {
                    "Start": {
                        "main": [
                            [
                                {
                                    "node": "HTTP Request 1",
                                    "type": "main",
                                    "index": 0
                                }
                            ]
                        ]
                    },
                    "HTTP Request 1": {
                        "main": [
                            [
                                {
                                    "node": "Transform Data",
                                    "type": "main",
                                    "index": 0
                                }
                            ]
                        ]
                    },
                    "Transform Data": {
                        "main": [
                            [
                                {
                                    "node": "Condition",
                                    "type": "main",
                                    "index": 0
                                }
                            ]
                        ]
                    },
                    "Condition": {
                        "main": [
                            [
                                {
                                    "node": "Webhook",
                                    "type": "main",
                                    "index": 0
                                }
                            ],
                            []
                        ]
                    }
                }
            },
            parameters=[
                WorkflowParameter(
                    name="api_url",
                    type=ParameterType.STRING,
                    required=True,
                    description="API URL to call",
                    validation=ValidationRule(
                        pattern=r"^https?://.*",
                        min_length=10,
                        max_length=200
                    )
                ),
                WorkflowParameter(
                    name="api_token",
                    type=ParameterType.STRING,
                    required=True,
                    description="API authentication token",
                    validation=ValidationRule(
                        min_length=20,
                        max_length=100
                    )
                ),
                WorkflowParameter(
                    name="enable_processing",
                    type=ParameterType.BOOLEAN,
                    required=False,
                    default_value=True,
                    description="Enable data processing"
                ),
                WorkflowParameter(
                    name="webhook_path",
                    type=ParameterType.STRING,
                    required=True,
                    description="Webhook endpoint path",
                    validation=ValidationRule(
                        pattern=r"^/[a-zA-Z0-9/_-]+$",
                        min_length=2,
                        max_length=50
                    )
                )
            ]
        )
        
        # Test parameters
        parameters = {
            "api_url": "https://api.example.com/data",
            "api_token": "abcdef123456789012345678901234567890",
            "enable_processing": True,
            "webhook_path": "/webhook/callback"
        }
        
        # Perform comprehensive validation
        template_result, param_results = validator.validate_comprehensive(template, parameters)
        
        # Verify all validations pass
        assert template_result.is_valid is True
        assert len(template_result.errors) == 0
        
        assert len(param_results) == 4
        assert all(result.is_valid for result in param_results)
        
        # Create and validate workflow execution
        workflow = Workflow(
            id="workflow_complex",
            name="Complex Workflow Instance",
            template_id=template.id,
            parameters=parameters,
            created_at=datetime.now()
        )
        
        execution = WorkflowExecution(
            id="exec_complex",
            workflow_id=workflow.id,
            status="running",
            started_at=datetime.now()
        )
        
        execution_result = validator.validate_workflow_execution(workflow, execution)
        
        assert execution_result.is_valid is True
        assert len(execution_result.errors) == 0
    
    def test_validation_performance_with_large_template(self):
        """Test validation performance with large templates."""
        import time
        
        config = ValidatorConfig()
        validator = WorkflowValidator(config)
        
        # Create large template with many nodes
        nodes = []
        connections = {}
        
        for i in range(50):  # Create 50 nodes
            node_id = f"node_{i}"
            nodes.append({
                "id": node_id,
                "name": f"Node {i}",
                "type": "n8n-nodes-base.function",
                "position": [100 + (i % 10) * 200, 100 + (i // 10) * 150],
                "parameters": {
                    "functionCode": f"return [{{id: {i}, data: 'node_{i}'}}];"
                }
            })
            
            # Connect to next node (linear chain)
            if i < 49:
                connections[f"Node {i}"] = {
                    "main": [
                        [
                            {
                                "node": f"Node {i + 1}",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
        
        large_template = WorkflowTemplate(
            id="large_template",
            name="Large Template",
            description="Template with many nodes",
            template_data={
                "nodes": nodes,
                "connections": connections
            },
            parameters=[]
        )
        
        # Measure validation time
        start_time = time.time()
        result = validator.validate_template(large_template)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Validation should complete within reasonable time (< 5 seconds)
        assert validation_time < 5.0
        assert result.is_valid is True