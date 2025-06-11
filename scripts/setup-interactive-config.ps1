#!/usr/bin/env pwsh

# Interactive Configuration Script for UnityAI Platform
# This script helps configure all necessary environment variables and credentials
# for a complete UnityAI deployment that can be controlled from outside the server.

Write-Host "=== UnityAI Platform Interactive Configuration Setup ===" -ForegroundColor Cyan
Write-Host "This script will help you configure all necessary credentials and settings." -ForegroundColor Green
Write-Host ""

# Function to prompt for input with validation
function Get-UserInput {
    param(
        [string]$Prompt,
        [string]$DefaultValue = "",
        [bool]$IsSecret = $false,
        [bool]$IsRequired = $true
    )
    
    do {
        if ($DefaultValue) {
            $displayPrompt = "$Prompt [$DefaultValue]"
        } else {
            $displayPrompt = $Prompt
        }
        
        if ($IsSecret) {
            $input = Read-Host -Prompt $displayPrompt -AsSecureString
            $input = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($input))
        } else {
            $input = Read-Host -Prompt $displayPrompt
        }
        
        if ([string]::IsNullOrWhiteSpace($input) -and $DefaultValue) {
            $input = $DefaultValue
        }
        
        if ($IsRequired -and [string]::IsNullOrWhiteSpace($input)) {
            Write-Host "This field is required. Please enter a value." -ForegroundColor Red
        }
    } while ($IsRequired -and [string]::IsNullOrWhiteSpace($input))
    
    return $input
}

