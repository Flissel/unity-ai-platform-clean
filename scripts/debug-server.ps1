# UnityAI Server Debug Script (PowerShell)
# This script connects to the server, executes debug commands, and sends results back

param(
    [string]$CustomCommand = "",
    [string]$ServerHost = "unit-y-ai.io",
    [string]$SshUser = "root",
    [string]$SshKey = "~/.ssh/id_rsa",
    [switch]$Help
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

# Configuration
$LogFile = "debug-results-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$RemoteLogFile = "/tmp/unityai-debug-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Logging functions
function Write-LogInfo {
    param([string]$Message)
    $LogMessage = "${Blue}[INFO]${Reset} $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value "[INFO] $Message"
}

function Write-LogSuccess {
    param([string]$Message)
    $LogMessage = "${Green}[SUCCESS]${Reset} $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value "[SUCCESS] $Message"
}

function Write-LogWarning {
    param([string]$Message)
    $LogMessage = "${Yellow}[WARNING]${Reset} $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value "[WARNING] $Message"
}

function Write-LogError {
    param([string]$Message)
    $LogMessage = "${Red}[ERROR]${Reset} $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value "[ERROR] $Message"
}

# Show help
function Show-Help {
    Write-Host "UnityAI Server Debug Script (PowerShell)"
    Write-Host ""
    Write-Host "Usage: .\debug-server.ps1 [-CustomCommand <command>] [-ServerHost <host>] [-SshUser <user>] [-SshKey <keypath>]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -CustomCommand  Custom command to execute on server"
    Write-Host "  -ServerHost     Target server hostname (default: unit-y-ai.io)"
    Write-Host "  -SshUser        SSH username (default: root)"
    Write-Host "  -SshKey         SSH private key path (default: ~/.ssh/id_rsa)"
    Write-Host "  -Help           Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\debug-server.ps1"
    Write-Host "  .\debug-server.ps1 -CustomCommand 'docker stack ps unityai'"
    Write-Host "  .\debug-server.ps1 -ServerHost myserver.com -SshUser admin"
    Write-Host ""
}

# Check prerequisites
function Test-Prerequisites {
    Write-LogInfo "Checking prerequisites..."
    
    # Check if SSH client is available
    try {
        $null = Get-Command ssh -ErrorAction Stop
        Write-LogSuccess "SSH client found"
    }
    catch {
        Write-LogError "SSH client not found. Please install OpenSSH or use WSL."
        return $false
    }
    
    # Check SSH key
    $expandedKeyPath = [Environment]::ExpandEnvironmentVariables($SshKey)
    if (-not (Test-Path $expandedKeyPath)) {
        Write-LogWarning "SSH key not found at $expandedKeyPath. Will try password authentication."
    }
    
    Write-LogSuccess "Prerequisites check completed"
    return $true
}

# Test SSH connection
function Test-SshConnection {
    Write-LogInfo "Testing SSH connection to $SshUser@$ServerHost..."
    
    $sshArgs = @(
        "-o", "ConnectTimeout=10",
        "-o", "BatchMode=yes",
        "-i", $SshKey,
        "$SshUser@$ServerHost",
        "echo 'SSH connection successful'"
    )
    
    try {
        $result = & ssh @sshArgs 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "SSH connection established"
            return $true
        }
        else {
            Write-LogError "SSH connection failed"
            return $false
        }
    }
    catch {
        Write-LogError "SSH connection failed: $($_.Exception.Message)"
        return $false
    }
}

# Execute remote command
function Invoke-RemoteCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-LogInfo "Executing: $Description"
    Add-Content -Path $LogFile -Value "Command: $Command"
    
    $sshArgs = @(
        "-i", $SshKey,
        "$SshUser@$ServerHost",
        $Command
    )
    
    try {
        $output = & ssh @sshArgs 2>&1
        $exitCode = $LASTEXITCODE
        
        # Log output
        $output | ForEach-Object { Add-Content -Path $LogFile -Value $_ }
        $output | Write-Host
        
        if ($exitCode -eq 0) {
            Write-LogSuccess "Command completed successfully"
        }
        else {
            Write-LogWarning "Command completed with exit code: $exitCode"
        }
        
        Add-Content -Path $LogFile -Value ""
        return $exitCode
    }
    catch {
        Write-LogError "Failed to execute command: $($_.Exception.Message)"
        return 1
    }
}

# Docker system information
function Test-DockerSystem {
    Write-LogInfo "=== DOCKER SYSTEM INFORMATION ==="
    
    Invoke-RemoteCommand "docker --version" "Docker version"
    Invoke-RemoteCommand "docker info" "Docker system info"
    Invoke-RemoteCommand "docker system df" "Docker disk usage"
    Invoke-RemoteCommand "docker system events --since 1h --until now" "Recent Docker events"
}

