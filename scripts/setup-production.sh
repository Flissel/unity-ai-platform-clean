#!/bin/bash
# Unity AI Production Setup Script
# Complete production environment setup with security hardening

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/unityai-setup.log"

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
trap 'error "Setup failed at line $LINENO. Exit code: $?"' ERR

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    error "This script should not be run as root for security reasons"
    exit 1
fi

# Function to prompt for user input
prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local default="${3:-}"
    local secret="${4:-false}"
    
    if [[ "$secret" == "true" ]]; then
        read -s -p "$prompt: " input
        echo
    else
        read -p "$prompt${default:+ [$default]}: " input
    fi
    
    if [[ -z "$input" && -n "$default" ]]; then
        input="$default"
    fi
    
    eval "$var_name='$input'"
}

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate JWT secret
generate_jwt_secret() {
    openssl rand -hex 32
}

# Function to create htpasswd entry
create_htpasswd() {
    local username="$1"
    local password="$2"
    echo "$username:$(openssl passwd -apr1 "$password")"
}

# Collect configuration
collect_configuration() {
    info "Collecting configuration for Unity AI production setup..."
    
    # Domain configuration
    prompt_input "Enter your domain (e.g., unit-y-ai.io)" DOMAIN
    
    # Cloudflare configuration
    prompt_input "Enter Cloudflare email" CLOUDFLARE_EMAIL
    prompt_input "Enter Cloudflare API token" CLOUDFLARE_TOKEN "" true
    
    # Database passwords
    prompt_input "Enter PostgreSQL password (leave empty to auto-generate)" POSTGRES_PASSWORD
    if [[ -z "$POSTGRES_PASSWORD" ]]; then
        POSTGRES_PASSWORD=$(generate_password)
        info "Generated PostgreSQL password: $POSTGRES_PASSWORD"
    fi
    
    prompt_input "Enter Redis password (leave empty to auto-generate)" REDIS_PASSWORD
    if [[ -z "$REDIS_PASSWORD" ]]; then
        REDIS_PASSWORD=$(generate_password)
        info "Generated Redis password: $REDIS_PASSWORD"
    fi
    
    # n8n configuration
    prompt_input "Enter n8n admin username" N8N_ADMIN_USER "admin"
    prompt_input "Enter n8n admin password (leave empty to auto-generate)" N8N_ADMIN_PASSWORD
    if [[ -z "$N8N_ADMIN_PASSWORD" ]]; then
        N8N_ADMIN_PASSWORD=$(generate_password)
        info "Generated n8n admin password: $N8N_ADMIN_PASSWORD"
    fi
    
    # Generate n8n encryption key
    N8N_ENCRYPTION_KEY=$(openssl rand -hex 16)
    
    # OpenAI configuration
    prompt_input "Enter OpenAI API key" OPENAI_API_KEY "" true
    
    # JWT secret
    JWT_SECRET=$(generate_jwt_secret)
    
    # Grafana configuration
    prompt_input "Enter Grafana admin password (leave empty to auto-generate)" GRAFANA_PASSWORD
    if [[ -z "$GRAFANA_PASSWORD" ]]; then
        GRAFANA_PASSWORD=$(generate_password)
        info "Generated Grafana admin password: $GRAFANA_PASSWORD"
    fi
    
    # Traefik basic auth
    TRAEFIK_AUTH=$(create_htpasswd "admin" "$GRAFANA_PASSWORD")
    
    # API key
    API_KEY=$(generate_password)
    
    success "Configuration collected successfully"
}

