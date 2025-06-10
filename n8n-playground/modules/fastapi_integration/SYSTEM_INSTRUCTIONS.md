# FastAPI Integration Module - System Instructions

## Module Overview

**Purpose**: Seamless integration between the n8n API Playground and the existing UnityAI FastAPI application, providing bidirectional communication, webhook handling, and API orchestration.

**Module Name**: `fastapi_integration`  
**Version**: 1.0.0  
**Author**: UnityAI Team  
**Dependencies**: FastAPI, Pydantic, aiohttp, structlog, Redis

## Core Responsibilities

### 1. API Bridge
- **Bidirectional Communication**: Enable n8n workflows to call UnityAI FastAPI endpoints
- **Request Forwarding**: Forward n8n requests to appropriate FastAPI endpoints
- **Response Transformation**: Convert FastAPI responses to n8n-compatible formats
- **Authentication Handling**: Manage API keys and authentication between systems

### 2. Webhook Management
- **Webhook Registration**: Register and manage webhook endpoints for n8n
- **Event Processing**: Process incoming webhook events from n8n workflows
- **Callback Handling**: Handle workflow completion callbacks
- **Event Routing**: Route webhook events to appropriate handlers

### 3. Task Orchestration
- **Task Triggering**: Trigger n8n workflows from FastAPI endpoints
- **Status Monitoring**: Monitor workflow execution status
- **Result Collection**: Collect and process workflow results
- **Error Handling**: Handle workflow errors and failures

### 4. Data Synchronization
- **State Management**: Synchronize state between FastAPI and n8n
- **Data Transformation**: Transform data between different formats
- **Cache Management**: Cache frequently accessed data
- **Event Streaming**: Stream real-time events between systems

## File Structure

```
modules/fastapi_integration/
├── SYSTEM_INSTRUCTIONS.md     # This file
├── __init__.py                # Module exports
├── api_bridge.py              # Main API bridge component
├── webhook_handler.py         # Webhook management
├── task_orchestrator.py       # Task orchestration
├── data_transformer.py        # Data transformation utilities
├── models.py                  # Pydantic models
├── api.py                     # FastAPI endpoints
├── config.py                  # Module configuration
├── exceptions.py              # Custom exceptions
├── middleware.py              # FastAPI middleware
├── utils.py                   # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_api_bridge.py
│   ├── test_webhook_handler.py
│   ├── test_task_orchestrator.py
│   └── test_integration.py
└── docs/
    ├── api_reference.md
    ├── webhook_guide.md
    └── integration_examples.md
```

## Implementation Guidelines

### 1. Code Standards
- **Python Version**: 3.9+
- **Type Hints**: Mandatory for all functions and methods
- **Docstrings**: Google-style docstrings for all public methods
- **Error Handling**: Comprehensive error handling with structured logging
- **Async/Await**: Use async/await for all I/O operations

### 2. Data Models
- **Pydantic Models**: Use Pydantic for all data validation
- **Serialization**: JSON serialization for API communication
- **Validation**: Input validation for all external data
- **Type Safety**: Strict type checking and validation

### 3. Error Handling
- **Custom Exceptions**: Define module-specific exceptions
- **Error Propagation**: Proper error propagation and logging
- **Retry Logic**: Implement retry mechanisms for transient failures
- **Circuit Breaker**: Implement circuit breaker pattern for external calls

### 4. Testing Requirements
- **Unit Tests**: 90%+ code coverage
- **Integration Tests**: Test integration with FastAPI and n8n
- **Mock Testing**: Mock external dependencies
- **Performance Tests**: Test under load conditions

## API Bridge Specifications

### Core Components

#### 1. ApiBridge Class
```python
class ApiBridge:
    """Main API bridge for FastAPI-n8n integration."""
    
    async def forward_request(self, request: BridgeRequest) -> BridgeResponse
    async def call_fastapi_endpoint(self, endpoint: str, data: dict) -> dict
    async def trigger_n8n_workflow(self, workflow_id: str, data: dict) -> dict
    async def health_check(self) -> bool
```

#### 2. Request/Response Models
```python
class BridgeRequest(BaseModel):
    source: str  # 'fastapi' or 'n8n'
    target_endpoint: str
    method: str
    headers: Dict[str, str]
    data: Optional[Dict[str, Any]]
    authentication: Optional[AuthInfo]

class BridgeResponse(BaseModel):
    status_code: int
    headers: Dict[str, str]
    data: Optional[Dict[str, Any]]
    execution_time: float
    success: bool
```

