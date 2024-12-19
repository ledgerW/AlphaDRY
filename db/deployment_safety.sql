-- Deployment Safety SQL
-- This script safely updates schema without dropping tables

DO $$
DECLARE
    env_prefix TEXT;
BEGIN
    -- Get environment prefix from environment variable via connection info
    -- In production, set REPLIT_DEPLOYMENT=1 in your environment
    IF current_setting('application_name') = 'prod' THEN
        env_prefix := 'prod_';
    ELSE
        env_prefix := 'dev_';
    END IF;

    -- Create Chain enum type if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chain') THEN
        CREATE TYPE chain AS ENUM (
            'ethereum',
            'polygon',
            'arbitrum',
            'optimism',
            'base',
            'solana'
        );
    END IF;

    -- Create tables if they don't exist (won't modify existing tables)
    
    -- 1. Create social_media_posts if not exists
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %Isocial_media_posts (
            id SERIAL PRIMARY KEY,
            source VARCHAR(50) NOT NULL,
            post_id VARCHAR(255) NOT NULL,
            author_id VARCHAR(255) NOT NULL,
            author_username VARCHAR(255) NOT NULL,
            author_display_name VARCHAR(255),
            text TEXT NOT NULL,
            original_timestamp TIMESTAMP NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            reactions_count INTEGER NOT NULL DEFAULT 0,
            replies_count INTEGER NOT NULL DEFAULT 0,
            reposts_count INTEGER NOT NULL DEFAULT 0,
            raw_data JSONB NOT NULL,
            token_report_id INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )', env_prefix);

    -- 2. Create token_reports if not exists
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %Itoken_reports (
            id SERIAL PRIMARY KEY,
            mentions_purchasable_token BOOLEAN NOT NULL,
            token_symbol VARCHAR(50),
            token_chain VARCHAR(50),
            token_address VARCHAR(255),
            is_listed_on_dex BOOLEAN,
            trading_pairs JSON,
            confidence_score INTEGER,
            reasoning TEXT NOT NULL,
            social_post_id INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )', env_prefix);

    -- 3. Create alpha_reports if not exists
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %Ialpha_reports (
            id SERIAL PRIMARY KEY,
            is_relevant BOOLEAN NOT NULL,
            analysis TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )', env_prefix);

    -- 4. Create warpcasts if not exists
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %Iwarpcasts (
            id SERIAL PRIMARY KEY,
            raw_cast JSONB NOT NULL,
            hash VARCHAR(255) NOT NULL UNIQUE,
            username VARCHAR(255) NOT NULL,
            user_fid INTEGER NOT NULL,
            text TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            replies INTEGER NOT NULL DEFAULT 0,
            reactions INTEGER NOT NULL DEFAULT 0,
            recasts INTEGER NOT NULL DEFAULT 0,
            pulled_from_user VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )', env_prefix);

    -- 5. Create token_opportunities if not exists
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %Itoken_opportunities (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            chain chain NOT NULL,  -- Make chain required and use enum type
            contract_address VARCHAR(255),
            market_cap DOUBLE PRECISION,
            community_score INTEGER NOT NULL DEFAULT 0,
            safety_score INTEGER NOT NULL DEFAULT 0,
            justification TEXT NOT NULL DEFAULT '''',
            sources JSON,
            recommendation VARCHAR(50) NOT NULL DEFAULT ''Hold'',
            report_id INTEGER,
            token_report_id INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )', env_prefix);

    -- Add foreign key constraints if they don't exist
    
    -- token_opportunities -> alpha_reports
    EXECUTE format('
        DO $constraint$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE constraint_name = ''fk_token_opportunities_report''
            ) THEN
                ALTER TABLE %Itoken_opportunities
                ADD CONSTRAINT fk_token_opportunities_report
                FOREIGN KEY (report_id)
                REFERENCES %Ialpha_reports(id);
            END IF;
        END $constraint$;
    ', env_prefix, env_prefix);

    -- token_opportunities -> token_reports
    EXECUTE format('
        DO $constraint$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE constraint_name = ''fk_token_opportunities_token_report''
            ) THEN
                ALTER TABLE %Itoken_opportunities
                ADD CONSTRAINT fk_token_opportunities_token_report
                FOREIGN KEY (token_report_id)
                REFERENCES %Itoken_reports(id);
            END IF;
        END $constraint$;
    ', env_prefix, env_prefix);

    -- token_reports -> social_media_posts
    EXECUTE format('
        DO $constraint$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE constraint_name = ''fk_token_reports_social_post''
            ) THEN
                ALTER TABLE %Itoken_reports
                ADD CONSTRAINT fk_token_reports_social_post
                FOREIGN KEY (social_post_id)
                REFERENCES %Isocial_media_posts(id);
            END IF;
        END $constraint$;
    ', env_prefix, env_prefix);

    -- social_media_posts -> token_reports
    EXECUTE format('
        DO $constraint$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE constraint_name = ''fk_social_media_posts_token_report''
            ) THEN
                ALTER TABLE %Isocial_media_posts
                ADD CONSTRAINT fk_social_media_posts_token_report
                FOREIGN KEY (token_report_id)
                REFERENCES %Itoken_reports(id);
            END IF;
        END $constraint$;
    ', env_prefix, env_prefix);

END $$;

-- Create or replace function to handle case-insensitive chain values
CREATE OR REPLACE FUNCTION normalize_chain(input_chain TEXT)
RETURNS chain
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN LOWER(input_chain)::chain;
EXCEPTION 
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;
