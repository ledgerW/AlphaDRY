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
    column_exists boolean;
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

    -- Check if token_id columns already exist
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'prod_token_reports' 
        AND column_name = 'token_id'
    ) INTO column_exists;
    
    IF column_exists THEN
        RAISE NOTICE 'WARNING: token_id column already exists in prod_token_reports';
    END IF;

    -- If prod_tokens is missing, we need to run the tokens migration
    IF array_length(missing_tables, 1) > 0 AND array_position(missing_tables, 'prod_tokens') IS NOT NULL THEN
        -- Create the tokens table directly to ensure it exists before running migrations
        CREATE TABLE IF NOT EXISTS prod_tokens (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            chain VARCHAR NOT NULL,
            address VARCHAR,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS ix_prod_tokens_symbol ON prod_tokens(symbol);
        CREATE INDEX IF NOT EXISTS ix_prod_tokens_address ON prod_tokens(address);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_prod_token_chain_address ON prod_tokens(chain, address);
        
        -- Reset alembic version to before the tokens migration
        UPDATE alembic_version SET version_num = 'convert_chain_to_string'
        WHERE version_num = 'fix_token_relationships';
        
        RAISE NOTICE 'Created prod_tokens table and reset migration version';
    END IF;
    
    -- Check alembic version
    RAISE NOTICE 'Current alembic version: %', (
        SELECT version_num FROM alembic_version
    );
END
$$;
