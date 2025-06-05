#!/usr/bin/env python3
"""
Unity AI Domino Automation Platform - FastAPI Bridge
Verbindet Chat/Webhook-Events mit Autogen-Agents und n8n-Workflows
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import redis.asyncio as redis
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# AutoGen Core Integration
from autogen_integration import autogen_manager
from code_testing_api import setup_code_testing_routes
from code_testing_agents import code_testing_manager

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/logs/fastapi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prometheus Metrics
REQUEST_COUNT = Counter('fastapi_requests_total', 'Total FastAPI requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('fastapi_request_duration_seconds', 'FastAPI request duration')
WORKFLOW_EXECUTIONS = Counter('workflow_executions_total', 'Total workflow executions', ['status'])
AUTOGEN_DECISIONS = Counter('autogen_decisions_total', 'Total Autogen decisions', ['topic'])

# FastAPI App
app = FastAPI(
    title="Unity AI Domino Automation Platform",
    description="Event-driven automation platform with Autogen agents and n8n workflows",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup Code Testing Routes
setup_code_testing_routes(app)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
N8N_API_URL = os.getenv('N8N_API_URL', 'http://n8n:5678/api/v1')
N8N_API_KEY = os.getenv('N8N_API_KEY', '')
AUTOGEN_ENABLED = os.getenv('AUTOGEN_ENABLED', 'false').lower() == 'true'

# Redis Connection
redis_client: Optional[redis.Redis] = None

# Pydantic Models
class WebhookEvent(BaseModel):
    """Eingehende Webhook-Events"""
    source: str = Field(..., description="Event source (slack, whatsapp, web, etc.)")
    event_type: str = Field(..., description="Type of event (message, command, etc.)")
    user_id: str = Field(..., description="User identifier")
    content: str = Field(..., description="Event content/message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class AutogenDecision(BaseModel):
    """Autogen Agent Decision"""
    topic: str = Field(..., description="Identified topic/category")
    workflow_id: Optional[str] = Field(None, description="Target n8n workflow ID")
    workflow_name: str = Field(..., description="Workflow name to create/update")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence")
    reasoning: str = Field(..., description="Decision reasoning")

class WorkflowExecution(BaseModel):
    """n8n Workflow Execution"""
    execution_id: str
    workflow_id: str
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    finished_at: Optional[datetime] = None

class TopicSubscription(BaseModel):
    """Topic Subscription for Agents"""
    agent_id: str
    topics: List[str]
    webhook_url: str
    active: bool = True

# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    global redis_client
    
    try:
        # Initialize Redis connection (optional for testing)
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        try:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            await redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
        except Exception as redis_error:
            logger.warning(f"⚠️ Redis not available: {redis_error}")
            redis_client = None
        
        # Initialize AutoGen Core if enabled
        if os.getenv('AUTOGEN_ENABLED', 'false').lower() == 'true':
            try:
                await autogen_manager.initialize()
                logger.info("✅ AutoGen Core initialized")
            except Exception as autogen_error:
                logger.warning(f"⚠️ AutoGen Core initialization failed: {autogen_error}")
        
        # Initialize Code Testing Manager (disabled for now due to AutoGen issues)
        # await code_testing_manager.initialize()
        logger.info("⚠️ Code Testing Manager initialization skipped")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_client
    
    # Shutdown AutoGen Core
    if AUTOGEN_ENABLED:
        try:
            await autogen_manager.shutdown()
            logger.info("🤖 AutoGen Core shutdown complete")
        except Exception as e:
            logger.warning(f"⚠️ AutoGen shutdown error: {e}")
    
    # Shutdown Code Testing Manager
    try:
        await code_testing_manager.shutdown()
        logger.info("🧪 Code Testing Manager shutdown complete")
    except Exception as e:
        logger.warning(f"⚠️ Code Testing Manager shutdown error: {e}")
    
    # Close Redis connection
    if redis_client:
        await redis_client.close()
        logger.info("🛑 Redis connection closed")
    
    logger.info("👋 Unity AI FastAPI shutdown complete")

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "redis": "connected" if redis_client else "disconnected",
        "autogen": "enabled" if AUTOGEN_ENABLED else "disabled"
    }
    return status

# Metrics Endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Main Event Processing Endpoint
@app.post("/decide")
async def decide_endpoint(event: WebhookEvent, background_tasks: BackgroundTasks):
    """Hauptendpoint für eingehende Events - Autogen Decision Engine"""
    REQUEST_COUNT.labels(method="POST", endpoint="/decide").inc()
    
    with REQUEST_DURATION.time():
        try:
            logger.info(f"📨 Received event from {event.source}: {event.event_type}")
            
            # Event in Redis Stream speichern
            if redis_client:
                await redis_client.xadd(
                    "events:incoming",
                    {
                        "source": event.source,
                        "event_type": event.event_type,
                        "user_id": event.user_id,
                        "content": event.content,
                        "metadata": json.dumps(event.metadata),
                        "timestamp": event.timestamp.isoformat()
                    }
                )
            
            # Autogen Decision (Mock Implementation)
            decision = await make_autogen_decision(event)
            AUTOGEN_DECISIONS.labels(topic=decision.topic).inc()
            
            # Workflow ausführen
            background_tasks.add_task(execute_workflow, decision, event)
            
            return {
                "status": "accepted",
                "event_id": f"{event.source}_{event.user_id}_{int(event.timestamp.timestamp())}",
                "decision": decision.dict(),
                "message": "Event wird verarbeitet"
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing event: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Workflow Callback Endpoint
@app.post("/callback/{execution_id}")
async def workflow_callback(execution_id: str, execution: WorkflowExecution):
    """Callback für n8n Workflow-Ergebnisse"""
    REQUEST_COUNT.labels(method="POST", endpoint="/callback").inc()
    
    try:
        logger.info(f"📋 Workflow callback: {execution_id} - {execution.status}")
        WORKFLOW_EXECUTIONS.labels(status=execution.status).inc()
        
        # Ergebnis in Redis Stream speichern
        if redis_client:
            await redis_client.xadd(
                "workflows:results",
                {
                    "execution_id": execution_id,
                    "workflow_id": execution.workflow_id,
                    "status": execution.status,
                    "data": json.dumps(execution.data),
                    "finished_at": execution.finished_at.isoformat() if execution.finished_at else ""
                }
            )
        
        # Weitere Domino-Schritte triggern
        if execution.status == "success":
            await trigger_domino_steps(execution)
        
        return {"status": "received", "execution_id": execution_id}
        
    except Exception as e:
        logger.error(f"❌ Error processing callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Topic Management
@app.post("/topics/subscribe")
async def subscribe_to_topics(subscription: TopicSubscription):
    """Agent für Topics registrieren"""
    REQUEST_COUNT.labels(method="POST", endpoint="/topics/subscribe").inc()
    
    try:
        if redis_client:
            await redis_client.hset(
                f"subscriptions:{subscription.agent_id}",
                mapping={
                    "topics": json.dumps(subscription.topics),
                    "webhook_url": subscription.webhook_url,
                    "active": str(subscription.active)
                }
            )
        
        logger.info(f"📡 Agent {subscription.agent_id} subscribed to topics: {subscription.topics}")
        return {"status": "subscribed", "agent_id": subscription.agent_id}
        
    except Exception as e:
        logger.error(f"❌ Error subscribing to topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/topics")
async def list_topics():
    """Verfügbare Topics auflisten"""
    # Mock Topics - in Realität aus Autogen-Konfiguration
    topics = [
        "customer_support",
        "data_analysis",
        "content_generation",
        "workflow_automation",
        "system_monitoring",
        "report_generation"
    ]
    return {"topics": topics}

# Helper Functions
async def make_autogen_decision(event: WebhookEvent) -> AutogenDecision:
    """Make an AI decision using AutoGen Core or fallback to keyword-based logic"""
    
    event_data = {
        'content': event.content,
        'source': event.source,
        'user_id': event.user_id,
        'metadata': event.metadata
    }
    
    if AUTOGEN_ENABLED:
        try:
            # Use real AutoGen Core for decision making
            decision_data = await autogen_manager.make_decision(event_data)
            logger.info(f"🤖 AutoGen decision: {decision_data['topic']} (confidence: {decision_data['confidence']:.2f})")
            
            return AutogenDecision(
                topic=decision_data['topic'],
                workflow_name=decision_data['workflow_name'],
                workflow_id=decision_data.get('workflow_id'),
                parameters=decision_data['parameters'],
                confidence=decision_data['confidence'],
                reasoning=decision_data['reasoning']
            )
        except Exception as e:
            logger.warning(f"⚠️ AutoGen decision failed, using fallback: {e}")
    
    # Fallback to keyword-based decision
    content_lower = event.content.lower()
    
    if any(word in content_lower for word in ["help", "support", "problem", "issue"]):
        topic = "customer_support"
        workflow_name = "customer_support_workflow"
        confidence = 0.85
    elif any(word in content_lower for word in ["analyze", "data", "report", "statistics"]):
        topic = "data_analysis"
        workflow_name = "data_analysis_workflow"
        confidence = 0.90
    elif any(word in content_lower for word in ["create", "generate", "write", "content"]):
        topic = "content_generation"
        workflow_name = "content_generation_workflow"
        confidence = 0.80
    elif any(word in content_lower for word in ["automate", "workflow", "process"]):
        topic = "workflow_automation"
        workflow_name = "workflow_automation"
        confidence = 0.75
    else:
        topic = "general"
        workflow_name = "general_workflow"
        confidence = 0.60
    
    return AutogenDecision(
        topic=topic,
        workflow_name=workflow_name,
        parameters={
            "user_input": event.content,
            "source": event.source,
            "user_id": event.user_id,
            "metadata": event.metadata,
            "priority": "normal"
        },
        confidence=confidence,
        reasoning=f"Keyword-based classification detected {topic} intent"
    )

async def execute_workflow(decision: AutogenDecision, event: WebhookEvent):
    """n8n Workflow ausführen"""
    try:
        # n8n API Call
        async with httpx.AsyncClient() as client:
            headers = {"X-N8N-API-KEY": N8N_API_KEY} if N8N_API_KEY else {}
            
            # Workflow-Execution starten
            response = await client.post(
                f"{N8N_API_URL}/workflows/{decision.workflow_name}/execute",
                json={
                    "data": decision.parameters
                },
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Workflow {decision.workflow_name} executed successfully")
                WORKFLOW_EXECUTIONS.labels(status="success").inc()
            else:
                logger.error(f"❌ Workflow execution failed: {response.status_code}")
                WORKFLOW_EXECUTIONS.labels(status="failed").inc()
                
    except Exception as e:
        logger.error(f"❌ Error executing workflow: {e}")
        WORKFLOW_EXECUTIONS.labels(status="error").inc()

async def trigger_domino_steps(execution: WorkflowExecution):
    """Domino-Folgeschritte basierend auf Workflow-Ergebnis"""
    try:
        # Analyse der Workflow-Ergebnisse für weitere Schritte
        if "next_action" in execution.data:
            next_action = execution.data["next_action"]
            logger.info(f"🎯 Triggering domino step: {next_action}")
            
            # Weitere Workflows oder Notifications triggern
            # Implementation abhängig von Business Logic
            
    except Exception as e:
        logger.error(f"❌ Error triggering domino steps: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )