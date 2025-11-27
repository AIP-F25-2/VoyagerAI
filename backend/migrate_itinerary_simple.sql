-- Simple SQL migration to add is_shared and share_token columns to itinerary table
-- Run this directly with psql (PostgreSQL) or sqlite3 (SQLite)

-- For PostgreSQL:
-- psql -d voyagerai -f migrate_itinerary_simple.sql

-- For SQLite:
-- sqlite3 voyagerai.db < migrate_itinerary_simple.sql

-- PostgreSQL version
DO $$
BEGIN
    -- Add is_shared column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'itinerary' AND column_name = 'is_shared'
    ) THEN
        ALTER TABLE itinerary ADD COLUMN is_shared BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added is_shared column';
    ELSE
        RAISE NOTICE 'is_shared column already exists';
    END IF;

    -- Add share_token column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'itinerary' AND column_name = 'share_token'
    ) THEN
        ALTER TABLE itinerary ADD COLUMN share_token VARCHAR(100);
        RAISE NOTICE 'Added share_token column';
    ELSE
        RAISE NOTICE 'share_token column already exists';
    END IF;

    -- Create unique index on share_token if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_itinerary_share_token'
    ) THEN
        CREATE UNIQUE INDEX idx_itinerary_share_token 
        ON itinerary(share_token) 
        WHERE share_token IS NOT NULL;
        RAISE NOTICE 'Created unique index on share_token';
    ELSE
        RAISE NOTICE 'Index on share_token already exists';
    END IF;
END $$;

