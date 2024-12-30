-- Fix dangling token references
DO $$
DECLARE
    table_name text;
    fk_column text;
BEGIN
    -- Find and fix all foreign key references to prod_tokens
    FOR table_name, fk_column IN
        SELECT
            tc.table_name,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        AND ccu.table_name = 'prod_tokens'
    LOOP
        -- Set dangling references to NULL
        EXECUTE format('
            UPDATE %I
            SET %I = NULL
            WHERE %I NOT IN (SELECT id FROM prod_tokens)
            AND %I IS NOT NULL',
            table_name,
            fk_column,
            fk_column,
            fk_column
        );
        
        RAISE NOTICE 'Cleaned up dangling references in %.% referencing prod_tokens',
            table_name, fk_column;
    END LOOP;
END
$$;
