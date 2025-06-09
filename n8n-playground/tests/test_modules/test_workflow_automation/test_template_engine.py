#!/usr/bin/env python3
"""
Tests for Template Engine.

Comprehensive test suite for the template engine that handles
workflow template loading, processing, and generation.

Author: UnityAI Team
Version: 1.0.0
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock, patch

from modules.workflow_automation.template_engine import (
    TemplateEngine,
    TemplateEngineConfig
)
from modules.workflow_automation.models import (
    WorkflowTemplate,
    WorkflowParameter,
    ParameterType,
    ValidationRule
)


class TestTemplateEngineConfig:
    """Test TemplateEngineConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TemplateEngineConfig()
        
        assert config.template_path == Path("templates")
        assert config.cache_templates is True
        assert config.validate_templates is True
        assert config.template_extension == ".json"
        assert config.enable_jinja2 is True
        assert config.jinja2_extensions == []
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = TemplateEngineConfig(
            template_path=Path("/custom/templates"),
            cache_templates=False,
            validate_templates=False,
            template_extension=".yaml",
            enable_jinja2=False,
            jinja2_extensions=["jinja2.ext.do"]
        )
        
        assert config.template_path == Path("/custom/templates")
        assert config.cache_templates is False
        assert config.validate_templates is False
        assert config.template_extension == ".yaml"
        assert config.enable_jinja2 is False
        assert config.jinja2_extensions == ["jinja2.ext.do"]