# Function to generate a secure random string
function New-SecureKey {
    param([int]$Length = 32)
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
    $key = ''
    for ($i = 0; $i -lt $Length; $i++) {
        $key += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $key
}

# Configuration object to store all settings
$config = @{}

Write-Host "1. Basic Application Configuration" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow

# Generate or ask for SECRET_KEY
$generateSecret = Read-Host "Generate a secure SECRET_KEY automatically? (y/n) [y]"
if ($generateSecret -eq "" -or $generateSecret.ToLower() -eq "y") {
    $config.SECRET_KEY = New-SecureKey -Length 64
    Write-Host "Generated secure SECRET_KEY" -ForegroundColor Green
} else {
    $config.SECRET_KEY = Get-UserInput "Enter SECRET_KEY (minimum 32 characters)" -IsSecret $true
}

$config.ENVIRONMENT = Get-UserInput "Environment (development/staging/production)" "production"
$config.DEBUG = Get-UserInput "Enable debug mode? (true/false)" "false"
$config.LOG_LEVEL = Get-UserInput "Log level (DEBUG/INFO/WARNING/ERROR)" "INFO"

Write-Host ""
Write-Host "2. Database Configuration" -ForegroundColor Yellow
Write-Host "========================" -ForegroundColor Yellow

$config.DB_HOST = Get-UserInput "Database host" "localhost"
$config.DB_PORT = Get-UserInput "Database port" "5432"
$config.DB_NAME = Get-UserInput "Database name" "unityai_db"
$config.DB_USER = Get-UserInput "Database username" "unityai_user"
$config.DB_PASSWORD = Get-UserInput "Database password" -IsSecret $true

Write-Host ""
Write-Host "3. Redis Configuration" -ForegroundColor Yellow
Write-Host "=====================" -ForegroundColor Yellow

$config.REDIS_HOST = Get-UserInput "Redis host" "localhost"
$config.REDIS_PORT = Get-UserInput "Redis port" "6379"
$config.REDIS_PASSWORD = Get-UserInput "Redis password (leave empty if none)" -IsRequired $false -IsSecret $true

Write-Host ""
Write-Host "4. n8n Integration Configuration" -ForegroundColor Yellow
Write-Host "===============================" -ForegroundColor Yellow

$config.N8N_HOST = Get-UserInput "n8n host URL (e.g., http://localhost:5678)"
$config.N8N_API_KEY = Get-UserInput "n8n API key" -IsSecret $true
$config.N8N_USERNAME = Get-UserInput "n8n username (if using basic auth)" -IsRequired $false
$config.N8N_PASSWORD = Get-UserInput "n8n password (if using basic auth)" -IsRequired $false -IsSecret $true

Write-Host ""
Write-Host "5. External API Configuration" -ForegroundColor Yellow
Write-Host "============================" -ForegroundColor Yellow

$config.OPENAI_API_KEY = Get-UserInput "OpenAI API key (optional)" -IsRequired $false -IsSecret $true
$config.ANTHROPIC_API_KEY = Get-UserInput "Anthropic API key (optional)" -IsRequired $false -IsSecret $true
$config.GOOGLE_API_KEY = Get-UserInput "Google API key (optional)" -IsRequired $false -IsSecret $true

Write-Host ""
Write-Host "6. Monitoring Configuration" -ForegroundColor Yellow
Write-Host "==========================" -ForegroundColor Yellow

$config.PROMETHEUS_ENABLED = Get-UserInput "Enable Prometheus monitoring? (true/false)" "true"
$config.GRAFANA_ADMIN_PASSWORD = Get-UserInput "Grafana admin password" -IsSecret $true

Write-Host ""
Write-Host "7. Security Configuration" -ForegroundColor Yellow
Write-Host "========================" -ForegroundColor Yellow

$config.JWT_SECRET_KEY = New-SecureKey -Length 64
Write-Host "Generated JWT secret key" -ForegroundColor Green

$config.CORS_ORIGINS = Get-UserInput "CORS allowed origins (comma-separated)" "http://localhost:3000,http://localhost:8080"
$config.ALLOWED_HOSTS = Get-UserInput "Allowed hosts (comma-separated)" "localhost,127.0.0.1"

Write-Host ""
Write-Host "8. Email Configuration (Optional)" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow

$config.SMTP_HOST = Get-UserInput "SMTP host (optional)" -IsRequired $false
$config.SMTP_PORT = Get-UserInput "SMTP port (optional)" "587" -IsRequired $false
$config.SMTP_USERNAME = Get-UserInput "SMTP username (optional)" -IsRequired $false
$config.SMTP_PASSWORD = Get-UserInput "SMTP password (optional)" -IsRequired $false -IsSecret $true
$config.FROM_EMAIL = Get-UserInput "From email address (optional)" -IsRequired $false

Write-Host ""
Write-Host "9. Deployment Configuration" -ForegroundColor Yellow
Write-Host "==========================" -ForegroundColor Yellow

$config.DOMAIN = Get-UserInput "Domain name (e.g., unityai.example.com)" -IsRequired $false
$config.SSL_ENABLED = Get-UserInput "Enable SSL/HTTPS? (true/false)" "true"
$config.TRAEFIK_ENABLED = Get-UserInput "Use Traefik for reverse proxy? (true/false)" "true"

# Create configuration files
Write-Host ""
Write-Host "Creating configuration files..." -ForegroundColor Cyan

# Create .env file for the main application
$envContent = @"
# UnityAI Platform Configuration
# Generated on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

# Basic Configuration
SECRET_KEY=$($config.SECRET_KEY)
ENVIRONMENT=$($config.ENVIRONMENT)
DEBUG=$($config.DEBUG)
LOG_LEVEL=$($config.LOG_LEVEL)

# Database Configuration
DB_HOST=$($config.DB_HOST)
DB_PORT=$($config.DB_PORT)
DB_NAME=$($config.DB_NAME)
DB_USER=$($config.DB_USER)
DB_PASSWORD=$($config.DB_PASSWORD)
DATABASE_URL=postgresql://$($config.DB_USER):$($config.DB_PASSWORD)@$($config.DB_HOST):$($config.DB_PORT)/$($config.DB_NAME)

# Redis Configuration
REDIS_HOST=$($config.REDIS_HOST)
REDIS_PORT=$($config.REDIS_PORT)
"@

if ($config.REDIS_PASSWORD) {
    $envContent += "REDIS_PASSWORD=$($config.REDIS_PASSWORD)`n"
    $envContent += "REDIS_URL=redis://:$($config.REDIS_PASSWORD)@$($config.REDIS_HOST):$($config.REDIS_PORT)/0`n"
} else {
    $envContent += "REDIS_URL=redis://$($config.REDIS_HOST):$($config.REDIS_PORT)/0`n"
}

$envContent += @"

# n8n Integration
N8N_HOST=$($config.N8N_HOST)
N8N_API_KEY=$($config.N8N_API_KEY)
"@

if ($config.N8N_USERNAME) {
    $envContent += "N8N_USERNAME=$($config.N8N_USERNAME)`n"
}
if ($config.N8N_PASSWORD) {
    $envContent += "N8N_PASSWORD=$($config.N8N_PASSWORD)`n"
}

$envContent += @"

# External APIs
"@

if ($config.OPENAI_API_KEY) {
    $envContent += "OPENAI_API_KEY=$($config.OPENAI_API_KEY)`n"
}
if ($config.ANTHROPIC_API_KEY) {
    $envContent += "ANTHROPIC_API_KEY=$($config.ANTHROPIC_API_KEY)`n"
}
if ($config.GOOGLE_API_KEY) {
    $envContent += "GOOGLE_API_KEY=$($config.GOOGLE_API_KEY)`n"
}

$envContent += @"

# Security
JWT_SECRET_KEY=$($config.JWT_SECRET_KEY)
CORS_ORIGINS=$($config.CORS_ORIGINS)
ALLOWED_HOSTS=$($config.ALLOWED_HOSTS)

# Monitoring
PROMETHEUS_ENABLED=$($config.PROMETHEUS_ENABLED)
GRAFANA_ADMIN_PASSWORD=$($config.GRAFANA_ADMIN_PASSWORD)
"@

if ($config.SMTP_HOST) {
    $envContent += @"

# Email Configuration
SMTP_HOST=$($config.SMTP_HOST)
SMTP_PORT=$($config.SMTP_PORT)
SMTP_USERNAME=$($config.SMTP_USERNAME)
SMTP_PASSWORD=$($config.SMTP_PASSWORD)
FROM_EMAIL=$($config.FROM_EMAIL)
"@
}

if ($config.DOMAIN) {
    $envContent += @"

# Deployment
DOMAIN=$($config.DOMAIN)
SSL_ENABLED=$($config.SSL_ENABLED)
TRAEFIK_ENABLED=$($config.TRAEFIK_ENABLED)
"@
}

# Save main .env file
$envPath = "c:\code\unityai\.env"
$envContent | Out-File -FilePath $envPath -Encoding UTF8
Write-Host "Created main .env file: $envPath" -ForegroundColor Green

# Save n8n-playground specific .env file
$n8nEnvPath = "c:\code\unityai\n8n-playground\.env"
$envContent | Out-File -FilePath $n8nEnvPath -Encoding UTF8
Write-Host "Created n8n-playground .env file: $n8nEnvPath" -ForegroundColor Green

# Create Docker Compose override for production
$dockerComposeOverride = @"
version: '3.8'

services:
  unityai-app:
    environment:
      - SECRET_KEY=$($config.SECRET_KEY)
      - ENVIRONMENT=$($config.ENVIRONMENT)
      - DEBUG=$($config.DEBUG)
      - LOG_LEVEL=$($config.LOG_LEVEL)
      - DB_HOST=$($config.DB_HOST)
      - DB_PORT=$($config.DB_PORT)
      - DB_NAME=$($config.DB_NAME)
      - DB_USER=$($config.DB_USER)
      - DB_PASSWORD=$($config.DB_PASSWORD)
      - REDIS_HOST=$($config.REDIS_HOST)
      - REDIS_PORT=$($config.REDIS_PORT)
"@

if ($config.REDIS_PASSWORD) {
    $dockerComposeOverride += "      - REDIS_PASSWORD=$($config.REDIS_PASSWORD)`n"
}

$dockerComposeOverride += @"
      - N8N_HOST=$($config.N8N_HOST)
      - N8N_API_KEY=$($config.N8N_API_KEY)
"@

if ($config.N8N_USERNAME) {
    $dockerComposeOverride += "      - N8N_USERNAME=$($config.N8N_USERNAME)`n"
}
if ($config.N8N_PASSWORD) {
    $dockerComposeOverride += "      - N8N_PASSWORD=$($config.N8N_PASSWORD)`n"
}

if ($config.OPENAI_API_KEY) {
    $dockerComposeOverride += "      - OPENAI_API_KEY=$($config.OPENAI_API_KEY)`n"
}
if ($config.ANTHROPIC_API_KEY) {
    $dockerComposeOverride += "      - ANTHROPIC_API_KEY=$($config.ANTHROPIC_API_KEY)`n"
}
if ($config.GOOGLE_API_KEY) {
    $dockerComposeOverride += "      - GOOGLE_API_KEY=$($config.GOOGLE_API_KEY)`n"
}

$dockerComposeOverride += @"
      - JWT_SECRET_KEY=$($config.JWT_SECRET_KEY)
      - CORS_ORIGINS=$($config.CORS_ORIGINS)
      - ALLOWED_HOSTS=$($config.ALLOWED_HOSTS)
      - PROMETHEUS_ENABLED=$($config.PROMETHEUS_ENABLED)
"@

if ($config.DOMAIN) {
    $dockerComposeOverride += @"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.unityai.rule=Host(\`$($config.DOMAIN)\`)"
      - "traefik.http.routers.unityai.tls=true"
      - "traefik.http.routers.unityai.tls.certresolver=letsencrypt"
"@
}

$dockerComposeOverride += @"

  grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=$($config.GRAFANA_ADMIN_PASSWORD)
"@

# Save Docker Compose override
$dockerComposePath = "c:\code\unityai\docker-compose.override.yml"
$dockerComposeOverride | Out-File -FilePath $dockerComposePath -Encoding UTF8
Write-Host "Created Docker Compose override: $dockerComposePath" -ForegroundColor Green

# Create deployment script
$deployScript = @"
#!/usr/bin/env pwsh

# UnityAI Platform Deployment Script
# Generated on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

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
Write-Host "Access your UnityAI platform at: http://localhost:8000" -ForegroundColor Cyan
"@

if ($config.DOMAIN) {
    $deployScript += "Write-Host `"Or at your domain: https://$($config.DOMAIN)`" -ForegroundColor Cyan`n"
}

$deployScript += @"
Write-Host "Grafana dashboard: http://localhost:3001 (admin/$($config.GRAFANA_ADMIN_PASSWORD))" -ForegroundColor Cyan
Write-Host "Prometheus: http://localhost:9090" -ForegroundColor Cyan
"@

# Save deployment script
$deployScriptPath = "c:\code\unityai\deploy-configured.ps1"
$deployScript | Out-File -FilePath $deployScriptPath -Encoding UTF8
Write-Host "Created deployment script: $deployScriptPath" -ForegroundColor Green

# Create backup script for configuration
$backupScript = @"
#!/usr/bin/env pwsh

# Configuration Backup Script
# Generated on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

`$backupDir = "config-backup-`$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path `$backupDir -Force

Copy-Item ".env" "`$backupDir/" -ErrorAction SilentlyContinue
Copy-Item "n8n-playground/.env" "`$backupDir/n8n-playground.env" -ErrorAction SilentlyContinue
Copy-Item "docker-compose.override.yml" "`$backupDir/" -ErrorAction SilentlyContinue

Write-Host "Configuration backed up to: `$backupDir" -ForegroundColor Green
"@

$backupScriptPath = "c:\code\unityai\backup-config.ps1"
$backupScript | Out-File -FilePath $backupScriptPath -Encoding UTF8
Write-Host "Created backup script: $backupScriptPath" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "=== Configuration Complete! ===" -ForegroundColor Green
Write-Host "Files created:" -ForegroundColor Cyan
Write-Host "  - .env (main configuration)" -ForegroundColor White
Write-Host "  - n8n-playground/.env (n8n-playground configuration)" -ForegroundColor White
Write-Host "  - docker-compose.override.yml (Docker configuration)" -ForegroundColor White
Write-Host "  - deploy-configured.ps1 (deployment script)" -ForegroundColor White
Write-Host "  - backup-config.ps1 (backup script)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the generated configuration files" -ForegroundColor White
Write-Host "2. Run: ./deploy-configured.ps1 to deploy the platform" -ForegroundColor White
Write-Host "3. Access your platform at the URLs shown after deployment" -ForegroundColor White
Write-Host ""
Write-Host "To backup your configuration, run: ./backup-config.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your UnityAI platform is ready for deployment!" -ForegroundColor Green