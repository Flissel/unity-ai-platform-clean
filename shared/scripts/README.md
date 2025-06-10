# Shared Python Scripts for n8n Integration

This directory contains Python scripts that can be executed directly from n8n workflows using the "Execute Command" or "Code" nodes.

## Directory Structure

```
shared/
├── scripts/
│   ├── data_processing/
│   │   ├── requirements.txt
│   │   ├── analyze_data.py
│   │   ├── transform_data.py
│   │   └── export_data.py
│   ├── web_scraping/
│   │   ├── requirements.txt
│   │   ├── scrape_website.py
│   │   ├── extract_content.py
│   │   └── monitor_changes.py
│   ├── ml_inference/
│   │   ├── requirements.txt
│   │   ├── sentiment_analysis.py
│   │   ├── text_classification.py
│   │   └── entity_extraction.py
│   ├── document_processing/
│   │   ├── requirements.txt
│   │   ├── pdf_extractor.py
│   │   ├── docx_processor.py
│   │   └── text_analyzer.py
│   └── utilities/
│       ├── requirements.txt
│       ├── file_operations.py
│       ├── api_helpers.py
│       └── data_validators.py
└── libs/
    ├── common.py
    ├── config.py
    └── logger.py
```

## Usage in n8n

### Method 1: Execute Command Node

```json
{
  "command": "python3",
  "arguments": [
    "/shared/scripts/data_processing/analyze_data.py",
    "--input", "{{$json.data}}",
    "--operation", "summary"
  ]
}
```

### Method 2: Code Node (Python)

```python
# Import shared libraries
import sys
sys.path.append('/shared/libs')
from common import process_data

# Your script logic here
result = process_data(items[0]['json'])
return [{'json': result}]
```

### Method 3: HTTP Request to Python Worker

```json
{
  "method": "POST",
  "url": "http://python-worker:8001/execute",
  "body": {
    "script_path": "/shared/scripts/data_processing/analyze_data.py",
    "parameters": "{{$json}}"
  }
}
```

## Script Standards

### Input/Output Format

All scripts should:
1. Accept JSON input via command line arguments or stdin
2. Output JSON results to stdout
3. Use stderr for error messages and logs
4. Exit with code 0 for success, non-zero for errors

### Example Script Template

```python
#!/usr/bin/env python3
import json
import sys
import argparse
from pathlib import Path

# Add shared libs to path
sys.path.append(str(Path(__file__).parent.parent / 'libs'))
from common import setup_logging, handle_errors
from config import get_config

def main():
    parser = argparse.ArgumentParser(description='Script description')
    parser.add_argument('--input', required=True, help='JSON input data')
    parser.add_argument('--operation', default='default', help='Operation type')
    args = parser.parse_args()
    
    try:
        # Parse input
        data = json.loads(args.input)
        
        # Process data
        result = process_data(data, args.operation)
        
        # Output result
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        error_result = {'error': str(e), 'success': False}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## Environment Setup

### Docker Volume Mount

In docker-compose.yml:

```yaml
services:
  n8n:
    volumes:
      - ../shared:/shared:ro  # Read-only access to scripts
      
  python-worker:
    volumes:
      - ../shared:/shared:rw  # Read-write access for script execution
```

### Dependencies Management

Each script category has its own `requirements.txt`:

```bash
# Install dependencies for a specific category
pip install -r /shared/scripts/data_processing/requirements.txt
```

## Security Considerations

1. **Read-only mounts**: n8n has read-only access to scripts
2. **Input validation**: All scripts validate input data
3. **Sandboxed execution**: Scripts run in isolated containers
4. **Resource limits**: Execution timeouts and memory limits
5. **Logging**: All script executions are logged

## Best Practices

1. **Modular design**: Keep scripts focused on single tasks
2. **Error handling**: Comprehensive error handling and logging
3. **Documentation**: Each script includes usage examples
4. **Testing**: Include test data and expected outputs
5. **Performance**: Optimize for n8n workflow execution times