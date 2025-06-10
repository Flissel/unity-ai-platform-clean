#!/bin/bash

# UnityAI Server Debug Script
# This script connects to the server, executes debug commands, and sends results back

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_HOST="${SERVER_HOST:-unit-y-ai.io}"
SSH_USER="${SSH_USER:-root}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"
LOG_FILE="debug-results-$(date +%Y%m%d-%H%M%S).log"
REMOTE_LOG_FILE="/tmp/unityai-debug-$(date +%Y%m%d-%H%M%S).log"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v ssh &> /dev/null; then
        log_error "SSH client not found. Please install OpenSSH."
        exit 1
    fi
    
    if [[ ! -f "$SSH_KEY" ]]; then
        log_warning "SSH key not found at $SSH_KEY. Will try password authentication."
    fi
    
    log_success "Prerequisites check completed"
}

# Test SSH connection
test_ssh_connection() {
    log_info "Testing SSH connection to $SSH_USER@$SERVER_HOST..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes -i "$SSH_KEY" "$SSH_USER@$SERVER_HOST" "echo 'SSH connection successful'" 2>/dev/null; then
        log_success "SSH connection established"
        return 0
    else
        log_error "SSH connection failed"
        return 1
    fi
}

# Execute remote command
execute_remote_command() {
    local command="$1"
    local description="$2"
    
    log_info "Executing: $description"
    echo "Command: $command" >> "$LOG_FILE"
    
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_HOST" "$command" 2>&1 | tee -a "$LOG_FILE"
    local exit_code=${PIPESTATUS[0]}
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Command completed successfully"
    else
        log_warning "Command completed with exit code: $exit_code"
    fi
    
    echo "" >> "$LOG_FILE"
    return $exit_code
}

# Docker system information
check_docker_system() {
    log_info "=== DOCKER SYSTEM INFORMATION ==="
    
    execute_remote_command "docker --version" "Docker version"
    execute_remote_command "docker info" "Docker system info"
    execute_remote_command "docker system df" "Docker disk usage"
    execute_remote_command "docker system events --since 1h --until now" "Recent Docker events"
}

# Docker Swarm status
check_swarm_status() {
    log_info "=== DOCKER SWARM STATUS ==="
    
    execute_remote_command "docker info --format '{{.Swarm.LocalNodeState}}'" "Swarm state"
    execute_remote_command "docker node ls" "Swarm nodes"
    execute_remote_command "docker network ls" "Docker networks"
    execute_remote_command "docker secret ls" "Docker secrets"
}

# UnityAI stack status
check_unityai_stack() {
    log_info "=== UNITYAI STACK STATUS ==="
    
    execute_remote_command "docker stack ls" "All stacks"
    execute_remote_command "docker stack services unityai" "UnityAI services"
    execute_remote_command "docker stack ps unityai" "UnityAI tasks"
    
    # Check individual service logs
    local services=("unityai_app" "unityai_frontend" "unityai_python-worker" "unityai_n8n-playground" "unityai_db" "unityai_redis" "unityai_n8n")
    
    for service in "${services[@]}"; do
        execute_remote_command "docker service ps $service --no-trunc" "Service tasks for $service"
        execute_remote_command "docker service logs --tail 50 $service" "Recent logs for $service"
    done
}

# Check images
check_images() {
    log_info "=== DOCKER IMAGES ==="
    
    execute_remote_command "docker images" "All images"
    execute_remote_command "docker images | grep unityai" "UnityAI custom images"
}

# System resources
check_system_resources() {
    log_info "=== SYSTEM RESOURCES ==="
    
    execute_remote_command "df -h" "Disk usage"
    execute_remote_command "free -h" "Memory usage"
    execute_remote_command "top -bn1 | head -20" "CPU and process info"
    execute_remote_command "netstat -tlnp" "Network ports"
}

# Check Traefik
check_traefik() {
    log_info "=== TRAEFIK STATUS ==="
    
    execute_remote_command "docker service logs --tail 50 unityai_traefik" "Traefik logs"
    execute_remote_command "curl -s http://localhost:8080/api/rawdata | jq ." "Traefik API (if available)"
}

# Check application endpoints
check_endpoints() {
    log_info "=== APPLICATION ENDPOINTS ==="
    
    local endpoints=(
        "https://api.unit-y-ai.io/health"
        "https://n8n.unit-y-ai.io"
        "https://traefik.unit-y-ai.io"
        "http://localhost:8000"
        "http://localhost:5678"
    )
    
    for endpoint in "${endpoints[@]}"; do
        execute_remote_command "curl -s -o /dev/null -w '%{http_code}' '$endpoint' || echo 'Connection failed'" "HTTP status for $endpoint"
    done
}

# Custom command execution
execute_custom_command() {
    if [[ -n "$1" ]]; then
        log_info "=== CUSTOM COMMAND ==="
        execute_remote_command "$1" "Custom command: $1"
    fi
}

