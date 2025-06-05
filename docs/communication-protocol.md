# Communication Protocol - FastAPI ↔ n8n

This document describes the communication protocol between the FastAPI service and n8n workflows within the Docker environment.

## Architecture Overview

```mermaid
graph TB
    subgraph "Docker Network (core)"
        subgraph "FastAPI Container"
            API[FastAPI Service<br/>Port: 8000]
            Router[Code Testing Router]
        end
        
        subgraph "n8n Container"
            N8N[n8n Service<br/>Port: 5678]
            Webhook[Webhook Endpoint<br/>/webhook]
            CodeNode[Code Node<br/>Python Execution]
            HTTPNode[HTTP Request Node]
        end
        
        subgraph "Infrastructure"
            Redis[(Redis Cache)]
            Postgres[(PostgreSQL DB)]
            Traefik[Traefik Proxy]
        end
    end
    
    subgraph "External Access"
        Client[Client/Browser]
        Domain[n8n.unit-y-ai.io]
    end
    
    %% Communication Flow
    Client -->|HTTPS| Traefik
    Traefik -->|Route| API
    Traefik -->|Route| Domain
    Domain --> N8N
    
    API -->|HTTP POST| Webhook
    Webhook --> CodeNode
    CodeNode -->|Execute Python| CodeNode
    HTTPNode -->|Send Results| API
    
    N8N --> Redis
    N8N --> Postgres
    API --> Redis
    
    classDef container fill:#e1f5fe
    classDef service fill:#f3e5f5
    classDef database fill:#e8f5e8
    classDef external fill:#fff3e0
    
    class API,N8N container
    class Router,Webhook,CodeNode,HTTPNode service
    class Redis,Postgres database
    class Client,Domain external
```

## Communication Protocols

### 1. FastAPI → n8n (Webhook Trigger)

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant n8n
    participant CodeNode
    participant HTTPResponse
    
    Client->>FastAPI: POST /api/code-testing
    Note over FastAPI: Validate request
    FastAPI->>n8n: POST http://n8n:5678/webhook
    Note over FastAPI,n8n: JSON payload with code & requirements
    
    n8n->>CodeNode: Execute Python script
    Note over CodeNode: Run code in isolated environment
    CodeNode->>CodeNode: Process results
    
    alt Success
        CodeNode->>HTTPResponse: Send results back
        HTTPResponse->>FastAPI: POST callback with results
        FastAPI->>Client: Return success response
    else Error
        CodeNode->>HTTPResponse: Send error details
        HTTPResponse->>FastAPI: POST callback with error
        FastAPI->>Client: Return error response
    end
```

### 2. FastAPI → n8n (API Calls)

```mermaid
sequenceDiagram
    participant FastAPI
    participant n8nAPI as n8n REST API
    participant Workflow
    
    FastAPI->>n8nAPI: GET /api/v1/workflows
    Note over FastAPI,n8nAPI: Bearer token authentication
    n8nAPI->>FastAPI: Return workflow list
    
    FastAPI->>n8nAPI: POST /api/v1/workflows/{id}/execute
    Note over FastAPI,n8nAPI: Execute specific workflow
    n8nAPI->>Workflow: Start execution
    Workflow->>n8nAPI: Return execution ID
    n8nAPI->>FastAPI: Return execution details
    
    loop Check Status
        FastAPI->>n8nAPI: GET /api/v1/executions/{id}
        n8nAPI->>FastAPI: Return execution status
    end
```

### 3. Network Communication Details

```mermaid
graph LR
    subgraph "Internal Docker Network"
        FastAPI[FastAPI<br/>http://fastapi:8000]
        n8n[n8n<br/>http://n8n:5678]
        Redis[Redis<br/>redis:6379]
        Postgres[PostgreSQL<br/>postgres:5432]
    end
    
    subgraph "External Access"
        Localhost[localhost:8000]
        Domain[n8n.unit-y-ai.io]
    end
    
    FastAPI <-->|Internal| n8n
    FastAPI <-->|Cache| Redis
    n8n <-->|Database| Postgres
    n8n <-->|Cache| Redis
    
    Localhost -->|Port Mapping| FastAPI
    Domain -->|Traefik Routing| n8n
    
    style FastAPI fill:#4CAF50
    style n8n fill:#FF6B35
    style Redis fill:#DC382D
    style Postgres fill:#336791
```

## Environment Configuration

### FastAPI Environment (.env.fastapi)
```bash
# n8n Communication
N8N_API_URL=http://n8n:5678/api/v1
N8N_API_KEY=your_api_key_here
N8N_WEBHOOK_URL=http://n8n:5678/webhook
```

### n8n Environment (.env.endpoints)
```bash
# Webhook Configuration
N8N_ENDPOINT_WEBHOOK=/webhook
N8N_ENDPOINT_WEBHOOK_TEST=/webhook-test
```

## Data Flow Patterns

### Code Testing Workflow

```mermaid
flowchart TD
    A[Client Request] --> B[FastAPI Validation]
    B --> C{Use Webhook or API?}
    
    C -->|Webhook| D[POST to n8n Webhook]
    C -->|API| E[POST to n8n API]
    
    D --> F[n8n Workflow Triggered]
    E --> F
    
    F --> G[Code Node Execution]
    G --> H{Execution Result}
    
    H -->|Success| I[Format Results]
    H -->|Error| J[Format Error]
    
    I --> K[Send Response Back]
    J --> K
    
    K --> L[FastAPI Processes Response]
    L --> M[Return to Client]
    
    style A fill:#e3f2fd
    style F fill:#fff3e0
    style G fill:#f3e5f5
    style M fill:#e8f5e8
```

## Security Considerations

1. **Internal Network**: All services communicate within the Docker `core` network
2. **API Authentication**: n8n API calls require Bearer token authentication
3. **Webhook Security**: Consider implementing webhook signatures for production
4. **Environment Variables**: Sensitive data stored in environment files
5. **Traefik Routing**: External access controlled through Traefik proxy

## Monitoring & Health Checks

```mermaid
graph TB
    subgraph "Health Monitoring"
        HC1[FastAPI Health Check<br/>/health]
        HC2[n8n Health Check<br/>/healthz]
        HC3[Redis Health Check]
        HC4[Postgres Health Check]
    end
    
    subgraph "Monitoring Tools"
        Prometheus[Prometheus Metrics]
        Logs[Centralized Logging]
    end
    
    HC1 --> Prometheus
    HC2 --> Prometheus
    HC3 --> Prometheus
    HC4 --> Prometheus
    
    HC1 --> Logs
    HC2 --> Logs
```

## Troubleshooting

### Common Issues
1. **Connection Refused**: Check if services are on the same Docker network
2. **Authentication Failed**: Verify n8n API key configuration
3. **Webhook Not Triggered**: Ensure webhook URL is correct and workflow is active
4. **Timeout Issues**: Check network connectivity and service health

### Debug Commands
```bash
# Check service connectivity
docker-compose exec fastapi curl http://n8n:5678/healthz

# View service logs
docker-compose logs fastapi
docker-compose logs n8n

# Check network configuration
docker network inspect unityai_core
```