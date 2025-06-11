#!/usr/bin/env python3
"""
Tests for Response Handler.

Comprehensive test suite for the response handler that processes
workflow execution responses and formats results.

Author: UnityAI Team
Version: 1.0.0
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from core.response_handler import (
    ResponseHandler,
    ResponseHandlerConfig,
    ResponseFormatter,
    ResponseTransformer
)
from modules.workflow_automation.models import (
    WorkflowExecution,
    ExecutionResult,
    ExecutionStatus,
    WorkflowMetrics
)
from core.api_client import N8nApiResponse


class TestResponseHandlerConfig:
    """Test ResponseHandlerConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ResponseHandlerConfig()
        
        assert config.enable_formatting is True
        assert config.enable_transformation is True
        assert config.include_metadata is True
        assert config.include_execution_time is True
        assert config.include_node_data is False
        assert config.max_response_size == 1024 * 1024  # 1MB
        assert config.truncate_large_responses is True
        assert config.response_timeout == 30
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ResponseHandlerConfig(
            enable_formatting=False,
            enable_transformation=False,
            include_metadata=False,
            include_execution_time=False,
            include_node_data=True,
            max_response_size=512 * 1024,
            truncate_large_responses=False,
            response_timeout=60
        )
        
        assert config.enable_formatting is False
        assert config.enable_transformation is False
        assert config.include_metadata is False
        assert config.include_execution_time is False
        assert config.include_node_data is True
        assert config.max_response_size == 512 * 1024
        assert config.truncate_large_responses is False
        assert config.response_timeout == 60


class TestResponseFormatter:
    """Test ResponseFormatter class."""
    
    @pytest.fixture
    def formatter(self):
        """Create ResponseFormatter instance."""
        return ResponseFormatter()
    
    @pytest.fixture
    def sample_execution_data(self):
        """Sample execution data."""
        return {
            "id": "exec_123",
            "status": "success",
            "finished": True,
            "startedAt": "2023-01-01T10:00:00.000Z",
            "stoppedAt": "2023-01-01T10:05:00.000Z",
            "data": {
                "resultData": {
                    "runData": {
                        "node1": [
                            {
                                "data": {
                                    "main": [
                                        [
                                            {
                                                "json": {"result": "success", "value": 42}
                                            }
                                        ]
                                    ]
                                },
                                "executionTime": 1500
                            }
                        ],
                        "node2": [
                            {
                                "data": {
                                    "main": [
                                        [
                                            {
                                                "json": {"processed": True, "count": 10}
                                            }
                                        ]
                                    ]
                                },
                                "executionTime": 800
                            }
                        ]
                    }
                }
            }
        }
    
    def test_format_success_response(self, formatter, sample_execution_data):
        """Test formatting successful execution response."""
        result = formatter.format_execution_result(sample_execution_data)
        
        assert result["success"] is True
        assert result["status"] == "success"
        assert result["execution_id"] == "exec_123"
        assert "execution_time" in result
        assert "started_at" in result
        assert "finished_at" in result
        assert "data" in result
        
        # Check execution time calculation
        assert result["execution_time"] == 300.0  # 5 minutes in seconds
    
    def test_format_failed_response(self, formatter):
        """Test formatting failed execution response."""
        failed_data = {
            "id": "exec_456",
            "status": "error",
            "finished": True,
            "startedAt": "2023-01-01T10:00:00.000Z",
            "stoppedAt": "2023-01-01T10:01:00.000Z",
            "data": {
                "resultData": {
                    "error": {
                        "message": "Node execution failed",
                        "stack": "Error stack trace..."
                    }
                }
            }
        }
        
        result = formatter.format_execution_result(failed_data)
        
        assert result["success"] is False
        assert result["status"] == "error"
        assert result["execution_id"] == "exec_456"
        assert "error" in result
        assert result["error"]["message"] == "Node execution failed"
    
    def test_format_running_response(self, formatter):
        """Test formatting running execution response."""
        running_data = {
            "id": "exec_789",
            "status": "running",
            "finished": False,
            "startedAt": "2023-01-01T10:00:00.000Z"
        }
        
        result = formatter.format_execution_result(running_data)
        
        assert result["success"] is None  # Unknown for running executions
        assert result["status"] == "running"
        assert result["execution_id"] == "exec_789"
        assert result["finished_at"] is None
    
    def test_extract_node_results(self, formatter, sample_execution_data):
        """Test extracting node results from execution data."""
        node_results = formatter.extract_node_results(sample_execution_data)
        
        assert len(node_results) == 2
        assert "node1" in node_results
        assert "node2" in node_results
        
        # Check node1 results
        node1_result = node_results["node1"]
        assert node1_result["success"] is True
        assert node1_result["execution_time"] == 1500
        assert len(node1_result["output"]) == 1
        assert node1_result["output"][0]["result"] == "success"
        
        # Check node2 results
        node2_result = node_results["node2"]
        assert node2_result["success"] is True
        assert node2_result["execution_time"] == 800
        assert node2_result["output"][0]["processed"] is True
    
    def test_extract_node_results_with_error(self, formatter):
        """Test extracting node results when node has error."""
        error_data = {
            "data": {
                "resultData": {
                    "runData": {
                        "error_node": [
                            {
                                "error": {
                                    "message": "Node failed",
                                    "name": "NodeError"
                                },
                                "executionTime": 500
                            }
                        ]
                    }
                }
            }
        }
        
        node_results = formatter.extract_node_results(error_data)
        
        assert len(node_results) == 1
        assert "error_node" in node_results
        
        error_node = node_results["error_node"]
        assert error_node["success"] is False
        assert error_node["execution_time"] == 500
        assert "error" in error_node
        assert error_node["error"]["message"] == "Node failed"
    
    def test_calculate_execution_time(self, formatter):
        """Test execution time calculation."""
        start_time = "2023-01-01T10:00:00.000Z"
        end_time = "2023-01-01T10:05:30.500Z"
        
        execution_time = formatter.calculate_execution_time(start_time, end_time)
        
        assert execution_time == 330.5  # 5 minutes 30.5 seconds
    
    def test_calculate_execution_time_invalid_format(self, formatter):
        """Test execution time calculation with invalid date format."""
        start_time = "invalid-date"
        end_time = "2023-01-01T10:05:00.000Z"
        
        execution_time = formatter.calculate_execution_time(start_time, end_time)
        
        assert execution_time is None
    
    def test_format_metrics(self, formatter, sample_execution_data):
        """Test formatting execution metrics."""
        metrics = formatter.format_metrics(sample_execution_data)
        
        assert "total_execution_time" in metrics
        assert "node_count" in metrics
        assert "success_rate" in metrics
        assert "average_node_time" in metrics
        
        assert metrics["total_execution_time"] == 300.0
        assert metrics["node_count"] == 2
        assert metrics["success_rate"] == 1.0  # All nodes successful
        assert metrics["average_node_time"] == 1150.0  # (1500 + 800) / 2


