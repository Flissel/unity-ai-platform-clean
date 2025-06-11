# UnityAI Docker Swarm Deployment Script (PowerShell)
# This script deploys the UnityAI stack to Docker Swarm on Windows

param(
    [string]$StackName = "unityai",
    [string]$ConfigDir = "./config",
    [string]$SecretsDir = "./secrets"
)

# Configuration
$EnvFile = "$ConfigDir/.env.production"
$ComposeFile = "docker-compose.swarm.yml"

Write-Host "=== UnityAI Docker Swarm Deployment ===" -ForegroundColor Blue

# Check if running on swarm manager
$swarmState = docker info --format '{{.Swarm.LocalNodeState}}' 2>$null
if ($swarmState -ne "active") {
    Write-Host "Error: This node is not part of a Docker Swarm or not a manager node" -ForegroundColor Red
    Write-Host "Please initialize swarm with: docker swarm init"
    exit 1
}

# Check if .env.production exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "Error: $EnvFile not found" -ForegroundColor Red
    Write-Host "Please create the production environment file first"
    exit 1
}

# Check if docker-compose.swarm.yml exists
if (-not (Test-Path $ComposeFile)) {
    Write-Host "Error: $ComposeFile not found" -ForegroundColor Red
    exit 1
}

# Create secrets directory if it doesn't exist
if (-not (Test-Path $SecretsDir)) {
    New-Item -ItemType Directory -Path $SecretsDir -Force | Out-Null
}

Write-Host "Creating Docker secrets..." -ForegroundColor Yellow

# Function to create secret if it doesn't exist
function Create-Secret {
    param(
        [string]$SecretName,
        [string]$SecretFile
    )
    
    $existingSecrets = docker secret ls --format "{{.Name}}" 2>$null
    if ($existingSecrets -contains $SecretName) {
        Write-Host "Secret $SecretName already exists, skipping..." -ForegroundColor Yellow
    } else {
        if (Test-Path $SecretFile) {
            docker secret create $SecretName $SecretFile
            Write-Host "Created secret: $SecretName" -ForegroundColor Green
        } else {
            Write-Host "Warning: Secret file $SecretFile not found for $SecretName" -ForegroundColor Red
            Write-Host "Creating placeholder secret. Please update it manually." -ForegroundColor Yellow
            "PLACEHOLDER_VALUE" | docker secret create $SecretName -
        }
    }
}

# Create all required secrets
Create-Secret "pg_pw" "$SecretsDir/postgres_password.txt"
Create-Secret "redis_pw" "$SecretsDir/redis_password.txt"
Create-Secret "n8n_admin_password" "$SecretsDir/n8n_admin_password.txt"
Create-Secret "n8n_encryption_key" "$SecretsDir/n8n_encryption_key.txt"
Create-Secret "n8n_api_key" "$SecretsDir/n8n_api_key.txt"
Create-Secret "cloudflare_email" "$SecretsDir/cloudflare_email.txt"
Create-Secret "cloudflare_token" "$SecretsDir/cloudflare_token.txt"
Create-Secret "openai_api_key" "$SecretsDir/openai_api_key.txt"
Create-Secret "anthropic_api_key" "$SecretsDir/anthropic_api_key.txt"
Create-Secret "groq_api_key" "$SecretsDir/groq_api_key.txt"
Create-Secret "grafana_admin_password" "$SecretsDir/grafana_admin_password.txt"
Create-Secret "runner_token" "$SecretsDir/runner_token.txt"

Write-Host "Deploying stack to Docker Swarm..." -ForegroundColor Yellow

# Deploy the stack
docker stack deploy -c $ComposeFile $StackName

Write-Host "Stack deployment initiated!" -ForegroundColor Green
Write-Host "Checking service status..." -ForegroundColor Blue

# Wait a moment for services to start
Start-Sleep -Seconds 5

# Show service status
docker stack services $StackName

Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Access points:" -ForegroundColor Blue
Write-Host "  • Main App: https://unit-y-ai.io"
Write-Host "  • API: https://api.unit-y-ai.io"
Write-Host "  • N8N: https://n8n.unit-y-ai.io"
Write-Host "  • Webhooks: https://webhooks.unit-y-ai.io"
Write-Host "  • Traefik Dashboard: https://traefik.unit-y-ai.io"
Write-Host "  • Grafana: https://grafana.unit-y-ai.io"

Write-Host "Note: Services may take a few minutes to become fully available" -ForegroundColor Yellow
Write-Host "Monitor with: docker stack services $StackName" -ForegroundColor Yellow
Write-Host "View logs with: docker service logs <service_name>" -ForegroundColor Yellow