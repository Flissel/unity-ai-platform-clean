"""Workflow service for orchestrating complex automation workflows."""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum

from ..core.config import get_settings
from ..core.logging import get_logger, log_execution_time
from ..core.exceptions import (
    WorkflowExecutionError, ValidationError, TimeoutError,
    ServiceUnavailableError, NotFoundError
)
from ..core.models import (
    WorkflowDefinition, WorkflowExecution, WorkflowTrigger,
    ExecutionStatus, Priority
)
from ..core.cache import cached, SessionCache
from .n8n_service import N8nService
from .autogen_service import AutoGenService
from .code_execution_service import CodeExecutionService

logger = get_logger(__name__)


class WorkflowType(str, Enum):
    """Types of workflows."""
    CODE_TESTING = "code_testing"
    DATA_PROCESSING = "data_processing"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    MONITORING = "monitoring"
    CUSTOM = "custom"


class WorkflowStep:
    """Represents a single step in a workflow."""
    
    def __init__(
        self,
        step_id: str,
        step_type: str,
        config: Dict[str, Any],
        dependencies: Optional[List[str]] = None
    ):
        self.step_id = step_id
        self.step_type = step_type
        self.config = config
        self.dependencies = dependencies or []
        self.status = ExecutionStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            'step_id': self.step_id,
            'step_type': self.step_type,
            'config': self.config,
            'dependencies': self.dependencies,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time': self.execution_time
        }