class TestTemplateEngine:
    """Test TemplateEngine class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for templates."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config(self, temp_dir):
        """Test configuration."""
        return TemplateEngineConfig(
            template_path=temp_dir,
            cache_templates=True,
            validate_templates=True
        )
    
    @pytest.fixture
    def template_engine(self, config):
        """Create TemplateEngine instance."""
        return TemplateEngine(config)
    
    @pytest.fixture
    def sample_template_data(self):
        """Sample template data."""
        return {
            "name": "simple_webhook",
            "description": "Simple webhook workflow",
            "version": "1.0.0",
            "category": "webhook",
            "tags": ["webhook", "simple"],
            "parameters": [
                {
                    "name": "webhook_path",
                    "type": "string",
                    "required": True,
                    "description": "Webhook endpoint path",
                    "validation": {
                        "type": "string",
                        "pattern": "^/[a-zA-Z0-9/_-]+$"
                    }
                },
                {
                    "name": "response_message",
                    "type": "string",
                    "default": "Hello World",
                    "description": "Response message"
                }
            ],
            "template_data": {
                "nodes": [
                    {
                        "id": "webhook",
                        "type": "n8n-nodes-base.webhook",
                        "typeVersion": 1,
                        "position": [100, 100],
                        "parameters": {
                            "path": "{{ webhook_path }}",
                            "httpMethod": "POST"
                        }
                    },
                    {
                        "id": "respond",
                        "type": "n8n-nodes-base.respondToWebhook",
                        "typeVersion": 1,
                        "position": [300, 100],
                        "parameters": {
                            "respondWith": "text",
                            "responseBody": "{{ response_message }}"
                        }
                    }
                ],
                "connections": {
                    "webhook": {
                        "main": [
                            [
                                {
                                    "node": "respond",
                                    "type": "main",
                                    "index": 0
                                }
                            ]
                        ]
                    }
                }
            }
        }
    
    @pytest.fixture
    def sample_template_file(self, temp_dir, sample_template_data):
        """Create sample template file."""
        template_file = temp_dir / "simple_webhook.json"
        with open(template_file, 'w') as f:
            json.dump(sample_template_data, f, indent=2)
        return template_file
    
    def test_initialization(self, config):
        """Test TemplateEngine initialization."""
        engine = TemplateEngine(config)
        
        assert engine.config == config
        assert engine._template_cache == {}
        assert engine._jinja_env is not None if config.enable_jinja2 else None
    
    def test_initialization_with_path_only(self, temp_dir):
        """Test TemplateEngine initialization with path only."""
        engine = TemplateEngine(temp_dir)
        
        assert isinstance(engine.config, TemplateEngineConfig)
        assert engine.config.template_path == temp_dir
    
    @pytest.mark.asyncio
    async def test_load_template_success(self, template_engine, sample_template_file, sample_template_data):
        """Test successful template loading."""
        template = await template_engine.load_template("simple_webhook")
        
        assert template is not None
        assert template.name == "simple_webhook"
        assert template.description == "Simple webhook workflow"
        assert template.version == "1.0.0"
        assert template.category == "webhook"
        assert template.tags == ["webhook", "simple"]
        assert len(template.parameters) == 2
        
        # Check parameters
        webhook_param = next(p for p in template.parameters if p.name == "webhook_path")
        assert webhook_param.type == ParameterType.STRING
        assert webhook_param.required is True
        assert webhook_param.validation.pattern == "^/[a-zA-Z0-9/_-]+$"
        
        response_param = next(p for p in template.parameters if p.name == "response_message")
        assert response_param.type == ParameterType.STRING
        assert response_param.default == "Hello World"
    
    @pytest.mark.asyncio
    async def test_load_template_not_found(self, template_engine):
        """Test loading non-existent template."""
        template = await template_engine.load_template("non_existent")
        assert template is None
    
    @pytest.mark.asyncio
    async def test_load_template_caching(self, template_engine, sample_template_file):
        """Test template caching."""
        # Load template first time
        template1 = await template_engine.load_template("simple_webhook")
        assert template1 is not None
        
        # Load template second time (should be cached)
        template2 = await template_engine.load_template("simple_webhook")
        assert template2 is not None
        assert template2 is template1  # Same object reference
        
        # Verify cache
        assert "simple_webhook" in template_engine._template_cache
    
    @pytest.mark.asyncio
    async def test_load_template_no_caching(self, temp_dir, sample_template_file, sample_template_data):
        """Test template loading without caching."""
        config = TemplateEngineConfig(
            template_path=temp_dir,
            cache_templates=False
        )
        engine = TemplateEngine(config)
        
        # Load template first time
        template1 = await engine.load_template("simple_webhook")
        assert template1 is not None
        
        # Load template second time (should not be cached)
        template2 = await engine.load_template("simple_webhook")
        assert template2 is not None
        assert template2 is not template1  # Different object reference
        
        # Verify no cache
        assert engine._template_cache == {}
    
    @pytest.mark.asyncio
    async def test_load_template_invalid_json(self, template_engine, temp_dir):
        """Test loading template with invalid JSON."""
        # Create invalid JSON file
        invalid_file = temp_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        template = await template_engine.load_template("invalid")
        assert template is None
    
    @pytest.mark.asyncio
    async def test_list_templates(self, template_engine, sample_template_file):
        """Test listing available templates."""
        # Create additional template file
        additional_template = {
            "name": "data_processor",
            "description": "Data processing workflow",
            "template_data": {"nodes": [], "connections": {}},
            "parameters": []
        }
        additional_file = template_engine.config.template_path / "data_processor.json"
        with open(additional_file, 'w') as f:
            json.dump(additional_template, f)
        
        templates = await template_engine.list_templates()
        
        assert len(templates) == 2
        template_names = [t.name for t in templates]
        assert "simple_webhook" in template_names
        assert "data_processor" in template_names
    
    @pytest.mark.asyncio
    async def test_list_templates_empty_directory(self, template_engine):
        """Test listing templates in empty directory."""
        templates = await template_engine.list_templates()
        assert templates == []
    
    @pytest.mark.asyncio
    async def test_generate_workflow_success(self, template_engine, sample_template_file):
        """Test successful workflow generation."""
        template = await template_engine.load_template("simple_webhook")
        
        parameters = {
            "webhook_path": "/test/webhook",
            "response_message": "Custom response"
        }
        
        workflow_data = await template_engine.generate_workflow(template, parameters)
        
        assert workflow_data is not None
        assert "nodes" in workflow_data
        assert "connections" in workflow_data
        
        # Check parameter substitution
        webhook_node = next(n for n in workflow_data["nodes"] if n["id"] == "webhook")
        assert webhook_node["parameters"]["path"] == "/test/webhook"
        
        respond_node = next(n for n in workflow_data["nodes"] if n["id"] == "respond")
        assert respond_node["parameters"]["responseBody"] == "Custom response"
    
    @pytest.mark.asyncio
    async def test_generate_workflow_with_defaults(self, template_engine, sample_template_file):
        """Test workflow generation with default parameters."""
        template = await template_engine.load_template("simple_webhook")
        
        parameters = {
            "webhook_path": "/test/webhook"
            # response_message should use default
        }
        
        workflow_data = await template_engine.generate_workflow(template, parameters)
        
        respond_node = next(n for n in workflow_data["nodes"] if n["id"] == "respond")
        assert respond_node["parameters"]["responseBody"] == "Hello World"  # default value
    
    @pytest.mark.asyncio
    async def test_generate_workflow_missing_required_param(self, template_engine, sample_template_file):
        """Test workflow generation with missing required parameter."""
        template = await template_engine.load_template("simple_webhook")
        
        parameters = {
            # Missing required webhook_path
            "response_message": "Custom response"
        }
        
        with pytest.raises(ValueError, match="Missing required parameter"):
            await template_engine.generate_workflow(template, parameters)
    
    @pytest.mark.asyncio
    async def test_generate_workflow_no_jinja2(self, temp_dir, sample_template_file, sample_template_data):
        """Test workflow generation without Jinja2 processing."""
        config = TemplateEngineConfig(
            template_path=temp_dir,
            enable_jinja2=False
        )
        engine = TemplateEngine(config)
        
        template = await engine.load_template("simple_webhook")
        
        parameters = {
            "webhook_path": "/test/webhook",
            "response_message": "Custom response"
        }
        
        workflow_data = await engine.generate_workflow(template, parameters)
        
        # Without Jinja2, templates should remain as-is
        webhook_node = next(n for n in workflow_data["nodes"] if n["id"] == "webhook")
        assert webhook_node["parameters"]["path"] == "{{ webhook_path }}"  # Not substituted
    
    @pytest.mark.asyncio
    async def test_validate_template_success(self, template_engine, sample_template_file):
        """Test successful template validation."""
        template = await template_engine.load_template("simple_webhook")
        
        result = await template_engine.validate_template(template)
        
        assert result.valid is True
        assert result.errors == []
    
    @pytest.mark.asyncio
    async def test_validate_template_missing_required_fields(self, template_engine):
        """Test template validation with missing required fields."""
        invalid_template = WorkflowTemplate(
            name="",  # Empty name
            template_data={}  # Missing nodes and connections
        )
        
        result = await template_engine.validate_template(invalid_template)
        
        assert result.valid is False
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_validate_template_invalid_nodes(self, template_engine):
        """Test template validation with invalid nodes."""
        invalid_template = WorkflowTemplate(
            name="invalid_template",
            template_data={
                "nodes": [
                    {
                        "id": "",  # Empty ID
                        "type": "invalid-type",  # Invalid type
                        "position": "invalid"  # Invalid position
                    }
                ],
                "connections": {}
            }
        )
        
        result = await template_engine.validate_template(invalid_template)
        
        assert result.valid is False
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_reload_template(self, template_engine, sample_template_file, sample_template_data):
        """Test template reloading."""
        # Load template first time
        template1 = await template_engine.load_template("simple_webhook")
        assert template1.description == "Simple webhook workflow"
        
        # Modify template file
        modified_data = sample_template_data.copy()
        modified_data["description"] = "Modified webhook workflow"
        with open(sample_template_file, 'w') as f:
            json.dump(modified_data, f, indent=2)
        
        # Reload template
        await template_engine.reload_template("simple_webhook")
        
        # Load template again
        template2 = await template_engine.load_template("simple_webhook")
        assert template2.description == "Modified webhook workflow"
    
    @pytest.mark.asyncio
    async def test_reload_template_not_cached(self, template_engine):
        """Test reloading template that's not cached."""
        # Should not raise error
        await template_engine.reload_template("non_existent")
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, template_engine, sample_template_file):
        """Test clearing template cache."""
        # Load template to populate cache
        await template_engine.load_template("simple_webhook")
        assert "simple_webhook" in template_engine._template_cache
        
        # Clear cache
        template_engine.clear_cache()
        assert template_engine._template_cache == {}
    
    @pytest.mark.asyncio
    async def test_get_template_info(self, template_engine, sample_template_file):
        """Test getting template information."""
        info = await template_engine.get_template_info("simple_webhook")
        
        assert info is not None
        assert info["name"] == "simple_webhook"
        assert info["description"] == "Simple webhook workflow"
        assert info["version"] == "1.0.0"
        assert info["category"] == "webhook"
        assert info["parameter_count"] == 2
        assert "file_path" in info
        assert "file_size" in info
        assert "modified_time" in info
    
    @pytest.mark.asyncio
    async def test_get_template_info_not_found(self, template_engine):
        """Test getting info for non-existent template."""
        info = await template_engine.get_template_info("non_existent")
        assert info is None
    
    def test_jinja2_environment_setup(self, template_engine):
        """Test Jinja2 environment setup."""
        if template_engine.config.enable_jinja2:
            assert template_engine._jinja_env is not None
            
            # Test custom filters
            assert 'default_if_none' in template_engine._jinja_env.filters
            assert 'to_json' in template_engine._jinja_env.filters
            assert 'from_json' in template_engine._jinja_env.filters
    
    @pytest.mark.asyncio
    async def test_jinja2_custom_filters(self, template_engine):
        """Test custom Jinja2 filters."""
        if not template_engine.config.enable_jinja2:
            pytest.skip("Jinja2 not enabled")
        
        # Test default_if_none filter
        template_str = "{{ value | default_if_none('default') }}"
        result = template_engine._jinja_env.from_string(template_str).render(value=None)
        assert result == "default"
        
        result = template_engine._jinja_env.from_string(template_str).render(value="actual")
        assert result == "actual"
        
        # Test to_json filter
        template_str = "{{ data | to_json }}"
        result = template_engine._jinja_env.from_string(template_str).render(data={"key": "value"})
        assert result == '{"key": "value"}'
        
        # Test from_json filter
        template_str = "{{ json_str | from_json }}"
        result = template_engine._jinja_env.from_string(template_str).render(json_str='{"key": "value"}')
        assert result == "{'key': 'value'}"


