# UnityAI - One-Click Production Setup

🚀 **Get your UnityAI platform running in production with a single command!**

## Prerequisites

- Windows 10/11 or Windows Server
- Docker Desktop installed and running
- PowerShell 5.1 or later
- At least 4GB RAM available
- Ports 8000, 3001, 9090 available
- Git (for cloning the repository)
- Administrative privileges (for Docker operations)

## Configuration Options

You have **two options** for configuration:

### Option 1: Template-based Configuration (Recommended for experienced users)
1. Copy `config/production-config-template.env` to `config/production-config.env`
2. Edit the template file with your values
3. Run the one-click script

### Option 2: Interactive Configuration
1. Run the one-click script
2. Follow the interactive prompts
3. Script will guide you through all settings

## Installation

### Step 1: Download UnityAI
```powershell
# Clone or download the UnityAI repository
git clone https://github.com/Flissel/unityai.git
cd unityai
```

### Step 2: Run One-Click Setup
```powershell
.\scripts\one-click-production.ps1
```

**That's it!** The script will:

1. ✅ **Configure** - Interactive setup for all settings
2. ✅ **Build** - Compile all Docker images automatically
3. ✅ **Clean** - Remove old deployments
4. ✅ **Deploy** - Start production environment
5. ✅ **Verify** - Check all services are running

## What You Get

### 🌐 Access URLs
- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana Dashboard**: http://localhost:3001
- **Prometheus Metrics**: http://localhost:9090

### 🔧 Built-in Features
- **AI Workflow Automation** with n8n integration
- **Real-time Monitoring** with Grafana + Prometheus
- **Secure Configuration** with encrypted secrets
- **Production Logging** with structured output
- **Health Monitoring** with automatic restarts
- **Database Management** with PostgreSQL
- **Caching Layer** with Redis

## Configuration Categories

The interactive setup covers:

### 🔐 Security & Authentication
- Application secret keys
- Database passwords
- API tokens
- SSL certificates

### 🌍 External Integrations
- n8n workflow credentials
- OpenAI API keys
- Email SMTP settings
- External API endpoints

### 📊 Monitoring & Logging
- Grafana admin credentials
- Log levels and retention
- Metrics collection
- Alert configurations

### 🚀 Deployment Settings
- Domain configuration
- Port mappings
- Resource limits
- Backup settings

## Management Commands

### View Logs
```powershell
docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml logs -f
```

### Check Service Status
```powershell
docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml ps
```

### Stop Services
```powershell
docker-compose -f compose/docker-compose.yml -f docker-compose.override.yml down
```

### Restart Everything
```powershell
.\scripts\one-click-production.ps1
```

### Update Configuration
```powershell
.\scripts\setup-interactive-config.ps1
.\scripts\deploy-with-config.ps1
```

## Troubleshooting

### Common Issues

**Docker not running:**
```powershell
# Start Docker Desktop and wait for it to be ready
# Then run the script again
```

**Port conflicts:**
```powershell
# Check what's using the ports
netstat -ano | findstr :8000
# Stop conflicting services or change ports in configuration
```

**Configuration errors:**
```powershell
# Reconfigure with the interactive script
.\scripts\setup-interactive-config.ps1
```

**Service startup failures:**
```powershell
# Check logs for specific service
docker-compose logs [service-name]
# Common services: unityai-app, postgres, redis, grafana
```

### Getting Help

1. **Check Logs**: Always start with `docker-compose logs`
2. **Verify Configuration**: Ensure `.env` file has all required values
3. **Resource Check**: Ensure sufficient RAM and disk space
4. **Network Check**: Verify ports are not in use

## Production Considerations

### Security
- Change all default passwords during setup
- Use strong secret keys (generated automatically)
- Configure SSL certificates for public domains
- Regularly update Docker images

### Performance
- Allocate at least 4GB RAM to Docker
- Use SSD storage for better performance
- Monitor resource usage via Grafana
- Scale services based on load

### Backup
- Database backups are configured automatically
- Configuration files are saved in `.env`
- Export Grafana dashboards regularly
- Document custom n8n workflows

## Commercial Deployment

This one-click setup is perfect for:
- **Customer Installations** - Simple deployment for clients
- **Demo Environments** - Quick setup for presentations
- **Development Teams** - Consistent production-like environments
- **Small to Medium Businesses** - Full-featured platform without complexity

---

**🎉 Congratulations!** Your UnityAI platform is now running in production mode.

For advanced configuration and customization, see the main [README.md](README.md) file.