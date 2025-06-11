#!/usr/bin/env pwsh

# UnityAI Platform - One-Click Production Deployment
# This script provides a complete one-click solution for production deployment
# Builds all images, configures the platform, and deploys everything

Write-Host "=== UnityAI Platform - One-Click Production Deployment ===" -ForegroundColor Cyan
Write-Host "This script will build all images and deploy a production-ready environment." -ForegroundColor Green
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker is not running. Please start Docker and try again." -ForegroundColor Red
        exit 1
    }
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not installed or not running. Please install Docker and try again." -ForegroundColor Red
    exit 1
}

# Check if configuration exists
if (-not (Test-Path "c:\code\unityai\.env")) {
    Write-Host "No configuration found. Checking for template..." -ForegroundColor Yellow
    
    # Check if user has filled out the template
    if (Test-Path "c:\code\unityai\config\production-config.env") {
        Write-Host "Found production-config.env template. Using it..." -ForegroundColor Green
        Copy-Item "c:\code\unityai\config\production-config.env" "c:\code\unityai\.env"
        Write-Host "Configuration loaded from template!" -ForegroundColor Green
    } elseif (Test-Path "c:\code\unityai\config\production-config-template.env") {
        Write-Host "" 
        Write-Host "CONFIGURATION REQUIRED:" -ForegroundColor Red
        Write-Host "1. Copy 'config/production-config-template.env' to 'config/production-config.env'" -ForegroundColor Yellow
        Write-Host "2. Edit 'config/production-config.env' and fill in your values" -ForegroundColor Yellow
        Write-Host "3. Run this script again" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Alternative: Run interactive configuration..." -ForegroundColor Cyan
        $choice = Read-Host "Use interactive configuration instead? (y/N)"
        
        if ($choice -eq 'y' -or $choice -eq 'Y') {
            # Run interactive configuration
            & "c:\code\unityai\scripts\setup-interactive-config.ps1"
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Configuration failed. Exiting." -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "Please configure the template file and run again." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "No configuration template found. Starting interactive configuration..." -ForegroundColor Yellow
        Write-Host ""
        
        # Run interactive configuration
        & "c:\code\unityai\scripts\setup-interactive-config.ps1"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Configuration failed. Exiting." -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "Configuration completed successfully!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Existing configuration found. Using existing settings." -ForegroundColor Green
    
    # Ask if user wants to reconfigure
    $reconfigure = Read-Host "Do you want to reconfigure? (y/n) [n]"
    if ($reconfigure.ToLower() -eq "y") {
        & "c:\code\unityai\scripts\setup-interactive-config.ps1"
        Write-Host "Reconfiguration completed!" -ForegroundColor Green
    }
    Write-Host ""
}

# Function to build all Docker images with progress
function Build-AllImages {
    Write-Host "=== Building All Docker Images ===" -ForegroundColor Cyan
    
    $images = @(
        @{Name="UnityAI Main Application"; Path="c:\code\unityai"; Tag="unityai-app:latest"},
        @{Name="n8n Playground"; Path="c:\code\unityai\n8n-playground"; Tag="unityai-n8n-playground:latest"},
        @{Name="Frontend"; Path="c:\code\unityai\frontend"; Tag="unityai-frontend:latest"},
        @{Name="Python Service"; Path="c:\code\unityai\python"; Tag="unityai-python:latest"}
    )
    
    # Add custom n8n image if Dockerfile exists
    if (Test-Path "c:\code\unityai\n8n\Dockerfile") {
        $images += @{Name="Custom n8n"; Path="c:\code\unityai\n8n"; Tag="unityai-n8n:latest"}
    }
    
    $totalImages = $images.Count
    $currentImage = 0
    
    foreach ($image in $images) {
        $currentImage++
        Write-Host "[$currentImage/$totalImages] Building $($image.Name)..." -ForegroundColor Yellow
        
        Set-Location $image.Path
        
        # Build with progress
        $buildStart = Get-Date
        docker build -t $image.Tag . --no-cache
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to build $($image.Name)" -ForegroundColor Red
            return $false
        }
        
        $buildTime = (Get-Date) - $buildStart
        Write-Host "✓ $($image.Name) built successfully in $([math]::Round($buildTime.TotalSeconds, 1))s" -ForegroundColor Green
    }
    
    Set-Location "c:\code\unityai"
    Write-Host "All Docker images built successfully!" -ForegroundColor Green
    return $true
}

# Function to clean up old deployments
function Clean-OldDeployment {
    Write-Host "=== Cleaning Up Old Deployment ===" -ForegroundColor Cyan
    
    # Stop existing services
    Write-Host "Stopping existing services..." -ForegroundColor Yellow
    docker-compose -f compose/docker-compose.yml down 2>$null
    docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml down 2>$null
    
    # Clean up containers, networks, and unused images
    Write-Host "Cleaning up containers and networks..." -ForegroundColor Yellow
    docker system prune -f
    
    # Remove old images with unityai prefix
    Write-Host "Removing old UnityAI images..." -ForegroundColor Yellow
    $oldImages = docker images --filter "reference=unityai-*" --format "{{.Repository}}:{{.Tag}}" 2>$null
    if ($oldImages) {
        docker rmi $oldImages -f 2>$null
    }
    
    Write-Host "Cleanup completed" -ForegroundColor Green
}

# Function to deploy production stack
function Deploy-ProductionStack {
    Write-Host "=== Deploying Production Stack ===" -ForegroundColor Cyan
    
    Set-Location "c:\code\unityai"
    
    # Check if override file exists
    if (-not (Test-Path "docker-compose.override.yml")) {
        Write-Host "docker-compose.override.yml not found. This should have been created by the configuration script." -ForegroundColor Red
        return $false
    }
    
    # Deploy the stack
    Write-Host "Starting production services..." -ForegroundColor Yellow
    docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to deploy production stack" -ForegroundColor Red
        return $false
    }
    
    # Wait for services to be ready
    Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 45
    
    # Check service health
    Write-Host "Checking service health..." -ForegroundColor Yellow
    $services = docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml ps --services
    $healthyServices = 0
    $totalServices = 0
    
    foreach ($service in $services) {
        $totalServices++
        $status = docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml ps $service --format "{{.State}}"
        if ($status -eq "running") {
            $healthyServices++
            Write-Host "✓ $service is running" -ForegroundColor Green
        } else {
            Write-Host "✗ $service is not running (Status: $status)" -ForegroundColor Red
        }
    }
    
    if ($healthyServices -eq $totalServices) {
        Write-Host "All services are running successfully!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Some services failed to start. Check logs for details." -ForegroundColor Yellow
        return $false
    }
}

