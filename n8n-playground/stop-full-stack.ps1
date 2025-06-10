#!/usr/bin/env pwsh
# PowerShell script to stop the full n8n-playground stack

Write-Host "🛑 Stopping n8n-playground Full Stack..." -ForegroundColor Yellow
Write-Host ""

# Stop all services
docker-compose -f docker-compose.full-stack.yml down

Write-Host ""
Write-Host "✅ Full Stack Stopped Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 To start again: .\start-full-stack.ps1" -ForegroundColor Cyan
Write-Host "🗑️  To remove volumes: docker-compose -f docker-compose.full-stack.yml down -v" -ForegroundColor Gray
Write-Host ""