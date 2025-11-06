#!/usr/bin/env python3
"""
Simple verification script - run this from the backend directory
Make sure your virtual environment is activated first!
"""
import os
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
backend_dir = Path(__file__).parent
load_dotenv(backend_dir / ".env")

print("🔍 Checking LLM Setup...")
print("=" * 50)

# Check 1: OpenAI library
try:
    from openai import OpenAI
    print("✅ OpenAI library installed")
except ImportError:
    print("❌ OpenAI library NOT installed")
    print("   Run: pip install openai")
    exit(1)

# Check 2: API Key
api_key = os.getenv("OPENAI_API_KEY", "").strip()
if api_key:
    print(f"✅ OPENAI_API_KEY found (length: {len(api_key)})")
    # Project-based keys (sk-proj-...) can be longer than standard keys
    if len(api_key) < 20:
        print("   ⚠️  Warning: API key seems too short")
    elif len(api_key) > 200:
        print("   ⚠️  Warning: API key seems unusually long")
else:
    print("❌ OPENAI_API_KEY not found")
    print("   Make sure it's in backend/.env file")
    exit(1)

# Check 3: Model
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
print(f"✅ Model configured: {model}")

# Check 4: Test client
try:
    client = OpenAI(api_key=api_key)
    print("✅ OpenAI client initialized")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

print("=" * 50)
print("✅ All checks passed! Your LLM service should work.")
print("\nTo test the API endpoint, visit:")
print("   http://localhost:5001/api/llm/status")