# Function to display access information
function Show-AccessInformation {
    Write-Host ""
    Write-Host "=== Production Environment Ready! ===" -ForegroundColor Green
    Write-Host ""
    
    # Load configuration to show custom URLs
    $envVars = @{}
    if (Test-Path "c:\code\unityai\.env") {
        Get-Content "c:\code\unityai\.env" | ForEach-Object {
            if ($_ -match '^([^#][^=]+)=(.*)$') {
                $envVars[$matches[1]] = $matches[2]
            }
        }
    }
    
    Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "   Main Application: http://localhost:8000" -ForegroundColor White
    Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   API Health Check: http://localhost:8000/health" -ForegroundColor White
    
    if ($envVars.ContainsKey("GRAFANA_ADMIN_PASSWORD")) {
        Write-Host "   Grafana Dashboard: http://localhost:3001" -ForegroundColor White
        Write-Host "     (Username: admin, Password: $($envVars['GRAFANA_ADMIN_PASSWORD']))" -ForegroundColor Gray
    }
    
    Write-Host "   Prometheus Metrics: http://localhost:9090" -ForegroundColor White
    
    if ($envVars.ContainsKey("DOMAIN") -and $envVars["DOMAIN"]) {
        $protocol = if ($envVars["SSL_ENABLED"] -eq "true") { "https" } else { "http" }
        Write-Host "   Production Domain: ${protocol}://$($envVars["DOMAIN"])" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "🔧 Management Commands:" -ForegroundColor Cyan
    Write-Host "   View logs: docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml logs -f" -ForegroundColor White
    Write-Host "   Check status: docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml ps" -ForegroundColor White
    Write-Host "   Stop services: docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml down" -ForegroundColor White
    Write-Host "   Restart: .\scripts\one-click-production.ps1" -ForegroundColor White
    
    Write-Host ""
    Write-Host "📁 Configuration Files:" -ForegroundColor Cyan
    Write-Host "   Main config: .env" -ForegroundColor White
    Write-Host "   Docker config: docker-compose.override.yml" -ForegroundColor White
    Write-Host "   Backup config: .\backup-config.ps1" -ForegroundColor White
    
    Write-Host ""
    Write-Host "🎉 Your UnityAI production environment is ready!" -ForegroundColor Green
}

# Main execution flow
try {
    $startTime = Get-Date
    
    # Step 1: Clean up old deployment
    Clean-OldDeployment
    
    # Step 2: Build all images
    if (-not (Build-AllImages)) {
        Write-Host "Image building failed. Deployment aborted." -ForegroundColor Red
        exit 1
    }
    
    # Step 3: Deploy production stack
    if (-not (Deploy-ProductionStack)) {
        Write-Host "Deployment failed. Check logs for details." -ForegroundColor Red
        Write-Host "Run: docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml logs" -ForegroundColor Yellow
        exit 1
    }
    
    # Step 4: Show access information
    Show-AccessInformation
    
    $totalTime = (Get-Date) - $startTime
    Write-Host ""
    Write-Host "Total deployment time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes" -ForegroundColor Cyan
    
} catch {
    Write-Host "An error occurred during deployment: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check the logs and try again." -ForegroundColor Yellow
    exit 1
}