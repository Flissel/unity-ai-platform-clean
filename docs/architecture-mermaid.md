# Unity AI Platform - Mermaid Architecture Diagrams

## System Architecture Overview

```mermaid
graph TB
  %% External
  U[👤 User / CLI]
  
  %% Ingress
  subgraph Ingress Layer
    Traefik[🚦 Traefik Gateway\nSSL/TLS, Routing]
  end
  
  %% Application Microservices
  subgraph App Layer
    API[🚀 Backend API Service\nFastAPI\n– Workflow-Management n8n-Proxy\n– Script-Registry-CRUD]
    N8N[⚙️ Workflow Service\nn8n Core\nExec-Command Nodes]
    Worker[🐍 Worker Service\nRedis-Queue Consumer\nShell-Exec Python-Scripts]
  end
  
  %% Data Services
  subgraph Data Layer
    Postgres[(🐘 PostgreSQL\nScript-Registry & Workflow Meta)]
    Redis[(🔴 Redis\nQueue & Session)]
    ScriptsVol[(📂 shared_scripts\nPython-Scripts Volume)]
  end
  
  %% Netz & Volumes
  subgraph Swarm Overlay
    Net[🌐 Overlay-Netzwerk]
  end
  
  U --> Traefik
  Traefik --> API
  Traefik --> N8N
  
  API --> Postgres
  API --> Redis
  %% FastAPI löst n8n Workflows aus
   API --> N8N
  
  N8N --> Redis
  N8N --> Worker
  
  Worker --> Redis
  Worker --> Postgres
  Worker --> ScriptsVol
  
  %% Netz/Volumes
  class Traefik,API,N8N,Worker,Postgres,Redis,Net,ScriptsVol app;
class ScriptsVol data;

```

## Data Flow Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant T as Traefik
    participant UA as Unity AI App
    participant N8N as n8n Core
    participant NW as n8n Worker
    participant PW as Python Worker
    participant R as Redis
    participant P as PostgreSQL
    participant S as Shared Scripts
    
    U->>T: HTTPS Request
    T->>UA: Route to FastAPI
    UA->>P: Query Database
    P-->>UA: Return Data
    UA->>R: Cache Result
    UA->>N8N: Trigger Workflow
    N8N->>R: Queue Job
    R-->>NW: Job Available
    NW->>S: Execute Script
    S-->>NW: Script Result
    NW->>P: Store Result
    NW->>R: Update Status
    UA->>PW: Background Task
    PW->>R: Process Queue
    PW->>P: Update Data
    UA-->>T: Response
    T-->>U: HTTPS Response
```

## Container Deployment Diagram

```mermaid
graph LR
    subgraph "Docker Host"
        subgraph "Unity AI Network"
            subgraph "Web Tier"
                T[Traefik:80,443]
            end
            
            subgraph "Application Tier"
                UA[Unity AI:8000]
                N8N[n8n Core:5678]
                NW[n8n Worker]
                PW[Python Worker:8001]
            end
            
            subgraph "Data Tier"
                P[PostgreSQL:5432]
                R[Redis:6379]
            end
            
            subgraph "Monitoring Tier"

            end
        end
        
        subgraph "Volumes"
            V1[postgres_data]
            V2[redis_data]
            V3[n8n_data]

            V6[shared_scripts]
        end
    end
    
    T --> UA
    T --> N8N
    T --> G
    UA --> P
    UA --> R
    N8N --> P
    N8N --> R
    NW --> R
    PW --> R
    PW --> P
    PR --> UA
    PR --> N8N
    PR --> P
    PR --> R
    G --> PR
    
    P -.-> V1
    R -.-> V2
    N8N -.-> V3
    G -.-> V4
    PR -.-> V5
    NW -.-> V6
    PW -.-> V6
```

## Service Dependencies

```mermaid
graph TD
    subgraph "Core Dependencies"
        P[PostgreSQL]
        R[Redis]
    end
    
    subgraph "Application Services"
        UA[Unity AI App]
        N8N[n8n Core]
        NW[n8n Worker]
        PW[Python Worker]
    end
    
    subgraph "Infrastructure"
        T[Traefik]

    end
    
    subgraph "Shared Resources"
        S[Shared Scripts]
        L[Common Libraries]
    end
    
    %% Dependencies
    UA --> P
    UA --> R
    N8N --> P
    N8N --> R
    NW --> R
    NW --> S
    NW --> L
    PW --> R
    PW --> P
    PW --> L
    T --> UA
    T --> N8N
    T --> G
    PR --> UA
    PR --> N8N
    PR --> NW
    PR --> PW
    PR --> P
    PR --> R
    G --> PR
    S --> L
    
    %% Startup Order
    P -.->|1| R
    R -.->|2| N8N
    N8N -.->|3| UA
    UA -.->|4| NW
    NW -.->|5| PW
    PW -.->|6| T
    T -.->|7| PR
    PR -.->|8| G
