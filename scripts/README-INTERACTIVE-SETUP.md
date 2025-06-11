# UnityAI Platform Interactive Setup Guide

This guide provides a complete interactive setup solution for the UnityAI platform, designed for easy deployment and configuration management. Perfect for selling the platform to customers who need full external control.

## Overview

The interactive setup system consists of three main scripts:

1. **`setup-interactive-config.ps1`** - Interactive configuration wizard
2. **`deploy-with-config.ps1`** - Automated deployment using generated configuration
3. **`backup-config.ps1`** - Configuration backup utility (auto-generated)

## Quick Start

### Step 1: Run Interactive Configuration

```powershell
# Navigate to the UnityAI directory
cd c:\code\unityai

# Run the interactive configuration script
.\scripts\setup-interactive-config.ps1
```

This script will:
- Guide you through all necessary configuration options
- Generate secure keys automatically
- Create all required configuration files
- Set up Docker deployment configurations

### Step 2: Deploy the Platform

```powershell
# Deploy using the generated configuration
.\scripts\deploy-with-config.ps1
```

This script will:
- Load your configuration
- Update existing Docker services or deploy new ones
- Provide access URLs and credentials

### Step 3: Access Your Platform

After deployment, you can access:
- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001
- **Prometheus**: http://localhost:9090

## Configuration Categories

The interactive setup covers all essential configuration areas:

### 1. Basic Application Configuration
- **SECRET_KEY**: Auto-generated secure key for application security
- **ENVIRONMENT**: development/staging/production
- **DEBUG**: Enable/disable debug mode
- **LOG_LEVEL**: Logging verbosity (DEBUG/INFO/WARNING/ERROR)

### 2. Database Configuration
- **Database Host**: PostgreSQL server location
- **Database Port**: Default 5432
- **Database Name**: Database name for the application
- **Database Credentials**: Username and password

### 3. Redis Configuration
- **Redis Host**: Redis server location
- **Redis Port**: Default 6379
- **Redis Password**: Optional authentication

### 4. n8n Integration
- **n8n Host URL**: Your n8n instance URL
- **n8n API Key**: API key for n8n integration
- **n8n Credentials**: Optional username/password for basic auth

### 5. External API Integration
- **OpenAI API Key**: For AI/ML features
- **Anthropic API Key**: For Claude integration
- **Google API Key**: For Google services

### 6. Monitoring Configuration
- **Prometheus**: Enable/disable metrics collection
- **Grafana**: Admin password for dashboard access

### 7. Security Settings
- **JWT Secret**: Auto-generated for token security
- **CORS Origins**: Allowed cross-origin domains
- **Allowed Hosts**: Permitted host headers

### 8. Email Configuration (Optional)
- **SMTP Settings**: For email notifications
- **Email Credentials**: SMTP authentication

### 9. Deployment Configuration
- **Domain Name**: Your production domain
- **SSL/HTTPS**: Enable secure connections
- **Traefik**: Reverse proxy configuration

## Generated Files

The setup process creates several important files:

### Configuration Files
- **`.env`**: Main environment configuration
- **`n8n-playground/.env`**: n8n-specific configuration
- **`docker-compose.override.yml`**: Docker deployment overrides

### Deployment Scripts
- **`deploy-configured.ps1`**: One-click deployment script
- **`backup-config.ps1`**: Configuration backup utility

## Advanced Usage

### Updating Configuration

To update your configuration:

1. Run the interactive setup again:
   ```powershell
   .\scripts\setup-interactive-config.ps1
   ```

2. Deploy the updated configuration:
   ```powershell
   .\scripts\deploy-with-config.ps1
   ```

### Backing Up Configuration

```powershell
# Create a timestamped backup of all configuration
.\backup-config.ps1
```

### Manual Configuration

You can also manually edit the generated `.env` files if needed:

- **Main configuration**: `.env`
- **n8n configuration**: `n8n-playground/.env`
- **Docker configuration**: `docker-compose.override.yml`

After manual changes, redeploy using:
```powershell
.\scripts\deploy-with-config.ps1
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```powershell
   # Check what's using the port
   netstat -ano | findstr :8000
   
   # Stop existing services
   docker-compose down
   ```

2. **Service Update Failed**
   ```powershell
   # Check service logs
   docker service logs unityai_unityai-app -f
   
   # Check service status
   docker service ps unityai_unityai-app
   ```

3. **Configuration Not Found**
   - Ensure you've run `setup-interactive-config.ps1` first
   - Check that `.env` file exists in the project root

### Checking Service Status

```powershell
# View all Docker services
docker service ls

# Check specific service status
docker service ps unityai_unityai-app

# View service logs
docker service logs unityai_unityai-app -f

# View container logs
docker-compose logs -f
```

### Resetting the Platform

To completely reset and redeploy:

```powershell
# Stop all services
docker-compose down

# Remove volumes (WARNING: This deletes all data)
docker-compose down -v

# Reconfigure
.\scripts\setup-interactive-config.ps1

# Redeploy
.\scripts\deploy-with-config.ps1
```

## Security Best Practices

1. **Keep Secrets Secure**
   - Never commit `.env` files to version control
   - Use strong, unique passwords
   - Regularly rotate API keys

2. **Network Security**
   - Configure proper CORS origins
   - Use HTTPS in production
   - Restrict allowed hosts

3. **Access Control**
   - Change default passwords
   - Use strong Grafana admin passwords
   - Secure your n8n instance

## Production Deployment

For production environments:

1. **Use a proper domain**:
   - Configure DNS to point to your server
   - Enable SSL/HTTPS
   - Use Traefik for reverse proxy

2. **Secure your database**:
   - Use strong database passwords
   - Configure database backups
   - Restrict database access

3. **Monitor your platform**:
   - Set up Grafana alerts
   - Monitor Prometheus metrics
   - Configure log aggregation

## Customer Deployment Guide

For customers deploying the platform:

1. **Prerequisites**:
   - Docker and Docker Compose installed
   - PowerShell (Windows) or Bash (Linux/Mac)
   - Network access to required services

2. **Deployment Steps**:
   ```powershell
   # 1. Clone or extract the UnityAI platform
   cd unityai-platform
   
   # 2. Run interactive setup
   .\scripts\setup-interactive-config.ps1
   
   # 3. Deploy the platform
   .\scripts\deploy-with-config.ps1
   
   # 4. Access your platform at the provided URLs
   ```

3. **Support**:
   - All configuration is externalized
   - Easy backup and restore
   - Comprehensive logging
   - Self-contained deployment

## License and Support

This interactive setup system is designed to make the UnityAI platform easily deployable and configurable for customers. All configuration is externalized, making it perfect for commercial deployment.

For support or questions, refer to the main UnityAI documentation or contact your platform provider.