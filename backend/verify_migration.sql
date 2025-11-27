-- Quick verification script to check if migration was successful
-- Run this to verify the columns exist

-- For PostgreSQL:
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'itinerary' 
AND column_name IN ('is_shared', 'share_token')
ORDER BY column_name;

-- Also check if the index was created
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'itinerary' 
AND indexname = 'idx_itinerary_share_token';

