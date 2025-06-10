#!/usr/bin/env python3
"""
Template Engine for Workflow Automation Module

Handles loading, processing, and generation of workflow templates.
Supports Jinja2 templating with custom filters and functions.

Author: UnityAI Team
Version: 1.0.0
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog
import yaml
from jinja2 import Environment, FileSystemLoader, Template, TemplateError
from pydantic import BaseModel, Field

from .models import WorkflowTemplate, WorkflowParameter, ParameterType, ValidationRule

# Setup structured logging
logger = structlog.get_logger(__name__)


class TemplateEngineConfig(BaseModel):
    """Configuration for template engine."""
    
    template_path: Path = Field(default=Path("templates"))
    cache_templates: bool = Field(default=True)
    auto_reload: bool = Field(default=True)
    strict_undefined: bool = Field(default=True)
    custom_filters: Dict[str, str] = Field(default_factory=dict)
    

class TemplateEngine:
    """Template engine for workflow generation."""
    
    def __init__(self, config: Optional[TemplateEngineConfig] = None):
        self.config = config or TemplateEngineConfig()
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.config.template_path)),
            auto_reload=self.config.auto_reload,
            undefined='StrictUndefined' if self.config.strict_undefined else 'Undefined'
        )
        
        # Add custom filters
        self._setup_custom_filters()
        
        # Template cache
        self._template_cache: Dict[str, WorkflowTemplate] = {}
        self._jinja_cache: Dict[str, Template] = {}
        
        logger.info(
            "Template engine initialized",
            template_path=str(self.config.template_path),
            cache_enabled=self.config.cache_templates
        )
    
    def _setup_custom_filters(self):
        """Setup custom Jinja2 filters."""
        
        # Date/time filters
        self.env.filters['datetime_format'] = self._filter_datetime_format
        self.env.filters['timestamp'] = self._filter_timestamp
        
        # String filters
        self.env.filters['slugify'] = self._filter_slugify
        self.env.filters['camel_case'] = self._filter_camel_case
        self.env.filters['snake_case'] = self._filter_snake_case
        
        # Data filters
        self.env.filters['json_encode'] = self._filter_json_encode
        self.env.filters['yaml_encode'] = self._filter_yaml_encode
        self.env.filters['base64_encode'] = self._filter_base64_encode
        
        # Validation filters
        self.env.filters['validate_email'] = self._filter_validate_email
        self.env.filters['validate_url'] = self._filter_validate_url
        
        # n8n specific filters
        self.env.filters['n8n_expression'] = self._filter_n8n_expression
        self.env.filters['n8n_webhook_url'] = self._filter_n8n_webhook_url
        
        # Global functions
        self.env.globals['uuid4'] = self._global_uuid4
        self.env.globals['now'] = self._global_now
        self.env.globals['env'] = self._global_env
    
    async def load_template(self, template_name: str) -> Optional[WorkflowTemplate]:
        """Load workflow template by name."""
        
        try:
            # Check cache first
            if self.config.cache_templates and template_name in self._template_cache:
                return self._template_cache[template_name]
            
            # Find template file
            template_file = self._find_template_file(template_name)
            if not template_file:
                logger.warning("Template not found", template_name=template_name)
                return None
            
            # Load template data
            template_data = self._load_template_file(template_file)
            if not template_data:
                return None
            
            # Create template object
            template = self._create_template_object(template_name, template_data)
            
            # Cache template
            if self.config.cache_templates:
                self._template_cache[template_name] = template
            
            logger.info(
                "Template loaded",
                template_name=template_name,
                version=template.version
            )
            
            return template
        
        except Exception as e:
            logger.error(
                "Failed to load template",
                template_name=template_name,
                error=str(e)
            )
            return None
    
    async def list_templates(self) -> List[str]:
        """List available template names."""
        
        templates = []
        
        if not self.config.template_path.exists():
            return templates
        
        # Scan for template files
        for file_path in self.config.template_path.rglob("*.yaml"):
            if file_path.name.startswith("."):
                continue
            
            # Get relative path as template name
            relative_path = file_path.relative_to(self.config.template_path)
            template_name = str(relative_path.with_suffix("")).replace("\\", "/")
            templates.append(template_name)
        
        return sorted(templates)
    
    async def generate_workflow(
        self,
        template: WorkflowTemplate,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate workflow from template with parameters."""
        
        try:
            # Prepare template context
            context = {
                'parameters': parameters,
                'template': {
                    'name': template.name,
                    'version': template.version,
                    'category': template.category
                },
                'metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'generator': 'UnityAI Template Engine'
                }
            }
            
            # Render template
            workflow_data = self._render_template_data(template.template_data, context)
            
            logger.info(
                "Workflow generated",
                template_name=template.name,
                parameters_count=len(parameters)
            )
            
            return workflow_data
        
        except Exception as e:
            logger.error(
                "Failed to generate workflow",
                template_name=template.name,
                error=str(e)
            )
            raise
    
    async def validate_template(self, template_name: str) -> Dict[str, Any]:
        """Validate template structure and syntax."""
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Load template
            template = await self.load_template(template_name)
            if not template:
                result['valid'] = False
                result['errors'].append(f"Template not found: {template_name}")
                return result
            
            # Validate template structure
            self._validate_template_structure(template, result)
            
            # Validate Jinja2 syntax
            self._validate_jinja_syntax(template, result)
            
            # Validate n8n workflow structure
            self._validate_n8n_structure(template, result)
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Validation error: {str(e)}")
        
        return result
    
    async def create_template(
        self,
        template_name: str,
        template_data: Dict[str, Any],
        parameters: Optional[List[WorkflowParameter]] = None
    ) -> WorkflowTemplate:
        """Create new template."""
        
        try:
            # Create template object
            template = WorkflowTemplate(
                name=template_name,
                template_data=template_data,
                parameters=parameters or []
            )
            
            # Save template file
            template_file = self.config.template_path / f"{template_name}.yaml"
            template_file.parent.mkdir(parents=True, exist_ok=True)
            
            template_content = {
                'name': template.name,
                'description': template.description,
                'version': template.version,
                'category': template.category,
                'tags': template.tags,
                'author': template.author,
                'parameters': [param.dict() for param in template.parameters],
                'template': template.template_data
            }
            
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_content, f, default_flow_style=False, indent=2)
            
            # Cache template
            if self.config.cache_templates:
                self._template_cache[template_name] = template
            
            logger.info(
                "Template created",
                template_name=template_name,
                file_path=str(template_file)
            )
            
            return template
        
        except Exception as e:
            logger.error(
                "Failed to create template",
                template_name=template_name,
                error=str(e)
            )
            raise
    
    def clear_cache(self):
        """Clear template cache."""
        
        self._template_cache.clear()
        self._jinja_cache.clear()
        
        logger.info("Template cache cleared")
    
    # Private methods
    def _find_template_file(self, template_name: str) -> Optional[Path]:
        """Find template file by name."""
        
        # Try different extensions
        extensions = ['.yaml', '.yml', '.json']
        
        for ext in extensions:
            template_file = self.config.template_path / f"{template_name}{ext}"
            if template_file.exists():
                return template_file
        
        return None
    
    def _load_template_file(self, template_file: Path) -> Optional[Dict[str, Any]]:
        """Load template data from file."""
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                if template_file.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
        
        except Exception as e:
            logger.error(
                "Failed to load template file",
                file_path=str(template_file),
                error=str(e)
            )
            return None
    
    def _create_template_object(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> WorkflowTemplate:
        """Create template object from data."""
        
        # Parse parameters
        parameters = []
        for param_data in template_data.get('parameters', []):
            if isinstance(param_data, dict):
                # Create validation rule if present
                validation = None
                if 'validation' in param_data:
                    validation = ValidationRule(**param_data['validation'])
                
                parameter = WorkflowParameter(
                    **{k: v for k, v in param_data.items() if k != 'validation'},
                    validation=validation
                )
                parameters.append(parameter)
        
        # Create template
        template = WorkflowTemplate(
            name=template_data.get('name', template_name),
            description=template_data.get('description'),
            version=template_data.get('version', '1.0.0'),
            category=template_data.get('category', 'general'),
            tags=template_data.get('tags', []),
            author=template_data.get('author'),
            template_data=template_data.get('template', {}),
            parameters=parameters
        )
        
        return template
    
    def _render_template_data(
        self,
        template_data: Any,
        context: Dict[str, Any]
    ) -> Any:
        """Recursively render template data."""
        
        if isinstance(template_data, dict):
            return {
                key: self._render_template_data(value, context)
                for key, value in template_data.items()
            }
        
        elif isinstance(template_data, list):
            return [
                self._render_template_data(item, context)
                for item in template_data
            ]
        
        elif isinstance(template_data, str):
            # Check if string contains Jinja2 template syntax
            if '{{' in template_data or '{%' in template_data:
                try:
                    template = self.env.from_string(template_data)
                    return template.render(context)
                except TemplateError as e:
                    logger.warning(
                        "Template rendering error",
                        template_string=template_data,
                        error=str(e)
                    )
                    return template_data
            else:
                return template_data
        
        else:
            return template_data
    
    def _validate_template_structure(self, template: WorkflowTemplate, result: Dict[str, Any]):
        """Validate template structure."""
        
        # Check required fields
        if not template.name:
            result['errors'].append("Template name is required")
        
        if not template.template_data:
            result['errors'].append("Template data is required")
        
        # Validate parameters
        for param in template.parameters:
            if not param.name:
                result['errors'].append("Parameter name is required")
            
            if param.type not in ParameterType:
                result['errors'].append(f"Invalid parameter type: {param.type}")
    
    def _validate_jinja_syntax(self, template: WorkflowTemplate, result: Dict[str, Any]):
        """Validate Jinja2 syntax in template."""
        
        def check_template_syntax(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    check_template_syntax(value, f"{path}.{key}")
            
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    check_template_syntax(item, f"{path}[{i}]")
            
            elif isinstance(data, str) and ('{{' in data or '{%' in data):
                try:
                    self.env.from_string(data)
                except TemplateError as e:
                    result['errors'].append(f"Jinja2 syntax error at {path}: {str(e)}")
        
        check_template_syntax(template.template_data)
    
    def _validate_n8n_structure(self, template: WorkflowTemplate, result: Dict[str, Any]):
        """Validate n8n workflow structure."""
        
        template_data = template.template_data
        
        # Check for required n8n fields
        if 'nodes' not in template_data:
            result['errors'].append("n8n workflow must have 'nodes' field")
        
        if 'connections' not in template_data:
            result['warnings'].append("n8n workflow should have 'connections' field")
        
        # Validate nodes
        nodes = template_data.get('nodes', [])
        if not isinstance(nodes, list):
            result['errors'].append("'nodes' must be a list")
        else:
            for i, node in enumerate(nodes):
                if not isinstance(node, dict):
                    result['errors'].append(f"Node {i} must be an object")
                    continue
                
                if 'type' not in node:
                    result['errors'].append(f"Node {i} must have 'type' field")
                
                if 'name' not in node:
                    result['warnings'].append(f"Node {i} should have 'name' field")
    
    # Custom filters
    def _filter_datetime_format(self, value, format_string='%Y-%m-%d %H:%M:%S'):
        """Format datetime value."""
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value.strftime(format_string)
    
    def _filter_timestamp(self, value):
        """Convert datetime to timestamp."""
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return int(value.timestamp())
    
    def _filter_slugify(self, value):
        """Convert string to slug."""
        value = str(value).lower()
        value = re.sub(r'[^a-z0-9]+', '-', value)
        return value.strip('-')
    
    def _filter_camel_case(self, value):
        """Convert string to camelCase."""
        components = str(value).split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])
    
    def _filter_snake_case(self, value):
        """Convert string to snake_case."""
        value = re.sub(r'([A-Z])', r'_\1', str(value))
        return value.lower().strip('_')
    
    def _filter_json_encode(self, value):
        """Encode value as JSON."""
        return json.dumps(value)
    
    def _filter_yaml_encode(self, value):
        """Encode value as YAML."""
        return yaml.dump(value, default_flow_style=False)
    
    def _filter_base64_encode(self, value):
        """Encode string as base64."""
        import base64
        return base64.b64encode(str(value).encode()).decode()
    
    def _filter_validate_email(self, value):
        """Validate email address."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(value)))
    
    def _filter_validate_url(self, value):
        """Validate URL."""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, str(value)))
    
    def _filter_n8n_expression(self, value):
        """Wrap value in n8n expression syntax."""
        return f"={{{{ {value} }}}}"
    
    def _filter_n8n_webhook_url(self, webhook_id):
        """Generate n8n webhook URL."""
        from core import get_config
        config = get_config()
        base_url = config.n8n.base_url.rstrip('/')
        return f"{base_url}/webhook/{webhook_id}"
    
    # Global functions
    def _global_uuid4(self):
        """Generate UUID4."""
        from uuid import uuid4
        return str(uuid4())
    
    def _global_now(self, format_string=None):
        """Get current datetime."""
        now = datetime.utcnow()
        if format_string:
            return now.strftime(format_string)
        return now.isoformat()
    
    def _global_env(self, key, default=None):
        """Get environment variable."""
        import os
        return os.getenv(key, default)