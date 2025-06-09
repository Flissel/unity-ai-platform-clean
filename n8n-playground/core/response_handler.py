#!/usr/bin/env python3
"""
Response Handler for n8n API Playground

Handles processing, validation, and transformation of n8n API responses.
Provides structured data extraction and error handling.

Author: UnityAI Team
Version: 1.0.0
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel, Field, validator

# Setup structured logging
logger = structlog.get_logger(__name__)


class ProcessedResponse(BaseModel):
    """Represents a processed n8n API response."""
    
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = None


class DataExtractor(BaseModel):
    """Configuration for data extraction from responses."""
    
    path: str  # JSONPath or dot notation
    name: str
    type: str = "string"  # string, number, boolean, array, object
    required: bool = False
    default: Optional[Any] = None
    transform: Optional[str] = None  # transformation function name


class ResponseValidator(BaseModel):
    """Configuration for response validation."""
    
    required_fields: List[str] = Field(default_factory=list)
    field_types: Dict[str, str] = Field(default_factory=dict)
    min_values: Dict[str, Union[int, float]] = Field(default_factory=dict)
    max_values: Dict[str, Union[int, float]] = Field(default_factory=dict)
    patterns: Dict[str, str] = Field(default_factory=dict)
    custom_rules: List[str] = Field(default_factory=list)


class ResponseHandler:
    """Main response handler class."""
    
    def __init__(self):
        self.extractors: Dict[str, List[DataExtractor]] = {}
        self.validators: Dict[str, ResponseValidator] = {}
        self.transformers: Dict[str, callable] = self._init_transformers()
        
        # Statistics
        self.processed_count = 0
        self.error_count = 0
        self.warning_count = 0
    
    def register_extractor(self, response_type: str, extractor: DataExtractor):
        """Register data extractor for specific response type."""
        
        if response_type not in self.extractors:
            self.extractors[response_type] = []
        
        self.extractors[response_type].append(extractor)
        
        logger.debug(
            "Data extractor registered",
            response_type=response_type,
            extractor_name=extractor.name
        )
    
    def register_validator(self, response_type: str, validator: ResponseValidator):
        """Register validator for specific response type."""
        
        self.validators[response_type] = validator
        
        logger.debug(
            "Validator registered",
            response_type=response_type,
            required_fields=len(validator.required_fields)
        )
    
    async def process_response(
        self,
        response_data: Dict[str, Any],
        response_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessedResponse:
        """Process n8n API response with validation and extraction."""
        
        start_time = datetime.utcnow()
        
        try:
            # Initialize processed response
            processed = ProcessedResponse(
                success=True,
                status_code=response_data.get('status_code', 200),
                data=response_data.copy(),
                metadata={
                    'response_type': response_type,
                    'context': context or {},
                    'original_size': len(str(response_data))
                }
            )
            
            # Validate response
            validation_result = await self._validate_response(
                response_data,
                response_type
            )
            
            if not validation_result['valid']:
                processed.success = False
                processed.error = validation_result['error']
                processed.warnings.extend(validation_result['warnings'])
                self.error_count += 1
                return processed
            
            processed.warnings.extend(validation_result['warnings'])
            
            # Extract structured data
            extracted_data = await self._extract_data(
                response_data,
                response_type
            )
            
            if extracted_data:
                processed.data.update(extracted_data)
                processed.metadata['extracted_fields'] = list(extracted_data.keys())
            
            # Transform data
            transformed_data = await self._transform_data(
                processed.data,
                response_type
            )
            
            if transformed_data:
                processed.data = transformed_data
                processed.metadata['transformed'] = True
            
            # Add processing metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            processed.processing_time = processing_time
            processed.metadata['processing_time'] = processing_time
            
            self.processed_count += 1
            
            if processed.warnings:
                self.warning_count += len(processed.warnings)
            
            logger.debug(
                "Response processed successfully",
                response_type=response_type,
                processing_time=processing_time,
                warnings=len(processed.warnings)
            )
            
            return processed
        
        except Exception as e:
            self.error_count += 1
            
            logger.error(
                "Response processing failed",
                response_type=response_type,
                error=str(e)
            )
            
            return ProcessedResponse(
                success=False,
                status_code=500,
                error=f"Processing error: {str(e)}",
                metadata={
                    'response_type': response_type,
                    'processing_error': True
                },
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def process_workflow_result(
        self,
        execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process workflow execution result."""
        
        try:
            result = {
                'execution_id': execution_data.get('id'),
                'workflow_id': execution_data.get('workflowId'),
                'status': 'success' if execution_data.get('finished') and execution_data.get('success') else 'error',
                'started_at': execution_data.get('startedAt'),
                'finished_at': execution_data.get('stoppedAt'),
                'execution_time': None,
                'node_results': {},
                'output_data': [],
                'error_data': []
            }
            
            # Calculate execution time
            if result['started_at'] and result['finished_at']:
                start = datetime.fromisoformat(result['started_at'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(result['finished_at'].replace('Z', '+00:00'))
                result['execution_time'] = (end - start).total_seconds()
            
            # Process node execution data
            execution_data_nodes = execution_data.get('data', {}).get('resultData', {}).get('runData', {})
            
            for node_name, node_data in execution_data_nodes.items():
                if isinstance(node_data, list) and node_data:
                    node_result = node_data[0]  # Take first execution
                    
                    result['node_results'][node_name] = {
                        'status': 'success' if not node_result.get('error') else 'error',
                        'execution_time': node_result.get('executionTime'),
                        'start_time': node_result.get('startTime'),
                        'data_count': len(node_result.get('data', {}).get('main', [[]]))
                    }
                    
                    # Extract output data
                    main_data = node_result.get('data', {}).get('main', [[]])
                    if main_data and main_data[0]:
                        for item in main_data[0]:
                            if isinstance(item, dict) and 'json' in item:
                                result['output_data'].append({
                                    'node': node_name,
                                    'data': item['json']
                                })
                    
                    # Extract error data
                    if node_result.get('error'):
                        result['error_data'].append({
                            'node': node_name,
                            'error': node_result['error']
                        })
            
            # Add summary statistics
            result['summary'] = {
                'total_nodes': len(result['node_results']),
                'successful_nodes': len([n for n in result['node_results'].values() if n['status'] == 'success']),
                'failed_nodes': len([n for n in result['node_results'].values() if n['status'] == 'error']),
                'total_output_items': len(result['output_data']),
                'total_errors': len(result['error_data'])
            }
            
            logger.debug(
                "Workflow result processed",
                execution_id=result['execution_id'],
                status=result['status'],
                nodes=result['summary']['total_nodes']
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "Failed to process workflow result",
                error=str(e)
            )
            
            return {
                'status': 'error',
                'error': f"Result processing failed: {str(e)}",
                'raw_data': execution_data
            }
    
    async def extract_webhook_data(
        self,
        webhook_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract and structure webhook data."""
        
        try:
            extracted = {
                'webhook_id': webhook_payload.get('webhookId'),
                'execution_id': webhook_payload.get('executionId'),
                'workflow_id': webhook_payload.get('workflowId'),
                'timestamp': webhook_payload.get('timestamp', datetime.utcnow().isoformat()),
                'event_type': webhook_payload.get('eventType', 'execution'),
                'data': webhook_payload.get('data', {}),
                'headers': webhook_payload.get('headers', {}),
                'query': webhook_payload.get('query', {})
            }
            
            # Extract specific data based on event type
            if extracted['event_type'] == 'execution':
                extracted['execution_data'] = await self.process_workflow_result(
                    webhook_payload.get('data', {})
                )
            
            logger.debug(
                "Webhook data extracted",
                webhook_id=extracted['webhook_id'],
                event_type=extracted['event_type']
            )
            
            return extracted
        
        except Exception as e:
            logger.error(
                "Failed to extract webhook data",
                error=str(e)
            )
            
            return {
                'error': f"Webhook extraction failed: {str(e)}",
                'raw_payload': webhook_payload
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'success_rate': (
                (self.processed_count - self.error_count) / max(self.processed_count, 1)
            ) * 100,
            'registered_extractors': len(self.extractors),
            'registered_validators': len(self.validators)
        }
    
    # Private methods
    async def _validate_response(
        self,
        response_data: Dict[str, Any],
        response_type: str
    ) -> Dict[str, Any]:
        """Validate response data."""
        
        result = {
            'valid': True,
            'error': None,
            'warnings': []
        }
        
        if response_type not in self.validators:
            result['warnings'].append(f"No validator registered for type: {response_type}")
            return result
        
        validator = self.validators[response_type]
        
        try:
            # Check required fields
            for field in validator.required_fields:
                if not self._get_nested_value(response_data, field):
                    result['valid'] = False
                    result['error'] = f"Required field missing: {field}"
                    return result
            
            # Check field types
            for field, expected_type in validator.field_types.items():
                value = self._get_nested_value(response_data, field)
                if value is not None and not self._check_type(value, expected_type):
                    result['warnings'].append(
                        f"Field {field} has unexpected type: {type(value).__name__} (expected: {expected_type})"
                    )
            
            # Check value ranges
            for field, min_val in validator.min_values.items():
                value = self._get_nested_value(response_data, field)
                if value is not None and isinstance(value, (int, float)) and value < min_val:
                    result['warnings'].append(
                        f"Field {field} value {value} is below minimum {min_val}"
                    )
            
            for field, max_val in validator.max_values.items():
                value = self._get_nested_value(response_data, field)
                if value is not None and isinstance(value, (int, float)) and value > max_val:
                    result['warnings'].append(
                        f"Field {field} value {value} is above maximum {max_val}"
                    )
            
            # Check patterns
            for field, pattern in validator.patterns.items():
                value = self._get_nested_value(response_data, field)
                if value is not None and isinstance(value, str):
                    if not re.match(pattern, value):
                        result['warnings'].append(
                            f"Field {field} does not match pattern: {pattern}"
                        )
        
        except Exception as e:
            result['valid'] = False
            result['error'] = f"Validation error: {str(e)}"
        
        return result
    
    async def _extract_data(
        self,
        response_data: Dict[str, Any],
        response_type: str
    ) -> Optional[Dict[str, Any]]:
        """Extract structured data from response."""
        
        if response_type not in self.extractors:
            return None
        
        extracted = {}
        
        for extractor in self.extractors[response_type]:
            try:
                value = self._get_nested_value(response_data, extractor.path)
                
                if value is None:
                    if extractor.required:
                        logger.warning(
                            "Required extraction field missing",
                            field=extractor.name,
                            path=extractor.path
                        )
                    value = extractor.default
                
                # Apply transformation
                if value is not None and extractor.transform:
                    if extractor.transform in self.transformers:
                        value = self.transformers[extractor.transform](value)
                
                # Type conversion
                if value is not None:
                    value = self._convert_type(value, extractor.type)
                
                extracted[extractor.name] = value
            
            except Exception as e:
                logger.warning(
                    "Data extraction failed",
                    field=extractor.name,
                    error=str(e)
                )
                
                if extractor.required:
                    extracted[extractor.name] = None
        
        return extracted if extracted else None
    
    async def _transform_data(
        self,
        data: Dict[str, Any],
        response_type: str
    ) -> Optional[Dict[str, Any]]:
        """Apply data transformations."""
        
        # Add response-type specific transformations here
        if response_type == 'workflow_execution':
            return self._transform_workflow_data(data)
        elif response_type == 'user_data':
            return self._transform_user_data(data)
        
        return None
    
    def _transform_workflow_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform workflow execution data."""
        
        transformed = data.copy()
        
        # Normalize timestamps
        for field in ['startedAt', 'stoppedAt', 'createdAt', 'updatedAt']:
            if field in transformed and transformed[field]:
                transformed[field] = self._normalize_timestamp(transformed[field])
        
        # Add computed fields
        if 'startedAt' in transformed and 'stoppedAt' in transformed:
            if transformed['startedAt'] and transformed['stoppedAt']:
                start = datetime.fromisoformat(transformed['startedAt'])
                end = datetime.fromisoformat(transformed['stoppedAt'])
                transformed['duration_seconds'] = (end - start).total_seconds()
        
        return transformed
    
    def _transform_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform user data."""
        
        transformed = data.copy()
        
        # Normalize email
        if 'email' in transformed and transformed['email']:
            transformed['email'] = transformed['email'].lower().strip()
        
        # Add computed fields
        if 'createdAt' in transformed and transformed['createdAt']:
            created = datetime.fromisoformat(transformed['createdAt'])
            transformed['account_age_days'] = (datetime.utcnow() - created).days
        
        return transformed
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value using dot notation."""
        
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'float': float,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        
        return True
    
    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        
        try:
            if target_type == 'string':
                return str(value)
            elif target_type == 'integer':
                return int(value)
            elif target_type == 'float':
                return float(value)
            elif target_type == 'boolean':
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif target_type == 'array':
                if isinstance(value, str):
                    return json.loads(value)
                return list(value)
            elif target_type == 'object':
                if isinstance(value, str):
                    return json.loads(value)
                return dict(value)
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
        
        return value
    
    def _normalize_timestamp(self, timestamp: str) -> str:
        """Normalize timestamp format."""
        
        try:
            # Handle various timestamp formats
            if timestamp.endswith('Z'):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(timestamp)
            
            return dt.isoformat()
        except ValueError:
            return timestamp
    
    def _init_transformers(self) -> Dict[str, callable]:
        """Initialize data transformers."""
        
        return {
            'lowercase': lambda x: x.lower() if isinstance(x, str) else x,
            'uppercase': lambda x: x.upper() if isinstance(x, str) else x,
            'strip': lambda x: x.strip() if isinstance(x, str) else x,
            'normalize_email': lambda x: x.lower().strip() if isinstance(x, str) else x,
            'timestamp_to_iso': self._normalize_timestamp,
            'json_parse': lambda x: json.loads(x) if isinstance(x, str) else x,
            'json_stringify': lambda x: json.dumps(x) if not isinstance(x, str) else x
        }