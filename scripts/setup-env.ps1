# Unity AI Platform - Environment Setup Script (PowerShell)
# Dieses Skript setzt alle notwendigen Umgebungsvariablen für die lokale Entwicklung

Write-Host "🚀 Unity AI Platform - Environment Setup" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Basis-Konfiguration
Write-Host "📋 Setze Basis-Konfiguration..." -ForegroundColor Yellow
$env:FASTAPI_ENV = "development"
$env:FASTAPI_DEBUG = "true"
$env:FASTAPI_WORKERS = "1"
$env:FASTAPI_LOG_LEVEL = "debug"
$env:FASTAPI_HOST = "0.0.0.0"
$env:FASTAPI_PORT = "8000"

# Datenbank-Konfiguration
Write-Host "🗄️  Setze Datenbank-Konfiguration..." -ForegroundColor Yellow
$env:DATABASE_URL = "sqlite:///./unityai.db"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "postgres"
$env:POSTGRES_DB = "unityai"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"

# Redis-Konfiguration
Write-Host "🔴 Setze Redis-Konfiguration..." -ForegroundColor Yellow
$env:REDIS_URL = "redis://localhost:6379/0"
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:REDIS_DB = "0"
$env:REDIS_PASSWORD = ""

# Sicherheits-Konfiguration
Write-Host "🔐 Setze Sicherheits-Konfiguration..." -ForegroundColor Yellow
$env:SECRET_KEY = "dev-secret-key-change-in-production"
$env:JWT_SECRET_KEY = "jwt-secret-key-change-in-production"
$env:ACCESS_TOKEN_EXPIRE_MINUTES = "30"
$env:API_KEYS = "dev-key-1,dev-key-2,dev-key-3"
$env:API_KEY_HEADER = "X-API-Key"
$env:API_KEY_REQUIRED = "false"

# CORS-Konfiguration
Write-Host "🌐 Setze CORS-Konfiguration..." -ForegroundColor Yellow
$env:CORS_ORIGINS = "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080"
$env:CORS_CREDENTIALS = "true"
$env:CORS_METHODS = "GET,POST,PUT,DELETE,OPTIONS"
$env:CORS_HEADERS = "*"

# n8n-Konfiguration
Write-Host "🔄 Setze n8n-Konfiguration..." -ForegroundColor Yellow
$env:N8N_HOST = "localhost"
$env:N8N_PORT = "5678"
$env:N8N_PROTOCOL = "http"
$env:N8N_API_URL = "http://localhost:5678/api/v1"
$env:N8N_WEBHOOK_URL = "http://localhost:5678/webhook"
$env:N8N_BASIC_AUTH_ACTIVE = "true"
$env:N8N_BASIC_AUTH_USER = "admin"
$env:N8N_BASIC_AUTH_PASSWORD = "admin"
$env:N8N_LOG_LEVEL = "info"
$env:N8N_ENCRYPTION_KEY = "your-n8n-encryption-key-here-64-chars-long"

# AutoGen/OpenAI-Konfiguration
Write-Host "🤖 Setze AutoGen/OpenAI-Konfiguration..." -ForegroundColor Yellow
$env:AUTOGEN_ENABLED = "true"
$env:AUTOGEN_MODEL = "gpt-4o"
$env:AUTOGEN_MAX_TOKENS = "2048"
$env:AUTOGEN_TEMPERATURE = "0.7"
$env:OPENAI_MAX_TOKENS = "2048"
$env:OPENAI_TEMPERATURE = "0.7"
$env:OPENAI_MODEL = "gpt-4o"

# Cache-Konfiguration
Write-Host "💾 Setze Cache-Konfiguration..." -ForegroundColor Yellow
$env:CACHE_TTL = "3600"
$env:CACHE_MAX_SIZE = "1000"
$env:CACHE_ENABLED = "true"

# Logging-Konfiguration
Write-Host "📝 Setze Logging-Konfiguration..." -ForegroundColor Yellow
$env:LOG_LEVEL = "DEBUG"
$env:LOG_FORMAT = "detailed"
$env:LOG_FILE = "logs/unityai.log"
$env:LOG_ROTATION = "daily"
$env:LOG_RETENTION = "30"

# Monitoring-Konfiguration
Write-Host "📊 Setze Monitoring-Konfiguration..." -ForegroundColor Yellow
$env:METRICS_ENABLED = "true"
$env:METRICS_PORT = "9090"
$env:HEALTH_CHECK_ENABLED = "true"


# Rate Limiting
Write-Host "⚡ Setze Rate Limiting..." -ForegroundColor Yellow
$env:RATE_LIMIT_ENABLED = "true"
$env:RATE_LIMIT_REQUESTS = "100"
$env:RATE_LIMIT_WINDOW = "60"

# File Upload
Write-Host "📁 Setze File Upload-Konfiguration..." -ForegroundColor Yellow
$env:UPLOAD_MAX_SIZE = "10485760"
$env:UPLOAD_ALLOWED_TYPES = "txt,py,json,yaml,yml,md"
$env:UPLOAD_DIR = "uploads"

# Development Tools
Write-Host "🛠️  Setze Development Tools..." -ForegroundColor Yellow
$env:RELOAD_ON_CHANGE = "true"
$env:DEBUG_MODE = "true"
$env:PROFILING_ENABLED = "false"

# Testing
Write-Host "🧪 Setze Testing-Konfiguration..." -ForegroundColor Yellow
$env:TESTING = "false"
$env:TEST_DATABASE_URL = "sqlite:///./test_unityai.db"
$env:TEST_REDIS_URL = "redis://localhost:6379/1"

Write-Host "" 
Write-Host "✅ Alle Umgebungsvariablen wurden gesetzt!" -ForegroundColor Green
Write-Host "" 
Write-Host "📋 Wichtige Hinweise:" -ForegroundColor Cyan
Write-Host "   • Setzen Sie OPENAI_API_KEY mit Ihrem echten API-Schlüssel:" -ForegroundColor White
Write-Host "     `$env:OPENAI_API_KEY = 'sk-...'" -ForegroundColor Gray
Write-Host "   • Setzen Sie N8N_API_KEY mit Ihrem n8n API-Schlüssel:" -ForegroundColor White
Write-Host "     `$env:N8N_API_KEY = 'your-n8n-api-key'" -ForegroundColor Gray
Write-Host "   • Für Produktion ändern Sie SECRET_KEY und JWT_SECRET_KEY!" -ForegroundColor White
Write-Host "" 
Write-Host "🚀 Starten Sie die Anwendung mit:" -ForegroundColor Cyan
Write-Host "   cd fastapi && python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Gray
Write-Host "" 
Write-Host "🌐 Die Anwendung ist dann verfügbar unter:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000" -ForegroundColor Gray
Write-Host "   http://localhost:8000/docs (API-Dokumentation)" -ForegroundColor Gray