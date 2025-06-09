#!/usr/bin/env python3
"""
Detailed debug script to inspect middleware structure
"""

import sys
sys.path.insert(0, '.')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from core.config import get_config

def inspect_middleware():
    """Inspect middleware configuration in detail"""
    try:
        # Load config
        config = get_config()
        print(f"Config loaded: {type(config)}")
        print(f"CORS origins: {config.security.cors_origins}")
        
        # Create minimal FastAPI app
        app = FastAPI(title="Test App")
        print("FastAPI app created successfully")
        
        # Inspect initial middleware
        print(f"\nInitial middleware: {app.middleware}")
        print(f"Initial middleware type: {type(app.middleware)}")
        print(f"Initial middleware length: {len(app.middleware)}")
        
        for i, item in enumerate(app.middleware):
            print(f"  Middleware {i}: {item} (type: {type(item)})")
        
        # Add CORS middleware
        print("\nAdding CORS middleware...")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.security.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Inspect after CORS
        print(f"\nAfter CORS middleware: {app.middleware}")
        print(f"Middleware length: {len(app.middleware)}")
        
        for i, item in enumerate(app.middleware):
            print(f"  Middleware {i}: {item} (type: {type(item)})")
            if hasattr(item, '__len__') and not isinstance(item, str):
                try:
                    print(f"    Length: {len(item)}")
                    for j, subitem in enumerate(item):
                        print(f"      Item {j}: {subitem} (type: {type(subitem)})")
                except Exception as e:
                    print(f"    Error inspecting item: {e}")
        
        # Add GZip middleware
        print("\nAdding GZip middleware...")
        app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Inspect after GZip
        print(f"\nAfter GZip middleware: {app.middleware}")
        print(f"Middleware length: {len(app.middleware)}")
        
        for i, item in enumerate(app.middleware):
            print(f"  Middleware {i}: {item} (type: {type(item)})")
            if hasattr(item, '__len__') and not isinstance(item, str):
                try:
                    print(f"    Length: {len(item)}")
                    for j, subitem in enumerate(item):
                        print(f"      Item {j}: {subitem} (type: {type(subitem)})")
                except Exception as e:
                    print(f"    Error inspecting item: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = inspect_middleware()
    if success:
        print("\nMiddleware inspection completed!")
    else:
        print("\nMiddleware inspection failed!")
        sys.exit(1)