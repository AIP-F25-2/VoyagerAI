# Database Migration Instructions

## Quick Fix: Add is_shared and share_token columns

You have **3 options** to run the migration:

### Option 1: Direct SQL (Recommended - No Python dependencies)

#### For PostgreSQL:
```bash
# Connect to your database and run:
psql -d voyagerai -c "
ALTER TABLE itinerary ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE;
ALTER TABLE itinerary ADD COLUMN IF NOT EXISTS share_token VARCHAR(100);
CREATE UNIQUE INDEX IF NOT EXISTS idx_itinerary_share_token ON itinerary(share_token) WHERE share_token IS NOT NULL;
"
```

Or if you need to specify connection details:
```bash
psql -h localhost -U your_username -d voyagerai -c "
ALTER TABLE itinerary ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE;
ALTER TABLE itinerary ADD COLUMN IF NOT EXISTS share_token VARCHAR(100);
CREATE UNIQUE INDEX IF NOT EXISTS idx_itinerary_share_token ON itinerary(share_token) WHERE share_token IS NOT NULL;
"
```

#### For SQLite:
```bash
sqlite3 voyagerai.db "
ALTER TABLE itinerary ADD COLUMN is_shared BOOLEAN DEFAULT 0;
ALTER TABLE itinerary ADD COLUMN share_token VARCHAR(100);
"
```

### Option 2: Python Script (Requires psycopg2-binary or sqlite3)

```bash
cd VoyagerAI/backend
python3 migrate_itinerary_direct.py
```

### Option 3: Install Dependencies and Use Original Script

```bash
cd VoyagerAI/backend
pip install flask flask-sqlalchemy python-dotenv
python3 migrate_itinerary_columns.py
```

## Verify Migration

After running the migration, verify it worked:

### PostgreSQL:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'itinerary' 
AND column_name IN ('is_shared', 'share_token');
```

### SQLite:
```sql
PRAGMA table_info(itinerary);
```

You should see both `is_shared` and `share_token` columns in the output.

## Next Steps After Migration

1. **Restart your backend server** (if it's running):
   ```bash
   # Stop the current server (Ctrl+C) and restart it
   python wsgi.py
   # or
   flask run
   ```

2. **Test creating a travel plan**:
   - Go to your frontend at `http://localhost:3000/travel-plans`
   - Try creating a new travel plan
   - The database error should be gone!

3. **Verify the migration worked**:
   ```sql
   -- Check columns exist
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'itinerary' 
   AND column_name IN ('is_shared', 'share_token');
   ```

4. **Test group planning features**:
   - Create a travel plan
   - Go to the plan detail page
   - You should see the "👥 Group Planning" section
   - Try inviting a collaborator or generating a share link

## Step 2: Create itinerary_collaborator Table

After adding the columns, you also need to create the `itinerary_collaborator` table for group planning:

```bash
# Run the SQL file
psql -d voyagerai -f create_collaborator_table.sql

# Or run directly:
psql -d voyagerai -c "
CREATE TABLE IF NOT EXISTS itinerary_collaborator (
    id SERIAL PRIMARY KEY,
    itinerary_id INTEGER NOT NULL,
    user_email VARCHAR(200) NOT NULL,
    user_id INTEGER,
    role VARCHAR(50) DEFAULT 'viewer',
    status VARCHAR(50) DEFAULT 'pending',
    invited_by INTEGER,
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    joined_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_itinerary_collaborator_itinerary 
        FOREIGN KEY (itinerary_id) REFERENCES itinerary(id) ON DELETE CASCADE,
    CONSTRAINT fk_itinerary_collaborator_user 
        FOREIGN KEY (user_id) REFERENCES \"user\"(id) ON DELETE SET NULL,
    CONSTRAINT fk_itinerary_collaborator_inviter 
        FOREIGN KEY (invited_by) REFERENCES \"user\"(id) ON DELETE SET NULL,
    CONSTRAINT uq_collaborator_itinerary_email UNIQUE (itinerary_id, user_email)
);
CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_itinerary_id ON itinerary_collaborator(itinerary_id);
CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_user_email ON itinerary_collaborator(user_email);
"
```

## Troubleshooting

If you still get errors:
- Make sure you restarted the backend server after migration
- Check that the columns were actually added (use the verification SQL above)
- Make sure the `itinerary_collaborator` table was created
- Check backend logs for any other errors

