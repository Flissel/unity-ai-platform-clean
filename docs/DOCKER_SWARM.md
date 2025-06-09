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
# FastAPI skalieren
docker service scale unityai_app=3

# Python Worker skalieren
docker service scale unityai_python-worker=5

# n8n Runner skalieren
docker service scale unityai_runner-launcher=3
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