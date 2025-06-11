#!/bin/bash

# UnityAI Docker Swarm Deployment Script
# Dieses Skript richtet Docker Swarm ein und deployt die UnityAI-Anwendung

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging-Funktionen
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Überprüfe ob Docker installiert ist
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker ist nicht installiert. Bitte installiere Docker zuerst."
        exit 1
    fi
    log_success "Docker ist installiert"
}

# Überprüfe ob Docker Swarm aktiv ist
check_swarm() {
    if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q "active"; then
        log_warning "Docker Swarm ist nicht aktiv. Initialisiere Swarm..."
        docker swarm init
        log_success "Docker Swarm initialisiert"
    else
        log_success "Docker Swarm ist bereits aktiv"
    fi
}

# Erstelle externe Netzwerke
create_networks() {
    log_info "Erstelle externe Netzwerke..."
    
    # Traefik Public Network
    if ! docker network ls --format '{{.Name}}' | grep -q "^traefik-public$"; then
        docker network create \
            --driver overlay \
            --attachable \
            traefik-public
        log_success "Netzwerk 'traefik-public' erstellt"
    else
        log_info "Netzwerk 'traefik-public' existiert bereits"
    fi
}

# Erstelle Docker Secrets
create_secrets() {
    log_info "Erstelle Docker Secrets..."
    
    # Überprüfe ob .env.secrets existiert
    if [[ ! -f ".env.secrets" ]]; then
        log_error ".env.secrets Datei nicht gefunden. Bitte erstelle diese Datei mit allen notwendigen Secrets."
        cat << EOF
Beispiel .env.secrets:
PG_PASSWORD=your_postgres_password
N8N_ADMIN_PASSWORD=your_n8n_password
N8N_ENCRYPTION_KEY=your_encryption_key
REDIS_PASSWORD=your_redis_password
RUNNER_TOKEN=your_runner_token
CLOUDFLARE_EMAIL=your_cloudflare_email
CLOUDFLARE_TOKEN=your_cloudflare_token
EOF
        exit 1
    fi
    
    # Lade Secrets aus .env.secrets
    source .env.secrets
    
    # Erstelle Secrets
    secrets=(
        "pg_pw:$PG_PASSWORD"
        "n8n_admin_password:$N8N_ADMIN_PASSWORD"
        "n8n_encryption_key:$N8N_ENCRYPTION_KEY"
        "redis_pw:$REDIS_PASSWORD"
        "runner_token:$RUNNER_TOKEN"
        "cloudflare_email:$CLOUDFLARE_EMAIL"
        "cloudflare_token:$CLOUDFLARE_TOKEN"
    )
    
    for secret in "${secrets[@]}"; do
        secret_name=$(echo $secret | cut -d':' -f1)
        secret_value=$(echo $secret | cut -d':' -f2-)
        
        if ! docker secret ls --format '{{.Name}}' | grep -q "^${secret_name}$"; then
            echo "$secret_value" | docker secret create "$secret_name" -
            log_success "Secret '$secret_name' erstellt"
        else
            log_info "Secret '$secret_name' existiert bereits"
        fi
    done
}

# Label Nodes für Placement Constraints
label_nodes() {
    log_info "Setze Node Labels für Service Placement..."
    
    # Node Labels setzen
    echo "Setting node labels..."
    docker node update --label-add postgres=true $(docker node ls --format "{{.Hostname}}" --filter "role=manager" | head -1)
    docker node update --label-add redis=true $(docker node ls --format "{{.Hostname}}" --filter "role=manager" | head -1)
    docker node update --label-add n8n=true $(docker node ls --format "{{.Hostname}}" --filter "role=manager" | head -1)
    
    # Worker Node Labels
    for node in $(docker node ls --format "{{.Hostname}}" --filter "role=worker"); do
        docker node update --label-add worker=true $node
        docker node update --label-add app=true $node
    done
}

# Erstelle notwendige Verzeichnisse auf Nodes
create_directories() {
    log_info "Erstelle notwendige Verzeichnisse..."
    
    directories=(
        "/opt/unityai/data"
        "/opt/unityai/logs"
        "/opt/unityai/uploads"
        "/opt/unityai/scripts"

    )
    
    for dir in "${directories[@]}"; do
        sudo mkdir -p "$dir"
        sudo chown -R 1000:1000 "$dir"
        log_success "Verzeichnis '$dir' erstellt"
    done
}

# Deploy Stack
deploy_stack() {
    log_info "Deploye UnityAI Stack..."
    
    # Überprüfe ob compose file existiert
    if [[ ! -f "compose/docker-compose.swarm.yml" ]]; then
        log_error "docker-compose.swarm.yml nicht gefunden!"
        exit 1
    fi
    
    # Deploy Stack
    docker stack deploy -c compose/docker-compose.swarm.yml unityai
    log_success "UnityAI Stack deployed"
    
    # Warte auf Services
    log_info "Warte auf Service-Start..."
    sleep 30
    
    # Zeige Service Status
    docker stack services unityai
}

# Überprüfe Service Health
check_health() {
    log_info "Überprüfe Service Health..."
    
    services=("unityai_app" "unityai_n8n" "unityai_python-worker")
    
    for service in "${services[@]}"; do
        replicas=$(docker service ls --filter name="$service" --format '{{.Replicas}}')
        log_info "$service: $replicas"
    done
    
    log_info "Für detaillierte Logs verwende: docker service logs <service_name>"
}

# Zeige Zugriffs-URLs
show_urls() {
    log_success "Deployment abgeschlossen!"
    echo
    log_info "Zugriffs-URLs:"
    echo "  • API: https://api.unit-y-ai.io"
    echo "  • n8n: https://n8n.unit-y-ai.io"
    echo "  • Traefik Dashboard: https://traefik.unit-y-ai.io"
    echo
    log_info "Nützliche Befehle:"
    echo "  • Stack Status: docker stack services unityai"
    echo "  • Service Logs: docker service logs unityai_<service_name>"
    echo "  • Stack entfernen: docker stack rm unityai"
}

# Hauptfunktion
main() {
    log_info "Starte UnityAI Docker Swarm Deployment..."
    
    check_docker
    check_swarm
    create_networks
    create_secrets
    label_nodes
    create_directories
    deploy_stack
    check_health
    show_urls
    
    log_success "Deployment erfolgreich abgeschlossen!"
}

# Führe Hauptfunktion aus
main "$@"