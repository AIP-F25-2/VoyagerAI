#!/bin/bash

# VoyagerAI Complete Startup Script
echo "🚀 Starting VoyagerAI Full Stack Application..."

# Function to start backend in background
start_backend() {
    echo "🔧 Starting Backend..."
    cd "$(dirname "$0")/backend"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Install Playwright browsers
    playwright install chromium > /dev/null 2>&1
    
    # Initialize database
    python init_db.py > /dev/null 2>&1
    
    # Start Flask server in background
    python wsgi.py &
    BACKEND_PID=$!
    echo "✅ Backend started (PID: $BACKEND_PID)"
}

# Function to start frontend in background
start_frontend() {
    echo "🔧 Starting Frontend..."
    cd "$(dirname "$0")/frontend"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install > /dev/null 2>&1
    fi
    
    # Start Next.js server in background
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start services
start_backend
sleep 3  # Give backend time to start
start_frontend

echo ""
echo "🎉 VoyagerAI is now running!"
echo "   Backend:  http://localhost:5000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait
