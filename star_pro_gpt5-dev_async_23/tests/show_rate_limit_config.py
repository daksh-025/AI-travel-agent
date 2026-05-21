#!/usr/bin/env python3
"""
Display current rate limiting configuration.
Run this to see what rate limit is currently configured.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    
    print()
    print("=" * 60)
    print("Current Rate Limiting Configuration")
    print("=" * 60)
    print()
    print(f"  Guest Rate Limit: {settings.guest_rate_limit_per_day} requests per day")
    print()
    print("  Redis URL:", settings.redis_url)
    print("  Redis Max Connections:", settings.redis_max_connections)
    print()
    print("=" * 60)
    print()
    print("To change the rate limit:")
    print("  1. Edit your .env file:")
    print(f"     GUEST_RATE_LIMIT_PER_DAY={settings.guest_rate_limit_per_day}")
    print()
    print("  2. Or set environment variable:")
    print(f"     export GUEST_RATE_LIMIT_PER_DAY=5")
    print()
    print("  3. Restart the application for changes to take effect")
    print()
    print("=" * 60)
    print()
    
except ImportError as e:
    print()
    print("ERROR: Could not import settings")
    print(f"  {e}")
    print()
    print("Make sure you're in the project directory and dependencies are installed:")
    print("  pip install -r requirements.txt")
    print()
    sys.exit(1)
except Exception as e:
    print()
    print(f"ERROR: {type(e).__name__}: {e}")
    print()
    sys.exit(1)

