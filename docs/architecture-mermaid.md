# Unity AI Platform - Mermaid Architecture Diagrams

## System Architecture Overview

```mermaid
graph TB
    %% External Layer
    Internet[🌐 Internet]
    Users[👥 Users]
    Clients[🔌 API Clients]
    Webhooks[🪝 Webhooks]
    
    %% Reverse Proxy Layer
    subgraph "Reverse Proxy & Load Balancing"
        Traefik[🚦 Traefik<br/>SSL/TLS Termination<br/>Load Balancing<br/>Service Discovery<br/>Rate Limiting]
    end
    
    %% Application Services Layer
    subgraph "Application Services"
        UnityAI[🚀 Unity AI App<br/>FastAPI Application<br/>REST API Endpoints<br/>Authentication<br/>Business Logic]
        N8NCore[⚙️ n8n Core<br/>Workflow Engine<br/>Web Interface<br/>Workflow Management<br/>Scheduler]
        N8NWorker[👷 n8n Worker<br/>Queue Worker<br/>Workflow Execution<br/>ML Libraries<br/>Python Scripts]
        PythonWorker[🐍 Python Worker<br/>Background Tasks<br/>Data Processing<br/>ML Inference<br/>Script Execution]
    end
    
    %% Shared Resources
    subgraph "Shared Scripts & Libraries"
        DataScripts[📊 Data Processing]
        MLScripts[🤖 ML Inference]
        ScrapingScripts[🕷️ Web Scraping]
        DocScripts[📄 Document Processing]
        ImgScripts[🖼️ Image Processing]
        APIScripts[🔗 API Integration]
        NotificationScripts[📢 Notifications]
        CommonLibs[📚 Common Libraries]
    end
    
    %% Data & Queue Layer
    subgraph "Data & Queue Layer"
        Postgres[(🐘 PostgreSQL<br/>Primary Database<br/>n8n Workflows<br/>User Data<br/>Configuration)]
        Redis[(🔴 Redis<br/>Queue Management<br/>Session Storage<br/>Caching<br/>Pub/Sub)]
        Volumes[(💾 Docker Volumes<br/>Persistent Storage<br/>File Uploads<br/>Logs<br/>Backups)]
    end
    
    %% Monitoring Layer
    subgraph "Monitoring & Observability"
        Prometheus[📈 Prometheus<br/>Metrics Collection<br/>Time Series DB<br/>Alerting Rules]
        Grafana[📊 Grafana<br/>Dashboards<br/>Visualization<br/>Alerting<br/>Reporting]
        Logs[📝 Logs<br/>Centralized Logging<br/>Log Aggregation<br/>Log Analysis]
    end
    
    %% Security Layer
    subgraph "Security & Configuration"
        Secrets[🔐 Docker Secrets]
        EnvFiles[⚙️ Environment Files]
        Certificates[🔒 SSL/TLS Certificates]
        Auth[🛡️ Authentication]
        RateLimit[⏱️ Rate Limiting]
    end
    
    %% Network Layer
    subgraph "Docker Network"
        Network[🌐 Overlay Network<br/>Service Discovery<br/>Internal Communication<br/>Network Isolation]
    end
    
    %% External Connections
    Internet --> Traefik
    Users --> Traefik
    Clients --> Traefik
    Webhooks --> Traefik
    
    %% Traefik Routing
    Traefik --> UnityAI
    Traefik --> N8NCore
    Traefik --> Grafana
    
    %% Application Service Connections
    UnityAI --> Postgres
    UnityAI --> Redis
    UnityAI --> PythonWorker
    
    N8NCore --> Postgres
    N8NCore --> Redis
    N8NCore --> N8NWorker
    
    N8NWorker --> Redis
    N8NWorker --> DataScripts
    N8NWorker --> MLScripts
    N8NWorker --> ScrapingScripts
    N8NWorker --> DocScripts
    N8NWorker --> ImgScripts
    N8NWorker --> APIScripts
    N8NWorker --> NotificationScripts
    
    PythonWorker --> Redis
    PythonWorker --> Postgres
    PythonWorker --> CommonLibs
    
    %% Shared Resources Dependencies
    DataScripts --> CommonLibs
    MLScripts --> CommonLibs
    ScrapingScripts --> CommonLibs
    DocScripts --> CommonLibs
    ImgScripts --> CommonLibs
    APIScripts --> CommonLibs
    NotificationScripts --> CommonLibs
    
    %% Monitoring Connections
    Prometheus --> UnityAI
    Prometheus --> N8NCore
    Prometheus --> N8NWorker
    Prometheus --> PythonWorker
    Prometheus --> Postgres
    Prometheus --> Redis
    Prometheus --> Traefik
    
    Grafana --> Prometheus
    Logs --> UnityAI
    Logs --> N8NCore
    Logs --> N8NWorker
    Logs --> PythonWorker
    
    %% Security Connections
    Secrets --> UnityAI
    Secrets --> N8NCore
    Secrets --> Postgres
    EnvFiles --> UnityAI
    EnvFiles --> N8NCore
    Certificates --> Traefik
    Auth --> Traefik
    RateLimit --> Traefik
    
    %% Network Layer
    Network --> UnityAI
    Network --> N8NCore
    Network --> N8NWorker
    Network --> PythonWorker
    Network --> Postgres
    Network --> Redis
    Network --> Prometheus
    Network --> Grafana
    
    %% Styling
    classDef external fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef proxy fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef app fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef monitor fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef security fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef network fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef shared fill:#f9fbe7,stroke:#827717,stroke-width:2px
    
    class Internet,Users,Clients,Webhooks external
    class Traefik proxy
    class UnityAI,N8NCore,N8NWorker,PythonWorker app
    class Postgres,Redis,Volumes data
    class Prometheus,Grafana,Logs monitor
    class Secrets,EnvFiles,Certificates,Auth,RateLimit security
    class Network network
    class DataScripts,MLScripts,ScrapingScripts,DocScripts,ImgScripts,APIScripts,NotificationScripts,CommonLibs shared
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
                PR[Prometheus:9090]
                G[Grafana:3000]
            end
        end
        
        subgraph "Volumes"
            V1[postgres_data]
            V2[redis_data]
            V3[n8n_data]
            V4[grafana_data]
            V5[prometheus_data]
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
        PR[Prometheus]
        G[Grafana]
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
                Traefik[Traefik Proxy<br/>:80, :443]
            end
            
            subgraph "Backend Services"
                UA[Unity AI<br/>:8000]
                N8N[n8n Core<br/>:5678]
                NW[n8n Worker]
                PW[Python Worker<br/>:8001]
            end
            
            subgraph "Data Services"
                PG[PostgreSQL<br/>:5432]
                RD[Redis<br/>:6379]
            end
            
            subgraph "Monitoring"
                PROM[Prometheus<br/>:9090]
                GRAF[Grafana<br/>:3000]
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
      Grafana
        Dashboards
        Alerting
        Visualization
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
      Prometheus
        Metrics Collection
        Time Series
        Alerting
      Grafana
        Visualization
        Dashboards
        Notifications
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