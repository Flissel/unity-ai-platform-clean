# n8n API Integration Guide

This guide explains how to use the n8n API integration in the UnityAI n8n Playground to execute and manage n8n workflows programmatically.

## Overview

The n8n integration provides a REST API interface to:
- List and manage n8n workflows
- Execute workflows with custom input data
- Monitor execution status and retrieve results
- Get workflow statistics and performance metrics
- Cancel running executions

## Setup

### 1. Environment Configuration

Add the following environment variables to your `.env` file:

```bash
# n8n API Configuration
N8N_API_BASE_URL=https://your-n8n-instance.com
N8N_API_KEY=your_n8n_api_key_here

# Optional settings
N8N_API_TIMEOUT=30
N8N_API_MAX_RETRIES=3
N8N_API_RETRY_DELAY=1.0
N8N_API_VERIFY_SSL=true
```

### 2. API Key Setup

To get your n8n API key:
1. Log into your n8n instance
2. Go to Settings → API
3. Generate a new API key
4. Copy the key to your `.env` file

## API Endpoints

All endpoints are available under `/workflow-automation/n8n/`:

### Health Check
```http
GET /workflow-automation/n8n/health
```
Check n8n API connectivity and health status.

### Workflow Management

#### List Workflows
```http
GET /workflow-automation/n8n/workflows?active_only=false&limit=100
```
List all available workflows with optional filtering.

#### Get Workflow Details
```http
GET /workflow-automation/n8n/workflows/{workflow_id}
```
Get detailed information about a specific workflow.

#### Get Workflow Statistics
```http
GET /workflow-automation/n8n/workflows/{workflow_id}/stats?days=30
```
Get execution statistics for a workflow over the specified period.

### Workflow Execution

#### Execute Workflow
```http
POST /workflow-automation/n8n/workflows/{workflow_id}/execute
```

Request body:
```json
{
  "workflow_id": "string",
  "input_data": {
    "key": "value"
  },
  "wait_for_completion": true,
  "timeout": 300,
  "metadata": {
    "source": "api_integration"
  }
}
```

#### Batch Execute Workflows
```http
POST /workflow-automation/n8n/workflows/batch-execute
```
Execute multiple workflows in a single request (max 10).

### Execution Management

#### Get Execution Status
```http
GET /workflow-automation/n8n/executions/{execution_id}
```
Get the status and results of a specific execution.

#### List Executions
```http
GET /workflow-automation/n8n/executions?workflow_id={workflow_id}&limit=50
```
List recent executions with optional workflow filtering.

#### Cancel Execution
```http
POST /workflow-automation/n8n/executions/{execution_id}/cancel
```
Cancel a running execution.

## Usage Examples

### Python Client Example

```python
import asyncio
import httpx

class N8nApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/workflow-automation/n8n"
    
    async def execute_workflow(self, workflow_id: str, input_data: dict = None):
        payload = {
            "workflow_id": workflow_id,
            "input_data": input_data or {},
            "wait_for_completion": True,
            "timeout": 300
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/workflows/{workflow_id}/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()

# Usage
async def main():
    client = N8nApiClient()
    
    # Execute a workflow
    result = await client.execute_workflow(
        workflow_id="your-workflow-id",
        input_data={"message": "Hello from API!"}
    )
    
    print(f"Execution completed: {result['status']}")
    print(f"Result: {result['result_data']}")

asyncio.run(main())
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

class N8nApiClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.apiBase = `${baseUrl}/workflow-automation/n8n`;
    }
    
    async executeWorkflow(workflowId, inputData = {}) {
        const payload = {
            workflow_id: workflowId,
            input_data: inputData,
            wait_for_completion: true,
            timeout: 300
        };
        
        try {
            const response = await axios.post(
                `${this.apiBase}/workflows/${workflowId}/execute`,
                payload
            );
            return response.data;
        } catch (error) {
            throw new Error(`Execution failed: ${error.response?.data?.detail || error.message}`);
        }
    }
    
    async listWorkflows(activeOnly = false) {
        try {
            const response = await axios.get(`${this.apiBase}/workflows`, {
                params: { active_only: activeOnly }
            });
            return response.data;
        } catch (error) {
            throw new Error(`Failed to list workflows: ${error.response?.data?.detail || error.message}`);
        }
    }
}

// Usage
async function main() {
    const client = new N8nApiClient();
    
    try {
        // List workflows
        const workflows = await client.listWorkflows(true);
        console.log(`Found ${workflows.length} active workflows`);
        
        if (workflows.length > 0) {
            // Execute the first workflow
            const result = await client.executeWorkflow(
                workflows[0].id,
                { message: 'Hello from Node.js!' }
            );
            
            console.log('Execution completed:', result.status);
            console.log('Result:', result.result_data);
        }
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

### cURL Examples

#### List Workflows
```bash
curl -X GET "http://localhost:8000/workflow-automation/n8n/workflows?active_only=true" \
  -H "Content-Type: application/json"
