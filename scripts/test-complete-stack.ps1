# Complete UnityAI Application Stack Testing Script
Write-Host "=== UnityAI Complete Application Stack Testing ===" -ForegroundColor Green

# Change to project root
Set-Location "c:\code\unityai"

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200,
        [int]$TimeoutSeconds = 10
    )
    
    try {
        Write-Host "Testing $Name at $Url..." -ForegroundColor Cyan
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "✓ $Name - HTTP $($response.StatusCode) OK" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ $Name - HTTP $($response.StatusCode) (expected $ExpectedStatus)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ $Name - Connection failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to test service port
function Test-ServicePort {
    param(
        [string]$ServiceName,
        [int]$Port,
        [string]$Host = "localhost"
    )
    
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $connect = $tcpClient.BeginConnect($Host, $Port, $null, $null)
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

# Check Docker and Docker Compose
Write-Host "\n=== Prerequisites Check ===" -ForegroundColor Yellow
$dockerOk = $false
$composeOk = $false

try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✓ Docker: $dockerVersion" -ForegroundColor Green
        $dockerOk = $true
    }
} catch {
    Write-Host "✗ Docker not available" -ForegroundColor Red
}

try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "✓ Docker Compose: $composeVersion" -ForegroundColor Green
        $composeOk = $true
    }
} catch {
    Write-Host "✗ Docker Compose not available" -ForegroundColor Red
}

if (-not $dockerOk -or -not $composeOk) {
    Write-Host "\nPrerequisites not met. Please install Docker and Docker Compose." -ForegroundColor Red
    exit 1
}

# Check configuration files
Write-Host "\n=== Configuration Files Check ===" -ForegroundColor Yellow

$configFiles = @(
    "docker-compose.prod.yml",
    "compose/docker-compose.yml",
    "n8n/docker-compose.yml",
    "n8n-playground/docker-compose.dev.yml"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "✗ $file missing" -ForegroundColor Red
    }
}

# Check running containers
Write-Host "\n=== Running Containers Check ===" -ForegroundColor Yellow