class TestResponseTransformer:
    """Test ResponseTransformer class."""
    
    @pytest.fixture
    def transformer(self):
        """Create ResponseTransformer instance."""
        return ResponseTransformer()
    
    @pytest.fixture
    def sample_raw_data(self):
        """Sample raw execution data."""
        return {
            "node1": [
                {"json": {"id": 1, "name": "John", "email": "john@example.com"}},
                {"json": {"id": 2, "name": "Jane", "email": "jane@example.com"}}
            ],
            "node2": [
                {"json": {"processed_count": 2, "status": "completed"}}
            ]
        }
    
    def test_transform_to_flat_structure(self, transformer, sample_raw_data):
        """Test transforming to flat structure."""
        result = transformer.transform_to_flat_structure(sample_raw_data)
        
        assert "node1" in result
        assert "node2" in result
        
        # Check node1 transformation
        node1_data = result["node1"]
        assert len(node1_data) == 2
        assert node1_data[0]["id"] == 1
        assert node1_data[0]["name"] == "John"
        
        # Check node2 transformation
        node2_data = result["node2"]
        assert len(node2_data) == 1
        assert node2_data[0]["processed_count"] == 2
    
    def test_transform_to_summary(self, transformer, sample_raw_data):
        """Test transforming to summary format."""
        result = transformer.transform_to_summary(sample_raw_data)
        
        assert "total_items" in result
        assert "nodes" in result
        assert "summary" in result
        
        assert result["total_items"] == 3  # 2 from node1 + 1 from node2
        assert len(result["nodes"]) == 2
        
        # Check node summaries
        node_summaries = {node["name"]: node for node in result["nodes"]}
        assert "node1" in node_summaries
        assert "node2" in node_summaries
        assert node_summaries["node1"]["item_count"] == 2
        assert node_summaries["node2"]["item_count"] == 1
    
    def test_transform_to_table_format(self, transformer):
        """Test transforming to table format."""
        table_data = {
            "data_node": [
                {"json": {"id": 1, "name": "John", "age": 30}},
                {"json": {"id": 2, "name": "Jane", "age": 25}},
                {"json": {"id": 3, "name": "Bob", "age": 35}}
            ]
        }
        
        result = transformer.transform_to_table_format(table_data, "data_node")
        
        assert "headers" in result
        assert "rows" in result
        assert "total_rows" in result
        
        # Check headers
        expected_headers = ["id", "name", "age"]
        assert set(result["headers"]) == set(expected_headers)
        
        # Check rows
        assert len(result["rows"]) == 3
        assert result["total_rows"] == 3
        
        # Check first row
        first_row = result["rows"][0]
        assert first_row["id"] == 1
        assert first_row["name"] == "John"
        assert first_row["age"] == 30
    
    def test_transform_to_table_format_node_not_found(self, transformer, sample_raw_data):
        """Test table transformation when node not found."""
        result = transformer.transform_to_table_format(sample_raw_data, "non_existent_node")
        
        assert result is None
    
    def test_filter_sensitive_data(self, transformer):
        """Test filtering sensitive data."""
        sensitive_data = {
            "node1": [
                {
                    "json": {
                        "id": 1,
                        "name": "John",
                        "password": "secret123",
                        "api_key": "key_abc123",
                        "email": "john@example.com",
                        "credit_card": "1234-5678-9012-3456"
                    }
                }
            ]
        }
        
        sensitive_fields = ["password", "api_key", "credit_card"]
        result = transformer.filter_sensitive_data(sensitive_data, sensitive_fields)
        
        node_data = result["node1"][0]["json"]
        
        # Sensitive fields should be removed or masked
        assert "password" not in node_data or node_data["password"] == "[FILTERED]"
        assert "api_key" not in node_data or node_data["api_key"] == "[FILTERED]"
        assert "credit_card" not in node_data or node_data["credit_card"] == "[FILTERED]"
        
        # Non-sensitive fields should remain
        assert node_data["id"] == 1
        assert node_data["name"] == "John"
        assert node_data["email"] == "john@example.com"
    
    def test_aggregate_results(self, transformer, sample_raw_data):
        """Test aggregating results across nodes."""
        result = transformer.aggregate_results(sample_raw_data)
        
        assert "total_items" in result
        assert "all_data" in result
        assert "node_summary" in result
        
        assert result["total_items"] == 3
        assert len(result["all_data"]) == 3
        
        # Check aggregated data
        all_data = result["all_data"]
        assert any(item.get("name") == "John" for item in all_data)
        assert any(item.get("name") == "Jane" for item in all_data)
        assert any(item.get("processed_count") == 2 for item in all_data)
    
    def test_paginate_results(self, transformer):
        """Test paginating large result sets."""
        large_data = {
            "data_node": [
                {"json": {"id": i, "value": f"item_{i}"}}
                for i in range(100)
            ]
        }
        
        # Test first page
        page1 = transformer.paginate_results(large_data, page=1, page_size=20)
        
        assert "data" in page1
        assert "pagination" in page1
        assert len(page1["data"]["data_node"]) == 20
        assert page1["pagination"]["current_page"] == 1
        assert page1["pagination"]["total_pages"] == 5
        assert page1["pagination"]["total_items"] == 100
        
        # Test last page
        page5 = transformer.paginate_results(large_data, page=5, page_size=20)
        assert len(page5["data"]["data_node"]) == 20
        assert page5["pagination"]["current_page"] == 5
    
    def test_paginate_results_invalid_page(self, transformer, sample_raw_data):
        """Test pagination with invalid page number."""
        result = transformer.paginate_results(sample_raw_data, page=10, page_size=20)
        
        # Should return empty results for invalid page
        assert result["data"] == {}
        assert result["pagination"]["current_page"] == 10
        assert result["pagination"]["total_items"] == 3


