# Basic test script for n8n services
Write-Host "=== N8N Service Status Check ===" -ForegroundColor Green

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Cyan
$dockerCheck = docker --version 2>$null
if ($dockerCheck) {
    Write-Host "Docker is available: $dockerCheck" -ForegroundColor Green
} else {
    Write-Host "Docker is not available" -ForegroundColor Red
    exit 1
}

# Check files
Write-Host "Checking configuration files..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    Write-Host "docker-compose.yml exists" -ForegroundColor Green
} else {
    Write-Host "docker-compose.yml missing" -ForegroundColor Red
}

if (Test-Path "env\.env") {
    Write-Host ".env configuration exists" -ForegroundColor Green
} else {
    Write-Host ".env configuration missing" -ForegroundColor Red
}

# Check running containers
Write-Host "Checking running containers..." -ForegroundColor Cyan
$runningContainers = docker ps --format "table {{.Names}}\t{{.Status}}" 2>$null
if ($runningContainers) {
    Write-Host "Running containers:" -ForegroundColor Yellow
    Write-Host $runningContainers -ForegroundColor White
} else {
    Write-Host "No containers are currently running" -ForegroundColor Yellow
}

# Test basic connectivity
Write-Host "Testing service ports..." -ForegroundColor Cyan

# Test N8N port 5678
$n8nTest = Test-NetConnection -ComputerName localhost -Port 5678 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($n8nTest) {
    Write-Host "N8N (port 5678) - accessible" -ForegroundColor Green
} else {
    Write-Host "N8N (port 5678) - not accessible" -ForegroundColor Red
}

# Test Traefik port 8080
$traefikTest = Test-NetConnection -ComputerName localhost -Port 8080 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($traefikTest) {
    Write-Host "Traefik (port 8080) - accessible" -ForegroundColor Green
} else {
    Write-Host "Traefik (port 8080) - not accessible" -ForegroundColor Red
}

# Test Prometheus port 9090
$prometheusTest = Test-NetConnection -ComputerName localhost -Port 9090 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($prometheusTest) {
    Write-Host "Prometheus (port 9090) - accessible" -ForegroundColor Green
} else {
    Write-Host "Prometheus (port 9090) - not accessible" -ForegroundColor Red
}

# Test Grafana port 3000
$grafanaTest = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($grafanaTest) {
    Write-Host "Grafana (port 3000) - accessible" -ForegroundColor Green
} else {
    Write-Host "Grafana (port 3000) - not accessible" -ForegroundColor Red
}

Write-Host "\n=== Summary ===" -ForegroundColor Green
if (-not $n8nTest -and -not $traefikTest -and -not $prometheusTest -and -not $grafanaTest) {
    Write-Host "No services are currently running." -ForegroundColor Yellow
    Write-Host "To start all services: docker-compose up -d" -ForegroundColor White
} else {
    Write-Host "Some services are accessible. Check individual results above." -ForegroundColor Yellow
    Write-Host "To view logs: docker-compose logs" -ForegroundColor White
}