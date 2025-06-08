#!/usr/bin/env python3
"""
Python Worker Service for UnityAI Platform.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import traceback

import aioredis
import structlog
from .config import settings

logger = structlog.get_logger(__name__)


class TaskStatus:
    """Task status constants."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class PythonWorkerService:
    """Main service class for Python worker operations."""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self._shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start the worker service."""
        logger.info("Starting Python Worker Service")
        
        # Initialize Redis connection
        try:
            self.redis_client = aioredis.from_url(
                settings.get_redis_url(),
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            # Continue without Redis for basic functionality
            
        # Start background task cleanup
        asyncio.create_task(self._cleanup_tasks())
        
        logger.info("Python Worker Service started successfully")
    
    async def stop(self):
        """Stop the worker service."""
        logger.info("Stopping Python Worker Service")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel running tasks
        for task_id, task in self.running_tasks.items():
            if not task.done():
                logger.info("Cancelling task", task_id=task_id)
                task.cancel()
        
        # Wait for tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Python Worker Service stopped")
    
    async def execute_task(self, task_type: str, parameters: Dict[str, Any], task_id: str = None) -> Dict[str, Any]:
        """Execute a Python task."""
        if not task_id:
            task_id = str(uuid.uuid4())
        
        logger.info("Executing task", task_id=task_id, task_type=task_type)
        
        # Store task info
        task_info = {
            "task_id": task_id,
            "task_type": task_type,
            "parameters": parameters,
            "status": TaskStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        self.task_results[task_id] = task_info
        
        # Create and start task
        task = asyncio.create_task(self._run_task(task_id, task_type, parameters))
        self.running_tasks[task_id] = task
        
        try:
            result = await task
            return {
                "task_id": task_id,
                "data": result
            }
        except Exception as e:
            logger.error("Task execution failed", task_id=task_id, error=str(e))
            raise
        finally:
            # Clean up
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    async def _run_task(self, task_id: str, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific task."""
        task_info = self.task_results[task_id]
        task_info["status"] = TaskStatus.RUNNING
        task_info["started_at"] = datetime.utcnow().isoformat()
        
        try:
            # Route to appropriate task handler
            if task_type == "data_processing":
                result = await self._handle_data_processing(parameters)
            elif task_type == "ml_inference":
                result = await self._handle_ml_inference(parameters)
            elif task_type == "web_scraping":
                result = await self._handle_web_scraping(parameters)
            elif task_type == "document_processing":
                result = await self._handle_document_processing(parameters)
            elif task_type == "image_processing":
                result = await self._handle_image_processing(parameters)
            elif task_type == "custom_script":
                result = await self._handle_custom_script(parameters)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # Update task info
            task_info["status"] = TaskStatus.COMPLETED
            task_info["completed_at"] = datetime.utcnow().isoformat()
            task_info["result"] = result
            
            logger.info("Task completed successfully", task_id=task_id)
            return result
            
        except Exception as e:
            # Update task info with error
            task_info["status"] = TaskStatus.FAILED
            task_info["completed_at"] = datetime.utcnow().isoformat()
            task_info["error"] = str(e)
            task_info["traceback"] = traceback.format_exc()
            
            logger.error("Task failed", task_id=task_id, error=str(e))
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and result."""
        return self.task_results.get(task_id)
    
    async def _handle_data_processing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data processing tasks."""
        # Example: CSV processing, data transformation, etc.
        operation = parameters.get("operation", "unknown")
        data = parameters.get("data", [])
        
        if operation == "sum":
            result = sum(data) if isinstance(data, list) else 0
        elif operation == "average":
            result = sum(data) / len(data) if data else 0
        elif operation == "count":
            result = len(data)
        else:
            result = f"Unknown operation: {operation}"
        
        return {"operation": operation, "result": result, "processed_items": len(data) if isinstance(data, list) else 0}
    
    async def _handle_ml_inference(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ML inference tasks."""
        # Example: Text classification, sentiment analysis, etc.
        model_type = parameters.get("model_type", "unknown")
        input_data = parameters.get("input_data", "")
        
        # Placeholder for actual ML inference
        if model_type == "sentiment":
            # Mock sentiment analysis
            result = {"sentiment": "positive", "confidence": 0.85}
        elif model_type == "classification":
            # Mock classification
            result = {"class": "category_a", "confidence": 0.92}
        else:
            result = {"error": f"Unknown model type: {model_type}"}
        
        return {"model_type": model_type, "prediction": result}
    
    async def _handle_web_scraping(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web scraping tasks."""
        url = parameters.get("url", "")
        selector = parameters.get("selector", "")
        
        # Placeholder for actual web scraping
        return {
            "url": url,
            "selector": selector,
            "scraped_data": ["example_data_1", "example_data_2"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_document_processing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document processing tasks."""
        document_type = parameters.get("document_type", "unknown")
        content = parameters.get("content", "")
        
        # Placeholder for actual document processing
        return {
            "document_type": document_type,
            "processed_content": f"Processed: {content[:100]}...",
            "word_count": len(content.split()) if content else 0
        }
    
    async def _handle_image_processing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle image processing tasks."""
        image_path = parameters.get("image_path", "")
        operation = parameters.get("operation", "unknown")
        
        # Placeholder for actual image processing
        return {
            "image_path": image_path,
            "operation": operation,
            "result": "Image processed successfully",
            "dimensions": {"width": 1920, "height": 1080}
        }
    
    async def _handle_custom_script(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom Python script execution."""
        script = parameters.get("script", "")
        script_args = parameters.get("args", {})
        
        # Security note: In production, this should be sandboxed
        # Placeholder for actual script execution
        return {
            "script_executed": True,
            "script_length": len(script),
            "args_count": len(script_args),
            "result": "Script executed successfully (placeholder)"
        }
    
    async def _cleanup_tasks(self):
        """Background task to clean up completed tasks."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up old task results (older than 1 hour)
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                tasks_to_remove = []
                for task_id, task_info in self.task_results.items():
                    if task_info.get("completed_at"):
                        completed_at = datetime.fromisoformat(task_info["completed_at"])
                        if completed_at < cutoff_time:
                            tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    del self.task_results[task_id]
                    logger.debug("Cleaned up old task result", task_id=task_id)
                
                # Wait before next cleanup
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error("Error in task cleanup", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute on error