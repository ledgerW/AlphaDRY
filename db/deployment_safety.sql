-- Simple backup verification
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'backup_%'
    ) THEN
        RAISE NOTICE 'Warning: No backup tables found. Consider taking a backup before proceeding.';
    END IF;
END
$$;

-- Check for existing prod tables and their relationships
DO $$
DECLARE
    missing_tables text[];
    table_issues text[];
BEGIN
    -- Check which required tables exist
    SELECT ARRAY_AGG(t) INTO missing_tables
    FROM unnest(ARRAY[
        'prod_tokens',
        'prod_token_reports',
        'prod_token_opportunities',
        'prod_alpha_reports',
        'prod_social_media_posts'
    ]) t
    WHERE NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = t
    );

    -- If any tables are missing, raise notice
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE NOTICE 'Missing tables: %', array_to_string(missing_tables, ', ');
    END IF;

    -- Check for chain type
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_type 
        WHERE typname = 'chain'
    ) THEN
        RAISE NOTICE 'Chain enum type is missing';
    END IF;
END
$$;
