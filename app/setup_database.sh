#!/bin/bash

# VoyagerAI Database Setup Script
echo "🚀 Setting up VoyagerAI Database..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo "   On macOS: brew install postgresql"
    echo "   On Ubuntu: sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL is not running. Starting PostgreSQL..."
    if command -v brew &> /dev/null; then
        brew services start postgresql
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql
    fi
    
    # Wait a moment for PostgreSQL to start
    sleep 3
fi

# Create database if it doesn't exist
echo "📊 Creating database 'voyagerai'..."
createdb voyagerai 2>/dev/null || echo "Database 'voyagerai' already exists or creation failed"

# Create development database
echo "📊 Creating development database 'voyagerai_dev'..."
createdb voyagerai_dev 2>/dev/null || echo "Database 'voyagerai_dev' already exists or creation failed"

echo "✅ Database setup complete!"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies: cd backend && pip install -r requirements.txt"
echo "2. Initialize database tables: cd backend && python init_db.py"
echo "3. Start the backend: cd backend && python wsgi.py"
echo "4. Start the frontend: cd frontend && npm run dev"