# Create production environment file
create_production_env() {
    info "Creating production environment file..."
    
    cat > "$PROJECT_DIR/.env.production" << EOF
# Unity AI Production Environment Configuration
# Generated on $(date)

# =============================================================================
# GENERAL APPLICATION SETTINGS
# =============================================================================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
APP_NAME="Unity AI Platform"
APP_VERSION=1.0.0

# =============================================================================
# DOMAIN AND SSL CONFIGURATION
# =============================================================================
DOMAIN=$DOMAIN
API_DOMAIN=api.$DOMAIN
N8N_DOMAIN=n8n.$DOMAIN
WEBHOOK_DOMAIN=webhooks.$DOMAIN
TRAEFIK_DOMAIN=traefik.$DOMAIN
GRAFANA_DOMAIN=grafana.$DOMAIN
METRICS_DOMAIN=metrics.$DOMAIN

# Cloudflare DNS API (for Let's Encrypt ACME)
CLOUDFLARE_EMAIL=$CLOUDFLARE_EMAIL
CLOUDFLARE_TOKEN=$CLOUDFLARE_TOKEN

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
POSTGRES_USER=unityai_prod
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=unityai_production
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/\${POSTGRES_DB}

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://:\${REDIS_PASSWORD}@\${REDIS_HOST}:\${REDIS_PORT}/\${REDIS_DB}

# =============================================================================
# N8N CONFIGURATION
# =============================================================================
N8N_ENCRYPTION_KEY=$N8N_ENCRYPTION_KEY
N8N_BASIC_AUTH_USER=$N8N_ADMIN_USER
N8N_BASIC_AUTH_PASSWORD=$N8N_ADMIN_PASSWORD
N8N_WEBHOOK_URL=https://\${WEBHOOK_DOMAIN}/
N8N_EDITOR_BASE_URL=https://\${N8N_DOMAIN}

# =============================================================================
# AUTOGEN / OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY=$OPENAI_API_KEY
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
API_KEY=$API_KEY
ALLOWED_HOSTS=api.$DOMAIN,webhooks.$DOMAIN,localhost
CORS_ORIGINS=https://$DOMAIN,https://api.$DOMAIN,https://n8n.$DOMAIN

# =============================================================================
# MONITORING AND OBSERVABILITY
# =============================================================================
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD

# =============================================================================
# TRAEFIK CONFIGURATION
# =============================================================================
TRAEFIK_BASIC_AUTH=$TRAEFIK_AUTH
ACME_EMAIL=$CLOUDFLARE_EMAIL

# =============================================================================
# FEATURE FLAGS
# =============================================================================
ENABLE_METRICS=true
ENABLE_TRACING=true
ENABLE_HEALTH_CHECKS=true
ENABLE_API_DOCS=false
ENABLE_CORS=true
ENABLE_RATE_LIMITING=true
ENABLE_AUTHENTICATION=true
EOF

    success "Production environment file created"
}

# Setup SSL certificates directory
setup_ssl() {
    info "Setting up SSL certificates directory..."
    
    mkdir -p "$PROJECT_DIR/traefik"
    touch "$PROJECT_DIR/traefik/acme.json"
    chmod 600 "$PROJECT_DIR/traefik/acme.json"
    
    success "SSL setup completed"
}

# Setup directories
setup_directories() {
    info "Setting up required directories..."
    
    local dirs=(
        "$PROJECT_DIR/logs"
        "$PROJECT_DIR/uploads"
        "$PROJECT_DIR/temp"
        "$PROJECT_DIR/backups"
        "$PROJECT_DIR/grafana/dashboards"
        "$PROJECT_DIR/grafana/datasources"
        "/opt/unityai/backups"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        info "Created directory: $dir"
    done
    
    success "Directory setup completed"
}

# Install system dependencies
install_dependencies() {
    info "Installing system dependencies..."
    
    # Update system
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        curl \
        wget \
        git \
        unzip \
        htop \
        vim \
        jq \
        openssl \
        ca-certificates \
        gnupg \
        lsb-release
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        info "Installing Docker..."
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        sudo usermod -aG docker $USER
        success "Docker installed successfully"
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        info "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        success "Docker Compose installed successfully"
    fi
    
    success "System dependencies installed"
}

# Setup firewall
setup_firewall() {
    info "Setting up firewall..."
    
    # Install UFW if not present
    if ! command -v ufw &> /dev/null; then
        sudo apt-get install -y ufw
    fi
    
    # Configure UFW
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow Traefik dashboard (optional, can be removed in production)
    sudo ufw allow 8080/tcp
    
    # Enable firewall
    sudo ufw --force enable
    
    success "Firewall configured"
}

# Setup systemd service
setup_systemd_service() {
    info "Setting up systemd service..."
    
    sudo tee /etc/systemd/system/unityai.service > /dev/null << EOF
[Unit]
Description=Unity AI Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=$USER
Group=docker

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable unityai.service
    
    success "Systemd service configured"
}

# Setup log rotation
setup_log_rotation() {
    info "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/unityai > /dev/null << EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f $PROJECT_DIR/docker-compose.prod.yml restart app
    endscript
}
EOF

    success "Log rotation configured"
}

