#!/usr/bin/env python3
"""
Quick test script to verify LLM service setup
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

# Check OpenAI library
try:
    from openai import OpenAI
    print("✓ OpenAI library is installed")
    OPENAI_AVAILABLE = True
except ImportError:
    print("✗ OpenAI library is NOT installed")
    print("  Install with: pip install openai")
    OPENAI_AVAILABLE = False
    sys.exit(1)

# Check API key
api_key = os.getenv("OPENAI_API_KEY", "").strip()
if api_key:
    print(f"✓ OPENAI_API_KEY found (length: {len(api_key)})")
    print(f"  First 10 chars: {api_key[:10]}...")
    print(f"  Last 4 chars: ...{api_key[-4:]}")
else:
    print("✗ OPENAI_API_KEY not found in environment")
    print("  Make sure it's set in backend/.env file")
    sys.exit(1)

# Test client initialization
try:
    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client initialized successfully")
    
    # Test with a simple API call (this will use a small amount of credits)
    print("\nTesting API connection...")
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": "Say 'Hello'"}],
        max_tokens=5
    )
    print("✓ API connection successful!")
    print(f"  Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"✗ Failed to initialize or test OpenAI client: {e}")
    sys.exit(1)

print("\n✅ All checks passed! LLM service is ready to use.")

