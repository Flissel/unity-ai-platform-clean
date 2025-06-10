#!/bin/bash

# Quick Debug Script for UnityAI
# This script provides quick access to common debug and fix operations

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SERVER_HOST="${SERVER_HOST:-unit-y-ai.io}"
SSH_USER="${SSH_USER:-root}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"

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

# Execute remote command
exec_remote() {
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_HOST" "$1"
}

# Show menu
show_menu() {
    echo "UnityAI Quick Debug Menu"
    echo "========================"
    echo "1. Check stack status"
    echo "2. View service logs"
    echo "3. Build missing images"
    echo "4. Restart failed services"
    echo "5. Full debug report"
    echo "6. Fix HTTP 521 error"
    echo "7. Check endpoints"
    echo "8. Custom command"
    echo "9. Exit"
    echo ""
}

# Check stack status
check_status() {
    log_info "Checking UnityAI stack status..."
    exec_remote "docker stack services unityai"
    echo ""
    exec_remote "docker stack ps unityai --no-trunc"
}

# View service logs
view_logs() {
    echo "Available services:"
    exec_remote "docker service ls --filter 'label=com.docker.stack.namespace=unityai' --format '{{.Name}}'"
    echo ""
    read -p "Enter service name (or 'all' for all services): " service_name
    
    if [[ "$service_name" == "all" ]]; then
        for service in $(exec_remote "docker service ls --filter 'label=com.docker.stack.namespace=unityai' --format '{{.Name}}'"); do
            log_info "Logs for $service:"
            exec_remote "docker service logs --tail 50 $service"
            echo "" 
        done
    else
        exec_remote "docker service logs --tail 100 $service_name"
    fi
}

# Build missing images
build_images() {
    log_info "Building missing Docker images..."
    
    # Build images locally first
    log_info "Building images locally..."
    
    # Main app image
    log_info "Building unityai-app..."
    docker build -t unityai-app .
    
    # Frontend image
    log_info "Building unityai-frontend..."
    docker build -t unityai-frontend ./frontend/
    
    # Python worker image
    log_info "Building unityai-python-worker..."
    docker build -t unityai-python-worker ./python/
    
    # N8N playground image
    log_info "Building unityai-n8n-playground..."
    docker build -t unityai-n8n-playground ./n8n-playground/
    
    log_success "All images built locally"
    
    # Save and transfer images to server
    log_info "Saving images to tar files..."
    docker save unityai-app | gzip > unityai-app.tar.gz
    docker save unityai-frontend | gzip > unityai-frontend.tar.gz
    docker save unityai-python-worker | gzip > unityai-python-worker.tar.gz
    docker save unityai-n8n-playground | gzip > unityai-n8n-playground.tar.gz
    
    log_info "Transferring images to server..."
    scp -i "$SSH_KEY" *.tar.gz "$SSH_USER@$SERVER_HOST:/tmp/"
    
    log_info "Loading images on server..."
    exec_remote "cd /tmp && docker load < unityai-app.tar.gz"
    exec_remote "cd /tmp && docker load < unityai-frontend.tar.gz"
    exec_remote "cd /tmp && docker load < unityai-python-worker.tar.gz"
    exec_remote "cd /tmp && docker load < unityai-n8n-playground.tar.gz"
    
    # Cleanup
    rm -f *.tar.gz
    exec_remote "rm -f /tmp/*.tar.gz"
    
    log_success "Images transferred and loaded on server"
}

# Restart failed services
restart_services() {
    log_info "Restarting failed services..."
    
    # Remove and redeploy stack
    log_warning "Removing current stack..."
    exec_remote "docker stack rm unityai"
    
    log_info "Waiting for cleanup..."
    sleep 30
    
    log_info "Redeploying stack..."
    exec_remote "cd /opt/unityai && docker stack deploy -c compose/docker-compose.swarm.yml unityai"
    
    log_info "Waiting for services to start..."
    sleep 30
    
    log_info "New service status:"
    exec_remote "docker stack services unityai"
}

# Full debug report
full_debug() {
    log_info "Running full debug report..."
    ./debug-server.sh
}

# Fix HTTP 521 error
fix_521_error() {
    log_info "Fixing HTTP 521 error..."
    
    log_info "Step 1: Building missing images..."
    build_images
    
    log_info "Step 2: Restarting services..."
    restart_services
    
    log_info "Step 3: Checking endpoints..."
    check_endpoints
    
    log_success "HTTP 521 fix completed"
}

# Check endpoints
check_endpoints() {
    log_info "Checking application endpoints..."
    
    endpoints=(
        "https://api.unit-y-ai.io/health"
        "https://n8n.unit-y-ai.io"
        "https://traefik.unit-y-ai.io"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log_info "Testing $endpoint..."
        status=$(exec_remote "curl -s -o /dev/null -w '%{http_code}' '$endpoint' || echo 'failed'")
        if [[ "$status" == "200" ]]; then
            log_success "$endpoint: OK ($status)"
        else
            log_error "$endpoint: FAILED ($status)"
        fi
    done
}

# Custom command
custom_command() {
    read -p "Enter command to execute on server: " command
    if [[ -n "$command" ]]; then
        log_info "Executing: $command"
        exec_remote "$command"
    fi
}

# Main menu loop
main() {
    while true; do
        show_menu
        read -p "Select option (1-9): " choice
        
        case $choice in
            1) check_status ;;
            2) view_logs ;;
            3) build_images ;;
            4) restart_services ;;
            5) full_debug ;;
            6) fix_521_error ;;
            7) check_endpoints ;;
            8) custom_command ;;
            9) log_info "Goodbye!"; exit 0 ;;
            *) log_error "Invalid option. Please try again." ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        clear
    done
}

# Check if running with argument
if [[ $# -gt 0 ]]; then
    case $1 in
        "status") check_status ;;
        "logs") view_logs ;;
        "build") build_images ;;
        "restart") restart_services ;;
        "debug") full_debug ;;
        "fix521") fix_521_error ;;
        "endpoints") check_endpoints ;;
        *) log_error "Unknown command: $1" ;;
    esac
else
    main
fi