-- Drop warpcasts tables and their backups
DO $$
DECLARE
    table_name text;
BEGIN
    -- Drop warpcasts tables if they exist
    FOR table_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE '%warpcasts'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', table_name);
        RAISE NOTICE 'Dropped table: %', table_name;
    END LOOP;
END
$$;
