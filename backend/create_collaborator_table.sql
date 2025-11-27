-- Create itinerary_collaborator table for group planning
-- Run this SQL directly in your PostgreSQL database

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

-- Create index on itinerary_id for faster queries
CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_itinerary_id 
    ON itinerary_collaborator(itinerary_id);

-- Create index on user_email for faster lookups
CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_user_email 
    ON itinerary_collaborator(user_email);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_user_id 
    ON itinerary_collaborator(user_id);

