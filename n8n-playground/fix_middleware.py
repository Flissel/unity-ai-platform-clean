from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware import Middleware

# Create a patched version of build_middleware_stack that handles Middleware objects correctly
def patched_build_middleware_stack(self):
    debug = self.debug
    error_handler = None
    exception_handlers = {}

    for key, value in self.exception_handlers.items():
        if key in (500, Exception):
            error_handler = value
        else:
            exception_handlers[key] = value

    from starlette.middleware.errors import ServerErrorMiddleware
    from starlette.middleware.exceptions import ExceptionMiddleware
    
    middleware = (
        [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]
        + self.user_middleware
        + [
            Middleware(
                ExceptionMiddleware, handlers=exception_handlers, debug=debug
            )
        ]
    )

    app = self.router
    
    # Fix: Properly handle Middleware objects by extracting cls and combining args/kwargs
    for middleware_item in reversed(middleware):
        if hasattr(middleware_item, 'cls'):
            # This is a Middleware object, extract the class and options
            cls = middleware_item.cls
            # Combine args and kwargs into options dict
            options = middleware_item.kwargs.copy()
            # If there are positional args, we need to handle them appropriately
            # Most middleware classes expect keyword arguments only
            app = cls(app=app, **options)
        else:
            # This might be a tuple (cls, options) - handle legacy format
            cls, options = middleware_item
            app = cls(app=app, **options)
    
    return app

# Test the fix
if __name__ == "__main__":
    app = FastAPI()
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Monkey patch the build_middleware_stack method
    import types
    app.build_middleware_stack = types.MethodType(patched_build_middleware_stack, app)
    
    print("Testing patched build_middleware_stack...")
    try:
        middleware_stack = app.build_middleware_stack()
        print("SUCCESS: Middleware stack built successfully!")
        print(f"Middleware stack type: {type(middleware_stack)}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()