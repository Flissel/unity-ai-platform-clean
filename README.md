# 🤖 Unity AI Platform

**Event-Driven Multi-Agent Automation Platform**

[![Build Status](https://github.com/your-org/unity-ai-platform/workflows/CI/badge.svg)](https://github.com/your-org/unity-ai-platform/actions)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/your-org/unity-ai)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

> **Intelligent automation platform combining AutoGen multi-agent systems, n8n workflow orchestration, and FastAPI for seamless event-driven processing.**

## 🎯 Overview

Unity AI Platform is a comprehensive automation solution that processes events through an intelligent pipeline:

```
📥 Webhook/Chat → 🤖 AutoGen Planning → ⚡ FastAPI Orchestration → 🔄 n8n Execution → 📊 Redis Streaming → 📤 Response
```

### Key Features

- 🤖 **Multi-Agent Intelligence** - AutoGen-powered planning and decision making
- 🔄 **Workflow Automation** - n8n-based execution engine
- ⚡ **High-Performance API** - FastAPI with async processing
- 🔒 **Secure Execution** - Sandboxed code execution environment
- 📊 **Real-time Monitoring** - Prometheus + Grafana observability
- 🛡️ **Enterprise Security** - JWT authentication, rate limiting, SSL/TLS
- 🚀 **Production Ready** - Docker Compose, CI/CD, automated deployments

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (v2.0+)
- **Python 3.11+** (for local development)
- **Git** (for version control)
- **Domain name** (for production deployment)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/unity-ai-platform.git
cd unity-ai-platform
```

### 2. Development Setup

```bash
# Copy development configuration
cp config/.env.development .env

# Start development environment
docker-compose up -d

# Verify services
curl http://localhost:8000/health
```

### 3. Production Deployment

```bash
# Run automated production setup
chmod +x scripts/setup-production.sh
./scripts/setup-production.sh

# Deploy services
docker-compose -f docker-compose.prod.yml up -d
```

## 📋 Service Architecture

| Service | Port | Description | URL |
|---------|------|-------------|-----|
| **FastAPI** | 8000 | Main API application | `http://localhost:8000` |
| **n8n Editor** | 5678 | Workflow designer | `http://localhost:5678` |
| **PostgreSQL** | 5432 | Primary database | Internal |
| **Redis** | 6379 | Cache & message broker | Internal |
| **Prometheus** | 9090 | Metrics collection | `http://localhost:9090` |
| **Grafana** | 3000 | Monitoring dashboards | `http://localhost:3000` |
| **Traefik** | 80/443 | Reverse proxy (prod) | `https://your-domain.io` |

## 🔧 Configuration

### Environment Files

- **Development**: `config/.env.development`
- **Production**: `config/.env.production` (auto-generated)
- **Template**: `config/.env.example`

### Key Configuration Options

```bash
# Application
APP_NAME=UnityAI
ENVIRONMENT=development
DEBUG=true

# Security
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key

# Services
N8N_API_KEY=your-n8n-api-key
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/db
```

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI development server
cd fastapi
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# Code formatting
black src/
isort src/
```

### API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Key API Endpoints

```bash
# Health check
GET /health

# AutoGen chat
POST /api/v1/autogen/chat

# Execute workflow
POST /api/v1/workflows/execute

# Webhook handler
POST /api/v1/webhooks/{webhook_id}

# Code execution
POST /api/v1/code/execute
```

## 📊 Monitoring

### Grafana Dashboards

- **Unity AI Overview** - System health and performance
- **API Metrics** - Request rates, response times, errors
- **Database Metrics** - Connection pools, query performance
- **Redis Metrics** - Cache hit rates, memory usage

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health

# Detailed health status
curl http://localhost:8000/health/detailed

# Service-specific checks
curl http://localhost:8000/health/database
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/n8n
```

## 🔒 Security

### Authentication

- **JWT Tokens** for API access
- **API Keys** for service-to-service communication
- **Basic Auth** for admin interfaces

### Security Features

- Rate limiting and DDoS protection
- CORS configuration
- Security headers (HSTS, CSP, etc.)
- Input validation and sanitization
- Secure code execution sandboxing

## 🚀 Production Deployment

### Automated Setup

```bash
# Complete production setup
./scripts/setup-production.sh
```

The script will:
1. Collect configuration (domain, API keys, passwords)
2. Install system dependencies
3. Configure firewall and security
4. Set up SSL certificates
5. Deploy all services
6. Configure monitoring and backups

### Manual Deployment

```bash
# Configure environment
cp config/.env.production .env
vim .env  # Edit configuration

# Deploy services
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
./scripts/deploy-production.sh health-check
```

### SSL/TLS Configuration

- **Automatic**: Let's Encrypt via Traefik
- **DNS Challenge**: Cloudflare API integration
- **Security**: A+ SSL rating with security headers

## 📁 Project Structure

```
unity-ai-platform/
├── 📁 config/              # Environment configurations
├── 📁 docs/                # Documentation
├── 📁 scripts/             # Automation scripts
├── 📁 src/                 # Source code
│   ├── 📁 api/             # FastAPI application
│   ├── 📁 core/            # Core utilities
│   └── 📁 services/        # Business logic
├── 📁 tests/               # Test suite
├── 📁 grafana/             # Monitoring dashboards
├── 📁 traefik/             # Reverse proxy config
├── 📁 .github/             # CI/CD workflows
├── 🐳 docker-compose.yml   # Development environment
├── 🐳 docker-compose.prod.yml # Production environment
└── 📄 README.md            # This file
```

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_api/test_health.py -v

# Integration tests
pytest tests/integration/ -v
```

### Test Categories

- **Unit Tests** - Individual component testing
- **Integration Tests** - Service interaction testing
- **API Tests** - Endpoint functionality testing
- **End-to-End Tests** - Complete workflow testing

## 📚 Documentation

- **[Production Deployment](docs/PRODUCTION-DEPLOYMENT.md)** - Complete deployment guide
- **[Configuration Template](docs/CONFIGURATION-TEMPLATE.md)** - Configuration options
- **[Project Overview](docs/PROJECT-OVERVIEW.md)** - Architecture and design
- **[API Reference](docs/API-REFERENCE.md)** - Complete API documentation
- **[Development Setup](docs/DEVELOPMENT-SETUP.md)** - Local development guide

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` directory
- **Issues**: [GitHub Issues](https://github.com/your-org/unity-ai-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/unity-ai-platform/discussions)
- **Email**: support@your-domain.io

## 🎉 Acknowledgments

- **AutoGen** - Microsoft's multi-agent framework
- **n8n** - Workflow automation platform
- **FastAPI** - Modern Python web framework
- **Traefik** - Cloud-native reverse proxy
- **Grafana** - Observability platform

---

**Made with ❤️ by the Unity AI Team**

*Transform your automation workflows with intelligent multi-agent processing.*