### Authentication
- **API Key Management**: Secure storage and rotation of API keys
- **Token Validation**: Validate incoming requests
- **Permission Checking**: Check permissions for requested operations
- **Rate Limiting**: Implement rate limiting for API calls

## Webhook Handler Specifications

### Core Components

#### 1. WebhookHandler Class
```python
class WebhookHandler:
    """Handle webhook events from n8n workflows."""
    
    async def register_webhook(self, webhook_config: WebhookConfig) -> str
    async def process_webhook(self, webhook_id: str, data: dict) -> dict
    async def unregister_webhook(self, webhook_id: str) -> bool
    async def list_webhooks(self) -> List[WebhookInfo]
```

#### 2. Webhook Models
```python
class WebhookConfig(BaseModel):
    name: str
    url: str
    method: str = 'POST'
    headers: Dict[str, str] = {}
    authentication: Optional[AuthInfo]
    retry_config: Optional[RetryConfig]

class WebhookEvent(BaseModel):
    webhook_id: str
    timestamp: datetime
    data: Dict[str, Any]
    source_workflow: Optional[str]
    event_type: str
```

### Event Processing
- **Event Validation**: Validate incoming webhook events
- **Event Routing**: Route events to appropriate handlers
- **Event Storage**: Store events for audit and replay
- **Event Filtering**: Filter events based on criteria

## Task Orchestrator Specifications

### Core Components

#### 1. TaskOrchestrator Class
```python
class TaskOrchestrator:
    """Orchestrate tasks between FastAPI and n8n."""
    
    async def create_task(self, task_config: TaskConfig) -> Task
    async def execute_task(self, task_id: str) -> TaskExecution
    async def monitor_task(self, task_id: str) -> TaskStatus
    async def cancel_task(self, task_id: str) -> bool
```

#### 2. Task Models
```python
class TaskConfig(BaseModel):
    name: str
    workflow_id: str
    parameters: Dict[str, Any]
    schedule: Optional[ScheduleConfig]
    callbacks: List[CallbackConfig]
    timeout: int = 300

class TaskExecution(BaseModel):
    task_id: str
    execution_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
```

### Execution Management
- **Task Queuing**: Queue tasks for execution
- **Status Tracking**: Track task execution status
- **Result Collection**: Collect and store task results
- **Error Recovery**: Handle and recover from task failures

## API Endpoints

### Bridge Endpoints
```
POST   /fastapi-integration/bridge/forward     # Forward request
GET    /fastapi-integration/bridge/health      # Health check
POST   /fastapi-integration/bridge/test        # Test connection
```

### Webhook Endpoints
```
POST   /fastapi-integration/webhooks           # Register webhook
GET    /fastapi-integration/webhooks           # List webhooks
GET    /fastapi-integration/webhooks/{id}      # Get webhook
DELETE /fastapi-integration/webhooks/{id}     # Unregister webhook
POST   /fastapi-integration/webhooks/{id}/test # Test webhook
```

### Task Endpoints
```
POST   /fastapi-integration/tasks              # Create task
GET    /fastapi-integration/tasks              # List tasks
GET    /fastapi-integration/tasks/{id}         # Get task
POST   /fastapi-integration/tasks/{id}/execute # Execute task
DELETE /fastapi-integration/tasks/{id}/cancel # Cancel task
GET    /fastapi-integration/tasks/{id}/status  # Get task status
```

## Configuration

### Environment Variables
```bash
# FastAPI Integration
FASTAPI_INTEGRATION_ENABLED=true
FASTAPI_BASE_URL=http://localhost:8000
FASTAPI_API_KEY=your_fastapi_api_key

# n8n Integration
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key

# Webhook Configuration
WEBHOOK_BASE_URL=http://localhost:8080
WEBHOOK_SECRET_KEY=your_webhook_secret

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_DB=2

# Security
API_RATE_LIMIT=100
WEBHOOK_TIMEOUT=30
TASK_TIMEOUT=300
```

### Module Configuration
```python
class FastAPIIntegrationConfig(BaseModel):
    enabled: bool = True
    fastapi_base_url: str
    fastapi_api_key: str
    n8n_base_url: str
    n8n_api_key: str
    webhook_base_url: str
    webhook_secret_key: str
    redis_url: str
    redis_db: int = 2
    api_rate_limit: int = 100
    webhook_timeout: int = 30
    task_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0
```

