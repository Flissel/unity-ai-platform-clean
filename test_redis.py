#!/usr/bin/env python3
"""
Simple Redis availability test script.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
print(f'Redis URL: {redis_url}')

try:
    import redis
    print('✅ Redis library is available')
    
    # Test connection
    print('Testing Redis connection...')
    r = redis.from_url(redis_url)
    
    # Ping test
    response = r.ping()
    print(f'✅ Redis is available! Ping response: {response}')
    
    # Set/Get test
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    print(f'✅ Redis read/write test successful: {value.decode()}')
    
    # Clean up
    r.delete('test_key')
    print('✅ Redis cleanup successful')
    
except ImportError:
    print('❌ Redis library not installed. Install with: pip install redis')
except redis.ConnectionError as e:
    print(f'❌ Redis connection failed: {e}')
    print('💡 Make sure Redis server is running on the configured URL')
except Exception as e:
    print(f'❌ Redis test failed: {e}')