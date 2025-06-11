# UnityAI Docker Swarm Secrets Creation Script (PowerShell)
# This script helps create the required secret files for Docker Swarm deployment on Windows

param(
    [string]$SecretsDir = "./secrets"
)

Write-Host "=== UnityAI Docker Swarm Secrets Setup ===" -ForegroundColor Blue

# Create secrets directory
if (-not (Test-Path $SecretsDir)) {
    New-Item -ItemType Directory -Path $SecretsDir -Force | Out-Null
}
Write-Host "Created secrets directory: $SecretsDir" -ForegroundColor Green

# Function to generate random password
function Generate-Password {
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    $password = ""
    for ($i = 0; $i -lt 25; $i++) {
        $password += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $password
}

# Function to create secret file
function Create-SecretFile {
    param(
        [string]$SecretName,
        [string]$PromptMessage,
        [bool]$GenerateRandom = $false
    )
    
    $secretFile = "$SecretsDir/$SecretName.txt"
    
    if (Test-Path $secretFile) {
        Write-Host "Secret file $secretFile already exists" -ForegroundColor Yellow
        $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            return
        }
    }
    
    Write-Host $PromptMessage -ForegroundColor Blue
    
    if ($GenerateRandom) {
        $generateChoice = Read-Host "Generate random password? (Y/n)"
        if ($generateChoice -eq "n" -or $generateChoice -eq "N") {
            $secretValue = Read-Host "Enter value" -AsSecureString
            $secretValue = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretValue))
        } else {
            $secretValue = Generate-Password
            Write-Host "Generated random password" -ForegroundColor Green
        }
    } else {
        $secretValue = Read-Host "Enter value" -AsSecureString
        $secretValue = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretValue))
    }
    
    $secretValue | Out-File -FilePath $secretFile -Encoding UTF8 -NoNewline
    Write-Host "Created: $secretFile" -ForegroundColor Green
}

Write-Host "This script will help you create all required secret files for Docker Swarm deployment." -ForegroundColor Yellow
Write-Host "You can generate random passwords for database/service passwords or enter your own values." -ForegroundColor Yellow
Write-Host ""

# Database secrets
Write-Host "=== Database Secrets ===" -ForegroundColor Blue
Create-SecretFile "postgres_password" "PostgreSQL database password" $true
Create-SecretFile "redis_pw" "Redis password" $true

# N8N secrets
Write-Host "=== N8N Secrets ===" -ForegroundColor Blue
Create-SecretFile "n8n_admin_password" "N8N admin password" $true
Create-SecretFile "n8n_encryption_key" "N8N encryption key (32+ characters)" $true
Create-SecretFile "n8n_api_key" "N8N API key (get from N8N interface after setup)"

# Cloudflare secrets
Write-Host "=== Cloudflare Secrets ===" -ForegroundColor Blue
Create-SecretFile "cloudflare_email" "Cloudflare account email"
Create-SecretFile "cloudflare_token" "Cloudflare API token (with DNS edit permissions)"

# API Keys
Write-Host "=== External API Keys ===" -ForegroundColor Blue
Create-SecretFile "openai_api_key" "OpenAI API key"
Create-SecretFile "anthropic_api_key" "Anthropic API key (optional)"
Create-SecretFile "groq_api_key" "Groq API key (optional)"

# Monitoring secrets
Write-Host "=== Monitoring Secrets ===" -ForegroundColor Blue
Create-SecretFile "grafana_admin_password" "Grafana admin password" $true

# Runner token (if using GitHub Actions runner)
Write-Host "=== GitHub Actions Runner (Optional) ===" -ForegroundColor Blue
$setupRunner = Read-Host "Do you want to set up GitHub Actions runner? (y/N)"
if ($setupRunner -eq "y" -or $setupRunner -eq "Y") {
    Create-SecretFile "runner_token" "GitHub Actions runner token"
} else {
    "PLACEHOLDER" | Out-File -FilePath "$SecretsDir/runner_token.txt" -Encoding UTF8 -NoNewline
    Write-Host "Created placeholder runner_token.txt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Secrets Creation Complete ===" -ForegroundColor Green
Write-Host "Created secret files in: $SecretsDir" -ForegroundColor Blue
Write-Host ""
Write-Host "Important Security Notes:" -ForegroundColor Yellow
Write-Host "  • Do NOT commit the secrets directory to version control"
Write-Host "  • Backup your secrets securely"
Write-Host "  • The secrets directory should be added to .gitignore"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Blue
Write-Host "  1. Review and update any placeholder values in the secret files"
Write-Host "  2. Run: .\deploy-swarm.ps1 to deploy the stack"
Write-Host "  3. Access N8N to get the API key and update n8n_api_key.txt if needed"

# Add secrets directory to .gitignore if it exists
if (Test-Path ".gitignore") {
    $gitignoreContent = Get-Content ".gitignore" -ErrorAction SilentlyContinue
    if ($gitignoreContent -notcontains "secrets/") {
        Add-Content ".gitignore" "secrets/"
        Write-Host "Added secrets/ to .gitignore" -ForegroundColor Green
    }
} else {
    "secrets/" | Out-File -FilePath ".gitignore" -Encoding UTF8
    Write-Host "Created .gitignore with secrets/ entry" -ForegroundColor Green
}