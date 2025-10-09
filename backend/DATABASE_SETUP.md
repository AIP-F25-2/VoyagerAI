# VoyagerAI PostgreSQL Database Setup Guide

This guide will help you set up PostgreSQL database for your VoyagerAI project.

## Prerequisites

1. **PostgreSQL installed and running**
   - Install PostgreSQL on your system
   - Make sure PostgreSQL service is running
   - Default port: 5432

2. **Python dependencies**
   - `psycopg2-binary` (already in requirements.txt)
   - `flask-sqlalchemy`
   - `python-dotenv`

## Quick Setup

### Step 1: Update Database Credentials

Edit the `.env` file in the backend directory:

```bash
# Replace with your actual PostgreSQL credentials
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/voyagerai
```

**Example configurations:**
```bash
# Local PostgreSQL with custom user
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/voyagerai

# Local PostgreSQL with default postgres user
DATABASE_URL=postgresql://postgres:password@localhost:5432/voyagerai

# Remote PostgreSQL
DATABASE_URL=postgresql://user:pass@your-server.com:5432/voyagerai
```

### Step 2: Create Database and Tables

Run the database setup script:

```bash
cd backend
source .venv/bin/activate
python setup_database.py
```

This will:
- Create the `voyagerai` database if it doesn't exist
- Create all necessary tables
- Test the connection

### Step 3: Test Database Connection

```bash
python db_manager.py test
```

### Step 4: Start the Application

```bash
python wsgi.py
```

## Database Management Commands

Use the `db_manager.py` script for database operations:

```bash
# Test database connection
python db_manager.py test

# Show database configuration
python db_manager.py info

# Add a sample event
python db_manager.py sample

# List all events
python db_manager.py list

# Clear all events
python db_manager.py clear

# Run full setup
python db_manager.py setup
```

## Database Schema

The application creates the following table:

### Events Table
```sql
CREATE TABLE event (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    date DATE,
    time TIME,
    venue VARCHAR(200),
    place VARCHAR(200),
    price VARCHAR(100),
    url VARCHAR(1000),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   Error: connection to server at "localhost" (127.0.0.1), port 5432 failed
   ```
   - Make sure PostgreSQL is running
   - Check if port 5432 is correct
   - Verify firewall settings

2. **Authentication Failed**
   ```
   Error: password authentication failed for user "username"
   ```
   - Check username and password in DATABASE_URL
   - Verify user has access to create databases

3. **Database Does Not Exist**
   ```
   Error: database "voyagerai" does not exist
   ```
   - Run `python setup_database.py` to create the database
   - Or manually create: `CREATE DATABASE voyagerai;`

4. **Permission Denied**
   ```
   Error: permission denied to create database
   ```
   - Grant CREATEDB privilege to your user
   - Or use a superuser account

### Manual Database Creation

If the setup script fails, you can manually create the database:

```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database
CREATE DATABASE voyagerai;

-- Create user (optional)
CREATE USER voyagerai_user WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE voyagerai TO voyagerai_user;
```

### Environment Variables

Make sure these are set in your `.env` file:

```bash
# Required
DATABASE_URL=postgresql://username:password@localhost:5432/voyagerai

# Optional
SECRET_KEY=your-secret-key-here
TICKETMASTER_API_KEY=your_api_key_here
EVENTBRITE_API_KEY=your_api_key_here
```

## API Endpoints

Once the database is set up, you can use these endpoints:

- `GET /api/events` - List all events
- `POST /api/scrape` - Scrape events from BookMyShow
- `GET /api/events/fetch` - Fetch events from external APIs
- `DELETE /api/events/<id>` - Delete an event

## Production Considerations

For production deployment:

1. **Use environment variables** for all sensitive data
2. **Set up proper database backups**
3. **Use connection pooling** for better performance
4. **Configure SSL** for database connections
5. **Set up monitoring** for database health

## Support

If you encounter issues:

1. Check the logs in the terminal
2. Verify PostgreSQL is running: `pg_ctl status`
3. Test connection manually: `psql -U username -d voyagerai`
4. Check the database manager: `python db_manager.py test`
