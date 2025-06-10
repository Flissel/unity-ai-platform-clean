# Docker Swarm Deployment Guide

Diese Anleitung beschreibt, wie UnityAI in einem Docker Swarm Cluster deployed wird.

## Überblick

Docker Swarm bietet folgende Vorteile für UnityAI:

- **Hochverfügbarkeit:** Services werden automatisch neu gestartet bei Ausfällen
- **Skalierbarkeit:** Einfache horizontale Skalierung von Services
- **Load Balancing:** Integriertes Load Balancing zwischen Service-Replicas
- **Service Discovery:** Automatische Service-Erkennung über DNS
- **Rolling Updates:** Zero-Downtime Updates
- **Secrets Management:** Sichere Verwaltung von Passwörtern und Tokens

## Voraussetzungen

### Hardware-Anforderungen

#### Minimum (Development/Testing)
- **Manager Node:** 2 CPU, 4GB RAM, 20GB Storage
- **Worker Node:** 2 CPU, 4GB RAM, 20GB Storage

#### Empfohlen (Production)
- **Manager Node:** 4 CPU, 8GB RAM, 100GB SSD
- **Worker Nodes:** 4 CPU, 16GB RAM, 100GB SSD (mindestens 2 Nodes)


### Software-Anforderungen

- Docker Engine 20.10+
- Docker Compose 2.0+
- Linux-basiertes Betriebssystem (Ubuntu 20.04+ empfohlen)
- Netzwerk-Konnektivität zwischen allen Nodes

## Cluster-Setup

### 1. Swarm Initialisierung

**Auf dem Manager Node:**
```bash
# Swarm initialisieren
docker swarm init --advertise-addr <MANAGER_IP>

# Join-Token für Worker anzeigen
docker swarm join-token worker
```

**Auf jedem Worker Node:**
```bash
# Mit dem Swarm beitreten (Token vom Manager Node)
docker swarm join --token <WORKER_TOKEN> <MANAGER_IP>:2377
```

### 2. Node Labels setzen

```bash
# Manager Node Labels
docker node update --label-add postgres=true <MANAGER_NODE>
docker node update --label-add redis=true <MANAGER_NODE>
docker node update --label-add n8n=true <MANAGER_NODE>

# Worker Node Labels
docker node update --label-add worker=true <WORKER_NODE_1>
docker node update --label-add app=true <WORKER_NODE_1>
docker node update --label-add worker=true <WORKER_NODE_2>
docker node update --label-add app=true <WORKER_NODE_2>


```

### 3. Externe Netzwerke erstellen

```bash
# Traefik Public Network
docker network create \
  --driver overlay \
  --attachable \
  traefik-public
```

## Secrets Management

### 1. Secrets-Datei erstellen

```bash
# Kopiere die Beispiel-Datei
cp .env.secrets.example .env.secrets

# Bearbeite die Datei mit echten Werten
nano .env.secrets
```

### 2. Docker Secrets erstellen

```bash
# Lade Secrets aus .env.secrets
source .env.secrets

# Erstelle Docker Secrets
echo "$PG_PASSWORD" | docker secret create pg_pw -
echo "$N8N_ADMIN_PASSWORD" | docker secret create n8n_admin_password -
echo "$N8N_ENCRYPTION_KEY" | docker secret create n8n_encryption_key -
echo "$REDIS_PASSWORD" | docker secret create redis_pw -
echo "$RUNNER_TOKEN" | docker secret create runner_token -

echo "$CLOUDFLARE_TOKEN" | docker secret create cloudflare_token -
```

## Verzeichnisstruktur

### Host-Verzeichnisse erstellen

**Auf allen Nodes:**
```bash
# Erstelle notwendige Verzeichnisse
sudo mkdir -p /opt/unityai/{data,logs,uploads,scripts}


# Setze Berechtigungen
sudo chown -R 1000:1000 /opt/unityai
```

## Deployment

### 1. Automatisches Deployment

```bash
# Führe das Deployment-Skript aus
./scripts/deploy-swarm.sh
```

### 2. Manuelles Deployment

```bash
# Deploy Stack
docker stack deploy -c compose/docker-compose.swarm.yml unityai

# Überprüfe Status
docker stack services unityai
```

## n8n-Playground Integration

### Überblick

Das n8n-Playground ist eine erweiterte API-Schnittstelle für n8n, die zusätzliche Funktionalitäten bietet:

- **Workflow-Automatisierung**: Erweiterte API-Endpunkte für Workflow-Management
- **FastAPI Integration**: Bidirektionale Kommunikation zwischen n8n und FastAPI
- **Monitoring**: Detaillierte Überwachung von Workflow-Ausführungen
- **User Management**: Erweiterte Benutzerverwaltung und Authentifizierung

