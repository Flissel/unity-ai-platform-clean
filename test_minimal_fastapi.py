from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

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

print("Middleware added successfully")
print(f"Number of user middleware: {len(app.user_middleware)}")

for i, middleware in enumerate(app.user_middleware):
    print(f"Middleware {i}: {middleware}")
    print(f"  Class: {middleware.cls}")
    print(f"  Args: {middleware.args}")
    print(f"  Kwargs: {middleware.kwargs}")
    print(f"  Middleware object type: {type(middleware)}")
    
    # Try to unpack like the build_middleware_stack does
    try:
        cls, args, kwargs = middleware
        print(f"  Unpacked successfully: cls={cls}, args={args}, kwargs={kwargs}")
    except ValueError as e:
        print(f"  Unpacking failed: {e}")
        # Try different unpacking approaches
        try:
            cls, kwargs = middleware
            print(f"  Unpacked as 2-tuple: cls={cls}, kwargs={kwargs}")
        except ValueError as e2:
            print(f"  2-tuple unpacking also failed: {e2}")

print("\nAttempting to build middleware stack...")
try:
    middleware_stack = app.build_middleware_stack()
    print("Middleware stack built successfully!")
except Exception as e:
    print(f"Error building middleware stack: {e}")
    import traceback
    traceback.print_exc()