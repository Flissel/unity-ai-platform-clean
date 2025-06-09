# UnityAI Application Stack Testing Guide

This guide provides comprehensive testing procedures for the complete UnityAI application stack, including all microservices and infrastructure components.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Testing](#quick-testing)
4. [Individual Service Testing](#individual-service-testing)
5. [Integration Testing](#integration-testing)
6. [Performance Testing](#performance-testing)
7. [Troubleshooting](#troubleshooting)
8. [Production Readiness](#production-readiness)

## 🎯 Overview

The UnityAI application stack consists of multiple microservices:

### Core Infrastructure
- **Traefik** - Reverse proxy and load balancer
- **PostgreSQL** - Primary database
- **Redis** - Caching and message queue

### Application Services
- **N8N** - Workflow automation platform
- **N8N Playground** - FastAPI integration service
- **Python Worker** - Background task processing
- **Main UnityAI App** - Primary application interface

### Monitoring & Observability
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards

## 🔧 Prerequisites

### System Requirements
- Windows 10/11 or Windows Server
- Docker Desktop or Docker Engine
- Docker Compose
- PowerShell 5.1 or later
- At least 8GB RAM
- 20GB free disk space

### Installation Check
```powershell
# Check Docker
docker --version
docker-compose --version

# Check PowerShell version
$PSVersionTable.PSVersion
```

## ⚡ Quick Testing

### 1. Complete Stack Test
Run the comprehensive test script to check all services:

```powershell
# Navigate to project root
cd c:\code\unityai

# Run complete stack test
.\test-complete-stack.ps1
```

This script will:
- ✅ Check prerequisites (Docker, Docker Compose)
- ✅ Verify configuration files
- ✅ Test all service ports
- ✅ Validate HTTP endpoints
- ✅ Provide detailed results and access URLs

### 2. Quick N8N Status Check
```powershell
# Quick N8N services check
cd c:\code\unityai\n8n
.\basic-test.ps1
```

## 🔍 Individual Service Testing

### N8N Services (Standalone)
```powershell
# Test each N8N service individually
cd c:\code\unityai\n8n
.\test-individual-services.ps1
```

This tests:
- PostgreSQL database connectivity
- Redis cache functionality
- N8N workflow engine
- Traefik reverse proxy
- Prometheus metrics
- Grafana dashboards

### N8N Playground (FastAPI)
```powershell
# Test N8N Playground API
cd c:\code\unityai\n8n-playground

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Test endpoints
Invoke-WebRequest -Uri "http://localhost:8000/health"
Invoke-WebRequest -Uri "http://localhost:8000/docs"
```

### Python Worker Service
```powershell
# Test Python worker
cd c:\code\unityai\python

# Build and run
docker build -t unityai-python .
docker run -d -p 8001:8000 --name test-python-worker unityai-python

# Test endpoints
Invoke-WebRequest -Uri "http://localhost:8001/health"
Invoke-WebRequest -Uri "http://localhost:8001/docs"

# Cleanup
docker stop test-python-worker
docker rm test-python-worker
```

### Main Application
```powershell
# Test main application
cd c:\code\unityai

# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Test main endpoints
Invoke-WebRequest -Uri "http://localhost"
Invoke-WebRequest -Uri "http://localhost/api/health"
```

## 🔗 Integration Testing

### End-to-End Workflow Test
```powershell
# 1. Start all services
docker-compose -f docker-compose.prod.yml up -d

# 2. Wait for services to be ready
Start-Sleep -Seconds 30

# 3. Test service communication
# N8N → PostgreSQL
Invoke-WebRequest -Uri "http://localhost:5678/healthz"

# N8N Playground → N8N API
Invoke-WebRequest -Uri "http://localhost:8000/api/workflows"

# Python Worker → Redis
Invoke-WebRequest -Uri "http://localhost:8001/tasks/status"
```

### API Integration Test
```powershell
# Test API endpoints integration
$headers = @{"Content-Type" = "application/json"}

# Test N8N Playground workflow execution
$body = @{
    workflow_id = "test-workflow"
    input_data = @{message = "Hello World"}
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/execute" -Method POST -Body $body -Headers $headers
```

## 📊 Performance Testing

### Load Testing
```powershell
# Install Apache Bench (if not available, use curl in loop)
# Test N8N endpoint
ab -n 100 -c 10 http://localhost:5678/

# Test N8N Playground API
ab -n 100 -c 10 http://localhost:8000/health

# Test Python Worker
ab -n 100 -c 10 http://localhost:8001/health
```

### Resource Monitoring
```powershell
# Monitor container resources
docker stats

# Check container logs
docker-compose logs -f

# Monitor specific service
docker-compose logs -f n8n
```

## 🐛 Troubleshooting

### Common Issues

#### Services Not Starting
```powershell
# Check container status
docker ps -a

# Check logs for errors
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]
```

#### Port Conflicts
```powershell
# Check what's using a port
netstat -ano | findstr :5678

# Kill process using port
Stop-Process -Id [PID] -Force
```

#### Database Connection Issues
```powershell
# Test PostgreSQL connection
docker exec -it unityai-postgres psql -U n8n_user -d n8n

# Test Redis connection
docker exec -it unityai-redis redis-cli ping
```

#### Memory Issues
```powershell
# Check Docker memory usage
docker system df

# Clean up unused resources
docker system prune -f
```

### Log Analysis
```powershell
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Filter logs by service
docker-compose logs n8n | Select-String "ERROR"
```

## ✅ Production Readiness

### Pre-Deployment Checklist

#### Security
- [ ] All default passwords changed
- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured
- [ ] Docker secrets properly set
- [ ] Environment variables secured

#### Performance
- [ ] Resource limits configured
- [ ] Health checks enabled
- [ ] Monitoring dashboards setup
- [ ] Log aggregation configured
- [ ] Backup procedures tested

#### Reliability
- [ ] Auto-restart policies enabled
- [ ] Data persistence configured
- [ ] Network isolation implemented
- [ ] Load balancing configured
- [ ] Failover procedures documented

### Production Testing Script
```powershell
# Run production readiness test
.\test-complete-stack.ps1

# Verify all services return HTTP 200
# Check response times < 2 seconds
# Verify monitoring endpoints accessible
# Test backup and restore procedures
```

### Monitoring Setup
```powershell
# Access monitoring dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Traefik: http://localhost:8080/dashboard/

# Import Grafana dashboards
# - Docker containers dashboard
# - N8N metrics dashboard
# - Application performance dashboard
```

## 📚 Additional Resources

### Documentation
- [N8N Documentation](https://docs.n8n.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)

### Testing Tools
- **PowerShell Scripts**: Located in project root and `n8n/` directory
- **Docker Health Checks**: Built into docker-compose configurations
- **Prometheus Metrics**: Available at `:9090/metrics`
- **Grafana Dashboards**: Available at `:3000`

### Support
- Check logs: `docker-compose logs [service]`
- Review configuration: Verify `.env` files and `docker-compose.yml`
- Community support: N8N community forums
- Documentation: Project README files

---

**Note**: Always test in a development environment before deploying to production. Ensure all security measures are in place and monitoring is configured before going live.