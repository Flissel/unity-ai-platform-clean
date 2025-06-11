#!/usr/bin/env pwsh

# Configuration Backup Script
# Generated on 2025-06-11 12:01:43

$backupDir = "config-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force

Copy-Item ".env" "$backupDir/" -ErrorAction SilentlyContinue
Copy-Item "n8n-playground/.env" "$backupDir/n8n-playground.env" -ErrorAction SilentlyContinue
Copy-Item "docker-compose.override.yml" "$backupDir/" -ErrorAction SilentlyContinue

Write-Host "Configuration backed up to: $backupDir" -ForegroundColor Green
