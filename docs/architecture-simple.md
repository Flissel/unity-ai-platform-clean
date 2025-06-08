# Unity AI Platform - Simplified Architecture

A simplified overview of the Unity AI platform's core components and data flow.

## Core System Overview

```mermaid
graph TB
    %% External Access
    User[👤 User] --> Traefik[🌐 Traefik Proxy]
    
    %% Core Services
    Traefik --> FastAPI[⚡ FastAPI]
    Traefik --> N8N[🔄 n8n Workflows]
    
    %% Data Layer
    FastAPI --> Redis[📦 Redis Cache]
    N8N --> PostgreSQL[🗄️ PostgreSQL]
    FastAPI --> PostgreSQL
    
    %% Processing
    N8N --> Worker[⚙️ n8n Worker]
    Worker --> Python[🐍 Python Scripts]
    
    %% Monitoring
    FastAPI --> Prometheus[📊 Prometheus]
    N8N --> Prometheus
    Prometheus --> Grafana[📈 Grafana]
    
    %% Styling
    classDef primary fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef secondary fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef data fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    
    class User,Traefik primary
    class FastAPI,N8N,Worker secondary
    class Redis,PostgreSQL,Python data
```

## Service Stack

```mermaid
graph LR
    subgraph "Frontend Layer"
        A[🌐 Traefik]
    end
    
    subgraph "Application Layer"
        B[⚡ FastAPI]
        C[🔄 n8n]
    end
    
    subgraph "Processing Layer"
        D[⚙️ Workers]
        E[🐍 Python]
    end
    
    subgraph "Data Layer"
        F[📦 Redis]
        G[🗄️ PostgreSQL]
    end
    
    A --> B
    A --> C
    B --> D
    C --> D
    D --> E
    B --> F
    C --> G
    B --> G
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant T as Traefik
    participant F as FastAPI
    participant N as n8n
    participant W as Worker
    participant P as Python
    
    U->>T: Request
    T->>F: Route to FastAPI
    F->>N: Trigger Workflow
    N->>W: Queue Task
    W->>P: Execute Script
    P-->>W: Results
    W-->>N: Complete
    N-->>F: Response
    F-->>T: API Response
    T-->>U: Final Response
```

## Quick Start Guide

### Development
```bash
# Start development environment
docker-compose up -d

# Access services
# FastAPI: http://localhost:8000
# n8n: http://localhost:5678
# Grafana: http://localhost:3000
```

### Production
```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose logs -f
```

## Key Features

- 🔄 **Automated Workflows**: n8n for complex automation
- ⚡ **Fast API**: High-performance REST endpoints
- 📦 **Caching**: Redis for improved performance
- 🗄️ **Persistence**: PostgreSQL for reliable data storage
- 📊 **Monitoring**: Prometheus + Grafana observability
- 🌐 **Load Balancing**: Traefik reverse proxy
- 🐍 **Extensible**: Python scripts for custom logic

---

*For detailed architecture diagrams, see:*
- [Detailed Mermaid Diagrams](./architecture-mermaid.md)
- [Professional PlantUML Diagrams](./architecture-plantuml.puml)