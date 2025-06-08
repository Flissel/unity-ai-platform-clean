# UnityAI Python Worker Service

A dedicated Python worker service for executing various computational tasks within the UnityAI platform.

## Overview

The Python Worker Service provides a scalable and isolated environment for running Python-based tasks including:

- **Data Processing**: Statistical analysis, data transformation, and aggregation
- **Machine Learning**: Text analysis, sentiment analysis, classification, and entity extraction
- **Web Scraping**: Content extraction from websites with customizable selectors
- **Document Processing**: Text extraction and analysis from various document formats
- **Image Processing**: Basic image manipulation and analysis
- **Custom Scripts**: Execution of user-defined Python scripts

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main App      │───▶│  Python Worker  │───▶│   Task Queue    │
│   (FastAPI)     │    │   (FastAPI)     │    │    (Redis)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Scripts &     │
                       │   Libraries     │
                       └─────────────────┘
```

## API Endpoints

### Health Check
```http
GET /health
```
Returns the service health status.

### Execute Task
```http
POST /execute
```
Execute a task with specified parameters.

**Request Body:**
```json
{
  "task_type": "data_processing|ml_inference|web_scraping|document_processing|image_processing|custom_script",
  "parameters": {
    // Task-specific parameters
  }
}
```

### Get Task Status
```http
GET /task/{task_id}
```
Retrieve the status and result of a specific task.

## Task Types

### 1. Data Processing

**Task Type:** `data_processing`

**Parameters:**
- `operation`: Operation to perform (`sum`, `average`, `count`, `statistics`, `correlation`)
- `data`: Array of numeric data or objects

**Example:**
```json
{
  "task_type": "data_processing",
  "parameters": {
    "operation": "statistics",
    "data": [
      {"value": 10, "category": "A"},
      {"value": 20, "category": "B"},
      {"value": 15, "category": "A"}
    ]
  }
}
```

### 2. Machine Learning Inference

**Task Type:** `ml_inference`

**Parameters:**
- `model_type`: Type of model (`sentiment`, `classification`, `entity_extraction`)
- `input_data`: Text or array of texts to analyze
- `categories`: (Optional) Custom categories for classification

**Example:**
```json
{
  "task_type": "ml_inference",
  "parameters": {
    "model_type": "sentiment",
    "input_data": "This product is absolutely amazing!"
  }
}
```

### 3. Web Scraping

**Task Type:** `web_scraping`

**Parameters:**
- `url`: Target URL to scrape
- `selector`: (Optional) CSS selector for specific elements
- `headers`: (Optional) Custom HTTP headers

**Example:**
```json
{
  "task_type": "web_scraping",
  "parameters": {
    "url": "https://example.com",
    "selector": "h1, h2, p"
  }
}
```

### 4. Document Processing

**Task Type:** `document_processing`

**Parameters:**
- `document_type`: Type of document (`pdf`, `docx`, `txt`)
- `content`: Document content or file path
- `operation`: Processing operation (`extract_text`, `analyze`, `summarize`)

### 5. Image Processing

**Task Type:** `image_processing`

**Parameters:**
- `image_path`: Path to the image file
- `operation`: Processing operation (`resize`, `crop`, `filter`, `analyze`)
- `options`: Operation-specific options

### 6. Custom Script

**Task Type:** `custom_script`

**Parameters:**
- `script`: Python script content or script name from `/app/scripts/`
- `args`: (Optional) Arguments to pass to the script

**Example:**
```json
{
  "task_type": "custom_script",
  "parameters": {
    "script": "data_analysis.py",
    "args": {
      "data": [{"x": 1, "y": 2}, {"x": 3, "y": 4}],
      "operation": "correlation"
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `N8N_WEBHOOK_URL` | n8n webhook base URL | Required |
| `FASTAPI_URL` | Main FastAPI service URL | Required |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (json/console) | `json` |
| `MAX_TASK_TIMEOUT` | Maximum task execution timeout (seconds) | `300` |
| `MAX_CONCURRENT_TASKS` | Maximum concurrent tasks | `10` |
| `CLEANUP_INTERVAL` | Task cleanup interval (seconds) | `3600` |

## Scripts Directory

The `/app/scripts/` directory contains pre-built Python scripts that can be executed via the `custom_script` task type:

- **`data_analysis.py`**: Advanced data analysis using pandas and numpy
- **`web_scraper.py`**: Web scraping with BeautifulSoup and requests
- **`ml_inference.py`**: Machine learning inference with various models

## Development

### Local Development

1. **Install Dependencies:**
   ```bash
   cd python
   pip install -r requirements.txt
   ```

2. **Set Environment Variables:**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost:5432/db"
   export REDIS_URL="redis://localhost:6379"
   export N8N_WEBHOOK_URL="http://localhost:5678"
   export FASTAPI_URL="http://localhost:8000"
   ```

3. **Run the Service:**
   ```bash
   python -m src.main
   ```

### Docker Development

```bash
# Build the image
docker build -t unityai-python .

# Run the container
docker run -p 8001:8001 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e REDIS_URL="redis://host:6379" \
  unityai-python
```

## Health Monitoring

The service includes comprehensive health checks:

- **HTTP Health Endpoint**: `GET /health`
- **Docker Health Check**: Built-in container health monitoring
- **Structured Logging**: JSON-formatted logs for monitoring systems
- **Metrics**: Task execution metrics and performance data

## Security

- **Non-root User**: Runs as `appuser` (UID 1000)
- **Input Validation**: All task parameters are validated
- **Timeout Protection**: Tasks have configurable execution timeouts
- **Resource Limits**: Memory and CPU limits can be set via Docker
- **Sandboxed Execution**: Custom scripts run in controlled environment

## Scaling

The Python Worker Service is designed for horizontal scaling:

- **Stateless Design**: No persistent state in the service
- **Redis Queue**: Shared task queue for multiple workers
- **Load Balancing**: Can run multiple instances behind a load balancer
- **Resource Isolation**: Each worker runs in its own container

## Troubleshooting

### Common Issues

1. **Task Timeout**: Increase `MAX_TASK_TIMEOUT` for long-running tasks
2. **Memory Issues**: Adjust Docker memory limits for data-intensive tasks
3. **Script Errors**: Check logs for detailed error messages
4. **Connection Issues**: Verify database and Redis connectivity

### Logs

Logs are structured and include:
- Task execution details
- Performance metrics
- Error traces
- Service health information

```bash
# View logs in Docker
docker logs unityai-python-worker

# Follow logs
docker logs -f unityai-python-worker
```

## Contributing

To add new task types or scripts:

1. Add the task handler in `src/services.py`
2. Update the configuration in `src/config.py`
3. Add validation in `src/utils.py`
4. Create example scripts in `scripts/`
5. Update this documentation

## License

This service is part of the UnityAI platform and follows the same licensing terms.