class TestResponseHandler:
    """Test ResponseHandler class."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return ResponseHandlerConfig(
            enable_formatting=True,
            enable_transformation=True,
            include_metadata=True
        )
    
    @pytest.fixture
    def response_handler(self, config):
        """Create ResponseHandler instance."""
        return ResponseHandler(config)
    
    @pytest.fixture
    def sample_api_response(self):
        """Sample N8nApiResponse."""
        return N8nApiResponse(
            success=True,
            data={
                "id": "exec_123",
                "status": "success",
                "finished": True,
                "startedAt": "2023-01-01T10:00:00.000Z",
                "stoppedAt": "2023-01-01T10:05:00.000Z",
                "data": {
                    "resultData": {
                        "runData": {
                            "webhook": [
                                {
                                    "data": {
                                        "main": [
                                            [
                                                {"json": {"message": "Hello World"}}
                                            ]
                                        ]
                                    },
                                    "executionTime": 100
                                }
                            ]
                        }
                    }
                }
            },
            status_code=200,
            execution_time=1.5
        )
    
    def test_initialization(self, config):
        """Test ResponseHandler initialization."""
        handler = ResponseHandler(config)
        
        assert handler.config == config
        assert isinstance(handler.formatter, ResponseFormatter)
        assert isinstance(handler.transformer, ResponseTransformer)
    
    @pytest.mark.asyncio
    async def test_process_execution_response_success(self, response_handler, sample_api_response):
        """Test processing successful execution response."""
        result = await response_handler.process_execution_response(sample_api_response)
        
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.execution_id == "exec_123"
        assert result.status == ExecutionStatus.SUCCESS
        assert result.execution_time == 300.0  # 5 minutes
        assert "webhook" in result.data
    
    @pytest.mark.asyncio
    async def test_process_execution_response_failure(self, response_handler):
        """Test processing failed execution response."""
        failed_response = N8nApiResponse(
            success=False,
            error="Execution failed",
            status_code=500
        )
        
        result = await response_handler.process_execution_response(failed_response)
        
        assert isinstance(result, ExecutionResult)
        assert result.success is False
        assert result.status == ExecutionStatus.FAILED
        assert "Execution failed" in result.error
    
    @pytest.mark.asyncio
    async def test_process_execution_response_with_transformation(self, response_handler, sample_api_response):
        """Test processing response with transformation."""
        # Enable specific transformation
        transformation_options = {
            "format": "summary",
            "include_node_details": True
        }
        
        result = await response_handler.process_execution_response(
            sample_api_response,
            transformation_options=transformation_options
        )
        
        assert result.success is True
        assert "summary" in result.metadata
        assert "node_details" in result.metadata
    
    @pytest.mark.asyncio
    async def test_process_execution_response_large_data(self, response_handler):
        """Test processing response with large data."""
        # Create response with large data
        large_data = {
            "id": "exec_large",
            "status": "success",
            "finished": True,
            "data": {
                "resultData": {
                    "runData": {
                        "data_node": [
                            {
                                "data": {
                                    "main": [
                                        [
                                            {"json": {"data": "x" * 1000000}}  # 1MB of data
                                        ]
                                    ]
                                },
                                "executionTime": 1000
                            }
                        ]
                    }
                }
            }
        }
        
        large_response = N8nApiResponse(
            success=True,
            data=large_data,
            status_code=200
        )
        
        # Configure to truncate large responses
        response_handler.config.max_response_size = 500 * 1024  # 500KB
        response_handler.config.truncate_large_responses = True
        
        result = await response_handler.process_execution_response(large_response)
        
        assert result.success is True
        assert "truncated" in result.metadata
        assert result.metadata["truncated"] is True
    
    @pytest.mark.asyncio
    async def test_format_response_data(self, response_handler, sample_api_response):
        """Test formatting response data."""
        formatted_data = await response_handler.format_response_data(sample_api_response.data)
        
        assert "execution_id" in formatted_data
        assert "status" in formatted_data
        assert "execution_time" in formatted_data
        assert "data" in formatted_data
        
        assert formatted_data["execution_id"] == "exec_123"
        assert formatted_data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_transform_response_data(self, response_handler):
        """Test transforming response data."""
        raw_data = {
            "node1": [
                {"json": {"id": 1, "value": "test"}}
            ]
        }
        
        transformation_options = {
            "format": "flat",
            "filter_sensitive": True,
            "sensitive_fields": ["password", "api_key"]
        }
        
        transformed_data = await response_handler.transform_response_data(
            raw_data,
            transformation_options
        )
        
        assert "node1" in transformed_data
        assert len(transformed_data["node1"]) == 1
        assert transformed_data["node1"][0]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_create_execution_result(self, response_handler):
        """Test creating ExecutionResult from processed data."""
        processed_data = {
            "execution_id": "exec_123",
            "status": "success",
            "success": True,
            "execution_time": 300.0,
            "data": {"result": "test"},
            "metadata": {"node_count": 1}
        }
        
        result = response_handler.create_execution_result(processed_data)
        
        assert isinstance(result, ExecutionResult)
        assert result.execution_id == "exec_123"
        assert result.status == ExecutionStatus.SUCCESS
        assert result.success is True
        assert result.execution_time == 300.0
        assert result.data == {"result": "test"}
        assert result.metadata == {"node_count": 1}
    
    @pytest.mark.asyncio
    async def test_handle_response_timeout(self, response_handler):
        """Test handling response processing timeout."""
        # Mock a slow processing operation
        with patch.object(response_handler.formatter, 'format_execution_result') as mock_format:
            async def slow_format(*args, **kwargs):
                await asyncio.sleep(2)  # Simulate slow processing
                return {"status": "success"}
            
            mock_format.side_effect = slow_format
            
            # Set short timeout
            response_handler.config.response_timeout = 0.1
            
            sample_response = N8nApiResponse(
                success=True,
                data={"id": "exec_123", "status": "success"},
                status_code=200
            )
            
            result = await response_handler.process_execution_response(sample_response)
            
            # Should return timeout error
            assert result.success is False
            assert result.status == ExecutionStatus.FAILED
            assert "timeout" in result.error.lower()
    
    def test_calculate_response_size(self, response_handler):
        """Test calculating response data size."""
        data = {
            "key1": "value1",
            "key2": [1, 2, 3],
            "key3": {"nested": "data"}
        }
        
        size = response_handler._calculate_response_size(data)
        
        # Size should be reasonable (exact value depends on JSON serialization)
        assert size > 0
        assert size < 1000  # Should be small for this test data
    
    def test_truncate_response_data(self, response_handler):
        """Test truncating large response data."""
        large_data = {
            "large_field": "x" * 1000,  # 1KB of data
            "small_field": "small"
        }
        
        max_size = 500  # 500 bytes
        truncated_data, was_truncated = response_handler._truncate_response_data(large_data, max_size)
        
        assert was_truncated is True
        assert response_handler._calculate_response_size(truncated_data) <= max_size
        assert "small_field" in truncated_data  # Small fields should be preserved


@pytest.mark.integration
class TestResponseHandlerIntegration:
    """Integration tests for ResponseHandler."""
    
    @pytest.mark.asyncio
    async def test_full_response_processing_pipeline(self):
        """Test complete response processing pipeline."""
        config = ResponseHandlerConfig(
            enable_formatting=True,
            enable_transformation=True,
            include_metadata=True,
            include_execution_time=True
        )
        
        handler = ResponseHandler(config)
        
        # Create complex execution response
        complex_response = N8nApiResponse(
            success=True,
            data={
                "id": "exec_complex",
                "status": "success",
                "finished": True,
                "startedAt": "2023-01-01T10:00:00.000Z",
                "stoppedAt": "2023-01-01T10:15:30.500Z",
                "data": {
                    "resultData": {
                        "runData": {
                            "http_request": [
                                {
                                    "data": {
                                        "main": [
                                            [
                                                {"json": {"id": 1, "name": "John", "email": "john@example.com"}},
                                                {"json": {"id": 2, "name": "Jane", "email": "jane@example.com"}}
                                            ]
                                        ]
                                    },
                                    "executionTime": 2000
                                }
                            ],
                            "data_transform": [
                                {
                                    "data": {
                                        "main": [
                                            [
                                                {"json": {"processed_count": 2, "status": "completed"}}
                                            ]
                                        ]
                                    },
                                    "executionTime": 500
                                }
                            ],
                            "webhook_response": [
                                {
                                    "data": {
                                        "main": [
                                            [
                                                {"json": {"message": "Processing completed", "timestamp": "2023-01-01T10:15:30Z"}}
                                            ]
                                        ]
                                    },
                                    "executionTime": 100
                                }
                            ]
                        }
                    }
                }
            },
            status_code=200,
            execution_time=2.5
        )
        
        # Process with different transformation options
        transformation_options = {
            "format": "summary",
            "include_node_details": True,
            "filter_sensitive": True,
            "sensitive_fields": ["email"]
        }
        
        result = await handler.process_execution_response(
            complex_response,
            transformation_options=transformation_options
        )
        
        # Verify comprehensive processing
        assert result.success is True
        assert result.execution_id == "exec_complex"
        assert result.status == ExecutionStatus.SUCCESS
        assert result.execution_time == 930.5  # 15 minutes 30.5 seconds
        
        # Verify metadata includes summary information
        assert "summary" in result.metadata
        assert "node_details" in result.metadata
        assert "total_execution_time" in result.metadata
        
        # Verify sensitive data filtering
        # Email addresses should be filtered out
        data_str = json.dumps(result.data)
        assert "john@example.com" not in data_str
        assert "jane@example.com" not in data_str
        
        # Verify node processing
        assert len(result.metadata["node_details"]) == 3
        node_names = [node["name"] for node in result.metadata["node_details"]]
        assert "http_request" in node_names
        assert "data_transform" in node_names
        assert "webhook_response" in node_names