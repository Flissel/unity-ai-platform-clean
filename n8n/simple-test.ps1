# Simple test script to verify n8n services
Write-Host "=== N8N Service Status Check ===" -ForegroundColor Green

# Change to n8n directory
Set-Location "c:\code\unityai\n8n"

# Check Docker
Write-Host "\nChecking Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✓ Docker: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Docker error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Check files
Write-Host "\nChecking configuration files..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    Write-Host "✓ docker-compose.yml exists" -ForegroundColor Green
} else {
    Write-Host "✗ docker-compose.yml missing" -ForegroundColor Red
}

if (Test-Path "env\.env") {
    Write-Host "✓ .env configuration exists" -ForegroundColor Green
} else {
    Write-Host "✗ .env configuration missing" -ForegroundColor Red
}

if (Test-Path "secrets") {
    Write-Host "✓ secrets directory exists" -ForegroundColor Green
} else {
    Write-Host "✗ secrets directory missing" -ForegroundColor Red
}

# Check running containers
Write-Host "\nChecking running containers..." -ForegroundColor Cyan
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}" 2>$null
    if ($containers) {
        Write-Host "Running containers:" -ForegroundColor Yellow
        $containers | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    } else {
        Write-Host "No containers are currently running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error checking containers: $($_.Exception.Message)" -ForegroundColor Red
}

# Test ports
Write-Host "\nTesting service ports..." -ForegroundColor Cyan

function Test-ServicePort {
    param([string]$ServiceName, [int]$Port)
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $connect = $tcpClient.BeginConnect("localhost", $Port, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
        if ($wait) {
            $tcpClient.EndConnect($connect)
            $tcpClient.Close()
            Write-Host "✓ $ServiceName (port $Port) - accessible" -ForegroundColor Green
            return $true
        } else {
            $tcpClient.Close()
            Write-Host "✗ $ServiceName (port $Port) - not accessible" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ $ServiceName (port $Port) - error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$services = @(
    @{Name="N8N"; Port=5678},
    @{Name="Traefik Dashboard"; Port=8080},
    @{Name="Prometheus"; Port=9090},
    @{Name="Grafana"; Port=3000}
)

$accessibleServices = 0
foreach ($service in $services) {
    if (Test-ServicePort -ServiceName $service.Name -Port $service.Port) {
        $accessibleServices++
    }
}

# Summary
Write-Host "\n=== Summary ===" -ForegroundColor Green
if ($accessibleServices -eq 0) {
    Write-Host "No services are currently running." -ForegroundColor Yellow
    Write-Host "To start all services: docker-compose up -d" -ForegroundColor White
} elseif ($accessibleServices -eq $services.Count) {
    Write-Host "All services are running and accessible!" -ForegroundColor Green
    Write-Host "\nAccess URLs:" -ForegroundColor Cyan
    Write-Host "• N8N: http://localhost:5678" -ForegroundColor White
    Write-Host "• Traefik: http://localhost:8080/dashboard/" -ForegroundColor White
    Write-Host "• Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "• Grafana: http://localhost:3000" -ForegroundColor White
} else {
    Write-Host "Some services are running ($accessibleServices/$($services.Count))" -ForegroundColor Yellow
    Write-Host "Check logs: docker-compose logs" -ForegroundColor White
}

Write-Host "\nFor detailed testing: .\test-services.ps1" -ForegroundColor Cyan