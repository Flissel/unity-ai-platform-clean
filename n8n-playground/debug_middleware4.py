import sys
sys.path.append('.')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from config import PlaygroundConfig

def debug_middleware():
    print("Loading configuration...")
    config = PlaygroundConfig()
    print(f"Config loaded: {type(config)}")
    print(f"CORS origins: {config.security.cors_origins}")
    
    print("\nCreating FastAPI app...")
    app = FastAPI()
    print(f"App created: {type(app)}")
    
    print(f"\nInitial user_middleware: {len(app.user_middleware)} items")
    for i, middleware in enumerate(app.user_middleware):
        print(f"  {i}: {middleware} (type: {type(middleware)})")
        if hasattr(middleware, '__dict__'):
            print(f"      attributes: {middleware.__dict__}")
    
    print("\nAdding CORSMiddleware...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    print(f"After CORS - user_middleware: {len(app.user_middleware)} items")
    for i, middleware in enumerate(app.user_middleware):
        print(f"  {i}: {middleware} (type: {type(middleware)})")
        if hasattr(middleware, '__dict__'):
            print(f"      attributes: {middleware.__dict__}")
        # Check if it's iterable and what it contains
        try:
            if hasattr(middleware, '__iter__') and not isinstance(middleware, str):
                items = list(middleware)
                print(f"      iterable contents: {items}")
                print(f"      length when unpacked: {len(items)}")
        except Exception as e:
            print(f"      error checking iteration: {e}")
    
    print("\nAdding GZipMiddleware...")
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    print(f"After GZip - user_middleware: {len(app.user_middleware)} items")
    for i, middleware in enumerate(app.user_middleware):
        print(f"  {i}: {middleware} (type: {type(middleware)})")
        if hasattr(middleware, '__dict__'):
            print(f"      attributes: {middleware.__dict__}")
        # Check if it's iterable and what it contains
        try:
            if hasattr(middleware, '__iter__') and not isinstance(middleware, str):
                items = list(middleware)
                print(f"      iterable contents: {items}")
                print(f"      length when unpacked: {len(items)}")
        except Exception as e:
            print(f"      error checking iteration: {e}")
    
    print("\nTrying to build middleware stack...")
    try:
        # Let's manually check what build_middleware_stack expects
        middleware_list = app.user_middleware
        print(f"Middleware list to process: {middleware_list}")
        
        # Simulate what build_middleware_stack does
        print("\nSimulating middleware stack building:")
        for i, middleware_item in enumerate(reversed(middleware_list)):
            print(f"Processing item {i}: {middleware_item}")
            try:
                # This is what causes the error
                cls, options = middleware_item
                print(f"  Successfully unpacked: cls={cls}, options={options}")
            except ValueError as e:
                print(f"  ERROR unpacking: {e}")
                print(f"  Item type: {type(middleware_item)}")
                print(f"  Item value: {middleware_item}")
                if hasattr(middleware_item, '__dict__'):
                    print(f"  Item attributes: {middleware_item.__dict__}")
                break
        
        # Try the actual build
        stack = app.build_middleware_stack()
        print(f"Middleware stack built successfully: {type(stack)}")
        
    except Exception as e:
        print(f"Error building middleware stack: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_middleware()