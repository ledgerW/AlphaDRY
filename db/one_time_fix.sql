-- One-time fix for production database issues

-- 1. Verify and fix chain column in prod_token_opportunities
DO $$
BEGIN
    -- Add chain column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'prod_token_opportunities' 
        AND column_name = 'chain'
    ) THEN
        ALTER TABLE prod_token_opportunities
        ADD COLUMN chain chain;
    END IF;
END $$;

-- 2. Clean up any dev_ tables that shouldn't be in production
DO $$
DECLARE
    dev_table text;
BEGIN
    FOR dev_table IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'dev_%'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', dev_table);
    END LOOP;
END $$;

-- 3. Verify prod_ tables exist and have correct structure
DO $$
BEGIN
    -- Verify prod_token_opportunities
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'prod_token_opportunities'
    ) THEN
        RAISE EXCEPTION 'prod_token_opportunities table is missing';
    END IF;

    -- Verify prod_alpha_reports
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'prod_alpha_reports'
    ) THEN
        RAISE EXCEPTION 'prod_alpha_reports table is missing';
    END IF;

    -- Verify chain column exists and is of type chain
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'prod_token_opportunities' 
        AND column_name = 'chain' 
        AND udt_name = 'chain'
    ) THEN
        RAISE EXCEPTION 'chain column is missing or has wrong type in prod_token_opportunities';
    END IF;
END $$;
