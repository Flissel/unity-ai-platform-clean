#!/usr/bin/env pwsh
# Quick test script to verify the current n8n setup
# This script checks if services are running and accessible

Write-Host "=== N8N Quick Service Verification ===" -ForegroundColor Green
Write-Host "Checking if services are currently running..." -ForegroundColor Yellow
Write-Host ""

# Change to the n8n directory
Set-Location "c:\code\unityai\n8n"

# Function to test if a port is available
function Test-Port {
    param(
        [string]$Host = "localhost",
        [int]$Port,
        [int]$Timeout = 3
    )
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $connect = $tcpClient.BeginConnect($Host, $Port, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne($Timeout * 1000, $false)
        if ($wait) {
            $tcpClient.EndConnect($connect)
            $tcpClient.Close()
            return $true
        } else {
            $tcpClient.Close()
            return $false
        }
    } catch {
        return $false
    }
}

# Function to check Docker container status
function Get-ContainerStatus {
    param([string]$ContainerName)
    try {
        $status = docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --no-trunc
        if ($status -and $status.Count -gt 1) {
            return $status[1]  # Skip header
        } else {
            return "Not running"
        }
    } catch {
        return "Error checking status"
    }
}

# Check Docker
Write-Host "=== Docker Status ===" -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker is available: $dockerVersion" -ForegroundColor Green
    
    $dockerComposeVersion = docker-compose --version
    Write-Host "✓ Docker Compose is available: $dockerComposeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not available or not running" -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is installed and running." -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose.yml exists
if (Test-Path "docker-compose.yml") {
    Write-Host "✓ docker-compose.yml found" -ForegroundColor Green
} else {
    Write-Host "✗ docker-compose.yml not found" -ForegroundColor Red
}

# Check if .env file exists
if (Test-Path "env\.env") {
    Write-Host "✓ .env configuration found" -ForegroundColor Green
} else {
    Write-Host "✗ .env configuration not found" -ForegroundColor Red
}

# Check secrets directory
if (Test-Path "secrets") {
    Write-Host "✓ Secrets directory found" -ForegroundColor Green
    $secretFiles = @(
        "n8n_admin_password.txt",
        "n8n_encryption_key.txt",
        "postgres_password.txt",
        "redis_password.txt",
        "grafana_admin_password.txt"
    )
    
    foreach ($file in $secretFiles) {
        if (Test-Path "secrets\$file") {
            Write-Host "  ✓ $file exists" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $file missing" -ForegroundColor Red
        }
    }
} else {
    Write-Host "✗ Secrets directory not found" -ForegroundColor Red
}

Write-Host ""

# Check running containers
Write-Host "=== Container Status ===" -ForegroundColor Cyan
$containers = @(
    @{Name="n8n"; Port=5678},
    @{Name="n8n_postgres"; Port=5432},
    @{Name="n8n_redis"; Port=6379},
    @{Name="n8n_traefik"; Port=8080},
    @{Name="n8n_prometheus"; Port=9090},
    @{Name="n8n_grafana"; Port=3000}
)

foreach ($container in $containers) {
    $status = Get-ContainerStatus -ContainerName $container.Name
    if ($status -ne "Not running" -and $status -ne "Error checking status") {
        Write-Host "✓ $($container.Name): $status" -ForegroundColor Green
    } else {
        Write-Host "✗ $($container.Name): $status" -ForegroundColor Red
    }
}

Write-Host ""

# Check service accessibility
Write-Host "=== Service Accessibility ===" -ForegroundColor Cyan
$services = @(
    @{Name="N8N Web Interface"; Host="localhost"; Port=5678; Path="/"},
    @{Name="N8N Health Check"; Host="localhost"; Port=5678; Path="/healthz"},
    @{Name="Traefik Dashboard"; Host="localhost"; Port=8080; Path="/dashboard/"},
    @{Name="Prometheus"; Host="localhost"; Port=9090; Path="/"},
    @{Name="Grafana"; Host="localhost"; Port=3000; Path="/login"}
)

foreach ($service in $services) {
    if (Test-Port -Host $service.Host -Port $service.Port) {
        Write-Host "✓ $($service.Name) - Port $($service.Port) is accessible" -ForegroundColor Green
        
        # Test HTTP endpoint if specified
        if ($service.Path) {
            try {
                $url = "http://$($service.Host):$($service.Port)$($service.Path)"
                $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
                if ($response.StatusCode -eq 200) {
                    Write-Host "  ✓ HTTP endpoint responding correctly" -ForegroundColor Green
                } else {
                    Write-Host "  ⚠ HTTP endpoint returned status: $($response.StatusCode)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  ⚠ HTTP endpoint not responding: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "✗ $($service.Name) - Port $($service.Port) is not accessible" -ForegroundColor Red
    }
}

Write-Host ""

# Check logs for errors (if containers are running)
Write-Host "=== Recent Log Check ===" -ForegroundColor Cyan
try {
    $runningContainers = docker ps --format "{{.Names}}" | Where-Object { $_ -like "n8n*" }
    if ($runningContainers) {
        Write-Host "Checking recent logs for errors..." -ForegroundColor Yellow
        foreach ($containerName in $runningContainers) {
            $logs = docker logs --tail 5 $containerName 2>&1
            $errorLines = $logs | Where-Object { $_ -match "error|Error|ERROR|failed|Failed|FAILED" }
            if ($errorLines) {
                Write-Host "⚠ $containerName has recent errors:" -ForegroundColor Yellow
                $errorLines | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
            } else {
                Write-Host "✓ $containerName - No recent errors" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "No n8n containers are currently running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not check container logs" -ForegroundColor Yellow
}

Write-Host ""

# Summary and recommendations
Write-Host "=== Summary & Recommendations ===" -ForegroundColor Green

# Check if all services are running
$allRunning = $true
foreach ($container in $containers) {
    $status = Get-ContainerStatus -ContainerName $container.Name
    if ($status -eq "Not running" -or $status -eq "Error checking status") {
        $allRunning = $false
        break
    }
}

if ($allRunning) {
    Write-Host "✓ All services appear to be running correctly!" -ForegroundColor Green
    Write-Host "`nYou can access:" -ForegroundColor Cyan
    Write-Host "• N8N Web Interface: http://localhost:5678" -ForegroundColor White
    Write-Host "• Traefik Dashboard: http://localhost:8080/dashboard/" -ForegroundColor White
    Write-Host "• Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "• Grafana: http://localhost:3000" -ForegroundColor White
} else {
    Write-Host "⚠ Some services are not running. To start all services:" -ForegroundColor Yellow
    Write-Host "  docker-compose up -d" -ForegroundColor White
    Write-Host "`nTo view logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs -f" -ForegroundColor White
    Write-Host "`nTo check individual service status:" -ForegroundColor Yellow
    Write-Host "  docker-compose ps" -ForegroundColor White
}

Write-Host "`nFor comprehensive individual service testing, run:" -ForegroundColor Cyan
Write-Host "  .\test-services.ps1" -ForegroundColor White

Write-Host "`nFor troubleshooting, check:" -ForegroundColor Cyan
Write-Host "• Docker logs: docker-compose logs [service_name]" -ForegroundColor White
Write-Host "• Service health: docker-compose ps" -ForegroundColor White
Write-Host "• Configuration files in ./env/ and ./secrets/" -ForegroundColor White