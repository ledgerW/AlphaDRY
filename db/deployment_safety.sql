-- Deployment Safety SQL
-- Run this in production to safely update database schema

-- 0. Drop and recreate tables to ensure schema is up to date
DO $$
BEGIN
    -- Drop existing tables in correct order
    DROP TABLE IF EXISTS prod_token_opportunities CASCADE;
    DROP TABLE IF EXISTS prod_alpha_reports CASCADE;
    DROP TABLE IF EXISTS prod_warpcasts CASCADE;
    DROP TABLE IF EXISTS prod_social_media_posts CASCADE;
    DROP TABLE IF EXISTS prod_token_reports CASCADE;
    
    -- Drop enum type if it exists
    DROP TYPE IF EXISTS chain CASCADE;
END $$;
