# Unity AI Server Setup Script for Windows
# This script automates the initial server setup for Unity AI deployment on Windows

param(
    [string]$AppDir = "C:\UnityAI",
    [string]$RepoUrl = ""
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "$Message" "Cyan"
}

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator"
    exit 1
}

Write-Info "Starting Unity AI Server Setup for Windows..."

# Step 1: Enable Windows Features
Write-Info "Enabling required Windows features..."
try {
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
    Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
    Write-Success "Windows features enabled"
} catch {
    Write-Warning "Some Windows features may already be enabled or require manual installation"
}

# Step 2: Install Chocolatey (Package Manager)
Write-Info "Installing Chocolatey package manager..."
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-Success "Chocolatey installed successfully"
} else {
    Write-Warning "Chocolatey already installed"
}

# Step 3: Install Required Software
Write-Info "Installing required software packages..."
$packages = @(
    "git",
    "docker-desktop",
    "openssl",
    "curl",
    "wget"
)

foreach ($package in $packages) {
    try {
        choco install $package -y
        Write-Success "$package installed successfully"
    } catch {
        Write-Warning "Failed to install $package or already installed"
    }
}

# Step 4: Create Application Directory
Write-Info "Creating application directory..."
if (!(Test-Path $AppDir)) {
    New-Item -ItemType Directory -Path $AppDir -Force
    Write-Success "Application directory created: $AppDir"
} else {
    Write-Warning "Application directory already exists: $AppDir"
}

# Step 5: Clone Repository
Set-Location $AppDir
if (!(Test-Path ".git")) {
    if ($RepoUrl -eq "") {
        $RepoUrl = Read-Host "Enter your Git repository URL"
    }
    Write-Info "Cloning Unity AI repository..."
    git clone $RepoUrl .
    Write-Success "Repository cloned successfully"
} else {
    Write-Warning "Repository already exists, updating..."
    git pull origin main
}

# Step 6: Create Required Directories
Write-Info "Creating required directories..."
$directories = @("logs", "traefik", "backups")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Success "Created directory: $dir"
    }
}

# Create acme.json file for Traefik
$acmeFile = "traefik\acme.json"
if (!(Test-Path $acmeFile)) {
    New-Item -ItemType File -Path $acmeFile -Force
    Write-Success "Created acme.json file"
}

# Step 7: Generate Environment Files
Write-Info "Generating environment files..."
if (Test-Path "generate_envs.py") {
    python generate_envs.py
    Write-Success "Environment files generated using Python script"
} elseif (Test-Path "generate_envs.sh") {
    # Convert shell script to PowerShell if needed
    Write-Warning "Shell script found but PowerShell equivalent needed"
} else {
    Write-Warning "No environment generation script found"
}

# Step 8: Create Windows Service Script
Write-Info "Creating Windows service management script..."
$serviceScript = @'
# Unity AI Service Management Script
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action
)

$AppDir = "C:\UnityAI"
Set-Location $AppDir

switch ($Action) {
    "start" {
        Write-Host "Starting Unity AI services..." -ForegroundColor Green
        docker-compose up -d
    }
    "stop" {
        Write-Host "Stopping Unity AI services..." -ForegroundColor Yellow
        docker-compose down
    }
    "restart" {
        Write-Host "Restarting Unity AI services..." -ForegroundColor Cyan
        docker-compose restart
    }
    "status" {
        Write-Host "Unity AI services status:" -ForegroundColor Blue
        docker-compose ps
    }
}
'@

$serviceScript | Out-File -FilePath "scripts\unity-service.ps1" -Encoding UTF8
Write-Success "Service management script created"

# Step 9: Create Backup Script
Write-Info "Creating backup script..."
$backupScript = @'
# Unity AI Backup Script
param(
    [string]$BackupDir = "C:\UnityAI\backups"
)

$Date = Get-Date -Format "yyyyMMdd_HHmmss"
$AppDir = "C:\UnityAI"

Set-Location $AppDir

# Create backup directory
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force
}

Write-Host "Starting backup process..." -ForegroundColor Green

# Backup database
try {
    docker-compose exec -T postgres pg_dump -U n8n_user n8n > "$BackupDir\db_backup_$Date.sql"
    Write-Host "Database backup completed" -ForegroundColor Green
} catch {
    Write-Host "Database backup failed: $_" -ForegroundColor Red
}

