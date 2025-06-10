# n8n Production Setup

This directory contains a complete production-ready n8n setup with security, monitoring, and scalability features.

## 🏗️ Architecture

- **n8n**: Workflow automation platform
- **PostgreSQL**: Primary database for n8n data
- **Redis**: Queue management and caching
- **Traefik**: Reverse proxy with automatic SSL
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## 📁 Directory Structure

```
n8n/
├── env/                    # Modular environment configurations
│   ├── .env               # Combined environment file
│   ├── .env.security      # Security settings
│   ├── .env.database      # Database configuration
│   ├── .env.deployment    # Deployment settings
│   ├── .env.endpoints     # API endpoints
│   ├── .env.fastapi       # FastAPI integration
│   ├── .env.nodes         # Node.js configuration
│   ├── .env.queue         # Redis queue settings
│   └── .env.taskrunners   # Task runner configuration
├── secrets/               # Docker secrets (passwords, keys)
├── monitoring/            # Prometheus configuration
├── docker-compose.yml     # Main orchestration file
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Domain names configured (n8n.unit-y-ai.io, etc.)
- SSL certificates (handled by Traefik + Let's Encrypt)

### 1. Environment Setup

The environment is already configured in `env/.env`. Review and modify as needed:

```bash
# Edit domain names and URLs
vim env/.env
```

### 2. Security Configuration

Secrets are stored in the `secrets/` directory. **Change default passwords**:

```bash
# Generate secure passwords
echo "$(openssl rand -base64 32)" > secrets/n8n_admin_password.txt
echo "$(openssl rand -base64 32)" > secrets/postgres_password.txt
echo "$(openssl rand -base64 32)" > secrets/redis_password.txt
echo "$(openssl rand -base64 32)" > secrets/grafana_admin_password.txt

# Generate encryption key (exactly 32 characters)
echo "$(openssl rand -hex 16)" > secrets/n8n_encryption_key.txt
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f n8n
```

### 4. Access Services

- **n8n UI**: https://n8n.unit-y-ai.io
- **Traefik Dashboard**: http://localhost:8080
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## 🔐 Security Features

### Authentication
- **HTTP Basic Auth** for n8n UI and API
- **JWT support** for external integrations
- **Docker Secrets** for password management

### Network Security
- **HTTPS/TLS** via Traefik + Let's Encrypt
- **CORS** restrictions to trusted domains
- **Internal Docker network** isolation

### Data Security
- **Encrypted credentials** in database
- **Secure password files** via Docker secrets
- **SSL/TLS** for all external communications

## 📊 Monitoring

### Metrics Collection
- **n8n metrics** exposed at `/metrics`
- **Prometheus** scraping configuration
- **Custom dashboards** in Grafana

### Health Checks
- All services have health check endpoints
- Automatic restart on failure
- Dependency management between services

## 🔧 Configuration

### Environment Variables

Key configuration options in `env/.env`:

```bash
# Security
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin

# Domain
N8N_HOST=n8n.unit-y-ai.io
N8N_PROTOCOL=https

# Database
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=postgres

# Queue
QUEUE_BULL_REDIS_HOST=redis

# Monitoring
N8N_METRICS=true
```

### Custom Nodes

Allowed external libraries in Function nodes:
- pdf-lib
- puppeteer
- pandas
- numpy
- scikit-learn

## 🚀 Production Deployment

### Docker Swarm

For production clusters, convert to Docker Swarm:

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml n8n-stack
```

### Scaling

```bash
# Scale n8n workers
docker-compose up -d --scale n8n=3

# Scale specific services
docker service scale n8n-stack_n8n=3
```

## 🔍 Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   docker-compose logs service-name
   ```

2. **Database connection issues**:
   ```bash
   docker-compose exec postgres pg_isready -U n8n_user
   ```

3. **Redis connection issues**:
   ```bash
   docker-compose exec redis redis-cli ping
   ```

4. **SSL certificate issues**:
   ```bash
   docker-compose logs traefik
   ```

### Health Checks

```bash
# Check all service health
docker-compose ps

# Manual health check
curl -f http://localhost:5678/healthz
```

## 📝 Maintenance

### Backups

```bash
# Database backup
docker-compose exec postgres pg_dump -U n8n_user n8n > backup.sql

# Volume backup
docker run --rm -v n8n_n8n_data:/data -v $(pwd):/backup alpine tar czf /backup/n8n_data.tar.gz /data
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d
```

## 🤝 Integration

### FastAPI Integration

The setup includes FastAPI integration variables:
- `N8N_API_URL`: n8n API endpoint
- `N8N_WEBHOOK_URL`: Webhook endpoint
- `REDIS_URL`: Shared Redis instance

### API Access

```bash
# Test n8n API
curl -u admin:password https://n8n.unit-y-ai.io/api/v1/workflows

# Test webhook
curl -X POST https://n8n.unit-y-ai.io/webhook/test
```

## 📚 Documentation

- [n8n Documentation](https://docs.n8n.io/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Prometheus Documentation](https://prometheus.io/docs/)

## 🆘 Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Review configuration files
3. Consult n8n community forums
4. Check GitHub issues