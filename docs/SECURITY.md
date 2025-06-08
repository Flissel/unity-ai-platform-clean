# Unity AI Platform - Security Documentation

## Overview

This document outlines the security architecture and best practices for the Unity AI Platform. The platform implements enterprise-grade security measures including Docker Swarm secrets management, API authentication, SSL/TLS encryption, and comprehensive monitoring.

## Security Architecture

### 1. Secrets Management

The platform uses **Docker Swarm Secrets** for secure credential management:

- **Encrypted at rest**: Secrets are encrypted using AES-256-GCM
- **Encrypted in transit**: TLS 1.2+ for all secret distribution
- **Access control**: Only authorized containers can access specific secrets
- **Audit logging**: All secret access is logged

#### Secret Types

| Secret Name | Purpose | Access |
|-------------|---------|--------|
| `postgres_password` | Database authentication | FastAPI, n8n |
| `redis_password` | Cache authentication | FastAPI, n8n |
| `secret_key` | JWT token signing | FastAPI |
| `api_keys` | API authentication | FastAPI |
| `n8n_api_key` | n8n integration | FastAPI |
| `n8n_admin_password` | n8n admin access | n8n |
| `n8n_encryption_key` | n8n data encryption | n8n |
| `openai_api_key` | OpenAI API access | FastAPI, n8n |
| `cloudflare_token` | DNS management | Traefik |
| `grafana_admin_password` | Monitoring access | Grafana |

### 2. Network Security

#### SSL/TLS Configuration

- **Automatic HTTPS**: Let's Encrypt certificates via Traefik
- **TLS 1.2+ only**: Older protocols disabled
- **HSTS enabled**: HTTP Strict Transport Security
- **Certificate rotation**: Automatic renewal every 60 days

#### Network Isolation

```yaml
# Docker networks provide isolation
networks:
  frontend:    # Public-facing services (Traefik)
  backend:     # Internal services (DB, Redis)
  monitoring:  # Monitoring stack (Grafana, Prometheus)
```

#### Firewall Rules

```bash
# Only allow necessary ports
80/tcp   - HTTP (redirects to HTTPS)
443/tcp  - HTTPS
22/tcp   - SSH (admin access only)
```

### 3. Application Security

#### Authentication & Authorization

- **JWT tokens**: Stateless authentication
- **API key validation**: Multiple authentication methods
- **Rate limiting**: Prevent abuse and DoS attacks
- **CORS protection**: Cross-origin request filtering

#### Input Validation

- **Pydantic models**: Automatic data validation
- **SQL injection prevention**: Parameterized queries
- **XSS protection**: Input sanitization
- **File upload restrictions**: Type and size limits

### 4. Database Security

#### PostgreSQL Hardening

- **Encrypted connections**: SSL/TLS required
- **User isolation**: Dedicated application user
- **Backup encryption**: AES-256 encrypted backups
- **Access logging**: All queries logged

#### Redis Security

- **Password authentication**: Required for all connections
- **Network isolation**: Backend network only
- **Memory encryption**: Sensitive data encrypted

## Security Setup Guide

### Prerequisites

1. **Docker Swarm**: Initialize swarm mode
2. **OpenSSL**: For secret generation
3. **Secure environment**: Isolated server/VPS

### Step 1: Initialize Docker Swarm

```bash
# Initialize swarm (if not already done)
docker swarm init

# Verify swarm status
docker info --format '{{.Swarm.LocalNodeState}}'
```

### Step 2: Configure Secrets

```bash
# 1. Update the secrets configuration
vim config/secrets.env

# 2. Run the secrets setup script
./scripts/setup-docker-secrets.sh

# 3. Verify secrets are created
docker secret ls

# 4. IMPORTANT: Delete the secrets file
rm config/secrets.env
```

### Step 3: Deploy with Security

```bash
# Deploy the production stack
./scripts/deploy-production.sh

# Verify all services are running
docker service ls

# Check service logs for security events
docker service logs unity-ai_fastapi
```

