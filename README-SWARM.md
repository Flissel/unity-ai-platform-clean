# UnityAI Docker Swarm Deployment Guide

This guide covers deploying UnityAI using Docker Swarm for production environments. Docker Swarm provides built-in orchestration, secrets management, and high availability.

## Prerequisites

- Docker Engine 20.10+ with Swarm mode enabled
- Domain name with DNS pointing to your server(s)
- Cloudflare account for DNS management and SSL certificates
- API keys for external services (OpenAI, etc.)

## Quick Start

1. **Initialize Docker Swarm** (if not already done):
   ```bash
   docker swarm init
   ```

2. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd unityai
   ```

3. **Create secrets**:
   ```bash
   chmod +x create-secrets.sh
   ./create-secrets.sh
   ```

4. **Deploy the stack**:
   ```bash
   chmod +x deploy-swarm.sh
   ./deploy-swarm.sh
   ```

## Detailed Setup

### 1. Environment Configuration

The `.env.production` file is pre-configured for Docker Swarm deployment with:
- Secret file references instead of hardcoded values
- Swarm-specific service configurations
- Proper network and volume settings

### 2. Secrets Management

Docker Swarm uses built-in secrets management for sensitive data:

#### Required Secrets:
- `pg_pw` - PostgreSQL password
- `redis_pw` - Redis password
- `n8n_admin_password` - N8N admin interface password
- `n8n_encryption_key` - N8N data encryption key
- `n8n_api_key` - N8N API access key
- `cloudflare_email` - Cloudflare account email
- `cloudflare_token` - Cloudflare API token
- `openai_api_key` - OpenAI API key
- `anthropic_api_key` - Anthropic API key (optional)
- `groq_api_key` - Groq API key (optional)
- `grafana_admin_password` - Grafana admin password
- `runner_token` - GitHub Actions runner token (optional)

#### Creating Secrets Manually:
```bash
# Example: Create a secret from a file
echo "your-secret-value" | docker secret create secret_name -

# Or from a file
docker secret create secret_name /path/to/secret/file
```

### 3. Network Configuration

The stack uses overlay networks for service communication:
- `unityai-network` - Internal service communication
- `traefik-public` - External traffic routing

### 4. Service Architecture

#### Core Services:
- **Traefik** - Reverse proxy and load balancer
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **N8N** - Workflow automation
- **FastAPI** - Main application backend
- **Frontend** - React/Next.js application

#### Monitoring (Optional):
- **Grafana** - Metrics visualization
- **Prometheus** - Metrics collection

#### CI/CD (Optional):
- **GitHub Actions Runner** - Self-hosted runner

### 5. Domain Configuration

The following subdomains are configured:
- `unit-y-ai.io` - Main application
- `api.unit-y-ai.io` - API backend
- `n8n.unit-y-ai.io` - N8N interface
- `webhooks.unit-y-ai.io` - Webhook endpoints
- `traefik.unit-y-ai.io` - Traefik dashboard
- `grafana.unit-y-ai.io` - Grafana dashboard

## Deployment Commands

### Deploy Stack
```bash
./deploy-swarm.sh
```

### Monitor Services
```bash
# List all services
docker stack services unityai

# Check service logs
docker service logs unityai_traefik
docker service logs unityai_n8n
docker service logs unityai_fastapi

# Scale a service
docker service scale unityai_fastapi=3
```

### Update Stack
```bash
# After making changes to docker-compose.swarm.yml
docker stack deploy -c docker-compose.swarm.yml unityai
```

### Remove Stack
```bash
docker stack rm unityai
```

## SSL/TLS Configuration

SSL certificates are automatically managed by Traefik using Let's Encrypt with Cloudflare DNS challenge:

1. Ensure your Cloudflare API token has DNS edit permissions
2. Certificates are automatically issued and renewed
3. All traffic is redirected to HTTPS

## High Availability Setup

### Multi-Node Swarm

1. **Add worker nodes**:
   ```bash
   # On manager node, get join token
   docker swarm join-token worker
   
   # On worker nodes, run the provided command
   docker swarm join --token <token> <manager-ip>:2377
   ```

2. **Label nodes for specific services**:
   ```bash
   # Label a node for PostgreSQL (for data persistence)
   docker node update --label-add postgres=true <node-id>
   
   # Label nodes for different roles
   docker node update --label-add role=database <node-id>
   docker node update --label-add role=application <node-id>
   ```

### Data Persistence

- PostgreSQL data is stored in named volumes
- Redis data can be persisted if needed
- Traefik ACME data is stored in volumes

## Monitoring and Logging

### Service Health
```bash
# Check service health
docker service ps unityai_fastapi

# View service details
docker service inspect unityai_fastapi
```

### Logs
```bash
# Follow logs for a service
docker service logs -f unityai_fastapi

# Get logs from specific time
docker service logs --since 1h unityai_traefik
```

### Grafana Dashboards
Access Grafana at `https://grafana.unit-y-ai.io` to view:
- System metrics
- Application performance
- Service health

## Troubleshooting

### Common Issues

1. **Services not starting**:
   ```bash
   docker service ps unityai_<service> --no-trunc
   ```

2. **Secret not found errors**:
   ```bash
   docker secret ls
   # Recreate missing secrets
   ```

3. **Network connectivity issues**:
   ```bash
   docker network ls
   docker network inspect unityai-network
   ```

4. **SSL certificate issues**:
   ```bash
   docker service logs unityai_traefik
   # Check Cloudflare API token permissions
   ```

### Service Recovery

```bash
# Force update a service (restart)
docker service update --force unityai_fastapi

# Rollback a service
docker service rollback unityai_fastapi
```

## Security Best Practices

1. **Secrets Management**:
   - Never commit secrets to version control
   - Use Docker secrets for all sensitive data
   - Rotate secrets regularly

2. **Network Security**:
   - Use overlay networks for service isolation
   - Limit external access to necessary ports only
   - Enable Traefik security headers

3. **Access Control**:
   - Use strong passwords for all services
   - Enable 2FA where possible
   - Regularly update service images

4. **Monitoring**:
   - Monitor service logs
   - Set up alerts for service failures
   - Track resource usage

## Backup and Recovery

### Database Backup
```bash
# PostgreSQL backup
docker exec $(docker ps -q -f name=unityai_postgres) pg_dump -U n8n_user n8n > backup.sql

# Restore
docker exec -i $(docker ps -q -f name=unityai_postgres) psql -U n8n_user n8n < backup.sql
```

### Secrets Backup
```bash
# Backup secrets (store securely)
mkdir -p backup/secrets
cp secrets/* backup/secrets/
```

## Scaling

### Horizontal Scaling
```bash
# Scale application services
docker service scale unityai_fastapi=3
docker service scale unityai_frontend=2

# Scale N8N for high availability
docker service scale unityai_n8n=2
```

### Resource Limits
Resource limits are defined in `docker-compose.swarm.yml`:
- CPU limits and reservations
- Memory limits and reservations
- Restart policies

## Support

For issues and questions:
1. Check service logs first
2. Review this documentation
3. Check Docker Swarm documentation
4. Open an issue in the repository

---

**Note**: This deployment is optimized for Docker Swarm. For single-server deployments, consider using the standard Docker Compose setup instead.