# Docker Swarm status
function Test-SwarmStatus {
    Write-LogInfo "=== DOCKER SWARM STATUS ==="
    
    Invoke-RemoteCommand "docker info --format '{{.Swarm.LocalNodeState}}'" "Swarm state"
    Invoke-RemoteCommand "docker node ls" "Swarm nodes"
    Invoke-RemoteCommand "docker network ls" "Docker networks"
    Invoke-RemoteCommand "docker secret ls" "Docker secrets"
}

# UnityAI stack status
function Test-UnityAIStack {
    Write-LogInfo "=== UNITYAI STACK STATUS ==="
    
    Invoke-RemoteCommand "docker stack ls" "All stacks"
    Invoke-RemoteCommand "docker stack services unityai" "UnityAI services"
    Invoke-RemoteCommand "docker stack ps unityai" "UnityAI tasks"
    
    # Check individual service logs
    $services = @("unityai_app", "unityai_frontend", "unityai_python-worker", "unityai_n8n-playground", "unityai_db", "unityai_redis", "unityai_n8n")
    
    foreach ($service in $services) {
        Invoke-RemoteCommand "docker service ps $service --no-trunc" "Service tasks for $service"
        Invoke-RemoteCommand "docker service logs --tail 50 $service" "Recent logs for $service"
    }
}

# Check images
function Test-Images {
    Write-LogInfo "=== DOCKER IMAGES ==="
    
    Invoke-RemoteCommand "docker images" "All images"
    Invoke-RemoteCommand "docker images | grep unityai" "UnityAI custom images"
}

# System resources
function Test-SystemResources {
    Write-LogInfo "=== SYSTEM RESOURCES ==="
    
    Invoke-RemoteCommand "df -h" "Disk usage"
    Invoke-RemoteCommand "free -h" "Memory usage"
    Invoke-RemoteCommand "top -bn1 | head -20" "CPU and process info"
    Invoke-RemoteCommand "netstat -tlnp" "Network ports"
}

# Check Traefik
function Test-Traefik {
    Write-LogInfo "=== TRAEFIK STATUS ==="
    
    Invoke-RemoteCommand "docker service logs --tail 50 unityai_traefik" "Traefik logs"
    Invoke-RemoteCommand "curl -s http://localhost:8080/api/rawdata | jq ." "Traefik API (if available)"
}

# Check application endpoints
function Test-Endpoints {
    Write-LogInfo "=== APPLICATION ENDPOINTS ==="
    
    $endpoints = @(
        "https://api.unit-y-ai.io/health",
        "https://n8n.unit-y-ai.io",
        "https://traefik.unit-y-ai.io",
        "http://localhost:8000",
        "http://localhost:5678"
    )
    
    foreach ($endpoint in $endpoints) {
        Invoke-RemoteCommand "curl -s -o /dev/null -w '%{http_code}' '$endpoint' || echo 'Connection failed'" "HTTP status for $endpoint"
    }
}

# Execute custom command
function Invoke-CustomCommand {
    param([string]$Command)
    
    if ($Command) {
        Write-LogInfo "=== CUSTOM COMMAND ==="
        Invoke-RemoteCommand $Command "Custom command: $Command"
    }
}

# Generate comprehensive report
function New-ComprehensiveReport {
    Write-LogInfo "=== GENERATING COMPREHENSIVE REPORT ==="
    
    $reportScript = "/tmp/unityai-debug-report.sh"
    
    # Create comprehensive debug script on remote server
    $scriptContent = @'
#!/bin/bash
echo "=== UNITYAI DEBUG REPORT ==="
echo "Generated on: $(date)"
echo "Hostname: $(hostname)"
echo ""

echo "--- Docker Version ---"
docker --version
echo ""

echo "--- Docker Swarm Status ---"
docker info --format "{{.Swarm.LocalNodeState}}"
echo ""

echo "--- UnityAI Stack Services ---"
docker stack services unityai 2>/dev/null || echo "UnityAI stack not found"
echo ""

echo "--- Service Tasks ---"
docker stack ps unityai --no-trunc 2>/dev/null || echo "No tasks found"
echo ""

echo "--- Failed Services ---"
docker service ls --filter "label=com.docker.stack.namespace=unityai" --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}" | grep "0/"
echo ""

