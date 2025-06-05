"""AutoGen service for AI agent management and execution."""

import asyncio
from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime
from uuid import uuid4

from autogen_core.base import MessageContext
from autogen_core.components import DefaultTopicId, RoutedAgent, message_handler
from autogen_core.components.models import (
    OpenAIChatCompletionClient,
    UserMessage,
    AssistantMessage,
    SystemMessage
)
from autogen_ext.models import OpenAIClientConfiguration

from ..core.config import get_settings
from ..core.logging import get_logger, log_execution_time
from ..core.exceptions import AutoGenError, ValidationError, TimeoutError
from ..core.models import AgentRequest, AgentResponse
from ..core.cache import cached, SessionCache

logger = get_logger(__name__)


class CodeAnalysisAgent(RoutedAgent):
    """Agent for code analysis and testing."""
    
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__("Code Analysis Agent")
        self._model_client = model_client
        self._system_prompt = """
        You are an expert code analysis agent. Your role is to:
        1. Analyze code for potential issues, bugs, and improvements
        2. Suggest optimizations and best practices
        3. Provide detailed explanations of code functionality
        4. Generate test cases and validation scenarios
        
        Always provide structured, actionable feedback with specific examples.
        """
    
    @message_handler
    async def handle_analysis_request(self, message: Dict[str, Any], ctx: MessageContext) -> Dict[str, Any]:
        """Handle code analysis requests."""
        try:
            code = message.get("code", "")
            language = message.get("language", "python")
            analysis_type = message.get("analysis_type", "general")
            
            if not code:
                raise ValidationError("Code is required for analysis")
            
            # Prepare messages for the model
            messages = [
                SystemMessage(content=self._system_prompt),
                UserMessage(content=f"""
                Please analyze the following {language} code:
                
                ```{language}
                {code}
                ```
                
                Analysis type: {analysis_type}
                
                Provide a detailed analysis including:
                1. Code quality assessment
                2. Potential issues or bugs
                3. Performance considerations
                4. Security implications
                5. Suggested improvements
                6. Test case recommendations
                """)
            ]
            
            # Get response from model
            response = await self._model_client.create(
                messages=messages,
                max_tokens=1500,
                temperature=0.3
            )
            
            analysis_result = response.content
            
            return {
                "success": True,
                "analysis": analysis_result,
                "code": code,
                "language": language,
                "analysis_type": analysis_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class DecisionMakingAgent(RoutedAgent):
    """Agent for intelligent decision making."""
    
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__("Decision Making Agent")
        self._model_client = model_client
        self._system_prompt = """
        You are an intelligent decision-making agent. Your role is to:
        1. Analyze complex scenarios and provide recommendations
        2. Evaluate multiple options and their trade-offs
        3. Consider risks, benefits, and constraints
        4. Provide structured decision frameworks
        
        Always provide clear reasoning and confidence scores for your recommendations.
        """
    
    @message_handler
    async def handle_decision_request(self, message: Dict[str, Any], ctx: MessageContext) -> Dict[str, Any]:
        """Handle decision-making requests."""
        try:
            scenario = message.get("scenario", "")
            options = message.get("options", [])
            criteria = message.get("criteria", [])
            context = message.get("context", {})
            
            if not scenario:
                raise ValidationError("Scenario description is required")
            
            # Prepare decision analysis prompt
            prompt_parts = [f"Scenario: {scenario}"]
            
            if options:
                prompt_parts.append("\nAvailable options:")
                for i, option in enumerate(options, 1):
                    prompt_parts.append(f"{i}. {option}")
            
            if criteria:
                prompt_parts.append("\nDecision criteria:")
                for criterion in criteria:
                    prompt_parts.append(f"- {criterion}")
            
            if context:
                prompt_parts.append("\nAdditional context:")
                for key, value in context.items():
                    prompt_parts.append(f"- {key}: {value}")
            
            prompt_parts.append("""
            
            Please provide:
            1. Analysis of each option
            2. Recommended decision with reasoning
            3. Risk assessment
            4. Confidence score (0-1)
            5. Alternative considerations
            """)
            
            messages = [
                SystemMessage(content=self._system_prompt),
                UserMessage(content="\n".join(prompt_parts))
            ]
            
            # Get response from model
            response = await self._model_client.create(
                messages=messages,
                max_tokens=1200,
                temperature=0.4
            )
            
            decision_result = response.content
            
            return {
                "success": True,
                "decision": decision_result,
                "scenario": scenario,
                "options": options,
                "criteria": criteria,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Decision making failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class WorkflowOptimizationAgent(RoutedAgent):
    """Agent for workflow optimization and automation."""
    
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__("Workflow Optimization Agent")
        self._model_client = model_client
        self._system_prompt = """
        You are a workflow optimization expert. Your role is to:
        1. Analyze existing workflows for inefficiencies
        2. Suggest automation opportunities
        3. Recommend process improvements
        4. Design optimized workflow structures
        
        Focus on practical, implementable solutions that improve efficiency and reliability.
        """
    
    @message_handler
    async def handle_optimization_request(self, message: Dict[str, Any], ctx: MessageContext) -> Dict[str, Any]:
        """Handle workflow optimization requests."""
        try:
            workflow_description = message.get("workflow", "")
            current_issues = message.get("issues", [])
            goals = message.get("goals", [])
            constraints = message.get("constraints", [])
            
            if not workflow_description:
                raise ValidationError("Workflow description is required")
            
            # Prepare optimization analysis prompt
            prompt_parts = [f"Current workflow: {workflow_description}"]
            
            if current_issues:
                prompt_parts.append("\nCurrent issues:")
                for issue in current_issues:
                    prompt_parts.append(f"- {issue}")
            
            if goals:
                prompt_parts.append("\nOptimization goals:")
                for goal in goals:
                    prompt_parts.append(f"- {goal}")
            
            if constraints:
                prompt_parts.append("\nConstraints:")
                for constraint in constraints:
                    prompt_parts.append(f"- {constraint}")
            
            prompt_parts.append("""
            
            Please provide:
            1. Workflow analysis and bottleneck identification
            2. Optimization recommendations
            3. Automation opportunities
            4. Implementation roadmap
            5. Expected benefits and metrics
            """)
            
            messages = [
                SystemMessage(content=self._system_prompt),
                UserMessage(content="\n".join(prompt_parts))
            ]
            
            # Get response from model
            response = await self._model_client.create(
                messages=messages,
                max_tokens=1500,
                temperature=0.3
            )
            
            optimization_result = response.content
            
            return {
                "success": True,
                "optimization": optimization_result,
                "workflow": workflow_description,
                "issues": current_issues,
                "goals": goals,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow optimization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class AutoGenService:
    """Service for managing AutoGen agents and executions."""
    
    def __init__(self):
        self.settings = get_settings()
        self._model_client: Optional[OpenAIChatCompletionClient] = None
        self._agents: Dict[str, RoutedAgent] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize AutoGen service."""
        if self._initialized:
            return
        
        try:
            if not self.settings.autogen.enabled:
                logger.info("AutoGen service is disabled")
                return
            
            # Initialize OpenAI client
            config = OpenAIClientConfiguration(
                api_key=self.settings.openai_api_key,
                model=self.settings.autogen.model
            )
            
            self._model_client = OpenAIChatCompletionClient(
                **config.model_dump(),
                model_capabilities={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True
                }
            )
            
            # Initialize agents
            self._agents = {
                "code_analysis": CodeAnalysisAgent(self._model_client),
                "decision_making": DecisionMakingAgent(self._model_client),
                "workflow_optimization": WorkflowOptimizationAgent(self._model_client)
            }
            
            self._initialized = True
            logger.info("AutoGen service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AutoGen service: {e}")
            raise AutoGenError(f"AutoGen service initialization failed: {e}")
    
    async def close(self) -> None:
        """Close AutoGen service."""
        self._agents.clear()
        self._model_client = None
        self._initialized = False
        logger.info("AutoGen service closed")
    
    async def _ensure_initialized(self) -> None:
        """Ensure service is initialized."""
        if not self._initialized:
            await self.initialize()
    
    @log_execution_time(logger, "AutoGen agent execution")
    async def execute_agent(
        self,
        agent_type: str,
        task_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> AgentResponse:
        """Execute an agent with the given task.
        
        Args:
            agent_type: Type of agent to execute
            task_data: Task data for the agent
            timeout: Execution timeout in seconds
            
        Returns:
            Agent execution response
        """
        await self._ensure_initialized()
        
        if not self.settings.autogen.enabled:
            raise AutoGenError("AutoGen service is disabled")
        
        if agent_type not in self._agents:
            raise ValidationError(f"Unknown agent type: {agent_type}")
        
        try:
            agent = self._agents[agent_type]
            execution_timeout = timeout or self.settings.autogen.timeout
            
            # Create execution context
            execution_id = str(uuid4())
            start_time = datetime.utcnow()
            
            logger.info(f"Starting agent execution: {agent_type} (ID: {execution_id})")
            
            # Execute agent with timeout
            result = await asyncio.wait_for(
                self._execute_agent_task(agent, task_data),
                timeout=execution_timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract confidence score if available
            confidence = None
            if isinstance(result, dict) and "confidence" in result:
                confidence = result["confidence"]
            
            response = AgentResponse(
                success=result.get("success", True) if isinstance(result, dict) else True,
                result=result,
                reasoning=result.get("reasoning") if isinstance(result, dict) else None,
                confidence=confidence,
                execution_time=execution_time,
                metadata={
                    "agent_type": agent_type,
                    "execution_id": execution_id,
                    "model": self.settings.autogen.model,
                    "timestamp": start_time.isoformat()
                }
            )
            
            logger.info(f"Agent execution completed: {execution_id} ({execution_time:.2f}s)")
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Agent execution timed out: {agent_type}")
            raise TimeoutError(f"Agent execution timed out after {execution_timeout}s")
        except Exception as e:
            logger.error(f"Agent execution failed: {agent_type} - {e}")
            raise AutoGenError(f"Agent execution failed: {e}")
    
    async def _execute_agent_task(self, agent: RoutedAgent, task_data: Dict[str, Any]) -> Any:
        """Execute agent task."""
        # Create message context
        ctx = MessageContext(sender=DefaultTopicId())
        
        # Execute agent handler based on agent type
        if isinstance(agent, CodeAnalysisAgent):
            return await agent.handle_analysis_request(task_data, ctx)
        elif isinstance(agent, DecisionMakingAgent):
            return await agent.handle_decision_request(task_data, ctx)
        elif isinstance(agent, WorkflowOptimizationAgent):
            return await agent.handle_optimization_request(task_data, ctx)
        else:
            raise AutoGenError(f"Unknown agent type: {type(agent)}")
    
    @cached(ttl=600, key_prefix="autogen:capabilities")
    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get available agent capabilities."""
        await self._ensure_initialized()
        
        capabilities = {
            "enabled": self.settings.autogen.enabled,
            "model": self.settings.autogen.model,
            "agents": {
                "code_analysis": {
                    "description": "Analyzes code for quality, bugs, and improvements",
                    "inputs": ["code", "language", "analysis_type"],
                    "outputs": ["analysis", "recommendations", "test_cases"]
                },
                "decision_making": {
                    "description": "Provides intelligent decision recommendations",
                    "inputs": ["scenario", "options", "criteria", "context"],
                    "outputs": ["recommendation", "reasoning", "confidence"]
                },
                "workflow_optimization": {
                    "description": "Optimizes workflows and suggests automation",
                    "inputs": ["workflow", "issues", "goals", "constraints"],
                    "outputs": ["optimization", "automation", "roadmap"]
                }
            },
            "limits": {
                "max_tokens": self.settings.autogen.max_tokens,
                "timeout": self.settings.autogen.timeout,
                "temperature": self.settings.autogen.temperature
            }
        }
        
        return capabilities
    
    async def health_check(self) -> bool:
        """Check AutoGen service health."""
        try:
            await self._ensure_initialized()
            
            if not self.settings.autogen.enabled:
                return True  # Service is "healthy" when disabled
            
            # Test with a simple request
            test_result = await self.execute_agent(
                "code_analysis",
                {
                    "code": "print('hello world')",
                    "language": "python",
                    "analysis_type": "basic"
                },
                timeout=10
            )
            
            return test_result.success
            
        except Exception as e:
            logger.error(f"AutoGen health check failed: {e}")
            return False
    
    async def get_usage_statistics(self) -> Dict[str, Any]:
        """Get service usage statistics."""
        # This would typically come from a database or metrics store
        # For now, return basic information
        return {
            "enabled": self.settings.autogen.enabled,
            "agents_available": len(self._agents),
            "model": self.settings.autogen.model,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global service instance
autogen_service = AutoGenService()


# Convenience functions
async def init_autogen_service() -> None:
    """Initialize AutoGen service."""
    await autogen_service.initialize()


async def close_autogen_service() -> None:
    """Close AutoGen service."""
    await autogen_service.close()