-- Cleanup dangling foreign key references
DO $$
DECLARE
    table_name text;
    column_name text;
    referenced_table text;
    referenced_column text;
    cleanup_sql text;
BEGIN
    -- Handle both dev_ and prod_ tables
    FOR table_name, column_name, referenced_table, referenced_column IN
        WITH table_pairs AS (
            -- Dev tables
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND tc.table_name LIKE 'dev_%'
            UNION ALL
            -- Prod tables
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND tc.table_name LIKE 'prod_%'
        )
        SELECT * FROM table_pairs
    LOOP
        -- Build and execute cleanup SQL for each foreign key
        cleanup_sql := format('
            UPDATE %I
            SET %I = NULL
            WHERE %I IN (
                SELECT %I
                FROM %I t1
                LEFT JOIN %I t2 ON t1.%I = t2.%I
                WHERE t2.%I IS NULL
            )',
            table_name,
            column_name,
            column_name,
            table_name,
            referenced_table,
            column_name,
            referenced_column,
            referenced_column
        );
        
        EXECUTE cleanup_sql;
        
        RAISE NOTICE 'Cleaned up dangling references in %.% referencing %.%',
            table_name, column_name, referenced_table, referenced_column;
    END LOOP;
END
$$;