echo "--- Recent Service Logs (Last 20 lines each) ---"
for service in $(docker service ls --filter "label=com.docker.stack.namespace=unityai" --format "{{.Name}}"); do
    echo "--- Logs for $service ---"
    docker service logs --tail 20 $service 2>/dev/null || echo "No logs available for $service"
    echo ""
done

echo "--- System Resources ---"
echo "Memory:"
free -h
echo "Disk:"
df -h
echo "Load:"
uptime
echo ""

echo "--- Network Connectivity ---"
echo "Listening ports:"
netstat -tlnp | grep LISTEN
echo ""

echo "--- Docker Images ---"
docker images | grep -E "(unityai|REPOSITORY)"
echo ""

echo "=== END OF REPORT ==="
'@
    
    # Upload and execute the script
    $createScriptCommand = "cat > $reportScript << 'EOF'`n$scriptContent`nEOF"
    Invoke-RemoteCommand $createScriptCommand "Creating comprehensive report script"
    
    # Execute the report script
    Invoke-RemoteCommand "chmod +x $reportScript && $reportScript" "Comprehensive debug report"
    
    # Clean up
    Invoke-RemoteCommand "rm -f $reportScript" "Cleanup temporary script"
}

# Download logs from server
function Get-ServerLogs {
    Write-LogInfo "Downloading logs from server..."
    
    # Create remote log collection script
    Invoke-RemoteCommand "mkdir -p /tmp/unityai-logs" "Creating log directory"
    
    # Collect service logs
    $collectLogsCommand = "docker service ls --filter 'label=com.docker.stack.namespace=unityai' --format '{{.Name}}' | xargs -I {} docker service logs --tail 100 {} > /tmp/unityai-logs/{}.log 2>&1"
    Invoke-RemoteCommand $collectLogsCommand "Collecting service logs"
    
    # Create archive
    $archiveCommand = "cd /tmp && tar -czf unityai-logs-$(date +%Y%m%d-%H%M%S).tar.gz unityai-logs/"
    Invoke-RemoteCommand $archiveCommand "Creating log archive"
    
    # Download archive
    Write-LogInfo "Downloading log archive..."
    try {
        $scpArgs = @(
            "-i", $SshKey,
            "$SshUser@${ServerHost}:/tmp/unityai-logs-*.tar.gz",
            "."
        )
        & scp @scpArgs 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Log archive downloaded successfully"
        }
        else {
            Write-LogWarning "Failed to download log archive"
        }
    }
    catch {
        Write-LogWarning "Failed to download log archive: $($_.Exception.Message)"
    }
    
    # Cleanup remote files
    Invoke-RemoteCommand "rm -rf /tmp/unityai-logs /tmp/unityai-logs-*.tar.gz" "Cleaning up remote log files"
}

# Main execution function
function Start-DebugSession {
    Write-LogInfo "Starting UnityAI Server Debug Session"
    Write-LogInfo "Log file: $LogFile"
    Write-LogInfo "Target server: $SshUser@$ServerHost"
    Add-Content -Path $LogFile -Value ""
    
    if (-not (Test-Prerequisites)) {
        Write-LogError "Prerequisites check failed. Exiting."
        return 1
    }
    
    if (-not (Test-SshConnection)) {
        Write-LogError "Cannot establish SSH connection. Exiting."
        return 1
    }
    
    # Execute debug checks
    Test-DockerSystem
    Test-SwarmStatus
    Test-UnityAIStack
    Test-Images
    Test-SystemResources
    Test-Traefik
    Test-Endpoints
    
    # Execute custom command if provided
    Invoke-CustomCommand $CustomCommand
    
    # Generate comprehensive report
    New-ComprehensiveReport
    
    # Download logs
    Get-ServerLogs
    
    Write-LogSuccess "Debug session completed"
    Write-LogInfo "Results saved to: $LogFile"
    
    # Show summary
    Write-Host ""
    Write-LogInfo "=== DEBUG SUMMARY ==="
    Write-Host "• Log file: $LogFile"
    Write-Host "• Server: $SshUser@$ServerHost"
    Write-Host "• Session completed at: $(Get-Date)"
    
    $logArchive = Get-ChildItem -Path "unityai-logs-*.tar.gz" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($logArchive) {
        Write-Host "• Downloaded logs: $($logArchive.Name)"
    }
    
    Write-Host ""
    Write-LogInfo "To view the complete log: Get-Content $LogFile"
    Write-LogInfo "To re-run with custom command: .\debug-server.ps1 -CustomCommand 'your-command-here'"
    
    return 0
}

# Main script execution
if ($Help) {
    Show-Help
    exit 0
}

# Run main function
$exitCode = Start-DebugSession
exit $exitCode