# Generate comprehensive report
generate_report() {
    log_info "=== GENERATING COMPREHENSIVE REPORT ==="
    
    local report_script="/tmp/unityai-debug-report.sh"
    
    # Create comprehensive debug script on remote server
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_HOST" "cat > $report_script << 'EOF'
#!/bin/bash
echo '=== UNITYAI DEBUG REPORT ==='
echo 'Generated on: \$(date)'
echo 'Hostname: \$(hostname)'
echo ''

echo '--- Docker Version ---'
docker --version
echo ''

echo '--- Docker Swarm Status ---'
docker info --format '{{.Swarm.LocalNodeState}}'
echo ''

echo '--- UnityAI Stack Services ---'
docker stack services unityai 2>/dev/null || echo 'UnityAI stack not found'
echo ''

echo '--- Service Tasks ---'
docker stack ps unityai --no-trunc 2>/dev/null || echo 'No tasks found'
echo ''

echo '--- Failed Services ---'
docker service ls --filter 'label=com.docker.stack.namespace=unityai' --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}' | grep '0/'
echo ''

echo '--- Recent Service Logs (Last 20 lines each) ---'
for service in \$(docker service ls --filter 'label=com.docker.stack.namespace=unityai' --format '{{.Name}}'); do
    echo "--- Logs for \$service ---"
    docker service logs --tail 20 \$service 2>/dev/null || echo "No logs available for \$service"
    echo ''
done

echo '--- System Resources ---'
echo 'Memory:'
free -h
echo 'Disk:'
df -h
echo 'Load:'
uptime
echo ''

echo '--- Network Connectivity ---'
echo 'Listening ports:'
netstat -tlnp | grep LISTEN
echo ''

echo '--- Docker Images ---'
docker images | grep -E '(unityai|REPOSITORY)'
echo ''

echo '=== END OF REPORT ==='
EOF"
    
    # Execute the report script
    execute_remote_command "chmod +x $report_script && $report_script" "Comprehensive debug report"
    
    # Clean up
    execute_remote_command "rm -f $report_script" "Cleanup temporary script"
}

# Download logs from server
download_logs() {
    log_info "Downloading logs from server..."
    
    # Create remote log collection script
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_HOST" "mkdir -p /tmp/unityai-logs"
    
    # Collect service logs
    execute_remote_command "docker service ls --filter 'label=com.docker.stack.namespace=unityai' --format '{{.Name}}' | xargs -I {} docker service logs --tail 100 {} > /tmp/unityai-logs/{}.log 2>&1" "Collecting service logs"
    
    # Create archive
    execute_remote_command "cd /tmp && tar -czf unityai-logs-$(date +%Y%m%d-%H%M%S).tar.gz unityai-logs/" "Creating log archive"
    
    # Download archive
    log_info "Downloading log archive..."
    scp -i "$SSH_KEY" "$SSH_USER@$SERVER_HOST:/tmp/unityai-logs-*.tar.gz" . 2>/dev/null || log_warning "Failed to download log archive"
    
    # Cleanup remote files
    execute_remote_command "rm -rf /tmp/unityai-logs /tmp/unityai-logs-*.tar.gz" "Cleaning up remote log files"
}

# Main execution function
main() {
    local custom_command="$1"
    
    log_info "Starting UnityAI Server Debug Session"
    log_info "Log file: $LOG_FILE"
    log_info "Target server: $SSH_USER@$SERVER_HOST"
    echo "" >> "$LOG_FILE"
    
    check_prerequisites
    
    if ! test_ssh_connection; then
        log_error "Cannot establish SSH connection. Exiting."
        exit 1
    fi
    
    # Execute debug checks
    check_docker_system
    check_swarm_status
    check_unityai_stack
    check_images
    check_system_resources
    check_traefik
    check_endpoints
    
    # Execute custom command if provided
    execute_custom_command "$custom_command"
    
    # Generate comprehensive report
    generate_report
    
    # Download logs
    download_logs
    
    log_success "Debug session completed"
    log_info "Results saved to: $LOG_FILE"
    
    # Show summary
    echo ""
    log_info "=== DEBUG SUMMARY ==="
    echo "• Log file: $LOG_FILE"
    echo "• Server: $SSH_USER@$SERVER_HOST"
    echo "• Session completed at: $(date)"
    
    if [[ -f "unityai-logs-*.tar.gz" ]]; then
        echo "• Downloaded logs: $(ls unityai-logs-*.tar.gz 2>/dev/null | head -1)"
    fi
    
    echo ""
    log_info "To view the complete log: cat $LOG_FILE"
    log_info "To re-run with custom command: $0 'your-command-here'"
}

# Help function
show_help() {
    echo "UnityAI Server Debug Script"
    echo ""
    echo "Usage: $0 [custom-command]"
    echo ""
    echo "Environment variables:"
    echo "  SERVER_HOST    - Target server hostname (default: unit-y-ai.io)"
    echo "  SSH_USER       - SSH username (default: root)"
    echo "  SSH_KEY        - SSH private key path (default: ~/.ssh/id_rsa)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run full debug session"
    echo "  $0 'docker stack ps unityai'         # Run with custom command"
    echo "  SERVER_HOST=myserver.com $0           # Use different server"
    echo ""
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"