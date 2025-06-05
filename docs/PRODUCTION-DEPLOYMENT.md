# Unity AI Platform - Production Deployment Guide

🚀 **Complete production deployment guide for the Unity AI Domino-Automation Platform**

## 📋 Prerequisites

### Server Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Storage**: Minimum 100GB SSD
- **Network**: Public IP with domain name

### Required Accounts & Services
- **Domain**: Registered domain name
- **Cloudflare**: Account with DNS management
- **OpenAI**: API key for Autogen functionality
- **Server**: VPS/Dedicated server with root access

## 🔧 Quick Production Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/unity-ai-platform.git
cd unity-ai-platform
```

### 2. Run Production Setup Script
```bash
chmod +x scripts/setup-production.sh
./scripts/setup-production.sh
```

The script will prompt you for:
- Domain name (e.g., `unit-y-ai.io`)
- Cloudflare email and API token
- Database passwords (auto-generated if left empty)
- OpenAI API key
- Admin passwords for services

### 3. Configure DNS
Point your domain's DNS records to your server:
```
A     @                  YOUR_SERVER_IP
A     api                YOUR_SERVER_IP
A     n8n                YOUR_SERVER_IP
A     webhooks           YOUR_SERVER_IP
A     grafana            YOUR_SERVER_IP
A     traefik            YOUR_SERVER_IP
A     metrics            YOUR_SERVER_IP
```

### 4. Deploy Services
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🌐 Service URLs

After successful deployment, your services will be available at:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | `https://api.your-domain.io` | Main FastAPI application |
| **n8n** | `https://n8n.your-domain.io` | Workflow automation interface |
| **Webhooks** | `https://webhooks.your-domain.io` | Webhook endpoints |
| **Grafana** | `https://grafana.your-domain.io` | Monitoring dashboard |
| **Traefik** | `https://traefik.your-domain.io` | Reverse proxy dashboard |
| **Metrics** | `https://metrics.your-domain.io` | Prometheus metrics |

## 🔐 Security Features

### SSL/TLS Certificates
- **Automatic**: Let's Encrypt certificates via Traefik
- **Renewal**: Automatic certificate renewal
- **Security**: A+ SSL rating with security headers

### Authentication & Authorization
- **JWT**: Secure API authentication
- **Basic Auth**: Protected admin interfaces
- **API Keys**: Service-to-service authentication
- **Rate Limiting**: DDoS protection

### Network Security
- **Firewall**: UFW configured with minimal ports
- **Docker Networks**: Isolated container communication
- **Secrets Management**: Environment-based secrets

## 📊 Monitoring & Observability

### Metrics Collection
- **Prometheus**: Metrics aggregation
- **Grafana**: Visualization dashboards
- **Health Checks**: Automated service monitoring
- **Alerting**: Configurable alert rules

### Logging
- **Structured Logging**: JSON format logs
- **Log Rotation**: Automatic log management
- **Centralized**: Docker container logs

### Key Metrics Monitored
- API request rates and response times
- Database connection pools and query performance
- Redis cache hit rates and memory usage
- n8n workflow execution statistics
- System resources (CPU, memory, disk)

## 🔄 Backup & Recovery

### Automated Backups
- **Schedule**: Daily at 2 AM
- **Retention**: 7 days local, 30 days remote
- **Components**: Database, volumes, configurations

### Manual Backup
```bash
# Create immediate backup
./scripts/backup.sh

# List available backups
ls -la /opt/unityai/backups/
```

### Restore from Backup
```bash
# Restore from specific backup
./scripts/deploy-production.sh rollback BACKUP_TIMESTAMP

# Restore from latest backup
./scripts/deploy-production.sh rollback
```

## 🚀 Deployment Operations

### Deploy New Version
```bash
# Deploy with automatic backup and rollback on failure
./scripts/deploy-production.sh deploy
```

### Service Management
```bash
# Check service status
systemctl status unityai

# Start services
sudo systemctl start unityai

# Stop services
sudo systemctl stop unityai

# Restart services
sudo systemctl restart unityai
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f n8n
docker-compose -f docker-compose.prod.yml logs -f db
```

## 🔧 Configuration Management

### Environment Variables
Production configuration is stored in `.env.production`:

```bash
# Edit production configuration
vim .env.production

# Restart services after config changes
docker-compose -f docker-compose.prod.yml restart
```

### Key Configuration Files
- `.env.production` - Main environment configuration
- `traefik/traefik.yml` - Reverse proxy configuration
- `traefik/dynamic.yml` - Dynamic routing rules
- `redis.conf` - Redis server configuration
- `prometheus.yml` - Metrics collection configuration

## 🛠️ Troubleshooting

### Common Issues

#### SSL Certificate Issues
```bash
# Check certificate status
docker-compose -f docker-compose.prod.yml logs traefik | grep acme

# Force certificate renewal
docker-compose -f docker-compose.prod.yml restart traefik
```

#### Database Connection Issues
```bash
# Check database status
docker-compose -f docker-compose.prod.yml exec db pg_isready -U postgres

# View database logs
docker-compose -f docker-compose.prod.yml logs db
```

#### Service Health Checks
```bash
# Check all service health
curl -f https://api.your-domain.io/health
curl -f https://n8n.your-domain.io
curl -f https://grafana.your-domain.io/api/health
```

### Performance Tuning

#### Database Optimization
```bash
# Monitor database performance
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

#### Redis Optimization
```bash
# Monitor Redis performance
docker-compose -f docker-compose.prod.yml exec redis redis-cli info
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale n8n workers
docker-compose -f docker-compose.prod.yml up -d --scale n8n-worker=4

# Scale API workers (edit docker-compose.prod.yml)
# Increase 'replicas' under deploy section
```

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Adjust Docker resource limits
- Tune database connection pools

## 🔒 Security Hardening

### Additional Security Measures
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Setup SSH key authentication
# Disable password authentication in /etc/ssh/sshd_config
```

### Security Checklist
- [ ] SSH key authentication enabled
- [ ] Password authentication disabled
- [ ] Firewall configured (UFW)
- [ ] SSL certificates active
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Regular security updates
- [ ] Backup encryption enabled

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- **Weekly**: Review logs and metrics
- **Monthly**: Update Docker images
- **Quarterly**: Security audit and updates
- **Annually**: SSL certificate review

### Health Monitoring
```bash
# System health check
./scripts/health-check.sh

# Service status overview
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats
```

### Getting Help
- **Documentation**: Check project README and docs
- **Logs**: Always check service logs first
- **Monitoring**: Use Grafana dashboards for insights
- **Community**: GitHub issues and discussions

---

## 🎉 Congratulations!

Your Unity AI Platform is now running in production! 🚀

**Next Steps:**
1. Configure your first n8n workflows
2. Set up monitoring alerts
3. Test the API endpoints
4. Import workflow templates
5. Configure notification channels

**Remember:**
- Keep your credentials secure
- Monitor system resources
- Maintain regular backups
- Stay updated with security patches

For additional support and advanced configurations, refer to the detailed documentation in the `/docs` directory.