### Service-Konfiguration

Fügen Sie den n8n-playground Service zur `docker-compose.swarm.yml` hinzu:

```yaml
  # ---------- n8n API Playground ----------
  n8n-playground:
    image: ${DOCKER_REGISTRY:-}unityai-n8n-playground:${IMAGE_TAG:-latest}
    secrets:
      - pg_pw
      - redis_pw
      - n8n_admin_password
    environment:
      # Datenbank
      DATABASE_URL: postgresql://n8n_user:$$(cat /run/secrets/pg_pw)@db:5432/n8n
      REDIS_URL: redis://default:$$(cat /run/secrets/redis_pw)@redis:6379/0
      # n8n Integration
      N8N_BASE_URL: http://n8n:5678
      N8N_API_KEY_FILE: /run/secrets/n8n_admin_password
      # FastAPI Integration
      FASTAPI_BASE_URL: http://app:8000
      # Production Settings
      ENVIRONMENT: production
      DEBUG: "false"
      LOG_LEVEL: INFO
      # Security
      JWT_SECRET_KEY_FILE: /run/secrets/n8n_encryption_key
      # Monitoring
      PROMETHEUS_ENABLED: "true"
      GRAFANA_ENABLED: "true"
    volumes:
      - type: bind
        source: /opt/unityai/logs
        target: /app/logs
      - type: bind
        source: /opt/unityai/data
        target: /app/data
    networks:
      - unityai-network
      - traefik-public
    deploy:
      mode: replicated
      replicas: 2
      placement:
        constraints:
          - node.labels.app == true
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
      labels:
        - "traefik.enable=true"
        - "traefik.docker.network=traefik-public"
        - "traefik.http.routers.playground.rule=Host(`playground.unit-y-ai.io`)"
        - "traefik.http.routers.playground.entrypoints=websecure"
        - "traefik.http.routers.playground.tls.certresolver=letsencrypt"
        - "traefik.http.services.playground.loadbalancer.server.port=8080"
        - "traefik.http.services.playground.loadbalancer.healthcheck.path=/health"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      - db
      - redis
      - n8n
```

### Frontend-Integration

Aktualisieren Sie die Frontend-Umgebungsvariablen für die Playground-Integration:

```yaml
# In der app Service-Konfiguration
environment:
  # ... bestehende Variablen ...
  REACT_APP_PLAYGROUND_API_URL: https://playground.unit-y-ai.io
  REACT_APP_N8N_PLAYGROUND_ENABLED: "true"
```

### Zusätzliche Secrets

Erstellen Sie zusätzliche Secrets für die Playground-Integration:

```bash
# n8n API Key (falls separater Key benötigt)
echo "$N8N_PLAYGROUND_API_KEY" | docker secret create n8n_playground_api_key -

# JWT Secret für Playground
echo "$PLAYGROUND_JWT_SECRET" | docker secret create playground_jwt_secret -
```

### DNS-Konfiguration

Fügen Sie den DNS-Eintrag für die Playground-Domain hinzu:

```bash
# Cloudflare DNS (Beispiel)
playground.unit-y-ai.io -> <SWARM_MANAGER_IP>
```

### Deployment

```bash
# Stack mit Playground deployen
docker stack deploy -c compose/docker-compose.swarm.yml unityai

# Playground-Service überprüfen
docker service ls | grep playground
docker service logs unityai_n8n-playground
```

### Monitoring Integration

Das n8n-Playground bietet erweiterte Monitoring-Funktionen:

- **Prometheus Metriken**: `/metrics` Endpunkt
- **Health Checks**: `/health` und `/health/detailed`
- **API Dokumentation**: `/docs` (nur in Development)

## Service-Überwachung

### Status überprüfen

```bash
# Alle Services anzeigen
docker stack services unityai

# Detaillierte Service-Informationen
docker service ls
docker service ps unityai_app

# Service-Logs anzeigen
docker service logs unityai_app
docker service logs -f unityai_n8n
```

### Health Checks

```bash
# Service Health überprüfen
curl -f http://localhost:8000/health  # FastAPI
curl -f http://localhost:8001/health  # Python Worker
```

## Skalierung

### Services skalieren

```bash
# FastAPI Service skalieren
docker service scale unityai_app=5

# Python Worker skalieren
docker service scale unityai_python-worker=10

# n8n Runner skalieren
docker service scale unityai_runner-launcher=3

# n8n Playground skalieren
docker service scale unityai_n8n-playground=4
```

### Auto-Scaling

