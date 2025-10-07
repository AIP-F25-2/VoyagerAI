#!/bin/bash

echo "🚀 Setting up VoyagerAI..."

# Using SQLite for simplicity - no database setup needed!
echo "📊 Using SQLite database (no setup required)"

# Setup backend
echo "🐍 Setting up Python backend..."
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Initialize database
python init_db.py

echo "✅ Backend setup complete!"

# Setup frontend
echo "⚛️  Setting up Next.js frontend..."
cd ../frontend

# Install dependencies
npm install

echo "✅ Frontend setup complete!"

echo ""
echo "🎉 VoyagerAI setup complete!"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source .venv/bin/activate && python wsgi.py"
echo "2. Frontend: cd frontend && npm run dev"
echo "3. Open: http://localhost:3000"
echo ""
echo "Happy coding! 🚀"
