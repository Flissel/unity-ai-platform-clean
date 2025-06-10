#!/usr/bin/env python3
"""
n8n API Playground Manager for UnityAI Platform

Central coordination component for all n8n API Playground operations.
Manages workflow execution, module coordination, and system integration.

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel, Field

from .api_client import N8nApiClient, create_n8n_client
from .workflow_executor import WorkflowExecutor
from .response_handler import ResponseHandler
from .config import N8nApiConfig

# Setup structured logging
logger = structlog.get_logger(__name__)


class PlaygroundSession(BaseModel):
    """Represents an active playground session."""
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    module_name: str
    workflow_name: str
    status: str = "active"  # active, completed, failed, timeout
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    results: List[Dict[str, Any]] = Field(default_factory=list)


class PlaygroundConfig(BaseModel):
    """Configuration for playground manager."""
    
    n8n_config: N8nApiConfig
    modules_path: str = Field(default="modules")
    templates_path: str = Field(default="templates")
    max_concurrent_sessions: int = Field(default=10)
    session_timeout: int = Field(default=3600)  # 1 hour
    auto_cleanup: bool = Field(default=True)
    enable_caching: bool = Field(default=True)


class PlaygroundManager:
    """Main playground manager class."""
    
    def __init__(self, config: PlaygroundConfig):
        self.config = config
        self.api_client: Optional[N8nApiClient] = None
        self.workflow_executor: Optional[WorkflowExecutor] = None
        self.response_handler: Optional[ResponseHandler] = None
        
        # Session management
        self.active_sessions: Dict[str, PlaygroundSession] = {}
        self.session_results: Dict[str, List[Dict[str, Any]]] = {}
        
        # Module registry
        self.registered_modules: Dict[str, Dict[str, Any]] = {}
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.execution_stats: Dict[str, Any] = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "average_execution_time": 0.0
        }
    
    async def start(self):
        """Initialize the playground manager."""
        logger.info("Starting n8n API Playground Manager")
        
        # Initialize API client
        self.api_client = N8nApiClient(self.config.n8n_config)
        await self.api_client.start()
        
        # Test connection
        if not await self.api_client.test_connection():
            raise ConnectionError("Failed to connect to n8n API")
        
        # Initialize components
        self.workflow_executor = WorkflowExecutor(self.api_client)
        self.response_handler = ResponseHandler()
        
        # Load modules and templates
        await self._load_modules()
        await self._load_templates()
        
        # Start cleanup task if enabled
        if self.config.auto_cleanup:
            asyncio.create_task(self._cleanup_sessions())
        
        logger.info(
            "Playground manager started successfully",
            modules_count=len(self.registered_modules),
            templates_count=len(self.workflow_templates)
        )
    
    async def stop(self):
        """Stop the playground manager."""
        logger.info("Stopping n8n API Playground Manager")
        
        # Cancel all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.cancel_session(session_id)
        
        # Close API client
        if self.api_client:
            await self.api_client.close()
        
        logger.info("Playground manager stopped")
    
    async def create_session(
        self,
        module_name: str,
        workflow_name: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PlaygroundSession:
        """Create a new playground session."""
        
        # Check concurrent session limit
        if len(self.active_sessions) >= self.config.max_concurrent_sessions:
            raise RuntimeError("Maximum concurrent sessions reached")
        
        # Validate module and workflow
        if module_name not in self.registered_modules:
            raise ValueError(f"Module '{module_name}' not found")
        
        if workflow_name not in self.workflow_templates:
            raise ValueError(f"Workflow template '{workflow_name}' not found")
        
        # Create session
        session = PlaygroundSession(
            user_id=user_id,
            module_name=module_name,
            workflow_name=workflow_name,
            metadata=metadata or {}
        )
        
        self.active_sessions[session.session_id] = session
        self.session_results[session.session_id] = []
        
        logger.info(
            "Playground session created",
            session_id=session.session_id,
            module_name=module_name,
            workflow_name=workflow_name,
            user_id=user_id
        )
        
        return session
    
    async def execute_workflow(
        self,
        session_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """Execute workflow in playground session."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session '{session_id}' not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Get workflow template
            template = self.workflow_templates[session.workflow_name]
            
            # Execute workflow
            start_time = datetime.utcnow()
            
            result = await self.workflow_executor.execute(
                template=template,
                parameters=parameters or {},
                session_id=session_id,
                wait_for_completion=wait_for_completion
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Process result
            processed_result = await self.response_handler.process_response(
                result,
                session_id=session_id,
                execution_time=execution_time
            )
            
            # Update session
            session.updated_at = datetime.utcnow()
            session.results.append(processed_result)
            self.session_results[session_id].append(processed_result)
            
            # Update stats
            self._update_execution_stats(True, execution_time)
            
            logger.info(
                "Workflow executed successfully",
                session_id=session_id,
                workflow_name=session.workflow_name,
                execution_time=execution_time
            )
            
            return processed_result
        
        except Exception as e:
            # Update session status
            session.status = "failed"
            session.updated_at = datetime.utcnow()
            
            # Update stats
            self._update_execution_stats(False, 0)
            
            logger.error(
                "Workflow execution failed",
                session_id=session_id,
                workflow_name=session.workflow_name,
                error=str(e)
            )
            
            raise
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of playground session."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session '{session_id}' not found")
        
        session = self.active_sessions[session_id]
        results = self.session_results.get(session_id, [])
        
        return {
            "session_id": session.session_id,
            "status": session.status,
            "module_name": session.module_name,
            "workflow_name": session.workflow_name,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "results_count": len(results),
            "latest_result": results[-1] if results else None,
            "metadata": session.metadata
        }
    
    async def get_session_results(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get results from playground session."""
        
        if session_id not in self.session_results:
            raise ValueError(f"Session '{session_id}' not found")
        
        results = self.session_results[session_id]
        
        if limit:
            return results[-limit:]
        
        return results
    
    async def cancel_session(self, session_id: str) -> bool:
        """Cancel active playground session."""
        
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.status = "cancelled"
        session.updated_at = datetime.utcnow()
        
        # Clean up
        del self.active_sessions[session_id]
        
        logger.info(
            "Playground session cancelled",
            session_id=session_id,
            module_name=session.module_name,
            workflow_name=session.workflow_name
        )
        
        return True
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active playground sessions."""
        
        sessions = []
        for session in self.active_sessions.values():
            sessions.append({
                "session_id": session.session_id,
                "module_name": session.module_name,
                "workflow_name": session.workflow_name,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "user_id": session.user_id
            })
        
        return sessions
    
    async def get_available_modules(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available modules."""
        return self.registered_modules.copy()
    
    async def get_available_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available workflow templates."""
        return self.workflow_templates.copy()
    
    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self.execution_stats.copy()
    
    # Private methods
    async def _load_modules(self):
        """Load available modules from filesystem."""
        modules_path = Path(self.config.modules_path)
        
        if not modules_path.exists():
            logger.warning("Modules path does not exist", path=str(modules_path))
            return
        
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir():
                await self._load_module(module_dir)
    
    async def _load_module(self, module_path: Path):
        """Load individual module."""
        try:
            # Look for SYSTEM_INSTRUCTIONS.md
            instructions_file = module_path / "SYSTEM_INSTRUCTIONS.md"
            if instructions_file.exists():
                with open(instructions_file, 'r', encoding='utf-8') as f:
                    instructions = f.read()
                
                self.registered_modules[module_path.name] = {
                    "name": module_path.name,
                    "path": str(module_path),
                    "instructions": instructions,
                    "loaded_at": datetime.utcnow().isoformat()
                }
                
                logger.debug("Module loaded", module_name=module_path.name)
        
        except Exception as e:
            logger.error(
                "Failed to load module",
                module_path=str(module_path),
                error=str(e)
            )
    
    async def _load_templates(self):
        """Load workflow templates from filesystem."""
        templates_path = Path(self.config.templates_path)
        
        if not templates_path.exists():
            logger.warning("Templates path does not exist", path=str(templates_path))
            return
        
        for template_file in templates_path.rglob("*.json"):
            await self._load_template(template_file)
    
    async def _load_template(self, template_path: Path):
        """Load individual workflow template."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            template_name = template_path.stem
            self.workflow_templates[template_name] = template_data
            
            logger.debug("Template loaded", template_name=template_name)
        
        except Exception as e:
            logger.error(
                "Failed to load template",
                template_path=str(template_path),
                error=str(e)
            )
    
    async def _cleanup_sessions(self):
        """Periodic cleanup of expired sessions."""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    session_age = (current_time - session.created_at).total_seconds()
                    if session_age > self.config.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.cancel_session(session_id)
                    logger.info("Expired session cleaned up", session_id=session_id)
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
            
            except Exception as e:
                logger.error("Error in session cleanup", error=str(e))
                await asyncio.sleep(60)  # Retry after 1 minute
    
    def _update_execution_stats(self, success: bool, execution_time: float):
        """Update execution statistics."""
        self.execution_stats["total_sessions"] += 1
        
        if success:
            self.execution_stats["successful_sessions"] += 1
        else:
            self.execution_stats["failed_sessions"] += 1
        
        # Update average execution time
        total = self.execution_stats["total_sessions"]
        current_avg = self.execution_stats["average_execution_time"]
        new_avg = ((current_avg * (total - 1)) + execution_time) / total
        self.execution_stats["average_execution_time"] = new_avg


# Factory function
def create_playground_manager(
    n8n_base_url: str,
    n8n_api_key: str,
    modules_path: str = "modules",
    templates_path: str = "templates"
) -> PlaygroundManager:
    """Factory function to create playground manager."""
    
    n8n_config = N8nApiConfig(
        base_url=n8n_base_url,
        api_key=n8n_api_key
    )
    
    config = PlaygroundConfig(
        n8n_config=n8n_config,
        modules_path=modules_path,
        templates_path=templates_path
    )
    
    return PlaygroundManager(config)