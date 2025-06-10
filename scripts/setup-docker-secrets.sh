#!/bin/bash
# Unity AI Platform - Docker Secrets Setup Script
# CRITICAL: This script handles sensitive API keys and secrets
# WARNING: Never commit this script with real secrets to version control!

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_FILE="$PROJECT_ROOT/config/secrets.env"
ENV_FILE="$PROJECT_ROOT/config/.env.production"
LOG_FILE="$PROJECT_ROOT/logs/secrets-setup-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================
log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# SECURITY FUNCTIONS
# =============================================================================
check_docker_swarm() {
    log_info "Checking Docker Swarm status..."
    
    if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q "active"; then
        log_warning "Docker Swarm is not initialized. Initializing now..."
        docker swarm init
        log_success "Docker Swarm initialized successfully"
    else
        log_info "Docker Swarm is already active"
    fi
}

load_secrets() {
    log_info "Loading secrets configuration..."
    
    if [[ ! -f "$SECRETS_FILE" ]]; then
        log_error "Secrets file not found: $SECRETS_FILE"
        log_error "Please ensure the secrets.env file exists with real API keys"
        log_error "This file should contain the actual secrets, not Docker secret references"
        exit 1
    fi
    
    # Source secrets file
    set -a
    source "$SECRETS_FILE"
    set +a
    
    log_success "Secrets configuration loaded"
}

load_environment() {
    log_info "Loading environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file not found: $ENV_FILE"
        log_error "Please ensure the production environment file exists"
        exit 1
    fi
    
    # Source environment file (for non-secret configs)
    set -a
    source "$ENV_FILE"
    set +a
    
    log_success "Environment configuration loaded"
}

create_secret_if_not_exists() {
    local secret_name="$1"
    local secret_value="$2"
    local description="$3"
    
    if docker secret inspect "$secret_name" &>/dev/null; then
        log_info "Secret '$secret_name' already exists, skipping"
        return 0
    fi
    
    if [[ -z "$secret_value" ]] || [[ "$secret_value" == *"CHANGE-THIS"* ]] || [[ "$secret_value" == *"your-"* ]]; then
        log_error "Invalid or placeholder value for secret '$secret_name' ($description)"
        log_error "Please update the environment file with real values"
        return 1
    fi
    
    echo -n "$secret_value" | docker secret create "$secret_name" -
    log_success "Created secret '$secret_name' ($description)"
}

