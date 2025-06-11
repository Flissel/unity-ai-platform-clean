#!/usr/bin/env pwsh

# UnityAI Platform Deployment Script
# Generated on 2025-06-11 12:01:43

Write-Host "Deploying UnityAI Platform..." -ForegroundColor Cyan

# Stop existing services
Write-Host "Stopping existing services..." -ForegroundColor Yellow
docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml down

# Pull latest images
Write-Host "Pulling latest images..." -ForegroundColor Yellow
docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml pull

# Build and start services
Write-Host "Building and starting services..." -ForegroundColor Yellow
docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml up -d --build

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service status
Write-Host "Checking service status..." -ForegroundColor Yellow
docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml ps

Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "Access your UnityAI platform at: http://localhost:8000" -ForegroundColor CyanWrite-Host "Or at your domain: https://unit-y-ai.io" -ForegroundColor Cyan
Write-Host "Grafana dashboard: http://localhost:3001 (admin/123123)" -ForegroundColor Cyan
Write-Host "Prometheus: http://localhost:9090" -ForegroundColor Cyan
