# Test each n8n service individually
Write-Host "=== Testing N8N Services Individually ===" -ForegroundColor Green

# Function to test a service
function Test-Service {
    param(
        [string]$ServiceName,
        [string]$Image,
        [int]$Port,
        [hashtable]$Environment = @{},
        [string]$TestCommand = ""
    )
    
    Write-Host "\nTesting $ServiceName..." -ForegroundColor Cyan
    
    # Create environment variables string
    $envVars = @()
    foreach ($key in $Environment.Keys) {
        $envVars += "-e"
        $envVars += "$key=$($Environment[$key])"
    }
    
    # Start container
    $containerName = "test-$ServiceName-$(Get-Random)"
    Write-Host "Starting container: $containerName"
    
    try {
        if ($envVars.Count -gt 0) {
            $result = docker run -d --name $containerName -p "${Port}:${Port}" @envVars $Image 2>&1
        } else {
            $result = docker run -d --name $containerName -p "${Port}:${Port}" $Image 2>&1
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to start $ServiceName container: $result" -ForegroundColor Red
            return $false
        }
        
        Write-Host "Container started successfully: $containerName"
        
        # Wait for service to start
        Write-Host "Waiting for service to start..."
        Start-Sleep -Seconds 10
        
        # Test connectivity
        $connected = $false
        for ($i = 1; $i -le 6; $i++) {
            Write-Host "Connection attempt $i/6..."
            $testResult = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
            if ($testResult) {
                $connected = $true
                break
            }
            Start-Sleep -Seconds 5
        }
        
        if ($connected) {
            Write-Host "SUCCESS: $ServiceName is accessible on port $Port" -ForegroundColor Green
            
            # Run additional test command if provided
            if ($TestCommand) {
                Write-Host "Running additional test: $TestCommand"
                $testOutput = docker exec $containerName $TestCommand 2>&1
                Write-Host "Test output: $testOutput"
            }
            
            $success = $true
        } else {
            Write-Host "FAILED: $ServiceName is not accessible on port $Port" -ForegroundColor Red
            
            # Show container logs for debugging
            Write-Host "Container logs:"
            docker logs $containerName
            $success = $false
        }
        
    } catch {
        Write-Host "ERROR testing ${ServiceName}: $($_.Exception.Message)" -ForegroundColor Red
        $success = $false
    } finally {
        # Cleanup
        Write-Host "Cleaning up container: $containerName"
        docker stop $containerName 2>$null
        docker rm $containerName 2>$null
    }
    
    return $success
}

# Test PostgreSQL
$postgresEnv = @{
    "POSTGRES_DB" = "n8n"
    "POSTGRES_USER" = "n8n"
    "POSTGRES_PASSWORD" = "n8n_password"
}
$postgresResult = Test-Service -ServiceName "PostgreSQL" -Image "postgres:13" -Port 5432 -Environment $postgresEnv -TestCommand "pg_isready -U n8n"

# Test Redis
$redisResult = Test-Service -ServiceName "Redis" -Image "redis:7-alpine" -Port 6379 -TestCommand "redis-cli ping"

# Test N8N (basic)
$n8nEnv = @{
    "N8N_BASIC_AUTH_ACTIVE" = "true"
    "N8N_BASIC_AUTH_USER" = "admin"
    "N8N_BASIC_AUTH_PASSWORD" = "admin"
    "GENERIC_TIMEZONE" = "UTC"
}
$n8nResult = Test-Service -ServiceName "N8N" -Image "n8nio/n8n:latest" -Port 5678 -Environment $n8nEnv

# Test Traefik
$traefikResult = Test-Service -ServiceName "Traefik" -Image "traefik:v2.10" -Port 8080

# Test Prometheus
$prometheusResult = Test-Service -ServiceName "Prometheus" -Image "prom/prometheus:latest" -Port 9090

# Test Grafana
$grafanaEnv = @{
    "GF_SECURITY_ADMIN_PASSWORD" = "admin"
}
$grafanaResult = Test-Service -ServiceName "Grafana" -Image "grafana/grafana:latest" -Port 3000 -Environment $grafanaEnv

# Summary
Write-Host "\n=== Test Results Summary ===" -ForegroundColor Green
Write-Host "PostgreSQL: $(if ($postgresResult) { 'PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($postgresResult) { 'Green' } else { 'Red' })
Write-Host "Redis: $(if ($redisResult) { 'PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($redisResult) { 'Green' } else { 'Red' })
Write-Host "N8N: $(if ($n8nResult) { 'PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($n8nResult) { 'Green' } else { 'Red' })
Write-Host "Traefik: $(if ($traefikResult) { 'PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($traefikResult) { 'Green' } else { 'Red' })
Write-Host "Prometheus: $(if ($prometheusResult) { 'PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($prometheusResult) { 'Green' } else { 'Red' })
Write-Host "Grafana: $(if ($grafanaResult) { 'PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($grafanaResult) { 'Green' } else { 'Red' })

$totalTests = 6
$passedTests = @($postgresResult, $redisResult, $n8nResult, $traefikResult, $prometheusResult, $grafanaResult) | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count

Write-Host "\nOverall: $passedTests/$totalTests tests passed" -ForegroundColor $(if ($passedTests -eq $totalTests) { 'Green' } else { 'Yellow' })

if ($passedTests -eq $totalTests) {
    Write-Host "All services are working correctly as standalone units!" -ForegroundColor Green
} else {
    Write-Host "Some services failed. Check the logs above for details." -ForegroundColor Yellow
}