generate_secure_password() {
    local length="${1:-32}"
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

generate_jwt_secret() {
    openssl rand -hex 32
}

# =============================================================================
# MAIN SECRETS SETUP
# =============================================================================
setup_production_secrets() {
    log_info "Setting up production secrets for Unity AI Platform..."
    
    # Generate secure passwords if they contain placeholders
    if [[ "$POSTGRES_PASSWORD" == *"CHANGE-THIS"* ]]; then
        POSTGRES_PASSWORD=$(generate_secure_password 24)
        log_info "Generated secure PostgreSQL password"
    fi
    
    if [[ "$REDIS_PASSWORD" == *"CHANGE-THIS"* ]]; then
        REDIS_PASSWORD=$(generate_secure_password 24)
        log_info "Generated secure Redis password"
    fi
    
    if [[ "$SECRET_KEY" == *"CHANGE-THIS"* ]]; then
        SECRET_KEY=$(generate_jwt_secret)
        log_info "Generated secure JWT secret key"
    fi
    
    if [[ "$N8N_ADMIN_PASSWORD" == *"CHANGE-THIS"* ]]; then
        N8N_ADMIN_PASSWORD=$(generate_secure_password 16)
        log_info "Generated secure n8n admin password"
    fi
    
    if [[ "$N8N_ENCRYPTION_KEY" == *"CHANGE-THIS"* ]]; then
        N8N_ENCRYPTION_KEY=$(openssl rand -hex 16)
        log_info "Generated secure n8n encryption key"
    fi
    
    # Create Docker secrets
    log_info "Creating Docker secrets..."
    
    # Database secrets
    create_secret_if_not_exists "postgres_user" "$POSTGRES_USER" "PostgreSQL username"
    create_secret_if_not_exists "postgres_password" "$POSTGRES_PASSWORD" "PostgreSQL password"
    create_secret_if_not_exists "postgres_db" "$POSTGRES_DB" "PostgreSQL database name"
    
    # Redis secrets
    create_secret_if_not_exists "redis_password" "$REDIS_PASSWORD" "Redis password"
    
    # Application secrets
    create_secret_if_not_exists "secret_key" "$SECRET_KEY" "JWT secret key"
    create_secret_if_not_exists "api_keys" "$API_KEYS" "API authentication keys"
    
    # n8n secrets
    create_secret_if_not_exists "n8n_admin_user" "$N8N_ADMIN_USER" "n8n admin username"
    create_secret_if_not_exists "n8n_admin_password" "$N8N_ADMIN_PASSWORD" "n8n admin password"
    create_secret_if_not_exists "n8n_encryption_key" "$N8N_ENCRYPTION_KEY" "n8n encryption key"
    create_secret_if_not_exists "n8n_api_key" "$N8N_API_KEY" "n8n API key for FastAPI integration"
    
    # External API secrets
    create_secret_if_not_exists "openai_api_key" "$OPENAI_API_KEY" "OpenAI API key"
    create_secret_if_not_exists "cloudflare_email" "$CLOUDFLARE_EMAIL" "Cloudflare email"
    create_secret_if_not_exists "cloudflare_token" "$CLOUDFLARE_TOKEN" "Cloudflare DNS API token"
    

    
    log_success "All Docker secrets created successfully!"
}

list_secrets() {
    log_info "Current Docker secrets:"
    docker secret ls --format "table {{.Name}}\t{{.CreatedAt}}\t{{.UpdatedAt}}"
}

validate_secrets() {
    log_info "Validating created secrets..."
    
    local required_secrets=(
        "postgres_password"
        "redis_password"
        "secret_key"
        "n8n_api_key"
        "openai_api_key"
        "cloudflare_token"
    )
    
    local missing_secrets=()
    for secret in "${required_secrets[@]}"; do
        if ! docker secret inspect "$secret" &>/dev/null; then
            missing_secrets+=("$secret")
        fi
    done
    
    if [[ ${#missing_secrets[@]} -gt 0 ]]; then
        log_error "Missing required secrets: ${missing_secrets[*]}"
        return 1
    fi
    
    log_success "All required secrets are present"
}

show_credentials() {
    log_info "=== IMPORTANT: Save these credentials securely ==="
    echo
    echo "PostgreSQL Database:"
    echo "  Username: $POSTGRES_USER"
    echo "  Password: $POSTGRES_PASSWORD"
    echo "  Database: $POSTGRES_DB"
    echo
    echo "Redis Cache:"
    echo "  Password: $REDIS_PASSWORD"
    echo
    echo "n8n Workflow Platform:"
    echo "  Admin User: $N8N_ADMIN_USER"
    echo "  Admin Password: $N8N_ADMIN_PASSWORD"
    echo "  URL: https://$N8N_DOMAIN"
    echo
    echo
    echo "FastAPI Application:"
    echo "  URL: https://$API_DOMAIN"
    echo "  Documentation: https://$API_DOMAIN/docs"
    echo
    log_warning "Store these credentials in a secure password manager!"
    log_warning "These will not be displayed again after this setup."
}

# =============================================================================
# CLEANUP AND SECURITY
# =============================================================================
secure_cleanup() {
    log_info "Performing security cleanup..."
    
    # Clear environment variables from memory
    unset POSTGRES_PASSWORD REDIS_PASSWORD SECRET_KEY N8N_ADMIN_PASSWORD
    unset N8N_ENCRYPTION_KEY N8N_API_KEY OPENAI_API_KEY CLOUDFLARE_TOKEN
    unset CLOUDFLARE_EMAIL
    
    # Clear bash history of this session
    history -c
    
    # Recommend deleting the secrets file
    if [[ -f "$SECRETS_FILE" ]]; then
        log_warning "SECURITY REMINDER: Delete the secrets file after setup!"
        log_warning "Run: rm \"$SECRETS_FILE\""
    fi
    
    log_success "Security cleanup completed"
}

trap secure_cleanup EXIT

# =============================================================================
# MAIN EXECUTION
# =============================================================================
main() {
    log_info "Unity AI Platform - Docker Secrets Setup"
    log_info "Log file: $LOG_FILE"
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check prerequisites
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL is not installed or not in PATH"
        exit 1
    fi
    
    # Setup Docker Swarm and secrets
    check_docker_swarm
    load_environment
    load_secrets
    setup_production_secrets
    validate_secrets
    
    # Display results
    list_secrets
    show_credentials
    
    log_success "Docker secrets setup completed successfully!"
    log_info "You can now deploy the Unity AI Platform using: ./deploy-production.sh"
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-setup}" in
        "setup")
            main
            ;;
        "list")
            list_secrets
            ;;
        "validate")
            load_environment
            load_secrets
            validate_secrets
            ;;
        "cleanup")
            log_warning "This will remove ALL Docker secrets. Are you sure? (y/N)"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                docker secret ls -q | xargs -r docker secret rm
                log_success "All secrets removed"
            else
                log_info "Cleanup cancelled"
            fi
            ;;
        *)
            echo "Usage: $0 [setup|list|validate|cleanup]"
            echo "  setup    - Create Docker secrets (default)"
            echo "  list     - List existing secrets"
            echo "  validate - Validate required secrets exist"
            echo "  cleanup  - Remove all secrets (DANGEROUS)"
            exit 1
            ;;
    esac
fi