-- Deployment Safety SQL
-- Run this in production to safely update database schema

DO $$
DECLARE
    table_count INTEGER;
    backup_exists BOOLEAN;
    env_prefix TEXT;
BEGIN
    -- Determine environment prefix
    IF current_setting('replit.deployment', TRUE) = '1' THEN
        env_prefix := 'prod_';
    ELSE
        env_prefix := 'dev_';
    END IF;

    -- Count existing production tables that have data
    EXECUTE format('
        SELECT COUNT(*) INTO table_count
        FROM (
            SELECT EXISTS (SELECT 1 FROM %Itoken_opportunities LIMIT 1) UNION ALL
            SELECT EXISTS (SELECT 1 FROM %Ialpha_reports LIMIT 1) UNION ALL
            SELECT EXISTS (SELECT 1 FROM %Iwarpcasts LIMIT 1) UNION ALL
            SELECT EXISTS (SELECT 1 FROM %Isocial_media_posts LIMIT 1) UNION ALL
            SELECT EXISTS (SELECT 1 FROM %Itoken_reports LIMIT 1)
        ) AS t', env_prefix, env_prefix, env_prefix, env_prefix, env_prefix);

    -- Check if backup exists from today
    SELECT EXISTS (
        SELECT 1 
        FROM pg_stat_file('backup_' || to_char(current_date, 'YYYYMMDD') || '%.sql')
    ) INTO backup_exists;

    -- If tables have data and no backup exists, raise an error
    IF table_count > 0 AND NOT backup_exists THEN
        RAISE EXCEPTION 'Cannot proceed: Tables contain data but no backup from today was found. Please run backup first.';
    END IF;

    -- Drop existing Chain enum type if it exists (to update with new values)
    DROP TYPE IF EXISTS chain CASCADE;
    
    -- Create Chain enum type with all supported chains
    CREATE TYPE chain AS ENUM (
        'ethereum',
        'polygon',
        'arbitrum',
        'optimism',
        'base',
        'solana'
    );

    -- Create tables in correct dependency order
    
    -- 1. Create social_media_posts first (no dependencies)
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

    -- 2. Create token_reports (depends on social_media_posts)
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
            social_post_id INTEGER REFERENCES %Isocial_media_posts(id),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )', env_prefix, env_prefix);

    -- 3. Create alpha_reports (no dependencies)
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %Ialpha_reports (
            id SERIAL PRIMARY KEY,
            is_relevant BOOLEAN NOT NULL,
            analysis TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )', env_prefix);

    -- 4. Create warpcasts (no dependencies)
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

    -- 5. Create token_opportunities (depends on alpha_reports and token_reports)
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %Itoken_opportunities (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            chain chain,
            contract_address VARCHAR(255),
            market_cap DOUBLE PRECISION,
            community_score INTEGER NOT NULL DEFAULT 0,
            safety_score INTEGER NOT NULL DEFAULT 0,
            justification TEXT NOT NULL DEFAULT '''',
            sources JSON,
            recommendation VARCHAR(50) NOT NULL DEFAULT ''Hold'',
            report_id INTEGER REFERENCES %Ialpha_reports(id),
            token_report_id INTEGER REFERENCES %Itoken_reports(id),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )', env_prefix, env_prefix, env_prefix);

    -- Add token_report_id foreign key to social_media_posts if it doesn't exist
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

    -- Create a function to handle case-insensitive chain values
    CREATE OR REPLACE FUNCTION normalize_chain(input_chain TEXT)
    RETURNS chain AS $$
    BEGIN
        RETURN LOWER(input_chain)::chain;
    EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

END $$;