# Setup backup cron job
setup_backup_cron() {
    info "Setting up backup cron job..."
    
    # Create backup script
    cat > "$PROJECT_DIR/scripts/backup.sh" << 'EOF'
#!/bin/bash
# Unity AI Backup Script

set -euo pipefail

PROJECT_DIR="$(dirname "$(dirname "$(realpath "$0")")")")
BACKUP_DIR="/opt/unityai/backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_PATH="$BACKUP_DIR/unityai_backup_$TIMESTAMP"

mkdir -p "$BACKUP_PATH"

# Backup database
docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T db pg_dumpall -U postgres > "$BACKUP_PATH/database_backup.sql"

# Backup volumes
docker run --rm -v unityai_postgres-data:/data -v "$BACKUP_PATH:/backup" alpine tar czf /backup/postgres_data.tar.gz -C /data .
docker run --rm -v unityai_redis-data:/data -v "$BACKUP_PATH:/backup" alpine tar czf /backup/redis_data.tar.gz -C /data .
docker run --rm -v unityai_n8n-data:/data -v "$BACKUP_PATH:/backup" alpine tar czf /backup/n8n_data.tar.gz -C /data .

# Cleanup old backups (keep 7 days)
find "$BACKUP_DIR" -name "unityai_backup_*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true

echo "Backup completed: $BACKUP_PATH"
EOF

    chmod +x "$PROJECT_DIR/scripts/backup.sh"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/scripts/backup.sh") | crontab -
    
    success "Backup cron job configured"
}

# Display final information
display_final_info() {
    success "Unity AI production setup completed successfully!"
    
    echo
    info "=== IMPORTANT INFORMATION ==="
    info "Domain: $DOMAIN"
    info "API URL: https://api.$DOMAIN"
    info "n8n URL: https://n8n.$DOMAIN"
    info "Grafana URL: https://grafana.$DOMAIN"
    info "Traefik Dashboard: https://traefik.$DOMAIN"
    echo
    info "=== CREDENTIALS ==="
    info "n8n Admin: $N8N_ADMIN_USER / $N8N_ADMIN_PASSWORD"
    info "Grafana Admin: admin / $GRAFANA_PASSWORD"
    info "API Key: $API_KEY"
    echo
    info "=== NEXT STEPS ==="
    info "1. Configure your DNS to point to this server"
    info "2. Start the services: cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml up -d"
    info "3. Check service status: systemctl status unityai"
    info "4. View logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo
    warn "SECURITY: Save the credentials above in a secure location!"
    warn "The .env.production file contains sensitive information."
}

# Main setup process
main() {
    info "Starting Unity AI production setup..."
    
    collect_configuration
    install_dependencies
    setup_directories
    create_production_env
    setup_ssl
    setup_firewall
    setup_systemd_service
    setup_log_rotation
    setup_backup_cron
    display_final_info
    
    success "Setup completed! You may need to log out and back in for Docker group changes to take effect."
}

# Create log directory
sudo mkdir -p "$(dirname "$LOG_FILE")"
sudo chown $USER:$USER "$(dirname "$LOG_FILE")"

# Run main function
main "$@"