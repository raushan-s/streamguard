"""
Pytest configuration for StreamGuard Lambda tests.

Loads environment variables from .env file before running tests.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
from dotenv import load_dotenv

# Path to .env file (parent directory of tests/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def pytest_configure(config):
    """Pytest configuration hook."""
    # Print environment info for debugging
    print(f"\n=== Environment Configuration ===")
    print(f"MODEL_PATH: {os.getenv('MODEL_PATH', 'NOT SET')}")
    print(f"HF_TOKEN: {'SET' if os.getenv('HF_TOKEN') else 'NOT SET'}")
    print(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    print(f"UPSTASH_REDIS_URL: {'SET' if os.getenv('UPSTASH_REDIS_URL') else 'NOT SET'}")
    print(f"ENABLE_LAYER4: {os.getenv('ENABLE_LAYER4', 'true')}")
    print(f"=================================\n")