## Security Considerations

### 1. Authentication
- **API Key Rotation**: Regular rotation of API keys
- **Token Validation**: Validate all incoming tokens
- **Permission Checking**: Check permissions for all operations
- **Audit Logging**: Log all authentication attempts

### 2. Data Protection
- **Input Validation**: Validate all input data
- **Output Sanitization**: Sanitize all output data
- **Encryption**: Encrypt sensitive data in transit and at rest
- **Access Control**: Implement proper access controls

### 3. Network Security
- **HTTPS Only**: Use HTTPS for all communications
- **IP Whitelisting**: Whitelist allowed IP addresses
- **Rate Limiting**: Implement rate limiting
- **DDoS Protection**: Protect against DDoS attacks

## Performance Requirements

### 1. Response Times
- **API Bridge**: < 100ms for simple requests
- **Webhook Processing**: < 50ms for event processing
- **Task Execution**: < 5s for task initiation

### 2. Throughput
- **Concurrent Requests**: Handle 1000+ concurrent requests
- **Webhook Events**: Process 10,000+ events per minute
- **Task Executions**: Support 100+ concurrent task executions

### 3. Scalability
- **Horizontal Scaling**: Support horizontal scaling
- **Load Balancing**: Distribute load across instances
- **Resource Management**: Efficient resource utilization

## Monitoring and Observability

### 1. Metrics
- **Request Metrics**: Track request count, latency, errors
- **Webhook Metrics**: Track webhook events and processing times
- **Task Metrics**: Track task execution statistics
- **System Metrics**: Monitor CPU, memory, network usage

### 2. Logging
- **Structured Logging**: Use structured logging format
- **Log Levels**: Appropriate log levels for different events
- **Log Aggregation**: Centralized log collection
- **Log Retention**: Appropriate log retention policies

### 3. Health Checks
- **Endpoint Health**: Monitor endpoint availability
- **Dependency Health**: Check external dependency health
- **System Health**: Monitor overall system health
- **Alerting**: Alert on health check failures

## Development Workflow

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Run tests
pytest tests/

# Start development server
uvicorn main:app --reload
```

### 2. Testing
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/

# Coverage report
pytest --cov=modules/fastapi_integration
```

### 3. Deployment
```bash
# Build Docker image
docker build -t unityai/fastapi-integration .

# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting Guide

### Common Issues

#### 1. Connection Failures
- **Symptoms**: API calls failing, timeouts
- **Causes**: Network issues, service unavailability
- **Solutions**: Check network connectivity, verify service status

#### 2. Authentication Errors
- **Symptoms**: 401/403 errors, access denied
- **Causes**: Invalid API keys, expired tokens
- **Solutions**: Verify API keys, refresh tokens

#### 3. Webhook Failures
- **Symptoms**: Webhook events not processed
- **Causes**: Invalid webhook configuration, network issues
- **Solutions**: Verify webhook configuration, check network

#### 4. Performance Issues
- **Symptoms**: Slow response times, high latency
- **Causes**: High load, resource constraints
- **Solutions**: Scale resources, optimize code

### Debugging
- **Enable Debug Logging**: Set log level to DEBUG
- **Check Health Endpoints**: Verify system health
- **Monitor Metrics**: Check performance metrics
- **Review Logs**: Analyze error logs

## Future Enhancements

### Phase 1 (Current)
- Basic API bridge functionality
- Webhook handling
- Task orchestration
- Basic monitoring

### Phase 2 (Next)
- Advanced authentication
- Enhanced error handling
- Performance optimizations
- Advanced monitoring

### Phase 3 (Future)
- Machine learning integration
- Advanced analytics
- Multi-tenant support
- Advanced security features

## Success Criteria

### Functional Requirements
- ✅ Successful API bridge implementation
- ✅ Webhook handling working correctly
- ✅ Task orchestration functional
- ✅ Data transformation working
- ✅ Error handling implemented

### Non-Functional Requirements
- ✅ Response times under target thresholds
- ✅ High availability (99.9% uptime)
- ✅ Scalability requirements met
- ✅ Security requirements satisfied
- ✅ Monitoring and alerting in place

### Quality Requirements
- ✅ Code coverage > 90%
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Security audit passed
- ✅ Performance benchmarks met