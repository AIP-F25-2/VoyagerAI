#!/bin/bash

# VoyagerAI Backend Startup Script
echo "🚀 Starting VoyagerAI Backend..."

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium

# Initialize database
echo "🗄️  Initializing database..."
python init_db.py

# Start the Flask server
echo "🌟 Starting Flask server on http://localhost:5001"
echo "   Press Ctrl+C to stop the server"
echo ""
python wsgi.py