```

## Network Architecture

```mermaid
graph TB
    subgraph "External Network"
        Internet[Internet]
        CDN[CDN/CloudFlare]
    end
    
    subgraph "DMZ"
        LB[Load Balancer]
        WAF[Web Application Firewall]
    end
    
    subgraph "Docker Host"
        subgraph "Unity AI Network (Overlay)"
            subgraph "Frontend"
                Traefik[Traefik Proxy\n:80, :443]
            end
            
            subgraph "Backend Services"
                UA[Unity AI\n:8000]
                N8N[n8n Core\n:5678]
                NW[n8n Worker]
                PW[Python Worker\n:8001]
            end
            
            subgraph "Data Services"
                PG[PostgreSQL\n:5432]
                RD[Redis\n:6379]
            end
            
            subgraph "Monitoring"

            end
        end
        
        subgraph "Host Network"
            SSH[SSH :22]
            Docker[Docker API :2376]
        end
    end
    
    Internet --> CDN
    CDN --> LB
    LB --> WAF
    WAF --> Traefik
    
    Traefik --> UA
    Traefik --> N8N
    Traefik --> GRAF
    
    UA <--> PG
    UA <--> RD
    N8N <--> PG
    N8N <--> RD
    NW <--> RD
    PW <--> RD
    PW <--> PG
    
    PROM --> UA
    PROM --> N8N
    PROM --> NW
    PROM --> PW
    PROM --> PG
    PROM --> RD
    GRAF --> PROM
```

## Technology Stack Mind Map

```mermaid
mindmap
  root((Unity AI Platform))
    Frontend
      Traefik
        SSL/TLS
        Load Balancing
        Service Discovery
        Rate Limiting
      n8n Web UI
        Workflow Designer
        Node Editor
        Execution History

    Backend
      FastAPI
        Python 3.11
        Async/Await
        OpenAPI/Swagger
        Pydantic
      n8n Core
        Node.js
        TypeScript
        Workflow Engine
        Scheduler
      n8n Worker
        Queue Processing
        ML Libraries
        Python Integration
      Python Worker
        Background Tasks
        Data Processing
        ML Inference
    Data Layer
      PostgreSQL
        Primary Database
        ACID Compliance
        JSON Support
        Full-text Search
      Redis
        Caching
        Session Storage
        Queue Management
        Pub/Sub
      Docker Volumes
        Persistent Storage
        File Uploads
        Backups
    Monitoring

      Logging
        Centralized Logs
        Log Aggregation
        Search & Analysis
    Infrastructure
      Docker
        Containerization
        Multi-stage Builds
        Health Checks
      Docker Compose
        Service Orchestration
        Network Management
        Volume Management
      GitHub Actions
        CI/CD Pipeline
        Automated Testing
        Deployment
    Security
      Docker Secrets
        Credential Management
        Secret Rotation
      Environment Variables
        Configuration
        Feature Flags
      SSL/TLS
        HTTPS Encryption
        Certificate Management
      Authentication
        JWT Tokens
        API Keys
        OAuth Integration
```

## Script Integration Flow

```mermaid
flowchart TD
    A[n8n Workflow Trigger] --> B{Script Type?}
    
    B -->|Data Processing| C[analyze_data.py]
    B -->|Web Scraping| D[scrape_website.py]
    B -->|ML Inference| E[predict_model.py]
    B -->|Document Processing| F[process_document.py]
    B -->|Image Processing| G[process_image.py]
    B -->|API Integration| H[api_client.py]
    B -->|Notifications| I[send_notification.py]
    
    C --> J[Execute Command Node]
    D --> J
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J
    
    J --> K[Python Script Execution]
    K --> L[Load Common Libraries]
    L --> M[Process Input Data]
    M --> N[Execute Business Logic]
    N --> O[Generate Output]
    O --> P[Return JSON Result]
    P --> Q[n8n Continue Workflow]
    
    subgraph "Shared Resources"
        R[common.py]
        S[config.py]
        T[utils.py]
    end
    
    L --> R
    L --> S
    L --> T
```