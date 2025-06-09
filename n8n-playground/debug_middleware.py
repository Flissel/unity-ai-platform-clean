#!/usr/bin/env python3
"""
Debug script to isolate middleware configuration issue
"""

import sys
sys.path.insert(0, '.')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from core.config import get_config

def test_middleware():
    """Test middleware configuration"""
    try:
        # Load config
        config = get_config()
        print(f"Config loaded: {type(config)}")
        print(f"CORS origins: {config.security.cors_origins}")
        print(f"CORS origins type: {type(config.security.cors_origins)}")
        
        # Create minimal FastAPI app
        app = FastAPI(title="Test App")
        print("FastAPI app created successfully")
        
        # Test CORS middleware
        print("Adding CORS middleware...")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.security.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        print("CORS middleware added successfully")
        
        # Test GZip middleware
        print("Adding GZip middleware...")
        app.add_middleware(GZipMiddleware, minimum_size=1000)
        print("GZip middleware added successfully")
        
        # Test middleware stack build
        print("Building middleware stack...")
        middleware_stack = app.build_middleware_stack()
        print(f"Middleware stack built successfully: {type(middleware_stack)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_middleware()
    if success:
        print("\nAll middleware tests passed!")
    else:
        print("\nMiddleware test failed!")
        sys.exit(1)