#!/usr/bin/env pwsh
# PowerShell script to start the full n8n-playground stack with frontend

Write-Host "🚀 Starting n8n-playground Full Stack..." -ForegroundColor Green
Write-Host "" 

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env file from .env.example" -ForegroundColor Green
        Write-Host "📝 Please review and update the .env file with your settings" -ForegroundColor Cyan
    } else {
        Write-Host "❌ .env.example file not found. Please create a .env file manually." -ForegroundColor Red
        exit 1
    }
}

# Stop any existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.full-stack.yml down

# Build and start all services
Write-Host "🔨 Building and starting all services..." -ForegroundColor Cyan
docker-compose -f docker-compose.full-stack.yml up --build -d

# Wait a moment for services to start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host "📊 Checking service status..." -ForegroundColor Cyan
docker-compose -f docker-compose.full-stack.yml ps

Write-Host ""
Write-Host "🎉 Full Stack Started Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Frontend (React):           http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 n8n-playground API:        http://localhost:8083" -ForegroundColor Cyan
Write-Host "🔄 n8n Workflow Engine:       http://localhost:5678" -ForegroundColor Cyan
Write-Host "📊 API Documentation:         http://localhost:8083/docs" -ForegroundColor Cyan
Write-Host "🗄️  Database (PostgreSQL):     localhost:5432" -ForegroundColor Cyan
Write-Host "🔴 Redis Cache:               localhost:6379" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔑 n8n Login: admin / admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 To view logs: docker-compose -f docker-compose.full-stack.yml logs -f" -ForegroundColor Gray
Write-Host "🛑 To stop: docker-compose -f docker-compose.full-stack.yml down" -ForegroundColor Gray
Write-Host ""
