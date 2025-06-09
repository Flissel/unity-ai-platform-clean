#!/usr/bin/env python3
"""
Minimal FastAPI test to isolate the middleware issue
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Create a minimal FastAPI app
app = FastAPI(title="Minimal Test")

print("Adding CORSMiddleware...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Adding GZipMiddleware...")
app.add_middleware(GZipMiddleware, minimum_size=1000)

print("Checking user_middleware list:")
for i, middleware in enumerate(app.user_middleware):
    print(f"  {i}: {middleware}")
    print(f"      Type: {type(middleware)}")
    print(f"      Class: {middleware.cls}")
    print(f"      Args: {middleware.args}")
    print(f"      Kwargs: {middleware.kwargs}")

print("\nTrying to build middleware stack...")
try:
    stack = app.build_middleware_stack()
    print(f"Success! Stack type: {type(stack)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest completed.")