@pytest.mark.integration
class TestTemplateEngineIntegration:
    """Integration tests for TemplateEngine."""
    
    @pytest.mark.asyncio
    async def test_full_template_workflow(self, temp_dir):
        """Test complete template workflow."""
        # Create template engine
        engine = TemplateEngine(temp_dir)
        
        # Create complex template
        complex_template = {
            "name": "data_pipeline",
            "description": "Complex data processing pipeline",
            "version": "2.0.0",
            "category": "data_processing",
            "tags": ["etl", "data", "pipeline"],
            "parameters": [
                {
                    "name": "source_url",
                    "type": "url",
                    "required": True,
                    "description": "Data source URL"
                },
                {
                    "name": "batch_size",
                    "type": "integer",
                    "default": 100,
                    "validation": {
                        "type": "integer",
                        "min_value": 1,
                        "max_value": 1000
                    }
                },
                {
                    "name": "output_format",
                    "type": "string",
                    "default": "json",
                    "validation": {
                        "type": "string",
                        "allowed_values": ["json", "csv", "xml"]
                    }
                }
            ],
            "template_data": {
                "nodes": [
                    {
                        "id": "http_request",
                        "type": "n8n-nodes-base.httpRequest",
                        "parameters": {
                            "url": "{{ source_url }}",
                            "options": {
                                "batchSize": "{{ batch_size }}"
                            }
                        }
                    },
                    {
                        "id": "data_transform",
                        "type": "n8n-nodes-base.function",
                        "parameters": {
                            "functionCode": "// Transform data to {{ output_format }} format\nreturn items;"
                        }
                    }
                ],
                "connections": {
                    "http_request": {
                        "main": [[{"node": "data_transform", "type": "main", "index": 0}]]
                    }
                }
            }
        }
        
        # Save template
        template_file = temp_dir / "data_pipeline.json"
        with open(template_file, 'w') as f:
            json.dump(complex_template, f, indent=2)
        
        # Load template
        template = await engine.load_template("data_pipeline")
        assert template is not None
        assert len(template.parameters) == 3
        
        # Validate template
        validation = await engine.validate_template(template)
        assert validation.valid is True
        
        # Generate workflow with parameters
        parameters = {
            "source_url": "https://api.example.com/data",
            "batch_size": 50,
            "output_format": "csv"
        }
        
        workflow_data = await engine.generate_workflow(template, parameters)
        
        # Verify parameter substitution
        http_node = next(n for n in workflow_data["nodes"] if n["id"] == "http_request")
        assert http_node["parameters"]["url"] == "https://api.example.com/data"
        assert http_node["parameters"]["options"]["batchSize"] == 50
        
        transform_node = next(n for n in workflow_data["nodes"] if n["id"] == "data_transform")
        assert "csv format" in transform_node["parameters"]["functionCode"]
        
        # Test template info
        info = await engine.get_template_info("data_pipeline")
        assert info["name"] == "data_pipeline"
        assert info["parameter_count"] == 3
        
        # Test listing templates
        templates = await engine.list_templates()
        assert len(templates) == 1
        assert templates[0].name == "data_pipeline"