```bash
# Beispiel: CPU-basierte Skalierung
# (Erfordert zusätzliche Tools wie Portainer oder externe Orchestrierung)
```

## Updates und Wartung

### Rolling Updates

```bash
# Service-Image aktualisieren
docker service update \
  --image ghcr.io/flissel/n8n:v2.0.0 \
  unityai_n8n

# Rollback bei Problemen
docker service rollback unityai_n8n
```

### Backup

```bash
# PostgreSQL Backup
docker exec $(docker ps -q -f name=unityai_db) \
  pg_dump -U n8n_user n8n > backup_$(date +%Y%m%d).sql

# Volume Backup
docker run --rm -v unityai_postgres-data:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data
```

### Secrets rotieren

```bash
# Altes Secret entfernen
docker secret rm pg_pw

# Neues Secret erstellen
echo "new_password" | docker secret create pg_pw_v2 -

# Service mit neuem Secret aktualisieren
docker service update \
  --secret-rm pg_pw \
  --secret-add pg_pw_v2 \
  unityai_db
```

## Troubleshooting

### Häufige Probleme

#### Service startet nicht
```bash
# Service-Events überprüfen
docker service ps unityai_app --no-trunc

# Node-Ressourcen überprüfen
docker node ls
docker system df
```

#### Netzwerk-Probleme
```bash
# Netzwerk-Konnektivität testen
docker exec -it $(docker ps -q -f name=unityai_app) \
  ping unityai_db

# Overlay-Netzwerk überprüfen
docker network ls
docker network inspect unityai_unityai-network
```

#### Performance-Probleme
```bash
# Resource-Nutzung überprüfen
docker stats

# Service-Status über Docker Swarm überprüfen
docker service ls
```

### Logs sammeln

```bash
# Alle Service-Logs sammeln
for service in $(docker stack services unityai --format "{{.Name}}"); do
  echo "=== $service ==="
  docker service logs --tail 100 $service
done > unityai_logs_$(date +%Y%m%d).txt
```

## Sicherheit

### Firewall-Konfiguration

```bash
# Swarm Ports öffnen
sudo ufw allow 2377/tcp  # Cluster management
sudo ufw allow 7946/tcp  # Node communication
sudo ufw allow 7946/udp  # Node communication
sudo ufw allow 4789/udp  # Overlay network

# Application Ports
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
```

### SSL/TLS Zertifikate

Traefik verwaltet automatisch Let's Encrypt Zertifikate für alle konfigurierten Domains.

### Secrets Best Practices

- Verwende starke, zufällige Passwörter
- Rotiere Secrets regelmäßig
- Beschränke Secret-Zugriff auf notwendige Services
- Verwende niemals Secrets in Umgebungsvariablen

## Health Monitoring

### Service Health Checks

- **FastAPI:** `/health` Endpoint für API-Status
- **Python Worker:** `/health` Endpoint für Worker-Status
- **n8n:** Integrierte Health Checks
- **PostgreSQL:** Database-Konnektivität
- **Redis:** Cache-Verfügbarkeit

### Docker Swarm Monitoring

- **Service-Status:** `docker service ls`
- **Service-Details:** `docker service ps <service>`
- **Service-Logs:** `docker service logs <service>`
- **Node-Status:** `docker node ls`
- **Resource-Nutzung:** `docker stats`

## Performance-Optimierung

### Resource-Limits

```yaml
# Beispiel Service-Konfiguration
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

### Caching-Strategien

- **Redis:** Session-Caching, API-Response-Caching
- **PostgreSQL:** Query-Optimierung, Connection-Pooling
- **Traefik:** Static-Content-Caching

### Load Balancing

```yaml
# Traefik Load Balancer Konfiguration
labels:
  - "traefik.http.services.api.loadbalancer.healthcheck.path=/health"
  - "traefik.http.services.api.loadbalancer.healthcheck.interval=30s"
```

## Disaster Recovery

### Backup-Strategie

1. **Tägliche PostgreSQL-Backups**
2. **Wöchentliche Volume-Backups**
3. **Monatliche Full-System-Backups**
4. **Offsite-Backup-Storage**

### Recovery-Prozedur

```bash
# 1. Cluster neu aufsetzen
docker swarm init

# 2. Secrets wiederherstellen
# (aus sicherem Backup)

# 3. Volumes wiederherstellen
docker run --rm -v unityai_postgres-data:/data \
  -v $(pwd):/backup alpine \
  tar xzf /backup/postgres_backup_YYYYMMDD.tar.gz -C /

# 4. Stack deployen
docker stack deploy -c compose/docker-compose.swarm.yml unityai
```

## Weiterführende Ressourcen

- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [n8n Documentation](https://docs.n8n.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)