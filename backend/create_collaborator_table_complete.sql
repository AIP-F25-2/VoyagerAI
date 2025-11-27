-- Complete SQL for creating itinerary_collaborator table
-- Copy and paste this entire block into pgAdmin

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
    
    CONSTRAINT uq_collaborator_itinerary_email 
        UNIQUE (itinerary_id, user_email)
);

CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_itinerary_id 
    ON itinerary_collaborator(itinerary_id);

CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_user_email 
    ON itinerary_collaborator(user_email);

CREATE INDEX IF NOT EXISTS idx_itinerary_collaborator_user_id 
    ON itinerary_collaborator(user_id);

