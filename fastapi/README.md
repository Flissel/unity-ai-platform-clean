# Unity AI FastAPI - AutoGen Core Integration

This FastAPI service provides intelligent decision-making capabilities using AutoGen Core 0.4.x for the Unity AI automation platform.

## 🤖 AutoGen Core Features

- **Intelligent Decision Making**: Uses GPT-4 to analyze incoming events and determine optimal workflows
- **Multi-Agent Architecture**: Separate agents for decision-making and topic analysis
- **Fallback Logic**: Graceful degradation to keyword-based decisions when AI is unavailable
- **Real-time Processing**: Async processing with Redis streams for high throughput
- **Monitoring**: Prometheus metrics and comprehensive logging

## 🚀 Quick Start

### 1. Environment Setup

Configure your `.env.fastapi` file:

```bash
# Enable AutoGen Core
AUTOGEN_ENABLED=true
AUTOGEN_MODEL=gpt-4

# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Redis for event streaming
REDIS_URL=redis://redis:6379

# n8n integration
N8N_API_URL=http://n8n:5678/api/v1
N8N_API_KEY=your_n8n_api_key
```

### 2. Docker Deployment

```bash
# Start the entire stack
docker compose up -d

# Check FastAPI logs
docker compose logs -f fastapi

# Scale workers if needed
docker compose up -d --scale n8n-worker=3
```

### 3. API Usage

#### Decision Endpoint

```bash
curl -X POST "http://localhost:8000/decide" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "web_chat",
    "event_type": "message",
    "user_id": "user123",
    "content": "I need help with my account",
    "metadata": {"channel": "support"}
  }'
```

**Response:**
```json
{
  "event_id": "evt_1234567890",
  "topic": "customer_support",
  "workflow_name": "customer_support_workflow",
  "workflow_id": "wf_abc123",
  "confidence": 0.92,
  "reasoning": "AI detected customer support request based on help-seeking language",
  "parameters": {
    "user_input": "I need help with my account",
    "priority": "normal",
    "source": "web_chat"
  }
}
```

## 🏗️ Architecture

### AutoGen Core Components

1. **DecisionAgent**: Main AI agent for workflow decisions
2. **TopicAnalyzer**: Specialized agent for content topic analysis
3. **AutoGenManager**: Runtime manager and coordinator
4. **Fallback Logic**: Keyword-based backup when AI is unavailable

### Event Flow

```
Webhook/API → FastAPI → AutoGen Core → Decision → n8n Workflow → Redis → Response
```

### Supported Workflows

- `customer_support` - Help requests, issues, complaints
- `data_analysis` - Analytics, reporting, data processing
- `content_generation` - Writing, creation, generation tasks
- `workflow_automation` - Process automation requests
- `system_monitoring` - Status checks, alerts, monitoring
- `general` - Fallback for unclear requests

## 🔧 Configuration

### AutoGen Settings

| Variable | Description | Default |
|----------|-------------|----------|
| `AUTOGEN_ENABLED` | Enable/disable AutoGen Core | `true` |
| `AUTOGEN_MODEL` | OpenAI model to use | `gpt-4` |
| `OPENAI_API_KEY` | OpenAI API key (required) | - |

### Performance Tuning

| Variable | Description | Default |
|----------|-------------|----------|
| `FASTAPI_WORKERS` | Number of FastAPI workers | `1` |
| `WORKER_CONCURRENCY` | Async task concurrency | `10` |
| `QUEUE_MAX_SIZE` | Redis queue size limit | `1000` |
| `WEBHOOK_TIMEOUT` | n8n webhook timeout (seconds) | `30` |

## 📊 Monitoring

### Health Checks

```bash
# FastAPI health
curl http://localhost:8000/health

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Key Metrics

- `fastapi_requests_total` - Total API requests
- `fastapi_request_duration_seconds` - Request latency
- `autogen_decisions_total` - AI decisions made
- `autogen_fallbacks_total` - Fallback decisions
- `workflow_executions_total` - n8n workflow triggers

### Logs

```bash
# View real-time logs
docker compose logs -f fastapi

# Search for AutoGen events
docker compose logs fastapi | grep "🤖"

# Check for errors
docker compose logs fastapi | grep "❌"
```

## 🔍 Troubleshooting

### Common Issues

#### 1. AutoGen Initialization Failed

```
⚠️ AutoGen Core initialization failed: Invalid API key
```

**Solution**: Check your `OPENAI_API_KEY` in `.env.fastapi`

#### 2. Fallback Mode Active

```
📝 Falling back to keyword-based decisions
```

**Causes**:
- Missing or invalid OpenAI API key
- OpenAI API rate limits
- Network connectivity issues

#### 3. Redis Connection Issues

```
❌ Redis connection failed
```

**Solution**: Ensure Redis service is running and accessible

### Debug Mode

Enable debug logging:

```bash
# In .env.fastapi
FASTAPI_DEBUG=true
LOG_LEVEL=DEBUG
```

## 🧪 Testing

### Unit Tests

```bash
# Run tests in container
docker compose exec fastapi python -m pytest tests/

# Test AutoGen integration
docker compose exec fastapi python -m pytest tests/test_autogen.py -v
```

### Load Testing

```bash
# Install dependencies
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

## 🔐 Security

### API Key Protection

- Store OpenAI API key in Docker secrets (production)
- Use environment-specific `.env` files
- Enable CORS restrictions
- Implement rate limiting

### Production Setup

```bash
# Create Docker secret for OpenAI API key
echo "your_openai_api_key" | docker secret create openai_api_key -

# Update docker-compose.yml
services:
  fastapi:
    secrets:
      - openai_api_key
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale FastAPI instances
docker compose up -d --scale fastapi=3

# Scale n8n workers
docker compose up -d --scale n8n-worker=5
```

### Performance Optimization

1. **Redis Clustering**: Use Redis Cluster for high availability
2. **Load Balancing**: Add Traefik load balancing for FastAPI
3. **Caching**: Implement decision caching for repeated requests
4. **Async Processing**: Use background tasks for heavy operations

## 🔄 Updates

### AutoGen Core Updates

```bash
# Update requirements.txt
autogen-core==0.4.1
autogen-ext[openai]==0.4.1

# Rebuild container
docker compose build fastapi
docker compose up -d fastapi
```

### Migration Guide

When updating AutoGen Core versions:

1. Check breaking changes in release notes
2. Update `requirements.txt`
3. Test in development environment
4. Update production with rolling deployment

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/unity-ai.git
cd unity-ai/fastapi

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run locally
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Code Style

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

## 📚 Resources

- [AutoGen Core Documentation](https://microsoft.github.io/autogen/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [n8n API Documentation](https://docs.n8n.io/api/)
- [Redis Streams Guide](https://redis.io/docs/data-types/streams/)

## 📄 License

MIT License - see LICENSE file for details.