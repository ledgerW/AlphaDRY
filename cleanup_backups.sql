-- Drop all backup tables from today except the most recent ones
DO $$
DECLARE
    backup_date text := to_char(current_date, 'YYYYMMDD');
    table_prefix text;
    latest_time text;
    old_backup text;
BEGIN
    -- For each unique table prefix (e.g., backup_prod_alpha_reports, backup_prod_social_media_posts)
    FOR table_prefix IN
        SELECT DISTINCT substring(tablename from '^(backup_prod_[^_]+)_')
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE 'backup_prod_%'
    LOOP
        -- Get the latest timestamp for this prefix
        SELECT substring(tablename from '_(\d{4})$')
        INTO latest_time
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE table_prefix || '_%'
        ORDER BY tablename DESC
        LIMIT 1;

        -- Drop all older backups for this prefix
        FOR old_backup IN
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE table_prefix || '_%'
            AND tablename NOT LIKE table_prefix || '_' || backup_date || '_' || latest_time
        LOOP
            EXECUTE format('DROP TABLE IF EXISTS %I', old_backup);
            RAISE NOTICE 'Dropped backup: %', old_backup;
        END LOOP;
    END LOOP;
END
$$;
