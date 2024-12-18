-- Deployment Safety SQL
-- Run this in production to safely update database schema

-- Safety check to prevent accidental data loss
DO $$
DECLARE
    table_count INTEGER;
    backup_exists BOOLEAN;
BEGIN
    -- Count existing production tables that have data
    SELECT COUNT(*) INTO table_count
    FROM (
        SELECT EXISTS (SELECT 1 FROM prod_token_opportunities LIMIT 1) UNION ALL
        SELECT EXISTS (SELECT 1 FROM prod_alpha_reports LIMIT 1) UNION ALL
        SELECT EXISTS (SELECT 1 FROM prod_warpcasts LIMIT 1) UNION ALL
        SELECT EXISTS (SELECT 1 FROM prod_social_media_posts LIMIT 1) UNION ALL
        SELECT EXISTS (SELECT 1 FROM prod_token_reports LIMIT 1)
    ) AS t;

    -- Check if backup exists from today
    SELECT EXISTS (
        SELECT 1 
        FROM pg_stat_file('backup_' || to_char(current_date, 'YYYYMMDD') || '%.sql')
    ) INTO backup_exists;

    -- If tables have data and no backup exists, raise an error
    IF table_count > 0 AND NOT backup_exists THEN
        RAISE EXCEPTION 'Cannot proceed: Production tables contain data but no backup from today was found. Please run backup first.';
    END IF;

    -- If we get here, either tables are empty or we have a backup
    -- Proceed with schema updates (ADD/ALTER commands only, no DROP)
    
    -- Example of safe schema updates:
    -- ALTER TABLE IF EXISTS prod_token_opportunities 
    --     ADD COLUMN IF NOT EXISTS new_column_name TEXT;
    
END $$;
