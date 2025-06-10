#!/usr/bin/env pwsh
# Test each service in the n8n stack individually
# This script tests PostgreSQL, Redis, n8n, Traefik, Prometheus, and Grafana as standalone services

Write-Host "=== N8N Services Individual Testing Script ===" -ForegroundColor Green
Write-Host "This script will test each service individually to verify they work correctly." -ForegroundColor Yellow
Write-Host ""

# Change to the n8n directory
Set-Location "c:\code\unityai\n8n"

# Function to test if a port is available
function Test-Port {
    param(
        [string]$Host = "localhost",
        [int]$Port,
        [int]$Timeout = 5
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

# Function to wait for service to be ready
function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Host = "localhost",
        [int]$Port,
        [int]$MaxWaitTime = 60
    )
    Write-Host "Waiting for $ServiceName to be ready on port $Port..." -ForegroundColor Yellow
    $elapsed = 0
    while ($elapsed -lt $MaxWaitTime) {
        if (Test-Port -Host $Host -Port $Port) {
            Write-Host "✓ $ServiceName is ready!" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "  Waiting... ($elapsed/$MaxWaitTime seconds)" -ForegroundColor Gray
    }
    Write-Host "✗ $ServiceName failed to start within $MaxWaitTime seconds" -ForegroundColor Red
    return $false
}

# Test 1: PostgreSQL Database
Write-Host "\n=== Test 1: PostgreSQL Database ===" -ForegroundColor Cyan
Write-Host "Starting PostgreSQL container..." -ForegroundColor Yellow

try {
    # Stop any existing postgres container
    docker stop n8n_postgres_test 2>$null
    docker rm n8n_postgres_test 2>$null
    
    # Start PostgreSQL with test configuration
    docker run -d `
        --name n8n_postgres_test `
        -e POSTGRES_DB=n8n_test `
        -e POSTGRES_USER=n8n_user `
        -e POSTGRES_PASSWORD=test_password `
        -p 5433:5432 `
        postgres:15-alpine
    
    if (Wait-ForService -ServiceName "PostgreSQL" -Port 5433) {
        # Test database connection
        Write-Host "Testing database connection..." -ForegroundColor Yellow
        $testResult = docker exec n8n_postgres_test psql -U n8n_user -d n8n_test -c "SELECT version();"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ PostgreSQL test PASSED - Database is working correctly" -ForegroundColor Green
        } else {
            Write-Host "✗ PostgreSQL test FAILED - Database connection failed" -ForegroundColor Red
        }
    }
    
    # Cleanup
    Write-Host "Cleaning up PostgreSQL test container..." -ForegroundColor Gray
    docker stop n8n_postgres_test
    docker rm n8n_postgres_test
    
} catch {
    Write-Host "✗ PostgreSQL test FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Redis Cache
Write-Host "\n=== Test 2: Redis Cache ===" -ForegroundColor Cyan
Write-Host "Starting Redis container..." -ForegroundColor Yellow

try {
    # Stop any existing redis container
    docker stop n8n_redis_test 2>$null
    docker rm n8n_redis_test 2>$null
    
    # Start Redis with test configuration
    docker run -d `
        --name n8n_redis_test `
        -p 6380:6379 `
        redis:7-alpine `
        redis-server --requirepass test_password
    
    if (Wait-ForService -ServiceName "Redis" -Port 6380) {
        # Test Redis connection
        Write-Host "Testing Redis connection..." -ForegroundColor Yellow
        $testResult = docker exec n8n_redis_test redis-cli -a test_password ping
        if ($testResult -eq "PONG") {
            Write-Host "✓ Redis test PASSED - Cache is working correctly" -ForegroundColor Green
            
            # Test basic operations
            docker exec n8n_redis_test redis-cli -a test_password set test_key "test_value"
            $getValue = docker exec n8n_redis_test redis-cli -a test_password get test_key
            if ($getValue -eq "test_value") {
                Write-Host "✓ Redis operations test PASSED" -ForegroundColor Green
            } else {
                Write-Host "✗ Redis operations test FAILED" -ForegroundColor Red
            }
        } else {
            Write-Host "✗ Redis test FAILED - Connection failed" -ForegroundColor Red
        }
    }
    
    # Cleanup
    Write-Host "Cleaning up Redis test container..." -ForegroundColor Gray
    docker stop n8n_redis_test
    docker rm n8n_redis_test
    
} catch {
    Write-Host "✗ Redis test FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: N8N Application (with dependencies)
Write-Host "\n=== Test 3: N8N Application ===" -ForegroundColor Cyan
Write-Host "Starting N8N with dependencies..." -ForegroundColor Yellow

try {
    # Create a temporary docker-compose for testing
    $testCompose = @"
version: '3.8'
services:
  postgres_test:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: n8n_test
      POSTGRES_USER: n8n_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5434:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U n8n_user -d n8n_test"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis_test:
    image: redis:7-alpine
    command: redis-server --requirepass test_password
    ports:
      - "6381:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "test_password", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  n8n_test:
    image: n8nio/n8n:latest
    ports:
      - "5679:5678"
    environment:
      - NODE_ENV=development
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=test_password
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres_test
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n_test
      - DB_POSTGRESDB_USER=n8n_user
      - DB_POSTGRESDB_PASSWORD=test_password
      - QUEUE_BULL_REDIS_HOST=redis_test
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_BULL_REDIS_PASSWORD=test_password
    depends_on:
      postgres_test:
        condition: service_healthy
      redis_test:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:5678/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
"@
    
    $testCompose | Out-File -FilePath "docker-compose.test.yml" -Encoding UTF8
    
    # Start the test stack
    docker-compose -f docker-compose.test.yml up -d
    
    # Wait for N8N to be ready
    if (Wait-ForService -ServiceName "N8N" -Port 5679 -MaxWaitTime 120) {
        # Test N8N health endpoint
        Write-Host "Testing N8N health endpoint..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5679/healthz" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Host "✓ N8N test PASSED - Application is healthy" -ForegroundColor Green
                
                # Test N8N login page
                Write-Host "Testing N8N login page..." -ForegroundColor Yellow
                $loginResponse = Invoke-WebRequest -Uri "http://localhost:5679" -TimeoutSec 10
                if ($loginResponse.StatusCode -eq 200) {
                    Write-Host "✓ N8N UI test PASSED - Login page accessible" -ForegroundColor Green
                } else {
                    Write-Host "✗ N8N UI test FAILED - Login page not accessible" -ForegroundColor Red
                }
            } else {
                Write-Host "✗ N8N test FAILED - Health check failed" -ForegroundColor Red
            }
        } catch {
            Write-Host "✗ N8N test FAILED - Health endpoint not accessible: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Cleanup
    Write-Host "Cleaning up N8N test stack..." -ForegroundColor Gray
    docker-compose -f docker-compose.test.yml down -v
    Remove-Item "docker-compose.test.yml" -Force
    
} catch {
    Write-Host "✗ N8N test FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Traefik Reverse Proxy
Write-Host "\n=== Test 4: Traefik Reverse Proxy ===" -ForegroundColor Cyan
Write-Host "Starting Traefik container..." -ForegroundColor Yellow

try {
    # Stop any existing traefik container
    docker stop traefik_test 2>$null
    docker rm traefik_test 2>$null
    
    # Start Traefik with test configuration
    docker run -d `
        --name traefik_test `
        -p 8081:8080 `
        -p 8082:80 `
        -v /var/run/docker.sock:/var/run/docker.sock:ro `
        traefik:v3.0 `
        --api.dashboard=true `
        --api.insecure=true `
        --providers.docker=true `
        --providers.docker.exposedbydefault=false `
        --entrypoints.web.address=:80
    
    if (Wait-ForService -ServiceName "Traefik" -Port 8081) {
        # Test Traefik dashboard
        Write-Host "Testing Traefik dashboard..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8081/dashboard/" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Host "✓ Traefik test PASSED - Dashboard is accessible" -ForegroundColor Green
            } else {
                Write-Host "✗ Traefik test FAILED - Dashboard not accessible" -ForegroundColor Red
            }
        } catch {
            Write-Host "✗ Traefik test FAILED - Dashboard error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Cleanup
    Write-Host "Cleaning up Traefik test container..." -ForegroundColor Gray
    docker stop traefik_test
    docker rm traefik_test
    
} catch {
    Write-Host "✗ Traefik test FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Prometheus Monitoring
Write-Host "\n=== Test 5: Prometheus Monitoring ===" -ForegroundColor Cyan
Write-Host "Starting Prometheus container..." -ForegroundColor Yellow

try {
    # Stop any existing prometheus container
    docker stop prometheus_test 2>$null
    docker rm prometheus_test 2>$null
    
    # Create a minimal prometheus config
    $prometheusConfig = @"
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
"@
    
    $prometheusConfig | Out-File -FilePath "prometheus.test.yml" -Encoding UTF8
    
    # Start Prometheus with test configuration
    docker run -d `
        --name prometheus_test `
        -p 9091:9090 `
        -v "${PWD}/prometheus.test.yml:/etc/prometheus/prometheus.yml" `
        prom/prometheus:latest
    
    if (Wait-ForService -ServiceName "Prometheus" -Port 9091) {
        # Test Prometheus web interface
        Write-Host "Testing Prometheus web interface..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:9091" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Host "✓ Prometheus test PASSED - Web interface is accessible" -ForegroundColor Green
                
                # Test Prometheus API
                $apiResponse = Invoke-WebRequest -Uri "http://localhost:9091/api/v1/query?query=up" -TimeoutSec 10
                if ($apiResponse.StatusCode -eq 200) {
                    Write-Host "✓ Prometheus API test PASSED" -ForegroundColor Green
                } else {
                    Write-Host "✗ Prometheus API test FAILED" -ForegroundColor Red
                }
            } else {
                Write-Host "✗ Prometheus test FAILED - Web interface not accessible" -ForegroundColor Red
            }
        } catch {
            Write-Host "✗ Prometheus test FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Cleanup
    Write-Host "Cleaning up Prometheus test container..." -ForegroundColor Gray
    docker stop prometheus_test
    docker rm prometheus_test
    Remove-Item "prometheus.test.yml" -Force
    
} catch {
    Write-Host "✗ Prometheus test FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Grafana Visualization
Write-Host "\n=== Test 6: Grafana Visualization ===" -ForegroundColor Cyan
Write-Host "Starting Grafana container..." -ForegroundColor Yellow

try {
    # Stop any existing grafana container
    docker stop grafana_test 2>$null
    docker rm grafana_test 2>$null
    
    # Start Grafana with test configuration
    docker run -d `
        --name grafana_test `
        -p 3001:3000 `
        -e GF_SECURITY_ADMIN_PASSWORD=test_password `
        grafana/grafana:latest
    
    if (Wait-ForService -ServiceName "Grafana" -Port 3001 -MaxWaitTime 90) {
        # Test Grafana login page
        Write-Host "Testing Grafana login page..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3001/login" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Host "✓ Grafana test PASSED - Login page is accessible" -ForegroundColor Green
            } else {
                Write-Host "✗ Grafana test FAILED - Login page not accessible" -ForegroundColor Red
            }
        } catch {
            Write-Host "✗ Grafana test FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Cleanup
    Write-Host "Cleaning up Grafana test container..." -ForegroundColor Gray
    docker stop grafana_test
    docker rm grafana_test
    
} catch {
    Write-Host "✗ Grafana test FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "\n=== Test Summary ===" -ForegroundColor Green
Write-Host "Individual service testing completed." -ForegroundColor Yellow
Write-Host "Check the results above to see which services are working correctly." -ForegroundColor Yellow
Write-Host "\nNext steps:" -ForegroundColor Cyan
Write-Host "1. If all tests passed, you can start the full stack with: docker-compose up -d" -ForegroundColor White
Write-Host "2. If any tests failed, check the Docker logs and configuration files" -ForegroundColor White
Write-Host "3. Ensure all required secrets are properly configured in ./secrets/" -ForegroundColor White
Write-Host "\nFor full stack testing, run: docker-compose up -d && docker-compose logs -f" -ForegroundColor White