## Security Monitoring

### 1. Log Aggregation

All security events are logged and monitored:

- **Authentication attempts**: Success/failure tracking
- **API access**: Rate limiting violations
- **System events**: Container starts/stops
- **Error tracking**: Security-related errors

### 2. Metrics Collection

Prometheus collects security metrics:

- **Failed login attempts**: `auth_failures_total`
- **API rate limits**: `rate_limit_exceeded_total`
- **Certificate expiry**: `ssl_cert_expiry_days`
- **Service health**: `service_up`

### 3. Alerting Rules

```yaml
# Example Prometheus alerting rules
groups:
  - name: security
    rules:
      - alert: HighFailedLogins
        expr: rate(auth_failures_total[5m]) > 10
        for: 2m
        annotations:
          summary: "High number of failed login attempts"
      
      - alert: CertificateExpiry
        expr: ssl_cert_expiry_days < 30
        for: 1h
        annotations:
          summary: "SSL certificate expires in {{ $value }} days"
```

## Security Best Practices

### 1. Server Hardening

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Configure fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

### 2. Docker Security

```bash
# Run Docker daemon with security options
sudo dockerd \
  --userns-remap=default \
  --live-restore \
  --userland-proxy=false

# Use non-root users in containers
# (Already configured in Dockerfiles)
```

### 3. Secret Rotation

```bash
# Rotate secrets regularly (every 90 days)
./scripts/rotate-secrets.sh

# Update API keys
./scripts/update-api-keys.sh

# Regenerate certificates
docker service update --force unity-ai_traefik
```

### 4. Backup Security

```bash
# Encrypted database backups
./scripts/backup-database.sh --encrypt

# Secure backup storage
aws s3 cp backup.sql.gpg s3://unity-ai-backups/ --sse AES256
```

## Incident Response

### 1. Security Incident Detection

**Indicators of compromise:**
- Unusual API access patterns
- Failed authentication spikes
- Unexpected service restarts
- Certificate validation errors

### 2. Response Procedures

```bash
# 1. Isolate affected services
docker service scale unity-ai_fastapi=0

# 2. Collect logs
docker service logs unity-ai_fastapi > incident-logs.txt

# 3. Rotate compromised secrets
./scripts/emergency-secret-rotation.sh

# 4. Restore from clean backup
./scripts/restore-from-backup.sh --date=2024-01-15
```

### 3. Post-Incident Actions

1. **Root cause analysis**: Identify vulnerability
2. **Security patches**: Apply necessary updates
3. **Process improvements**: Update security procedures
4. **Documentation**: Record lessons learned

## Compliance & Auditing

### 1. Audit Logging

All security-relevant events are logged:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "authentication",
  "user_id": "user123",
  "ip_address": "192.168.1.100",
  "result": "success",
  "resource": "/api/v1/workflows"
}
```

### 2. Security Scanning

```bash
# Container vulnerability scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image unity-ai/fastapi:latest

# Dependency scanning
safety check -r requirements.txt

# Code security analysis
bandit -r fastapi/
```

### 3. Compliance Reports

- **Monthly security reports**: Automated generation
- **Vulnerability assessments**: Quarterly scans
- **Penetration testing**: Annual third-party testing
- **Compliance audits**: SOC 2 Type II ready

## Emergency Contacts

| Role | Contact | Availability |
|------|---------|-------------|
| Security Lead | security@unit-y-ai.io | 24/7 |
| DevOps Team | devops@unit-y-ai.io | Business hours |
| Incident Response | incident@unit-y-ai.io | 24/7 |

## Security Updates

This document is reviewed and updated:
- **Monthly**: Security procedures review
- **Quarterly**: Threat model updates
- **Annually**: Complete security audit

---

**Last Updated**: January 2024  
**Version**: 1.0  
**Next Review**: April 2024