try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
    if ($containers) {
        Write-Host "Running containers:" -ForegroundColor Cyan
        $containers | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    } else {
        Write-Host "No containers are currently running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error checking containers: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Core Infrastructure Services
Write-Host "\n=== Core Infrastructure Services ===" -ForegroundColor Yellow

$infraServices = @(
    @{Name="Traefik Dashboard"; Port=8080; Url="http://localhost:8080/dashboard/"},
    @{Name="PostgreSQL"; Port=5432},
    @{Name="Redis"; Port=6379}
)

$infraResults = @{}
foreach ($service in $infraServices) {
    $portResult = Test-ServicePort -ServiceName $service.Name -Port $service.Port
    $infraResults[$service.Name] = $portResult
    
    if ($service.Url -and $portResult) {
        $httpResult = Test-HttpEndpoint -Name $service.Name -Url $service.Url
        $infraResults[$service.Name] = $httpResult
    }
}

# Test N8N Services
Write-Host "\n=== N8N Workflow Automation ===" -ForegroundColor Yellow

$n8nServices = @(
    @{Name="N8N Main"; Port=5678; Url="http://localhost:5678"},
    @{Name="N8N Prometheus"; Port=9090; Url="http://localhost:9090"},
    @{Name="N8N Grafana"; Port=3000; Url="http://localhost:3000"}
)

$n8nResults = @{}
foreach ($service in $n8nServices) {
    $portResult = Test-ServicePort -ServiceName $service.Name -Port $service.Port
    $n8nResults[$service.Name] = $portResult
    
    if ($service.Url -and $portResult) {
        $httpResult = Test-HttpEndpoint -Name $service.Name -Url $service.Url
        $n8nResults[$service.Name] = $httpResult
    }
}

# Test N8N Playground (FastAPI)
Write-Host "\n=== N8N Playground (FastAPI) ===" -ForegroundColor Yellow

$playgroundServices = @(
    @{Name="N8N Playground API"; Port=8000; Url="http://localhost:8000/docs"},
    @{Name="N8N Playground Health"; Port=8000; Url="http://localhost:8000/health"}
)

$playgroundResults = @{}
foreach ($service in $playgroundServices) {
    $portResult = Test-ServicePort -ServiceName $service.Name -Port $service.Port
    $playgroundResults[$service.Name] = $portResult
    
    if ($service.Url -and $portResult) {
        $httpResult = Test-HttpEndpoint -Name $service.Name -Url $service.Url
        $playgroundResults[$service.Name] = $httpResult
    }
}

# Test Python Worker Service
Write-Host "\n=== Python Worker Service ===" -ForegroundColor Yellow

$pythonServices = @(
    @{Name="Python Worker API"; Port=8001; Url="http://localhost:8001/health"},
    @{Name="Python Worker Docs"; Port=8001; Url="http://localhost:8001/docs"}
)

$pythonResults = @{}
foreach ($service in $pythonServices) {
    $portResult = Test-ServicePort -ServiceName $service.Name -Port $service.Port
    $pythonResults[$service.Name] = $portResult
    
    if ($service.Url -and $portResult) {
        $httpResult = Test-HttpEndpoint -Name $service.Name -Url $service.Url
        $pythonResults[$service.Name] = $httpResult
    }
}

# Test Main UnityAI Application
Write-Host "\n=== Main UnityAI Application ===" -ForegroundColor Yellow

$mainAppServices = @(
    @{Name="UnityAI Main App"; Port=80; Url="http://localhost"},
    @{Name="UnityAI API"; Port=80; Url="http://localhost/api/health"},
    @{Name="UnityAI Docs"; Port=80; Url="http://localhost/docs"}
)

$mainAppResults = @{}
foreach ($service in $mainAppServices) {
    $portResult = Test-ServicePort -ServiceName $service.Name -Port $service.Port
    $mainAppResults[$service.Name] = $portResult
    
    if ($service.Url -and $portResult) {
        $httpResult = Test-HttpEndpoint -Name $service.Name -Url $service.Url
        $mainAppResults[$service.Name] = $httpResult
    }
}

# Calculate overall results
Write-Host "\n=== Overall Test Results ===" -ForegroundColor Green

$allResults = @{}
$allResults += $infraResults
$allResults += $n8nResults
$allResults += $playgroundResults
$allResults += $pythonResults
$allResults += $mainAppResults

$totalTests = $allResults.Count
$passedTests = ($allResults.Values | Where-Object { $_ -eq $true }).Count

Write-Host "\nInfrastructure Services:" -ForegroundColor Cyan
foreach ($key in $infraResults.Keys) {
    $status = if ($infraResults[$key]) { "PASSED" } else { "FAILED" }
    $color = if ($infraResults[$key]) { "Green" } else { "Red" }
    Write-Host "  $key: $status" -ForegroundColor $color
}

Write-Host "\nN8N Services:" -ForegroundColor Cyan
foreach ($key in $n8nResults.Keys) {
    $status = if ($n8nResults[$key]) { "PASSED" } else { "FAILED" }
    $color = if ($n8nResults[$key]) { "Green" } else { "Red" }
    Write-Host "  $key: $status" -ForegroundColor $color
}

Write-Host "\nN8N Playground:" -ForegroundColor Cyan
foreach ($key in $playgroundResults.Keys) {
    $status = if ($playgroundResults[$key]) { "PASSED" } else { "FAILED" }
    $color = if ($playgroundResults[$key]) { "Green" } else { "Red" }
    Write-Host "  $key: $status" -ForegroundColor $color
}

Write-Host "\nPython Worker:" -ForegroundColor Cyan
foreach ($key in $pythonResults.Keys) {
    $status = if ($pythonResults[$key]) { "PASSED" } else { "FAILED" }
    $color = if ($pythonResults[$key]) { "Green" } else { "Red" }
    Write-Host "  $key: $status" -ForegroundColor $color
}

Write-Host "\nMain Application:" -ForegroundColor Cyan
foreach ($key in $mainAppResults.Keys) {
    $status = if ($mainAppResults[$key]) { "PASSED" } else { "FAILED" }
    $color = if ($mainAppResults[$key]) { "Green" } else { "Red" }
    Write-Host "  $key: $status" -ForegroundColor $color
}

Write-Host "\n=== Summary ===" -ForegroundColor Green
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $($totalTests - $passedTests)" -ForegroundColor Red
Write-Host "Success Rate: $([math]::Round(($passedTests / $totalTests) * 100, 2))%" -ForegroundColor Yellow

if ($passedTests -eq $totalTests) {
    Write-Host "\n🎉 All services are running and accessible!" -ForegroundColor Green
    Write-Host "\nQuick Access URLs:" -ForegroundColor Cyan
    Write-Host "• Main App: http://localhost" -ForegroundColor White
    Write-Host "• N8N: http://localhost:5678" -ForegroundColor White
    Write-Host "• N8N Playground: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "• Python Worker: http://localhost:8001/docs" -ForegroundColor White
    Write-Host "• Traefik Dashboard: http://localhost:8080/dashboard/" -ForegroundColor White
    Write-Host "• Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "• Grafana: http://localhost:3000" -ForegroundColor White
} elseif ($passedTests -gt 0) {
    Write-Host "\n⚠️  Some services are running. Check failed services above." -ForegroundColor Yellow
    Write-Host "\nTroubleshooting:" -ForegroundColor Cyan
    Write-Host "• Check logs: docker-compose logs [service-name]" -ForegroundColor White
    Write-Host "• Restart services: docker-compose restart" -ForegroundColor White
    Write-Host "• Check configuration files" -ForegroundColor White
} else {
    Write-Host "\n❌ No services are running." -ForegroundColor Red
    Write-Host "\nTo start services:" -ForegroundColor Cyan
    Write-Host "• Production: docker-compose -f docker-compose.prod.yml up -d" -ForegroundColor White
    Write-Host "• Development: docker-compose -f compose/docker-compose.yml up -d" -ForegroundColor White
    Write-Host "• N8N only: cd n8n && docker-compose up -d" -ForegroundColor White
}

Write-Host "\nFor individual service testing:" -ForegroundColor Cyan
Write-Host "• N8N services: .\n8n\test-individual-services.ps1" -ForegroundColor White
Write-Host "• Quick status: .\n8n\basic-test.ps1" -ForegroundColor White