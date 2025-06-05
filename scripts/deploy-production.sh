#!/bin/bash
# Unity AI Production Deployment Script
# Automated deployment with health checks and rollback capability

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/unityai-deploy.log"
BACKUP_DIR="/opt/unityai/backups"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
MAX_ROLLBACK_ATTEMPTS=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

info() { log "INFO" "$*"; }
warn() { log "WARN" "${YELLOW}$*${NC}"; }
error() { log "ERROR" "${RED}$*${NC}"; }
success() { log "SUCCESS" "${GREEN}$*${NC}"; }

# Error handling
trap 'error "Deployment failed at line $LINENO. Exit code: $?"' ERR

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    error "This script should not be run as root for security reasons"
    exit 1
fi

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if required files exist
    local required_files=(
        "$PROJECT_DIR/$DOCKER_COMPOSE_FILE"
        "$PROJECT_DIR/.env.production"
        "$PROJECT_DIR/traefik/traefik.yml"
        "$PROJECT_DIR/traefik/dynamic.yml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file not found: $file"
            exit 1
        fi
    done
    
    success "Prerequisites check passed"
}

# Create backup
create_backup() {
    info "Creating backup..."
    
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="$BACKUP_DIR/unityai_backup_$backup_timestamp"
    
    mkdir -p "$backup_path"
    
    # Backup database
    if docker-compose -f "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" ps | grep -q unityai-db; then
        info "Backing up database..."
        docker-compose -f "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" exec -T db pg_dumpall -U postgres > "$backup_path/database_backup.sql"
    fi
    
    # Backup volumes
    info "Backing up Docker volumes..."
    docker run --rm -v unityai_postgres-data:/data -v "$backup_path:/backup" alpine tar czf /backup/postgres_data.tar.gz -C /data .
    docker run --rm -v unityai_redis-data:/data -v "$backup_path:/backup" alpine tar czf /backup/redis_data.tar.gz -C /data .
    docker run --rm -v unityai_n8n-data:/data -v "$backup_path:/backup" alpine tar czf /backup/n8n_data.tar.gz -C /data .
    
    # Backup configuration
    cp -r "$PROJECT_DIR/.env*" "$backup_path/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/traefik" "$backup_path/" 2>/dev/null || true
    
    echo "$backup_timestamp" > "$BACKUP_DIR/latest_backup"
    success "Backup created: $backup_path"
}

# Health check function
health_check() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    info "Performing health check for $service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            success "$service is healthy"
            return 0
        fi
        
        info "Health check attempt $attempt/$max_attempts for $service failed, retrying in 10s..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed for $service after $max_attempts attempts"
    return 1
}

# Deploy function
deploy() {
    info "Starting deployment..."
    
    cd "$PROJECT_DIR"
    
    # Pull latest images
    info "Pulling latest Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    # Build custom images
    info "Building custom images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    
    # Start services
    info "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    sleep 30
    
    # Perform health checks
    local health_checks=(
        "UnityAI API:https://api.unit-y-ai.io/health"
        "n8n:https://n8n.unit-y-ai.io"
        "Traefik:https://traefik.unit-y-ai.io/ping"
        "Grafana:https://grafana.unit-y-ai.io/api/health"
    )
    
    for check in "${health_checks[@]}"; do
        IFS=':' read -r service url <<< "$check"
        if ! health_check "$service" "$url"; then
            error "Deployment failed: $service health check failed"
            return 1
        fi
    done
    
    success "Deployment completed successfully"
}

# Rollback function
rollback() {
    local backup_timestamp=$1
    local backup_path="$BACKUP_DIR/unityai_backup_$backup_timestamp"
    
    if [[ ! -d "$backup_path" ]]; then
        error "Backup not found: $backup_path"
        return 1
    fi
    
    warn "Starting rollback to backup: $backup_timestamp"
    
    cd "$PROJECT_DIR"
    
    # Stop current services
    info "Stopping current services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    
    # Restore volumes
    info "Restoring Docker volumes..."
    docker run --rm -v unityai_postgres-data:/data -v "$backup_path:/backup" alpine tar xzf /backup/postgres_data.tar.gz -C /data
    docker run --rm -v unityai_redis-data:/data -v "$backup_path:/backup" alpine tar xzf /backup/redis_data.tar.gz -C /data
    docker run --rm -v unityai_n8n-data:/data -v "$backup_path:/backup" alpine tar xzf /backup/n8n_data.tar.gz -C /data
    
    # Restore configuration
    cp -r "$backup_path/.env"* "$PROJECT_DIR/" 2>/dev/null || true
    cp -r "$backup_path/traefik" "$PROJECT_DIR/" 2>/dev/null || true
    
    # Start services
    info "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    success "Rollback completed"
}

# Cleanup old backups
cleanup_backups() {
    info "Cleaning up old backups..."
    find "$BACKUP_DIR" -name "unityai_backup_*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    success "Old backups cleaned up"
}

# Main deployment process
main() {
    local action=${1:-deploy}
    
    case $action in
        "deploy")
            info "Starting Unity AI production deployment"
            check_prerequisites
            create_backup
            
            if deploy; then
                cleanup_backups
                success "Deployment completed successfully!"
                info "Services are available at:"
                info "  - API: https://api.unit-y-ai.io"
                info "  - n8n: https://n8n.unit-y-ai.io"
                info "  - Grafana: https://grafana.unit-y-ai.io"
                info "  - Traefik: https://traefik.unit-y-ai.io"
            else
                error "Deployment failed, initiating rollback..."
                local latest_backup=$(cat "$BACKUP_DIR/latest_backup" 2>/dev/null || echo "")
                if [[ -n "$latest_backup" ]]; then
                    rollback "$latest_backup"
                else
                    error "No backup available for rollback"
                fi
                exit 1
            fi
            ;;
        "rollback")
            local backup_timestamp=${2:-$(cat "$BACKUP_DIR/latest_backup" 2>/dev/null || echo "")}
            if [[ -z "$backup_timestamp" ]]; then
                error "No backup timestamp provided and no latest backup found"
                exit 1
            fi
            rollback "$backup_timestamp"
            ;;
        "status")
            info "Checking service status..."
            docker-compose -f "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" ps
            ;;
        "logs")
            local service=${2:-}
            if [[ -n "$service" ]]; then
                docker-compose -f "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" logs -f "$service"
            else
                docker-compose -f "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" logs -f
            fi
            ;;
        "backup")
            check_prerequisites
            create_backup
            ;;
        *)
            echo "Usage: $0 {deploy|rollback [timestamp]|status|logs [service]|backup}"
            exit 1
            ;;
    esac
}

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Run main function
main "$@"