# Backup n8n data
try {
    docker-compose exec -T n8n tar -czf - /opt/unity/n8n > "$BackupDir\n8n_data_$Date.tar.gz"
    Write-Host "n8n data backup completed" -ForegroundColor Green
} catch {
    Write-Host "n8n data backup failed: $_" -ForegroundColor Red
}

# Clean old backups (keep last 7 days)
$cutoffDate = (Get-Date).AddDays(-7)
Get-ChildItem $BackupDir -Filter "*backup*" | Where-Object { $_.LastWriteTime -lt $cutoffDate } | Remove-Item -Force

Write-Host "Backup process completed: $Date" -ForegroundColor Green
'@

$backupScript | Out-File -FilePath "scripts\backup.ps1" -Encoding UTF8
Write-Success "Backup script created"

# Step 10: Create Scheduled Task for Backups
Write-Info "Creating scheduled task for automated backups..."
try {
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"$AppDir\scripts\backup.ps1`""
    $trigger = New-ScheduledTaskTrigger -Daily -At "2:00AM"
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Register-ScheduledTask -TaskName "UnityAI-Backup" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
    Write-Success "Scheduled backup task created (daily at 2 AM)"
} catch {
    Write-Warning "Failed to create scheduled task: $_"
}

# Step 11: Configure Windows Firewall
Write-Info "Configuring Windows Firewall..."
try {
    New-NetFirewallRule -DisplayName "Unity AI HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
    New-NetFirewallRule -DisplayName "Unity AI HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
    New-NetFirewallRule -DisplayName "Unity AI FastAPI" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
    New-NetFirewallRule -DisplayName "Unity AI n8n" -Direction Inbound -Protocol TCP -LocalPort 5678 -Action Allow
    Write-Success "Firewall rules configured"
} catch {
    Write-Warning "Failed to configure firewall rules: $_"
}

# Step 12: Create Environment Configuration Helper
Write-Info "Creating environment configuration helper..."
$configHelper = @'
# Unity AI Environment Configuration Helper

Write-Host "Unity AI Environment Configuration" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

$envFiles = @(
    ".env.fastapi",
    ".env.database", 
    ".env.security"
)

foreach ($file in $envFiles) {
    if (Test-Path $file) {
        Write-Host "\nConfiguring $file..." -ForegroundColor Yellow
        notepad $file
        $continue = Read-Host "Press Enter to continue to next file or ''q'' to quit"
        if ($continue -eq "q") { break }
    } else {
        Write-Host "$file not found" -ForegroundColor Red
    }
}

Write-Host "\nNext steps:" -ForegroundColor Green
Write-Host "1. Set your API keys in the environment files" -ForegroundColor White
Write-Host "2. Update domain configuration in docker-compose.yml" -ForegroundColor White
Write-Host "3. Run: docker-compose up -d" -ForegroundColor White
Write-Host "4. Import workflows: .\scripts\import-workflows.ps1" -ForegroundColor White
'@

$configHelper | Out-File -FilePath "scripts\configure-env.ps1" -Encoding UTF8
Write-Success "Environment configuration helper created"

# Step 13: Display Next Steps
Write-Success "Unity AI Server Setup for Windows Complete!"

Write-Host "`n" -ForegroundColor Green
Write-Host "=== NEXT STEPS ===" -ForegroundColor Green
Write-Host "1. Configure your environment variables:" -ForegroundColor Yellow
Write-Host "   .\scripts\configure-env.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Update domain configuration in docker-compose.yml" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Start Docker Desktop and ensure it's running" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Start the services:" -ForegroundColor Yellow
Write-Host "   docker-compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Import n8n workflows:" -ForegroundColor Yellow
Write-Host "   .\scripts\import-workflows.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "6. Generate n8n API key and update .env.fastapi" -ForegroundColor Yellow
Write-Host ""
Write-Host "Service Management:" -ForegroundColor Green
Write-Host "   .\scripts\unity-service.ps1 start|stop|restart|status" -ForegroundColor Cyan
Write-Host ""
Write-Host "For detailed instructions, see: DEPLOYMENT-GUIDE.md" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Restart your computer to complete Docker Desktop setup" -ForegroundColor Red

Write-Success "Setup script completed successfully!"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker version: $(docker --version)" -ForegroundColor Cyan
} else {
    Write-Warning "Docker not found in PATH. Please restart your computer and ensure Docker Desktop is running."
}

if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    Write-Host "Docker Compose version: $(docker-compose --version)" -ForegroundColor Cyan
} else {
    Write-Warning "Docker Compose not found in PATH. Please restart your computer."
}