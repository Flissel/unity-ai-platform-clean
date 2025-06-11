#!/usr/bin/env pwsh

# UnityAI Platform Deployment Script with Configuration
# This script deploys the platform using the generated configuration

Write-Host "=== UnityAI Platform Deployment ===" -ForegroundColor Cyan

# Check if configuration exists
if (-not (Test-Path "c:\code\unityai\.env")) {
    Write-Host "Configuration not found! Please run setup-interactive-config.ps1 first." -ForegroundColor Red
    exit 1
}

# Load environment variables from .env file
Write-Host "Loading configuration..." -ForegroundColor Yellow
$envVars = @{}
Get-Content "c:\code\unityai\.env" | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $envVars[$matches[1]] = $matches[2]
    }
}

Write-Host "Found $($envVars.Count) configuration variables" -ForegroundColor Green

# Build all Docker images first
Write-Host "" 
Write-Host "=== Building Docker Images ===" -ForegroundColor Cyan
if (-not (Build-DockerImages)) {
    Write-Host "Failed to build Docker images. Deployment aborted." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Deploying Services ===" -ForegroundColor Cyan

# Function to build all Docker images
function Build-DockerImages {
    Write-Host "Building Docker images..." -ForegroundColor Cyan
    
    # Build main application image
    Write-Host "Building UnityAI main application image..." -ForegroundColor Yellow
    Set-Location "c:\code\unityai"
    docker build -t unityai-app:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to build main application image" -ForegroundColor Red
        return $false
    }
    Write-Host "Main application image built successfully" -ForegroundColor Green
    
    # Build n8n-playground image
    Write-Host "Building n8n-playground image..." -ForegroundColor Yellow
    Set-Location "c:\code\unityai\n8n-playground"
    docker build -t unityai-n8n-playground:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to build n8n-playground image" -ForegroundColor Red
        return $false
    }
    Write-Host "n8n-playground image built successfully" -ForegroundColor Green
    
    # Build frontend image
    Write-Host "Building frontend image..." -ForegroundColor Yellow
    Set-Location "c:\code\unityai\frontend"
    docker build -t unityai-frontend:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to build frontend image" -ForegroundColor Red
        return $false
    }
    Write-Host "Frontend image built successfully" -ForegroundColor Green
    
    # Build Python service image
    Write-Host "Building Python service image..." -ForegroundColor Yellow
    Set-Location "c:\code\unityai\python"
    docker build -t unityai-python:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to build Python service image" -ForegroundColor Red
        return $false
    }
    Write-Host "Python service image built successfully" -ForegroundColor Green
    
    # Build n8n custom image if Dockerfile exists
    if (Test-Path "c:\code\unityai\n8n\Dockerfile") {
        Write-Host "Building custom n8n image..." -ForegroundColor Yellow
        Set-Location "c:\code\unityai\n8n"
        docker build -t unityai-n8n:latest .
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to build custom n8n image" -ForegroundColor Red
            return $false
        }
        Write-Host "Custom n8n image built successfully" -ForegroundColor Green
    }
    
    Set-Location "c:\code\unityai"
    Write-Host "All Docker images built successfully!" -ForegroundColor Green
    return $true
}

# Function to update Docker service with environment variables
function Update-DockerService {
    param(
        [string]$ServiceName,
        [hashtable]$EnvVars
    )
    
    Write-Host "Updating Docker service: $ServiceName" -ForegroundColor Yellow
    
    # Build environment variable arguments
    $envArgs = @()
    foreach ($key in $EnvVars.Keys) {
        $envArgs += "--env-add"
        $envArgs += "$key=$($EnvVars[$key])"
    }
    
    # Update the service
    $updateCmd = @("docker", "service", "update") + $envArgs + @($ServiceName)
    
    try {
        & $updateCmd[0] $updateCmd[1..($updateCmd.Length-1)]
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Successfully updated $ServiceName" -ForegroundColor Green
        } else {
            Write-Host "Failed to update $ServiceName" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "Error updating $ServiceName: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Check if Docker service exists
Write-Host "Checking Docker service status..." -ForegroundColor Yellow
$serviceExists = $false
try {
    $services = docker service ls --format "{{.Name}}" 2>$null
    if ($services -contains "unityai_unityai-app") {
        $serviceExists = $true
        Write-Host "Found existing Docker service: unityai_unityai-app" -ForegroundColor Green
    }
} catch {
    Write-Host "Error checking Docker services: $($_.Exception.Message)" -ForegroundColor Red
}

if ($serviceExists) {
    # Update existing service
    Write-Host "Updating existing Docker service with new configuration..." -ForegroundColor Cyan
    
    if (Update-DockerService -ServiceName "unityai_unityai-app" -EnvVars $envVars) {
        Write-Host "Service updated successfully!" -ForegroundColor Green
        
        # Wait for service to be ready
        Write-Host "Waiting for service to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        
        # Check service status
        Write-Host "Checking service status..." -ForegroundColor Yellow
        docker service ps unityai_unityai-app --no-trunc
        
    } else {
        Write-Host "Failed to update service. Please check the logs." -ForegroundColor Red
        exit 1
    }
    
} else {
    # Deploy new stack
    Write-Host "No existing service found. Deploying new stack..." -ForegroundColor Cyan
    
    # Check if docker-compose.override.yml exists
    if (Test-Path "c:\code\unityai\docker-compose.override.yml") {
        Write-Host "Using docker-compose.override.yml for deployment" -ForegroundColor Green
        
        # Deploy using docker-compose
        Set-Location "c:\code\unityai"
        
        try {
            # Stop any existing containers
            Write-Host "Stopping existing containers..." -ForegroundColor Yellow
            docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml down
            
            # Remove old containers and volumes for clean deployment
            Write-Host "Cleaning up old containers and networks..." -ForegroundColor Yellow
            docker system prune -f
            
            # Deploy the stack (images are already built)
            Write-Host "Starting production stack..." -ForegroundColor Yellow
            docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml up -d
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Production stack deployed successfully!" -ForegroundColor Green
            } else {
                Write-Host "Failed to deploy production stack" -ForegroundColor Red
                exit 1
            }
            
        } catch {
            Write-Host "Error during deployment: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
        
    } else {
        Write-Host "docker-compose.override.yml not found. Please run setup-interactive-config.ps1 first." -ForegroundColor Red
        exit 1
    }
}

# Display access information
Write-Host ""
Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host "Access your UnityAI platform at:" -ForegroundColor Cyan
Write-Host "  - Main Application: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Documentation: http://localhost:8000/docs" -ForegroundColor White

if ($envVars.ContainsKey("GRAFANA_ADMIN_PASSWORD")) {
    Write-Host "  - Grafana Dashboard: http://localhost:3001" -ForegroundColor White
    Write-Host "    (admin/$($envVars['GRAFANA_ADMIN_PASSWORD']))" -ForegroundColor Gray
}

Write-Host "  - Prometheus: http://localhost:9090" -ForegroundColor White

if ($envVars.ContainsKey("DOMAIN") -and $envVars["DOMAIN"]) {
    $protocol = if ($envVars["SSL_ENABLED"] -eq "true") { "https" } else { "http" }
    Write-Host "  - Domain: $protocol://$($envVars['DOMAIN'])" -ForegroundColor White
}

Write-Host ""
Write-Host "To check logs: docker service logs unityai_unityai-app -f" -ForegroundColor Cyan
Write-Host "To check status: docker service ps unityai_unityai-app" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your UnityAI platform is now running!" -ForegroundColor Green