```

#### Execute Workflow
```bash
curl -X POST "http://localhost:8000/workflow-automation/n8n/workflows/your-workflow-id/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "your-workflow-id",
    "input_data": {
      "message": "Hello from cURL!",
      "timestamp": "2024-01-01T00:00:00Z"
    },
    "wait_for_completion": true,
    "timeout": 300
  }'
```

#### Get Execution Status
```bash
curl -X GET "http://localhost:8000/workflow-automation/n8n/executions/execution-id" \
  -H "Content-Type: application/json"
```

## Response Models

### Workflow Information
```json
{
  "id": "workflow-id",
  "name": "My Workflow",
  "active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "tags": ["automation", "api"],
  "nodes": [...],
  "connections": {...}
}
```

### Execution Response
```json
{
  "execution_id": "execution-id",
  "workflow_id": "workflow-id",
  "status": "success",
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:00:00Z",
  "duration": 5.23,
  "result_data": {
    "output": "Workflow completed successfully"
  },
  "error_message": null,
  "metadata": {
    "source": "api_integration"
  }
}
```

### Workflow Statistics
```json
{
  "workflow_id": "workflow-id",
  "period_days": 30,
  "total_executions": 150,
  "successful_executions": 145,
  "failed_executions": 5,
  "success_rate_percent": 96.67,
  "average_duration_seconds": 4.52,
  "analysis_timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found (workflow/execution not found)
- `408` - Request Timeout (execution timeout)
- `422` - Validation Error
- `500` - Internal Server Error

Error responses include detailed information:
```json
{
  "error": "Workflow not found",
  "status_code": 404,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Best Practices

### 1. Timeout Management
- Set appropriate timeouts based on your workflow complexity
- Use `wait_for_completion: false` for long-running workflows
- Poll execution status for async workflows

### 2. Error Handling
- Always handle HTTP exceptions in your client code
- Check execution status before processing results
- Implement retry logic for transient failures

### 3. Input Data Validation
- Validate input data before sending to workflows
- Use consistent data formats across executions
- Include metadata for tracking and debugging

### 4. Monitoring
- Use workflow statistics to monitor performance
- Set up alerts for high failure rates
- Track execution duration trends

### 5. Security
- Keep API keys secure and rotate regularly
- Use HTTPS in production environments
- Validate SSL certificates (`N8N_API_VERIFY_SSL=true`)

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if n8n instance is running
   - Verify `N8N_API_BASE_URL` is correct
   - Ensure network connectivity

2. **Authentication Failed**
   - Verify `N8N_API_KEY` is correct
   - Check if API key has necessary permissions
   - Ensure API is enabled in n8n settings

3. **Workflow Not Found**
   - Verify workflow ID is correct
   - Check if workflow exists and is accessible
   - Ensure workflow is not deleted

4. **Execution Timeout**
   - Increase timeout value for complex workflows
   - Use async execution for long-running processes
   - Check workflow performance and optimize if needed

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will provide detailed information about API requests and responses.

## Integration Examples

See the `examples/n8n_integration_example.py` file for a comprehensive demonstration of all features.

To run the example:
```bash
cd examples
python n8n_integration_example.py
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the API documentation
3. Check n8n logs for workflow-specific issues
4. Contact the UnityAI team for integration support