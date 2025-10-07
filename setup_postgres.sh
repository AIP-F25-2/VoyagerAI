#!/bin/bash

echo "🐘 Setting up PostgreSQL for VoyagerAI..."

# Check if PostgreSQL is running
if pgrep -f "postgres" > /dev/null; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL is not running. Please start it first:"
    echo "   1. Open 'PostgreSQL 17' from Applications"
    echo "   2. Or start it via System Preferences"
    echo "   3. Or run: brew services start postgresql (if installed via Homebrew)"
    exit 1
fi

# Try to find psql command
PSQL_CMD=""
if command -v psql &> /dev/null; then
    PSQL_CMD="psql"
elif [ -f "/Applications/PostgreSQL 17/SQL Shell (psql).app/Contents/MacOS/psql" ]; then
    PSQL_CMD="/Applications/PostgreSQL 17/SQL Shell (psql).app/Contents/MacOS/psql"
elif [ -f "/usr/local/bin/psql" ]; then
    PSQL_CMD="/usr/local/bin/psql"
elif [ -f "/opt/homebrew/bin/psql" ]; then
    PSQL_CMD="/opt/homebrew/bin/psql"
else
    echo "❌ psql command not found. Please add PostgreSQL to your PATH:"
    echo "   Add this to your ~/.zshrc or ~/.bash_profile:"
    echo "   export PATH=\"/Applications/PostgreSQL 17/bin:\$PATH\""
    echo "   Then run: source ~/.zshrc"
    exit 1
fi

echo "✅ Found psql at: $PSQL_CMD"

# Create database
echo "📊 Creating database 'voyagerai'..."
$PSQL_CMD -U postgres -c "CREATE DATABASE voyagerai;" 2>/dev/null || echo "Database might already exist"

echo "✅ Database setup complete!"
echo ""
echo "🎉 PostgreSQL is ready for VoyagerAI!"
echo ""
echo "Next steps:"
echo "1. cd backend"
echo "2. source .venv/bin/activate"
echo "3. pip install -r requirements.txt"
echo "4. python init_db.py"
echo "5. python wsgi.py"