class WorkflowEngine:
    """Engine for executing workflow steps."""
    
    def __init__(
        self,
        n8n_service: N8nService,
        autogen_service: AutoGenService,
        code_execution_service: CodeExecutionService
    ):
        self.n8n_service = n8n_service
        self.autogen_service = autogen_service
        self.code_execution_service = code_execution_service
        self.settings = get_settings()
    
    async def execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> None:
        """Execute a single workflow step."""
        step.start_time = datetime.utcnow()
        step.status = ExecutionStatus.RUNNING
        
        try:
            logger.info(f"Executing workflow step: {step.step_id} ({step.step_type})")
            
            if step.step_type == "n8n_workflow":
                result = await self._execute_n8n_step(step, context)
            elif step.step_type == "autogen_agent":
                result = await self._execute_autogen_step(step, context)
            elif step.step_type == "code_execution":
                result = await self._execute_code_step(step, context)
            elif step.step_type == "data_transformation":
                result = await self._execute_transformation_step(step, context)
            elif step.step_type == "condition":
                result = await self._execute_condition_step(step, context)
            elif step.step_type == "delay":
                result = await self._execute_delay_step(step, context)
            else:
                raise ValidationError(f"Unknown step type: {step.step_type}")
            
            step.result = result
            step.status = ExecutionStatus.COMPLETED
            
            logger.info(f"Step completed: {step.step_id}")
            
        except Exception as e:
            step.error = str(e)
            step.status = ExecutionStatus.FAILED
            logger.error(f"Step failed: {step.step_id} - {e}")
            raise
        finally:
            step.end_time = datetime.utcnow()
    
    async def _execute_n8n_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute n8n workflow step."""
        workflow_id = step.config.get('workflow_id')
        if not workflow_id:
            raise ValidationError("workflow_id required for n8n_workflow step")
        
        # Prepare input data
        input_data = step.config.get('input_data', {})
        
        # Substitute context variables
        input_data = self._substitute_context_variables(input_data, context)
        
        # Execute n8n workflow
        execution = await self.n8n_service.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data
        )
        
        # Wait for completion if required
        if step.config.get('wait_for_completion', True):
            timeout = step.config.get('timeout', 300)
            result = await self.n8n_service.wait_for_execution(
                execution_id=execution['id'],
                timeout=timeout
            )
            return result
        
        return execution
    
    async def _execute_autogen_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute AutoGen agent step."""
        agent_type = step.config.get('agent_type')
        if not agent_type:
            raise ValidationError("agent_type required for autogen_agent step")
        
        # Prepare task data
        task_data = step.config.get('task_data', {})
        task_data = self._substitute_context_variables(task_data, context)
        
        # Execute agent
        timeout = step.config.get('timeout')
        result = await self.autogen_service.execute_agent(
            agent_type=agent_type,
            task_data=task_data,
            timeout=timeout
        )
        
        return result.model_dump()
    
    async def _execute_code_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute code execution step."""
        code = step.config.get('code')
        language = step.config.get('language', 'python')
        
        if not code:
            raise ValidationError("code required for code_execution step")
        
        # Substitute context variables in code
        code = self._substitute_context_variables(code, context)
        
        # Execute code
        timeout = step.config.get('timeout')
        result = await self.code_execution_service.execute_code(
            code=code,
            language=language,
            timeout=timeout
        )
        
        return result.model_dump()
    
    async def _execute_transformation_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute data transformation step."""
        transformation = step.config.get('transformation')
        input_data = step.config.get('input_data', context)
        
        if not transformation:
            raise ValidationError("transformation required for data_transformation step")
        
        # Apply transformation
        if transformation == 'json_extract':
            path = step.config.get('path')
            return self._extract_json_path(input_data, path)
        elif transformation == 'filter':
            condition = step.config.get('condition')
            return self._filter_data(input_data, condition)
        elif transformation == 'map':
            mapping = step.config.get('mapping')
            return self._map_data(input_data, mapping)
        else:
            raise ValidationError(f"Unknown transformation: {transformation}")
    
    async def _execute_condition_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute condition step."""
        condition = step.config.get('condition')
        if not condition:
            raise ValidationError("condition required for condition step")
        
        # Evaluate condition
        result = self._evaluate_condition(condition, context)
        
        return {
            'condition': condition,
            'result': result,
            'context': context
        }
    
    async def _execute_delay_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute delay step."""
        delay_seconds = step.config.get('delay_seconds', 1)
        
        await asyncio.sleep(delay_seconds)
        
        return {
            'delayed_seconds': delay_seconds,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _substitute_context_variables(self, data: Any, context: Dict[str, Any]) -> Any:
        """Substitute context variables in data."""
        if isinstance(data, str):
            # Simple variable substitution
            for key, value in context.items():
                data = data.replace(f"${{{key}}}", str(value))
            return data
        elif isinstance(data, dict):
            return {k: self._substitute_context_variables(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_context_variables(item, context) for item in data]
        else:
            return data
    
    def _extract_json_path(self, data: Any, path: str) -> Any:
        """Extract data using JSON path."""
        # Simple path extraction (e.g., "result.data.items")
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                current = current[index] if 0 <= index < len(current) else None
            else:
                return None
        
        return current
    
    def _filter_data(self, data: Any, condition: Dict[str, Any]) -> Any:
        """Filter data based on condition."""
        # Simple filtering implementation
        if not isinstance(data, list):
            return data
        
        field = condition.get('field')
        operator = condition.get('operator', 'eq')
        value = condition.get('value')
        
        filtered = []
        for item in data:
            item_value = self._extract_json_path(item, field) if field else item
            
            if operator == 'eq' and item_value == value:
                filtered.append(item)
            elif operator == 'ne' and item_value != value:
                filtered.append(item)
            elif operator == 'gt' and item_value > value:
                filtered.append(item)
            elif operator == 'lt' and item_value < value:
                filtered.append(item)
            elif operator == 'contains' and value in str(item_value):
                filtered.append(item)
        
        return filtered
    
    def _map_data(self, data: Any, mapping: Dict[str, str]) -> Any:
        """Map data fields."""
        if isinstance(data, dict):
            mapped = {}
            for new_key, old_key in mapping.items():
                mapped[new_key] = self._extract_json_path(data, old_key)
            return mapped
        elif isinstance(data, list):
            return [self._map_data(item, mapping) for item in data]
        else:
            return data
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a condition."""
        field = condition.get('field')
        operator = condition.get('operator', 'eq')
        value = condition.get('value')
        
        actual_value = self._extract_json_path(context, field) if field else context
        
        if operator == 'eq':
            return actual_value == value
        elif operator == 'ne':
            return actual_value != value
        elif operator == 'gt':
            return actual_value > value
        elif operator == 'lt':
            return actual_value < value
        elif operator == 'gte':
            return actual_value >= value
        elif operator == 'lte':
            return actual_value <= value
        elif operator == 'in':
            return actual_value in value
        elif operator == 'contains':
            return value in str(actual_value)
        else:
            return False


class WorkflowService:
    """Service for managing and executing workflows."""
    
    def __init__(
        self,
        n8n_service: N8nService,
        autogen_service: AutoGenService,
        code_execution_service: CodeExecutionService
    ):
        self.n8n_service = n8n_service
        self.autogen_service = autogen_service
        self.code_execution_service = code_execution_service
        self.engine = WorkflowEngine(
            n8n_service, autogen_service, code_execution_service
        )
        self.settings = get_settings()
        self._active_workflows: Dict[str, asyncio.Task] = {}
        self._workflow_cache = SessionCache("workflows")
    
    @log_execution_time(logger, "Workflow execution")
    async def execute_workflow(
        self,
        workflow_definition: WorkflowDefinition,
        input_data: Optional[Dict[str, Any]] = None,
        priority: Priority = Priority.MEDIUM
    ) -> WorkflowExecution:
        """Execute a workflow.
        
        Args:
            workflow_definition: Workflow definition
            input_data: Input data for the workflow
            priority: Execution priority
            
        Returns:
            Workflow execution result
        """
        execution_id = str(uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Validate workflow
            self._validate_workflow(workflow_definition)
            
            # Check execution limits
            await self._check_execution_limits()
            
            logger.info(f"Starting workflow execution: {execution_id} ({workflow_definition.name})")
            
            # Create execution context
            context = {
                'execution_id': execution_id,
                'workflow_name': workflow_definition.name,
                'start_time': start_time.isoformat(),
                'input_data': input_data or {},
                'priority': priority.value
            }
            
            # Execute workflow steps
            steps_results = await self._execute_workflow_steps(
                workflow_definition.steps,
                context
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create execution result
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_name=workflow_definition.name,
                status=ExecutionStatus.COMPLETED,
                input_data=input_data or {},
                output_data=self._extract_output_data(steps_results),
                execution_time=execution_time,
                steps_executed=len(steps_results),
                metadata={
                    'workflow_type': workflow_definition.workflow_type,
                    'priority': priority.value,
                    'steps': [step.to_dict() for step in steps_results],
                    'timestamp': start_time.isoformat()
                }
            )
            
            # Cache execution
            await self._cache_execution(execution_id, execution)
            
            logger.info(f"Workflow execution completed: {execution_id} ({execution_time:.2f}s)")
            return execution
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {execution_id} - {e}")
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return WorkflowExecution(
                execution_id=execution_id,
                workflow_name=workflow_definition.name,
                status=ExecutionStatus.FAILED,
                input_data=input_data or {},
                error=str(e),
                execution_time=execution_time,
                steps_executed=0
            )
        finally:
            # Cleanup active workflow tracking
            self._active_workflows.pop(execution_id, None)
    
    async def _execute_workflow_steps(
        self,
        steps_config: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Execute workflow steps."""
        # Create step objects
        steps = []
        for step_config in steps_config:
            step = WorkflowStep(
                step_id=step_config['id'],
                step_type=step_config['type'],
                config=step_config.get('config', {}),
                dependencies=step_config.get('dependencies', [])
            )
            steps.append(step)
        
        # Execute steps in dependency order
        executed_steps = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            # Find steps with satisfied dependencies
            ready_steps = [
                step for step in remaining_steps
                if all(
                    dep_id in [s.step_id for s in executed_steps if s.status == ExecutionStatus.COMPLETED]
                    for dep_id in step.dependencies
                )
            ]
            
            if not ready_steps:
                # Check for circular dependencies or failed dependencies
                failed_deps = [
                    step for step in executed_steps
                    if step.status == ExecutionStatus.FAILED
                ]
                if failed_deps:
                    raise WorkflowExecutionError(
                        f"Workflow failed due to failed dependencies: {[s.step_id for s in failed_deps]}"
                    )
                else:
                    raise WorkflowExecutionError("Circular dependency detected in workflow")
            
            # Execute ready steps (can be parallel if no dependencies between them)
            if len(ready_steps) == 1:
                # Single step execution
                step = ready_steps[0]
                await self.engine.execute_step(step, context)
                executed_steps.append(step)
                remaining_steps.remove(step)
                
                # Update context with step result
                if step.result:
                    context[f"step_{step.step_id}"] = step.result
            else:
                # Parallel execution of independent steps
                tasks = []
                for step in ready_steps:
                    task = asyncio.create_task(
                        self.engine.execute_step(step, context.copy())
                    )
                    tasks.append((step, task))
                
                # Wait for all tasks to complete
                for step, task in tasks:
                    try:
                        await task
                        executed_steps.append(step)
                        remaining_steps.remove(step)
                        
                        # Update context with step result
                        if step.result:
                            context[f"step_{step.step_id}"] = step.result
                    except Exception as e:
                        step.error = str(e)
                        step.status = ExecutionStatus.FAILED
                        executed_steps.append(step)
                        remaining_steps.remove(step)
        
        return executed_steps
    
    def _validate_workflow(self, workflow: WorkflowDefinition) -> None:
        """Validate workflow definition."""
        if not workflow.steps:
            raise ValidationError("Workflow must have at least one step")
        
        # Check for duplicate step IDs
        step_ids = [step['id'] for step in workflow.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValidationError("Duplicate step IDs found in workflow")
        
        # Validate step dependencies
        for step in workflow.steps:
            for dep_id in step.get('dependencies', []):
                if dep_id not in step_ids:
                    raise ValidationError(f"Unknown dependency: {dep_id} in step {step['id']}")
    
    async def _check_execution_limits(self) -> None:
        """Check if execution limits are exceeded."""
        max_concurrent = self.settings.workflow.max_concurrent_workflows
        if len(self._active_workflows) >= max_concurrent:
            raise WorkflowExecutionError(
                f"Maximum concurrent workflows exceeded: {max_concurrent}"
            )
    
    def _extract_output_data(self, steps: List[WorkflowStep]) -> Dict[str, Any]:
        """Extract output data from executed steps."""
        output = {}
        for step in steps:
            if step.result:
                output[step.step_id] = step.result
        return output
    
    async def _cache_execution(
        self,
        execution_id: str,
        execution: WorkflowExecution
    ) -> None:
        """Cache workflow execution."""
        try:
            await self._workflow_cache.set(
                execution_id,
                execution.model_dump(),
                ttl=3600  # Cache for 1 hour
            )
        except Exception as e:
            logger.warning(f"Failed to cache workflow execution: {e}")
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get cached workflow execution."""
        try:
            cached_data = await self._workflow_cache.get(execution_id)
            if cached_data:
                return WorkflowExecution(**cached_data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached execution: {e}")
        return None
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow."""
        task = self._active_workflows.get(execution_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled workflow: {execution_id}")
            return True
        return False
    
    async def get_active_workflows(self) -> List[str]:
        """Get list of active workflow execution IDs."""
        return [
            exec_id for exec_id, task in self._active_workflows.items()
            if not task.done()
        ]
    
    @cached(ttl=300, key_prefix="workflow:templates")
    async def get_workflow_templates(self) -> Dict[str, WorkflowDefinition]:
        """Get predefined workflow templates."""
        templates = {
            'code_testing': WorkflowDefinition(
                name="Code Testing Workflow",
                description="Automated code testing and validation",
                workflow_type=WorkflowType.CODE_TESTING,
                steps=[
                    {
                        'id': 'validate_code',
                        'type': 'autogen_agent',
                        'config': {
                            'agent_type': 'code_analysis',
                            'task_data': {
                                'code': '${input_data.code}',
                                'language': '${input_data.language}',
                                'analysis_type': 'security'
                            }
                        }
                    },
                    {
                        'id': 'execute_code',
                        'type': 'code_execution',
                        'config': {
                            'code': '${input_data.code}',
                            'language': '${input_data.language}',
                            'timeout': 30
                        },
                        'dependencies': ['validate_code']
                    },
                    {
                        'id': 'analyze_results',
                        'type': 'autogen_agent',
                        'config': {
                            'agent_type': 'decision_making',
                            'task_data': {
                                'scenario': 'Code execution completed',
                                'options': ['pass', 'fail', 'review'],
                                'context': {
                                    'execution_result': '${step_execute_code}',
                                    'validation_result': '${step_validate_code}'
                                }
                            }
                        },
                        'dependencies': ['execute_code']
                    }
                ]
            ),
            'data_processing': WorkflowDefinition(
                name="Data Processing Workflow",
                description="Process and transform data",
                workflow_type=WorkflowType.DATA_PROCESSING,
                steps=[
                    {
                        'id': 'extract_data',
                        'type': 'data_transformation',
                        'config': {
                            'transformation': 'json_extract',
                            'path': '${input_data.data_path}',
                            'input_data': '${input_data}'
                        }
                    },
                    {
                        'id': 'filter_data',
                        'type': 'data_transformation',
                        'config': {
                            'transformation': 'filter',
                            'condition': '${input_data.filter_condition}',
                            'input_data': '${step_extract_data}'
                        },
                        'dependencies': ['extract_data']
                    },
                    {
                        'id': 'process_data',
                        'type': 'n8n_workflow',
                        'config': {
                            'workflow_id': '${input_data.n8n_workflow_id}',
                            'input_data': '${step_filter_data}',
                            'wait_for_completion': True
                        },
                        'dependencies': ['filter_data']
                    }
                ]
            )
        }
        
        return templates
    
    async def health_check(self) -> bool:
        """Check workflow service health."""
        try:
            # Check dependent services
            n8n_healthy = await self.n8n_service.health_check()
            autogen_healthy = await self.autogen_service.health_check()
            code_exec_healthy = await self.code_execution_service.health_check()
            
            return n8n_healthy and autogen_healthy and code_exec_healthy
            
        except Exception as e:
            logger.error(f"Workflow service health check failed: {e}")
            return False
    
    async def get_usage_statistics(self) -> Dict[str, Any]:
        """Get service usage statistics."""
        return {
            'active_workflows': len(self._active_workflows),
            'max_concurrent': self.settings.workflow.max_concurrent_workflows,
            'templates_available': len(await self.get_workflow_templates()),
            'services': {
                'n8n': await self.n8n_service.health_check(),
                'autogen': await self.autogen_service.health_check(),
                'code_execution': await self.code_execution_service.health_check()
            },
            'timestamp': datetime.utcnow().isoformat()
        }


# Global service instance (will be initialized in main app)
workflow_service: Optional[WorkflowService] = None


# Convenience functions
async def init_workflow_service(
    n8n_service: N8nService,
    autogen_service: AutoGenService,
    code_execution_service: CodeExecutionService
) -> None:
    """Initialize workflow service."""
    global workflow_service
    workflow_service = WorkflowService(
        n8n_service, autogen_service, code_execution_service
    )


async def get_workflow_service() -> WorkflowService:
    """Get workflow service instance."""
    if workflow_service is None:
        raise RuntimeError("Workflow service not initialized")
    return workflow_service