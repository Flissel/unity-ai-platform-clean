# Unity AI Platform - Simplified Architecture

A simplified overview of the Unity AI platform's core components and data flow.

## Architektur-Grundstruktur

### n8n als Orchestrator
Workflows dienen als "Jobs" und steuern Ausführung, Kettenbildung und Übergabe.

### Python Scripts via Execute Command
Skripte werden über den Exec Command Node ausgeführt, der Pfad und Parameter übernimmt. Damit können beliebige Simulationen, ML, Datenprozesse usw. außerhalb der eigentlichen n8n-Engine laufen.

### Webhook-Triggers für Skalierbarkeit
Jeder Workflow kann (und sollte für asynchrone Jobs) einen eigenen Webhook-Trigger erhalten, um von außen ausgelöst zu werden (z. B. per FastAPI).

### FastAPI + Autogen
Steuert das Anstoßen und die Koordination der Workflows, verteilt Aufgaben (bspw. teilt große Tasks auf viele Jobs auf).

## Core System Overview

```mermaid
graph TB 
   %% External 
   U[👤 User / CLI] 
   
   %% Ingress 
   subgraph "Ingress Layer" 
     Traefik[🚦 Traefik Gateway\nSSL/TLS, Routing] 
   end 
   
   %% Application Microservices 
   subgraph "App Layer" 
     API[🚀 Backend API Service\nFastAPI\n– Workflow-Management n8n-Proxy\n– Script-Registry-CRUD] 
     N8N[⚙️ Workflow Service\nn8n Core\nExec-Command Nodes] 
     Worker[🐍 Worker Service\nRedis-Queue Consumer\nShell-Exec Python-Scripts] 
   end 
   
   %% Data Services 
   subgraph "Data Layer" 
     Postgres[(🐘 PostgreSQL\nScript-Registry & Workflow Meta)] 
     Redis[(🔴 Redis\nQueue & Session)] 
     ScriptsVol[(📂 shared_scripts\nPython-Scripts Volume)] 
   end 
   
   %% Netz & Volumes 
   subgraph "Swarm Overlay" 
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

## Praktische Umsetzung (Step-by-Step)

### 1. Python Scripts via n8n Execute Command
- **Integration:** Python-Skripte werden über n8n's "Execute Command" Nodes ausgeführt
- **Vorteile:** Direkte Integration, einfache Parameter-Übergabe, Logging
- **Verwendung:** Datenverarbeitung, API-Calls, Berechnungen
- **Swarm-Deployment:** Skripte werden auf Worker-Nodes ausgeführt

### 2. Workflow Design mit n8n und Webhooks
- **Trigger:** HTTP Webhook Nodes als Einstiegspunkte
- **Orchestrierung:** n8n koordiniert die Ausführung verschiedener Python-Skripte
- **Monitoring:** Eingebaute Execution-Historie und Error-Handling
- **High Availability:** n8n läuft als Swarm Service mit Restart-Policy

### 3. Verteilung/Parallelisierung via FastAPI
- **Load Balancing:** FastAPI ruft n8n Webhooks auf verschiedenen Instanzen auf
- **Skalierung:** Horizontale Skalierung durch mehrere n8n Worker und FastAPI Replicas
- **Queue Management:** Redis als Message Broker für Task-Verteilung
- **Service Discovery:** Docker Swarm's integrierte Service-Discovery

### 4. Ergebnis-Verarbeitung
- **Rückgabe:** Python-Skripte geben Ergebnisse an n8n zurück
- **Weiterleitung:** n8n leitet Ergebnisse an FastAPI weiter
- **Persistierung:** Ergebnisse werden in PostgreSQL gespeichert
- **Redundanz:** Daten werden über Swarm Volumes persistent gespeichert

### 5. Docker Swarm Deployment
- **Orchestrierung:** Docker Swarm verwaltet Service-Deployment und -Skalierung
- **Load Balancing:** Traefik als Reverse Proxy mit automatischer Service-Discovery
- **SSL/TLS:** Automatische Zertifikatserstellung über Let's Encrypt
- **Health Monitoring:** Integrierte Health Checks für Service-Überwachung
- **Secrets Management:** Docker Secrets für sichere Passwort-Verwaltung

## Workflow-Flussdiagramm

```mermaid
flowchart TD 
  subgraph "API Layer" 
    FAPI[FastAPI + Autogen] 
  end 
  subgraph "Workflow Layer" 
    N8N1[n8n Workflow 1 Webhook Trigger] 
    N8N2[n8n Workflow 2 z.B. HTML umformen] 
  end 
  subgraph "Execution Layer" 
    PYSCRIPT[Python Script Exec Command] 
  end 

  FAPI -- POST Payload-Komponente 1 --> N8N1 
  FAPI -- POST Payload-Komponente 2 --> N8N1 
  FAPI -- POST Payload-Komponente 3... --> N8N1 

  N8N1 -- Startet --> PYSCRIPT 
  PYSCRIPT -- Ergebnis JSON/File --> N8N1 

  N8N1 -- POST Ergebnis an --> FAPI 

  FAPI -- nach jedem Ergebnis oder am Ende --> N8N2
```

## Service Stack

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Web Interface]
        API[FastAPI]
    end
    
    subgraph "Application Layer"
        N8N[n8n Workflows]
        Worker[Python Workers]
        Queue[Redis Queue]
    end
    
    subgraph "Processing Layer"
        Scripts[Python Scripts]
        ML[ML Models]
        Data[Data Processing]
    end
    
    UI --> API
    API --> N8N
    API --> Queue
    N8N --> Worker
    Queue --> Worker
    Worker --> Scripts
    Worker --> ML
    Worker --> Data
```

## Docker Swarm Architektur

### Service-Verteilung

```mermaid
graph TB
    subgraph "Manager Node"
        Traefik[Traefik Load Balancer]
        DB[PostgreSQL]
        Redis[Redis Queue]
        N8N[n8n Core]
    end
    
    subgraph "Worker Node 1"
        API1[FastAPI Replica 1]
        Worker1[Python Worker 1]
        Runner1[n8n Runner 1]
    end
    
    subgraph "Worker Node 2"
        API2[FastAPI Replica 2]
        Worker2[Python Worker 2]
        Runner2[n8n Runner 2]
    end
    

    
    Internet --> Traefik
    Traefik --> API1
    Traefik --> API2
    Traefik --> N8N
    
    API1 --> DB
    API2 --> DB
    API1 --> Redis
    API2 --> Redis
    
    N8N --> Runner1
    N8N --> Runner2
    
    Runner1 --> Worker1
    Runner2 --> Worker2
    

```

### Deployment-Konfiguration

| Service | Replicas | Placement | Resources |
|---------|----------|-----------|----------|
| Traefik | 1 | Manager Node | 256MB RAM |
| PostgreSQL | 1 | Manager Node | 512MB RAM |
| Redis | 1 | Manager Node | 256MB RAM |
| n8n Core | 1 | Manager Node | 1GB RAM |
| FastAPI | 2 | Worker Nodes | 1GB RAM each |
| Python Worker | 3 | Worker Nodes | 2GB RAM each |
| n8n Runner | 2 | Worker Nodes | 512MB RAM each |


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
- 📊 **Monitoring**: Application observability
- 🌐 **Load Balancing**: Traefik reverse proxy
- 🐍 **Extensible**: Python scripts for custom logic

---

*For detailed architecture diagrams, see:*
- [Detailed Mermaid Diagrams](./architecture-mermaid.md)
- [Professional PlantUML Diagrams](./architecture-plantuml.puml)