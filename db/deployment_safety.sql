-- Deployment Safety Script

-- Check for today's backup
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' 
        AND c.relname LIKE 'backup_%'
        AND c.relkind = 'r'
        AND c.reltuples > 0
        AND date_trunc('day', now()) = date_trunc('day', c.relcreated)
    ) THEN
        RAISE EXCEPTION 'DEPLOYMENT BLOCKED: No backup found from today. Run pg_dump first.';
    END IF;
END
$$;

-- Verify prod tables exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'prod_token_opportunities'
    ) THEN
        RAISE EXCEPTION 'prod_token_opportunities table not found';
    END IF;
END
$$;

-- Store current data counts
CREATE TEMP TABLE IF NOT EXISTS pre_deployment_counts AS
SELECT 
    (SELECT COUNT(*) FROM prod_token_opportunities) as token_opportunities_count,
    (SELECT COUNT(*) FROM prod_alpha_reports) as alpha_reports_count,
    (SELECT COUNT(*) FROM prod_token_reports) as token_reports_count;

-- Create chain enum type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_type 
        WHERE typname = 'prod_chain_type'
    ) THEN
        CREATE TYPE prod_chain_type AS ENUM (
            'ethereum',
            'polygon',
            'arbitrum',
            'optimism',
            'base',
            'solana'
        );
    END IF;
END
$$;

-- Add chain column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'prod_token_opportunities' 
        AND column_name = 'chain'
    ) THEN
        ALTER TABLE prod_token_opportunities 
        ADD COLUMN chain prod_chain_type;
    END IF;
END
$$;

-- Verify data counts haven't changed
DO $$
DECLARE
    pre_counts RECORD;
    post_counts RECORD;
BEGIN
    SELECT * FROM pre_deployment_counts INTO pre_counts;
    
    SELECT 
        (SELECT COUNT(*) FROM prod_token_opportunities) as token_opportunities_count,
        (SELECT COUNT(*) FROM prod_alpha_reports) as alpha_reports_count,
        (SELECT COUNT(*) FROM prod_token_reports) as token_reports_count
    INTO post_counts;
    
    IF pre_counts.token_opportunities_count != post_counts.token_opportunities_count
        OR pre_counts.alpha_reports_count != post_counts.alpha_reports_count
        OR pre_counts.token_reports_count != post_counts.token_reports_count
    THEN
        RAISE EXCEPTION 'Data count mismatch after deployment';
    END IF;
END
$$;

-- Cleanup
DROP TABLE IF EXISTS pre_deployment_counts;
