# Unity AI Server Deployment Guide

This guide provides complete instructions for deploying the Unity AI system on your server with AutoGen Core integration and n8n workflows.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: 4+ cores
- **Storage**: 50GB+ SSD
- **Network**: Public IP with ports 80, 443 accessible

### Required Software
- Docker 24.0+
- Docker Compose 2.0+
- Git
- OpenSSL (for certificates)

## 🚀 Step 1: Server Preparation

### Install Docker & Docker Compose
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Create Application Directory
```bash
sudo mkdir -p /opt/unityai
sudo chown $USER:$USER /opt/unityai
cd /opt/unityai
```

## 📥 Step 2: Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/your-org/unityai.git .

# Make scripts executable
chmod +x scripts/*.sh
chmod +x generate_envs.sh
```

## 🔧 Step 3: Environment Configuration

### Generate Base Environment Files
```bash
# Generate all environment files
./generate_envs.sh

# Or use Python script
python3 generate_envs.py
```

### Configure Critical Environment Variables

#### 1. Database Configuration (`.env.database`)
```bash
# Edit database settings
nano .env.database
```
```env
POSTGRES_DB=n8n
POSTGRES_USER=n8n_user
POSTGRES_PASSWORD=your_secure_db_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

#### 2. FastAPI Configuration (`.env.fastapi`)
```bash
nano .env.fastapi
```
```env
# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_DB=0

# n8n API Configuration
N8N_API_URL=http://n8n:5678/api/v1
N8N_API_KEY=your_n8n_api_key_here
N8N_WEBHOOK_URL=http://n8n:5678/webhook

# Autogen Configuration
AUTOGEN_ENABLED=true
AUTOGEN_MODEL=gpt-4
AUTOGEN_API_KEY=your_autogen_api_key
# OpenAI API Key for AutoGen Core
OPENAI_API_KEY=your_openai_api_key_here

# FastAPI Configuration
FASTPAPI_ENV=production
FASTPAPI_DEBUG=false
FASTPAPI_WORKERS=4
FASTPAPI_LOG_LEVEL=info

# Security
CORS_ORIGINS=https://yourdomain.com
API_KEY_HEADER=X-API-Key
API_KEY=your_secure_api_key
```

#### 3. Security Configuration (`.env.security`)
```bash
nano .env.security
```
```env
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD_FILE=/run/secrets/n8n_pw
N8N_COOKIE_SAME_SITE=lax
```

#### 4. Domain Configuration
Update `docker-compose.yml` with your domain:
```yaml
labels:
  - traefik.http.routers.n8n.rule=Host(`n8n.yourdomain.com`)
  - traefik.http.routers.fastapi.rule=Host(`api.yourdomain.com`)
```

## 🔐 Step 4: Security Setup

### Create Docker Secrets
```bash
# Initialize Docker Swarm (required for secrets)
docker swarm init

# Create database password secret
echo "your_secure_db_password" | docker secret create pg_pw -

# Create n8n password secret
echo "your_secure_n8n_password" | docker secret create n8n_pw -

# Verify secrets
docker secret ls
```

### SSL Certificate Setup
```bash
# Create Traefik directory
mkdir -p traefik
touch traefik/acme.json
chmod 600 traefik/acme.json

# Set Cloudflare API token (if using Cloudflare)
export CF_DNS_API_TOKEN=your_cloudflare_api_token
```

## 🏗️ Step 5: Build and Deploy

### Build Custom Images
```bash
# Build n8n image
docker-compose build n8n

# Build FastAPI image
docker-compose build fastapi
```

### Start Core Services
```bash
# Start infrastructure services first
docker-compose up -d traefik redis postgres

# Wait for services to be healthy
docker-compose ps

# Start application services
docker-compose up -d n8n fastapi
```

### Verify Deployment
```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs -f fastapi
docker-compose logs -f n8n

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:5678/healthz
```

## 🔄 Step 6: n8n Workflow Setup

### Import Workflows
```bash
# Make import script executable
chmod +x scripts/import-workflows.sh

# Import all workflows
./scripts/import-workflows.sh

# Or use PowerShell on Windows
# powershell -ExecutionPolicy Bypass -File scripts/import-workflows.ps1
```

### Generate n8n API Key
1. Access n8n UI: `https://n8n.yourdomain.com`
2. Login with admin credentials
3. Go to **Settings** → **API Keys**
4. Create new API key
5. Update `.env.fastapi` with the key:
   ```bash
   nano .env.fastapi
   # Update: N8N_API_KEY=your_generated_api_key
   ```
6. Restart FastAPI service:
   ```bash
   docker-compose restart fastapi
   ```

## 🔍 Step 7: Testing and Validation

### Test AutoGen Integration
```bash
# Test decision endpoint
curl -X POST https://api.yourdomain.com/decide \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your_api_key' \
  -d '{
    "event_type": "automation_request",
    "data": {
      "topic": "notification",
      "message": "Test message",
      "channel_type": "slack"
    }
  }'
```

### Test n8n Workflows
```bash
# Test workflow execution
curl -X POST https://api.yourdomain.com/execute-workflow \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your_api_key' \
  -d '{
    "workflow_name": "example-automation-workflow",
    "parameters": {
      "topic": "email",
      "recipient": "test@example.com",
      "subject": "Test Email"
    }
  }'
```

### Monitor System Health
```bash
# Check metrics
curl https://api.yourdomain.com/metrics

# View logs
docker-compose logs -f --tail=100

# Check resource usage
docker stats
```

## 📊 Step 8: Monitoring Setup

### Prometheus Metrics
- FastAPI metrics: `https://api.yourdomain.com/metrics`
- n8n metrics: Available in n8n logs

### Log Management
```bash
# Create log rotation
sudo nano /etc/logrotate.d/unityai
```
```
/opt/unityai/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        docker-compose restart fastapi n8n
    endscript
}
```

## 🔄 Step 9: Backup and Maintenance

### Database Backup
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/unityai/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec postgres pg_dump -U n8n_user n8n > $BACKUP_DIR/db_backup_$DATE.sql

# Backup n8n data
docker-compose exec n8n tar -czf - /opt/unity/n8n > $BACKUP_DIR/n8n_data_$DATE.tar.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*backup*" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab
echo "0 2 * * * /opt/unityai/backup.sh" | crontab -
```

### Update Procedure
```bash
# Update system
git pull origin main

# Rebuild images
docker-compose build

# Rolling update
docker-compose up -d --force-recreate

# Verify health
docker-compose ps
```

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
docker-compose logs service_name

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose restart
```

#### API Key Issues
```bash
# Regenerate n8n API key
# Access n8n UI → Settings → API Keys → Create New

# Update environment
nano .env.fastapi
docker-compose restart fastapi
```

#### SSL Certificate Issues
```bash
# Check Traefik logs
docker-compose logs traefik

# Verify DNS settings
nslookup yourdomain.com

# Force certificate renewal
docker-compose exec traefik rm /acme/acme.json
docker-compose restart traefik
```

## 📞 Support

### Health Check URLs
- FastAPI: `https://api.yourdomain.com/health`
- n8n: `https://n8n.yourdomain.com/healthz`
- Metrics: `https://api.yourdomain.com/metrics`

### Log Locations
- Application logs: `/opt/unityai/logs/`
- Docker logs: `docker-compose logs service_name`

### Performance Tuning
```bash
# Increase worker processes
# Edit .env.fastapi:
FASTPAPI_WORKERS=8
WORKER_CONCURRENCY=20

# Optimize database
# Edit .env.database:
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

## 🎯 Success Criteria

Your Unity AI system is successfully deployed when:

✅ All services show "healthy" status
✅ FastAPI responds to `/health` endpoint
✅ n8n UI is accessible and workflows are imported
✅ AutoGen Core makes decisions successfully
✅ Workflows execute and return results
✅ Metrics are being collected
✅ SSL certificates are valid
✅ Backups are running automatically

**Your 30-second automation system is now live! 🚀**

---

*For additional support, check the logs and refer to the individual service documentation in the `fastapi/README.md` and `n8n/workflows/README.md` files.*