-- Complete Migration Script for Group Planning Features
-- Run this to add all necessary tables and columns

-- Step 1: Add columns to itinerary table
ALTER TABLE itinerary ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE;
ALTER TABLE itinerary ADD COLUMN IF NOT EXISTS share_token VARCHAR(100);
CREATE UNIQUE INDEX IF NOT EXISTS idx_itinerary_share_token 
    ON itinerary(share_token) 
    WHERE share_token IS NOT NULL;

-- Step 2: Create itinerary_collaborator table
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
    
    -- Foreign keys
    CONSTRAINT fk_itinerary_collaborator_itinerary 
        FOREIGN KEY (itinerary_id) 
        REFERENCES itinerary(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_itinerary_collaborator_user 
        FOREIGN KEY (user_id) 
        REFERENCES "user"(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_itinerary_collaborator_inviter 
        FOREIGN KEY (invited_by) 
        REFERENCES "user"(id) 
        ON DELETE SET NULL,
    
    -- Unique constraint: one collaboration per user per itinerary
    CONSTRAINT uq_collaborator_itinerary_email 
        UNIQUE (itinerary_id, user_email)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_itinerary_id 
    ON itinerary_collaborator(itinerary_id);

CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_user_email 
    ON itinerary_collaborator(user_email);

CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_user_id 
    ON itinerary_collaborator(user_id);

-- Verification queries (optional - run these to verify)
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'itinerary' AND column_name IN ('is_shared', 'share_token');
-- SELECT table_name FROM information_schema.tables WHERE table_name = 'itinerary_collaborator';

