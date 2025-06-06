# Unity AI Platform

🚀 **Production-ready AI automation platform** combining n8n workflows with FastAPI backend and intelligent code execution capabilities.

## 📁 Project Structure

```
/opt/unity/
├── compose/                       # Docker Compose configurations
│   ├── docker-compose.yml         # Main development/production stack
│   └── docker-compose.prod.yml    # Production-specific overrides
├── n8n/                          # n8n workflow automation
│   ├── env/                      # Configuration files (no secrets!)
│   │   ├── .env.common           # Shared n8n configuration
│   │   ├── .env.queue            # Queue/Redis configuration
│   │   ├── .env.database         # Database configuration
│   │   ├── .env.nodes            # Node-specific settings
│   │   ├── .env.taskrunners      # Task runner configuration
│   │   ├── .env.security         # Security settings
│   │   ├── .env.timezone         # Timezone configuration
│   │   └── .env.binarydata       # Binary data handling
│   └── Dockerfile                # Custom n8n image (pandas, ML libs)
├── fastapi/                      # FastAPI backend application
│   ├── app.py                    # Main application entry point
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # FastAPI container image
├── traefik/                      # Reverse proxy & SSL termination
│   ├── traefik.yml              # Static configuration
│   ├── dynamic.yml              # Security headers, rate limits
│   └── acme.json                # Let's Encrypt certificates (chmod 600)
├── scripts/                      # Deployment & management scripts
│   ├── export-dev.sh            # Export development configuration
│   ├── import-prod.sh           # Import to production environment
│   ├── setup-server.sh          # Server initialization
│   ├── setup-production.sh      # Production deployment
│   └── deploy-production.sh     # Production update script
├── logs/                         # Application logs (host-bind)
├── uploads/                      # File uploads (host-bind)
├── docs/                         # Documentation
├── tests/                        # Test suites
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- OpenAI API Key
- Domain with Cloudflare DNS (for production)

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd unity-ai-platform
   ```

2. **Configure environment:**
   ```bash
   # Copy template and edit with your values
   cp .env.local.template .env.local
   
   # Set required API keys
   export OPENAI_API_KEY="sk-your-openai-key"
   export N8N_API_KEY="your-n8n-api-key"
   export N8N_ENCRYPTION_KEY="$(openssl rand -hex 32)"
   ```

3. **Start development stack:**
   ```bash
   cd compose
   docker-compose up -d
   ```

4. **Access services:**
   - **n8n Workflows:** http://localhost:5678
   - **FastAPI Docs:** http://localhost:8000/docs
   - **API Health:** http://localhost:8000/health

### Production Deployment

1. **Server preparation:**
   ```bash
   ./scripts/setup-server.sh
   ```

2. **Configure secrets:**
   ```bash
   # Create Docker secrets
   echo "your-postgres-password" | docker secret create pg_pw -
   echo "your-n8n-admin-password" | docker secret create n8n_admin_password -
   echo "$(openssl rand -hex 32)" | docker secret create n8n_encryption_key -
   echo "your-redis-password" | docker secret create redis_pw -
   echo "$(openssl rand -hex 32)" | docker secret create runner_token -
   ```

3. **Deploy production stack:**
   ```bash
   ./scripts/deploy-production.sh
   ```

## 🔧 Configuration

### Environment Files

Configuration is split across multiple files in `n8n/env/`:

- **`.env.common`** - Basic n8n settings, database connection
- **`.env.queue`** - Redis queue configuration
- **`.env.database`** - PostgreSQL settings
- **`.env.nodes`** - Node execution settings
- **`.env.security`** - Security and authentication
- **`.env.taskrunners`** - External task runner config
- **`.env.timezone`** - Timezone settings
- **`.env.binarydata`** - File handling configuration

### Secrets Management

Production uses Docker Secrets for sensitive data:

- `pg_pw` - PostgreSQL password
- `n8n_admin_password` - n8n admin password
- `n8n_encryption_key` - n8n encryption key
- `redis_pw` - Redis password
- `runner_token` - Task runner authentication

## 🔄 GitOps Workflow

### Export Development Configuration

```bash
./scripts/export-dev.sh
```

Exports:
- All n8n workflows
- Credential metadata (no secrets)
- Environment configuration
- Recent execution history

### Import to Production

```bash
./scripts/import-prod.sh ./exports/20241201_143000
```

Imports configuration with automatic backup of existing setup.

## 🏗️ Architecture

### Services

- **Traefik** - Reverse proxy, SSL termination, load balancing
- **PostgreSQL** - Primary database for n8n and FastAPI
- **Redis** - Queue management and caching
- **n8n** - Workflow automation engine
- **n8n-runner** - External task execution
- **FastAPI** - REST API backend with AI integration

### Key Features

- 🔐 **Security-first** - Docker secrets, rate limiting, CORS protection
- 🚀 **Scalable** - Docker Swarm ready, horizontal scaling
- 📊 **Observable** - Comprehensive logging, health checks, metrics
- 🔄 **GitOps** - Configuration export/import, version control
- 🤖 **AI-powered** - OpenAI integration, AutoGen support
- 📁 **File handling** - Secure upload/download with validation

## 🛠️ Development

### Local Development

```bash
# Start only required services
docker-compose up postgres redis -d

# Run FastAPI locally
cd fastapi
python -m uvicorn app:app --reload

# Run n8n locally
n8n start
```

### Testing

```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=src

# Integration tests
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Pre-commit hooks
pre-commit run --all-files
```

## 📚 API Documentation

- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

### Key Endpoints

- `GET /health` - Health check
- `POST /api/v1/workflows/execute` - Execute n8n workflow
- `POST /api/v1/code/execute` - Execute Python code
- `POST /api/v1/files/upload` - Upload files
- `GET /api/v1/files/{file_id}` - Download files

## 🔍 Monitoring

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health

# Check n8n
curl http://localhost:5678/healthz

# Check database
docker exec -it postgres pg_isready
```

### Logs

```bash
# View all logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f app
docker-compose logs -f n8n

# Application logs
tail -f logs/unityai.log
```

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check port usage
   netstat -tulpn | grep :8000
   
   # Stop conflicting services
   docker-compose down
   ```

2. **Permission issues:**
   ```bash
   # Fix log directory permissions
   sudo chown -R $USER:$USER logs/
   
   # Fix upload directory permissions
   sudo chown -R $USER:$USER uploads/
   ```

3. **Database connection:**
   ```bash
   # Reset database
   docker-compose down -v
   docker-compose up -d
   ```

### Support

- 📖 **Documentation:** `/docs` directory
- 🐛 **Issues:** GitHub Issues
- 💬 **Discussions:** GitHub Discussions

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

**Unity AI Platform** - Empowering automation with intelligent workflows 🚀