#!/usr/bin/env python3
"""
Validators for Workflow Automation Module

Provides validation functionality for workflows, parameters, templates,
and n8n-specific structures.

Author: UnityAI Team
Version: 1.0.0
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import structlog
from pydantic import BaseModel, Field, validator

from .models import (
    WorkflowParameter,
    ParameterType,
    ValidationRule,
    ValidationResult,
    WorkflowTemplate,
    Workflow
)

# Setup structured logging
logger = structlog.get_logger(__name__)


class ValidatorConfig(BaseModel):
    """Configuration for validators."""
    
    strict_validation: bool = Field(default=True)
    allow_unknown_parameters: bool = Field(default=False)
    max_string_length: int = Field(default=10000)
    max_array_length: int = Field(default=1000)
    max_object_depth: int = Field(default=10)
    

class WorkflowValidator:
    """Main validator class for workflows and parameters."""
    
    def __init__(self, config: Optional[ValidatorConfig] = None):
        self.config = config or ValidatorConfig()
        
        # Validation patterns
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'url': re.compile(r'^https?://[^\s/$.?#].[^\s]*$'),
            'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
            'slug': re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$'),
            'version': re.compile(r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$')
        }
        
        logger.info(
            "Workflow validator initialized",
            strict_validation=self.config.strict_validation
        )
    
    async def validate_parameters(
        self,
        parameters: Dict[str, Any],
        parameter_definitions: List[WorkflowParameter]
    ) -> ValidationResult:
        """Validate parameters against definitions."""
        
        result = ValidationResult(valid=True)
        
        try:
            # Create parameter lookup
            param_defs = {param.name: param for param in parameter_definitions}
            
            # Check required parameters
            for param_def in parameter_definitions:
                if param_def.required and param_def.name not in parameters:
                    result.errors.append(f"Required parameter missing: {param_def.name}")
                    result.valid = False
            
            # Validate provided parameters
            for param_name, param_value in parameters.items():
                param_def = param_defs.get(param_name)
                
                if not param_def:
                    if not self.config.allow_unknown_parameters:
                        result.errors.append(f"Unknown parameter: {param_name}")
                        if self.config.strict_validation:
                            result.valid = False
                        else:
                            result.warnings.append(f"Unknown parameter will be ignored: {param_name}")
                    continue
                
                # Validate parameter value
                param_result = await self._validate_parameter_value(
                    param_name,
                    param_value,
                    param_def
                )
                
                if not param_result.valid:
                    result.errors.extend(param_result.errors)
                    result.valid = False
                
                result.warnings.extend(param_result.warnings)
            
            logger.debug(
                "Parameter validation completed",
                valid=result.valid,
                errors_count=len(result.errors),
                warnings_count=len(result.warnings)
            )
        
        except Exception as e:
            result.valid = False
            result.errors.append(f"Parameter validation error: {str(e)}")
            logger.error("Parameter validation failed", error=str(e))
        
        return result
    
    async def validate_workflow_template(self, template: WorkflowTemplate) -> ValidationResult:
        """Validate workflow template structure and content."""
        
        result = ValidationResult(valid=True)
        
        try:
            # Validate basic template structure
            await self._validate_template_metadata(template, result)
            
            # Validate parameters
            await self._validate_template_parameters(template, result)
            
            # Validate template data
            await self._validate_template_data(template, result)
            
            # Validate n8n specific structure
            await self._validate_n8n_workflow(template.template_data, result)
            
            logger.debug(
                "Template validation completed",
                template_name=template.name,
                valid=result.valid,
                errors_count=len(result.errors)
            )
        
        except Exception as e:
            result.valid = False
            result.errors.append(f"Template validation error: {str(e)}")
            logger.error(
                "Template validation failed",
                template_name=template.name,
                error=str(e)
            )
        
        return result
    
    async def validate_workflow(self, workflow: Workflow) -> ValidationResult:
        """Validate workflow instance."""
        
        result = ValidationResult(valid=True)
        
        try:
            # Validate basic workflow structure
            if not workflow.name:
                result.errors.append("Workflow name is required")
                result.valid = False
            
            if not workflow.template_name:
                result.errors.append("Template name is required")
                result.valid = False
            
            # Validate workflow data
            if not workflow.workflow_data:
                result.errors.append("Workflow data is required")
                result.valid = False
            else:
                await self._validate_n8n_workflow(workflow.workflow_data, result)
            
            # Validate parameters if template is available
            # This would require loading the template, which we skip for now
            
            logger.debug(
                "Workflow validation completed",
                workflow_id=workflow.id,
                valid=result.valid
            )
        
        except Exception as e:
            result.valid = False
            result.errors.append(f"Workflow validation error: {str(e)}")
            logger.error(
                "Workflow validation failed",
                workflow_id=workflow.id,
                error=str(e)
            )
        
        return result
    
    async def validate_n8n_workflow_data(self, workflow_data: Dict[str, Any]) -> ValidationResult:
        """Validate n8n workflow data structure."""
        
        result = ValidationResult(valid=True)
        
        try:
            await self._validate_n8n_workflow(workflow_data, result)
        
        except Exception as e:
            result.valid = False
            result.errors.append(f"n8n workflow validation error: {str(e)}")
        
        return result
    
    # Private validation methods
    async def _validate_parameter_value(
        self,
        param_name: str,
        param_value: Any,
        param_def: WorkflowParameter
    ) -> ValidationResult:
        """Validate individual parameter value."""
        
        result = ValidationResult(valid=True)
        
        # Handle None values
        if param_value is None:
            if param_def.required:
                result.errors.append(f"Parameter {param_name} cannot be None")
                result.valid = False
            return result
        
        # Type validation
        type_result = await self._validate_parameter_type(param_name, param_value, param_def.type)
        if not type_result.valid:
            result.errors.extend(type_result.errors)
            result.valid = False
            return result  # Skip further validation if type is wrong
        
        # Custom validation rules
        if param_def.validation:
            validation_result = await self._validate_with_rules(
                param_name,
                param_value,
                param_def.validation
            )
            if not validation_result.valid:
                result.errors.extend(validation_result.errors)
                result.valid = False
            result.warnings.extend(validation_result.warnings)
        
        return result
    
    async def _validate_parameter_type(
        self,
        param_name: str,
        param_value: Any,
        param_type: ParameterType
    ) -> ValidationResult:
        """Validate parameter type."""
        
        result = ValidationResult(valid=True)
        
        if param_type == ParameterType.STRING:
            if not isinstance(param_value, str):
                result.errors.append(f"Parameter {param_name} must be a string")
                result.valid = False
            elif len(param_value) > self.config.max_string_length:
                result.errors.append(
                    f"Parameter {param_name} exceeds maximum length of {self.config.max_string_length}"
                )
                result.valid = False
        
        elif param_type == ParameterType.INTEGER:
            if not isinstance(param_value, int) or isinstance(param_value, bool):
                result.errors.append(f"Parameter {param_name} must be an integer")
                result.valid = False
        
        elif param_type == ParameterType.FLOAT:
            if not isinstance(param_value, (int, float)) or isinstance(param_value, bool):
                result.errors.append(f"Parameter {param_name} must be a number")
                result.valid = False
        
        elif param_type == ParameterType.BOOLEAN:
            if not isinstance(param_value, bool):
                result.errors.append(f"Parameter {param_name} must be a boolean")
                result.valid = False
        
        elif param_type == ParameterType.ARRAY:
            if not isinstance(param_value, list):
                result.errors.append(f"Parameter {param_name} must be an array")
                result.valid = False
            elif len(param_value) > self.config.max_array_length:
                result.errors.append(
                    f"Parameter {param_name} exceeds maximum array length of {self.config.max_array_length}"
                )
                result.valid = False
        
        elif param_type == ParameterType.OBJECT:
            if not isinstance(param_value, dict):
                result.errors.append(f"Parameter {param_name} must be an object")
                result.valid = False
            else:
                depth = self._get_object_depth(param_value)
                if depth > self.config.max_object_depth:
                    result.errors.append(
                        f"Parameter {param_name} exceeds maximum object depth of {self.config.max_object_depth}"
                    )
                    result.valid = False
        
        elif param_type == ParameterType.EMAIL:
            if not isinstance(param_value, str):
                result.errors.append(f"Parameter {param_name} must be a string")
                result.valid = False
            elif not self.patterns['email'].match(param_value):
                result.errors.append(f"Parameter {param_name} must be a valid email address")
                result.valid = False
        
        elif param_type == ParameterType.URL:
            if not isinstance(param_value, str):
                result.errors.append(f"Parameter {param_name} must be a string")
                result.valid = False
            elif not self.patterns['url'].match(param_value):
                result.errors.append(f"Parameter {param_name} must be a valid URL")
                result.valid = False
        
        elif param_type == ParameterType.DATE:
            if isinstance(param_value, str):
                try:
                    datetime.strptime(param_value, '%Y-%m-%d')
                except ValueError:
                    result.errors.append(f"Parameter {param_name} must be a valid date (YYYY-MM-DD)")
                    result.valid = False
            else:
                result.errors.append(f"Parameter {param_name} must be a date string")
                result.valid = False
        
        elif param_type == ParameterType.DATETIME:
            if isinstance(param_value, str):
                try:
                    datetime.fromisoformat(param_value.replace('Z', '+00:00'))
                except ValueError:
                    result.errors.append(f"Parameter {param_name} must be a valid ISO datetime")
                    result.valid = False
            else:
                result.errors.append(f"Parameter {param_name} must be a datetime string")
                result.valid = False
        
        return result
    
    async def _validate_with_rules(
        self,
        param_name: str,
        param_value: Any,
        validation_rule: ValidationRule
    ) -> ValidationResult:
        """Validate parameter with custom rules."""
        
        result = ValidationResult(valid=True)
        
        # Min/max value validation
        if validation_rule.min_value is not None:
            if isinstance(param_value, (int, float)) and param_value < validation_rule.min_value:
                result.errors.append(
                    f"Parameter {param_name} must be >= {validation_rule.min_value}"
                )
                result.valid = False
        
        if validation_rule.max_value is not None:
            if isinstance(param_value, (int, float)) and param_value > validation_rule.max_value:
                result.errors.append(
                    f"Parameter {param_name} must be <= {validation_rule.max_value}"
                )
                result.valid = False
        
        # Min/max length validation
        if validation_rule.min_length is not None:
            if hasattr(param_value, '__len__') and len(param_value) < validation_rule.min_length:
                result.errors.append(
                    f"Parameter {param_name} must have at least {validation_rule.min_length} characters/items"
                )
                result.valid = False
        
        if validation_rule.max_length is not None:
            if hasattr(param_value, '__len__') and len(param_value) > validation_rule.max_length:
                result.errors.append(
                    f"Parameter {param_name} must have at most {validation_rule.max_length} characters/items"
                )
                result.valid = False
        
        # Pattern validation
        if validation_rule.pattern and isinstance(param_value, str):
            try:
                pattern = re.compile(validation_rule.pattern)
                if not pattern.match(param_value):
                    result.errors.append(
                        f"Parameter {param_name} does not match required pattern"
                    )
                    result.valid = False
            except re.error:
                result.warnings.append(
                    f"Invalid regex pattern for parameter {param_name}"
                )
        
        # Allowed values validation
        if validation_rule.allowed_values:
            if param_value not in validation_rule.allowed_values:
                result.errors.append(
                    f"Parameter {param_name} must be one of: {validation_rule.allowed_values}"
                )
                result.valid = False
        
        return result
    
    async def _validate_template_metadata(self, template: WorkflowTemplate, result: ValidationResult):
        """Validate template metadata."""
        
        if not template.name:
            result.errors.append("Template name is required")
            result.valid = False
        
        if template.version and not self.patterns['version'].match(template.version):
            result.warnings.append("Template version should follow semantic versioning (x.y.z)")
        
        if not template.template_data:
            result.errors.append("Template data is required")
            result.valid = False
    
    async def _validate_template_parameters(self, template: WorkflowTemplate, result: ValidationResult):
        """Validate template parameters."""
        
        param_names = set()
        
        for param in template.parameters:
            # Check for duplicate names
            if param.name in param_names:
                result.errors.append(f"Duplicate parameter name: {param.name}")
                result.valid = False
            param_names.add(param.name)
            
            # Validate parameter definition
            if not param.name:
                result.errors.append("Parameter name is required")
                result.valid = False
            
            if param.type not in ParameterType:
                result.errors.append(f"Invalid parameter type: {param.type}")
                result.valid = False
            
            # Validate default value type
            if param.default is not None:
                default_result = await self._validate_parameter_type(
                    param.name,
                    param.default,
                    param.type
                )
                if not default_result.valid:
                    result.errors.append(f"Invalid default value for parameter {param.name}")
                    result.valid = False
    
    async def _validate_template_data(self, template: WorkflowTemplate, result: ValidationResult):
        """Validate template data structure."""
        
        template_data = template.template_data
        
        if not isinstance(template_data, dict):
            result.errors.append("Template data must be an object")
            result.valid = False
            return
        
        # Check for template syntax issues
        self._check_template_syntax(template_data, result)
    
    async def _validate_n8n_workflow(self, workflow_data: Dict[str, Any], result: ValidationResult):
        """Validate n8n workflow structure."""
        
        # Check required fields
        if 'nodes' not in workflow_data:
            result.errors.append("n8n workflow must have 'nodes' field")
            result.valid = False
            return
        
        nodes = workflow_data['nodes']
        if not isinstance(nodes, list):
            result.errors.append("'nodes' must be an array")
            result.valid = False
            return
        
        if len(nodes) == 0:
            result.warnings.append("Workflow has no nodes")
        
        # Validate nodes
        node_names = set()
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                result.errors.append(f"Node {i} must be an object")
                result.valid = False
                continue
            
            # Check required node fields
            if 'type' not in node:
                result.errors.append(f"Node {i} must have 'type' field")
                result.valid = False
            
            if 'name' not in node:
                result.warnings.append(f"Node {i} should have 'name' field")
            else:
                node_name = node['name']
                if node_name in node_names:
                    result.errors.append(f"Duplicate node name: {node_name}")
                    result.valid = False
                node_names.add(node_name)
            
            # Validate node position
            if 'position' in node:
                position = node['position']
                if not isinstance(position, list) or len(position) != 2:
                    result.warnings.append(f"Node {i} position should be [x, y] array")
        
        # Validate connections
        if 'connections' in workflow_data:
            connections = workflow_data['connections']
            if not isinstance(connections, dict):
                result.warnings.append("'connections' should be an object")
            else:
                self._validate_n8n_connections(connections, node_names, result)
    
    def _validate_n8n_connections(
        self,
        connections: Dict[str, Any],
        node_names: set,
        result: ValidationResult
    ):
        """Validate n8n workflow connections."""
        
        for source_node, outputs in connections.items():
            if source_node not in node_names:
                result.warnings.append(f"Connection references unknown source node: {source_node}")
            
            if not isinstance(outputs, dict):
                result.warnings.append(f"Connections for {source_node} should be an object")
                continue
            
            for output_index, connections_list in outputs.items():
                if not isinstance(connections_list, list):
                    result.warnings.append(
                        f"Connections for {source_node}[{output_index}] should be an array"
                    )
                    continue
                
                for connection in connections_list:
                    if not isinstance(connection, dict):
                        result.warnings.append("Connection should be an object")
                        continue
                    
                    if 'node' not in connection:
                        result.warnings.append("Connection must have 'node' field")
                        continue
                    
                    target_node = connection['node']
                    if target_node not in node_names:
                        result.warnings.append(
                            f"Connection references unknown target node: {target_node}"
                        )
    
    def _check_template_syntax(self, data: Any, result: ValidationResult, path: str = ""):
        """Check for template syntax issues."""
        
        if isinstance(data, dict):
            for key, value in data.items():
                self._check_template_syntax(value, result, f"{path}.{key}")
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_template_syntax(item, result, f"{path}[{i}]")
        
        elif isinstance(data, str):
            # Check for unmatched template brackets
            open_count = data.count('{{')
            close_count = data.count('}}')
            if open_count != close_count:
                result.warnings.append(f"Unmatched template brackets at {path}")
            
            # Check for common template errors
            if '{{' in data and '}}' not in data:
                result.warnings.append(f"Unclosed template expression at {path}")
    
    def _get_object_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum depth of nested object."""
        
        if not isinstance(obj, dict):
            return current_depth
        
        if not obj:
            return current_depth
        
        max_depth = current_depth
        for value in obj.values():
            if isinstance(value, dict):
                depth = self._get_object_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth


class N8nWorkflowValidator:
    """Specialized validator for n8n workflows."""
    
    def __init__(self):
        # Known n8n node types (this could be loaded from n8n API)
        self.known_node_types = {
            'n8n-nodes-base.start',
            'n8n-nodes-base.httpRequest',
            'n8n-nodes-base.webhook',
            'n8n-nodes-base.function',
            'n8n-nodes-base.set',
            'n8n-nodes-base.if',
            'n8n-nodes-base.switch',
            'n8n-nodes-base.merge',
            'n8n-nodes-base.wait',
            'n8n-nodes-base.executeWorkflow',
            'n8n-nodes-base.stopAndError'
        }
    
    async def validate_workflow(self, workflow_data: Dict[str, Any]) -> ValidationResult:
        """Validate n8n workflow with detailed checks."""
        
        result = ValidationResult(valid=True)
        
        try:
            # Basic structure validation
            if not isinstance(workflow_data, dict):
                result.errors.append("Workflow data must be an object")
                result.valid = False
                return result
            
            # Validate nodes
            await self._validate_nodes(workflow_data.get('nodes', []), result)
            
            # Validate connections
            await self._validate_connections(
                workflow_data.get('connections', {}),
                workflow_data.get('nodes', []),
                result
            )
            
            # Validate settings
            await self._validate_settings(workflow_data.get('settings', {}), result)
            
        except Exception as e:
            result.valid = False
            result.errors.append(f"n8n workflow validation error: {str(e)}")
        
        return result
    
    async def _validate_nodes(self, nodes: List[Dict[str, Any]], result: ValidationResult):
        """Validate n8n nodes."""
        
        if not isinstance(nodes, list):
            result.errors.append("Nodes must be an array")
            result.valid = False
            return
        
        node_names = set()
        has_start_node = False
        
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                result.errors.append(f"Node {i} must be an object")
                result.valid = False
                continue
            
            # Check required fields
            node_type = node.get('type')
            if not node_type:
                result.errors.append(f"Node {i} must have 'type' field")
                result.valid = False
                continue
            
            # Check if it's a start node
            if node_type == 'n8n-nodes-base.start':
                has_start_node = True
            
            # Validate node type
            if node_type not in self.known_node_types:
                result.warnings.append(f"Unknown node type: {node_type}")
            
            # Check node name
            node_name = node.get('name')
            if not node_name:
                result.warnings.append(f"Node {i} should have a name")
            elif node_name in node_names:
                result.errors.append(f"Duplicate node name: {node_name}")
                result.valid = False
            else:
                node_names.add(node_name)
            
            # Validate node parameters
            await self._validate_node_parameters(node, result)
        
        # Check for start node
        if not has_start_node:
            result.warnings.append("Workflow should have a start node")
    
    async def _validate_node_parameters(self, node: Dict[str, Any], result: ValidationResult):
        """Validate node parameters."""
        
        node_type = node.get('type')
        parameters = node.get('parameters', {})
        
        if not isinstance(parameters, dict):
            result.warnings.append(f"Node {node.get('name', 'unknown')} parameters should be an object")
            return
        
        # Type-specific validation
        if node_type == 'n8n-nodes-base.httpRequest':
            await self._validate_http_request_node(parameters, result)
        elif node_type == 'n8n-nodes-base.webhook':
            await self._validate_webhook_node(parameters, result)
        elif node_type == 'n8n-nodes-base.function':
            await self._validate_function_node(parameters, result)
    
    async def _validate_http_request_node(self, parameters: Dict[str, Any], result: ValidationResult):
        """Validate HTTP Request node parameters."""
        
        url = parameters.get('url')
        if url and not isinstance(url, str):
            result.warnings.append("HTTP Request URL should be a string")
        
        method = parameters.get('requestMethod', 'GET')
        if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
            result.warnings.append(f"Invalid HTTP method: {method}")
    
    async def _validate_webhook_node(self, parameters: Dict[str, Any], result: ValidationResult):
        """Validate Webhook node parameters."""
        
        webhook_id = parameters.get('webhookId')
        if not webhook_id:
            result.warnings.append("Webhook node should have a webhook ID")
        
        http_method = parameters.get('httpMethod', 'GET')
        if http_method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']:
            result.warnings.append(f"Invalid webhook HTTP method: {http_method}")
    
    async def _validate_function_node(self, parameters: Dict[str, Any], result: ValidationResult):
        """Validate Function node parameters."""
        
        function_code = parameters.get('functionCode')
        if not function_code:
            result.warnings.append("Function node should have function code")
        elif not isinstance(function_code, str):
            result.warnings.append("Function code should be a string")
    
    async def _validate_connections(
        self,
        connections: Dict[str, Any],
        nodes: List[Dict[str, Any]],
        result: ValidationResult
    ):
        """Validate workflow connections."""
        
        if not isinstance(connections, dict):
            result.warnings.append("Connections should be an object")
            return
        
        node_names = {node.get('name') for node in nodes if node.get('name')}
        
        for source_node, outputs in connections.items():
            if source_node not in node_names:
                result.warnings.append(f"Connection references unknown source node: {source_node}")
    
    async def _validate_settings(self, settings: Dict[str, Any], result: ValidationResult):
        """Validate workflow settings."""
        
        if not isinstance(settings, dict):
            result.warnings.append("Settings should be an object")
            return
        
        # Validate timezone
        timezone = settings.get('timezone')
        if timezone and not isinstance(timezone, str):
            result.warnings.append("Timezone should be a string")
        
        # Validate save data on error
        save_data_error_execution = settings.get('saveDataErrorExecution')
        if save_data_error_execution is not None and not isinstance(save_data_error_execution, str):
            result.warnings.append("saveDataErrorExecution should be a string")