#!/usr/bin/env python3
"""
Test script to verify .env configuration is working correctly.
This script loads environment variables and displays their values.
"""

import os
from pathlib import Path
from typing import Dict, Any

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv not installed. Install with: pip install python-dotenv")
    exit(1)

def load_env_file(env_file: str = ".env") -> bool:
    """Load environment file and return success status."""
    env_path = Path(env_file)
    if not env_path.exists():
        print(f"❌ Environment file '{env_file}' not found")
        print(f"💡 Copy .env.example to .env: cp .env.example .env")
        return False
    
    load_dotenv(env_path)
    print(f"✅ Loaded environment file: {env_path.absolute()}")
    return True

def test_required_variables() -> Dict[str, Any]:
    """Test that required environment variables are set."""
    required_vars = {
        # Application
        "APP_NAME": "string",
        "VERSION": "string",
        "ENVIRONMENT": "string",
        "DEBUG": "boolean",
        
        # Server
        "HOST": "string",
        "PORT": "integer",
        
        # Security
        "SECRET_KEY": "string",
        "JWT_SECRET_KEY": "string",
        "API_KEYS": "string",
        
        # Database
        "DATABASE_URL": "string",
        "POSTGRES_USER": "string",
        "POSTGRES_PASSWORD": "string",
        "POSTGRES_DB": "string",
        
        # Redis
        "REDIS_URL": "string",
        
        # Logging
        "LOG_LEVEL": "string",
    }
    
    results = {}
    missing_vars = []
    
    print("\n🔍 Testing required environment variables:")
    print("=" * 50)
    
    for var_name, var_type in required_vars.items():
        value = os.getenv(var_name)
        
        if value is None:
            print(f"❌ {var_name}: NOT SET")
            missing_vars.append(var_name)
            results[var_name] = None
        else:
            # Mask sensitive values
            if any(sensitive in var_name.lower() for sensitive in ['password', 'secret', 'key']):
                display_value = "*" * min(len(value), 8) if value else "NOT SET"
            else:
                display_value = value
            
            print(f"✅ {var_name}: {display_value}")
            results[var_name] = value
    
    if missing_vars:
        print(f"\n❌ Missing {len(missing_vars)} required variables: {', '.join(missing_vars)}")
    else:
        print(f"\n✅ All {len(required_vars)} required variables are set!")
    
    return results

def test_optional_variables() -> Dict[str, Any]:
    """Test optional environment variables."""
    optional_vars = {
        # n8n
        "N8N_BASE_URL": "string",
        "N8N_API_KEY": "string",
        "N8N_BASIC_AUTH_USER": "string",
        "N8N_BASIC_AUTH_PASSWORD": "string",
        
        # AutoGen
        "AUTOGEN_MODEL": "string",
        "AUTOGEN_API_KEY": "string",
        
        # Monitoring
        "PROMETHEUS_PORT": "integer",
        "GRAFANA_PORT": "integer",
        
        # CORS
        "CORS_ORIGINS": "string",
    }
    
    results = {}
    set_vars = 0
    
    print("\n🔍 Testing optional environment variables:")
    print("=" * 50)
    
    for var_name, var_type in optional_vars.items():
        value = os.getenv(var_name)
        
        if value is None:
            print(f"⚪ {var_name}: NOT SET (optional)")
            results[var_name] = None
        else:
            # Mask sensitive values
            if any(sensitive in var_name.lower() for sensitive in ['password', 'secret', 'key']):
                display_value = "*" * min(len(value), 8) if value else "NOT SET"
            else:
                display_value = value
            
            print(f"✅ {var_name}: {display_value}")
            results[var_name] = value
            set_vars += 1
    
    print(f"\n📊 Optional variables set: {set_vars}/{len(optional_vars)}")
    return results

def test_variable_types() -> bool:
    """Test that variables have correct types/formats."""
    print("\n🔍 Testing variable types and formats:")
    print("=" * 50)
    
    errors = []
    
    # Test PORT is integer
    port = os.getenv("PORT")
    if port:
        try:
            port_int = int(port)
            if 1 <= port_int <= 65535:
                print(f"✅ PORT: {port} (valid integer)")
            else:
                print(f"❌ PORT: {port} (out of range 1-65535)")
                errors.append("PORT out of range")
        except ValueError:
            print(f"❌ PORT: {port} (not an integer)")
            errors.append("PORT not integer")
    
    # Test DEBUG is boolean
    debug = os.getenv("DEBUG")
    if debug:
        if debug.lower() in ['true', 'false', '1', '0', 'yes', 'no']:
            print(f"✅ DEBUG: {debug} (valid boolean)")
        else:
            print(f"❌ DEBUG: {debug} (not a valid boolean)")
            errors.append("DEBUG not boolean")
    
    # Test DATABASE_URL format
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith(('postgresql://', 'sqlite://')):
            print(f"✅ DATABASE_URL: Valid format")
        else:
            print(f"❌ DATABASE_URL: Invalid format (should start with postgresql:// or sqlite://)")
            errors.append("DATABASE_URL invalid format")
    
    # Test REDIS_URL format
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        if redis_url.startswith('redis://'):
            print(f"✅ REDIS_URL: Valid format")
        else:
            print(f"❌ REDIS_URL: Invalid format (should start with redis://)")
            errors.append("REDIS_URL invalid format")
    
    # Test LOG_LEVEL
    log_level = os.getenv("LOG_LEVEL")
    if log_level:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level.upper() in valid_levels:
            print(f"✅ LOG_LEVEL: {log_level} (valid)")
        else:
            print(f"❌ LOG_LEVEL: {log_level} (should be one of {valid_levels})")
            errors.append("LOG_LEVEL invalid")
    
    if errors:
        print(f"\n❌ Found {len(errors)} type/format errors")
        return False
    else:
        print(f"\n✅ All variable types and formats are correct!")
        return True

def test_config_import():
    """Test importing the config module."""
    print("\n🔍 Testing config module import:")
    print("=" * 50)
    
    try:
        # Add src to path
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from core.config import get_settings
        settings = get_settings()
        
        print(f"✅ Config module imported successfully")
        print(f"✅ Settings loaded: {settings.app_name} v{settings.version}")
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Debug mode: {settings.debug}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import config module: {e}")
        print("💡 Make sure the src/core/config.py file exists")
        return False
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 UnityAI Environment Configuration Test")
    print("=" * 50)
    
    # Load .env file
    if not load_env_file():
        return 1
    
    # Run tests
    required_results = test_required_variables()
    optional_results = test_optional_variables()
    types_ok = test_variable_types()
    config_ok = test_config_import()
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    
    required_missing = sum(1 for v in required_results.values() if v is None)
    required_total = len(required_results)
    
    if required_missing == 0:
        print(f"✅ Required variables: {required_total}/{required_total} set")
    else:
        print(f"❌ Required variables: {required_total - required_missing}/{required_total} set")
    
    optional_set = sum(1 for v in optional_results.values() if v is not None)
    optional_total = len(optional_results)
    print(f"📊 Optional variables: {optional_set}/{optional_total} set")
    
    print(f"{'✅' if types_ok else '❌'} Variable types and formats: {'OK' if types_ok else 'ERRORS'}")
    print(f"{'✅' if config_ok else '❌'} Config module import: {'OK' if config_ok else 'FAILED'}")
    
    # Overall result
    if required_missing == 0 and types_ok and config_ok:
        print("\n🎉 All tests passed! Your .env configuration is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())