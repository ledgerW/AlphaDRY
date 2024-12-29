-- Function to create backup tables
CREATE OR REPLACE FUNCTION backup_prod_tables() RETURNS void AS $$
DECLARE
    table_name text;
    backup_timestamp text;
    backup_table text;
BEGIN
    -- Generate timestamp for backup tables
    backup_timestamp := to_char(current_timestamp, 'YYYYMMDD_HH24MI');
    
    -- Backup each production table
    FOR table_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'prod_%'
    LOOP
        backup_table := 'backup_' || table_name || '_' || backup_timestamp;
        EXECUTE format('CREATE TABLE %I AS SELECT * FROM %I', backup_table, table_name);
        RAISE NOTICE 'Created backup: %', backup_table;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to verify data integrity after migration
CREATE OR REPLACE FUNCTION verify_prod_data_integrity() RETURNS boolean AS $$
DECLARE
    table_name text;
    backup_table text;
    orig_count bigint;
    new_count bigint;
    data_preserved boolean := true;
    latest_backup_ts text;
BEGIN
    -- Get the most recent backup timestamp
    SELECT backup_ts INTO latest_backup_ts
    FROM (
        SELECT split_part(tablename, '_', 3) || '_' || split_part(tablename, '_', 4) as backup_ts
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'backup_prod_%'
        ORDER BY split_part(tablename, '_', 3) || '_' || split_part(tablename, '_', 4) DESC
        LIMIT 1
    ) latest_backup;
    
    -- Check each production table against its backup
    FOR table_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'prod_%'
    LOOP
        backup_table := 'backup_' || table_name || '_' || latest_backup_ts;
        
        -- Get row counts
        EXECUTE format('SELECT COUNT(*) FROM %I', table_name) INTO new_count;
        EXECUTE format('SELECT COUNT(*) FROM %I', backup_table) INTO orig_count;
        
        -- Check if data was preserved
        IF new_count < orig_count THEN
            RAISE WARNING 'Data loss detected in %: Original count: %, New count: %', 
                        table_name, orig_count, new_count;
            data_preserved := false;
        END IF;
    END LOOP;
    
    RETURN data_preserved;
END;
$$ LANGUAGE plpgsql;

-- Function to rollback if data loss is detected
CREATE OR REPLACE FUNCTION rollback_to_backup() RETURNS void AS $$
DECLARE
    table_name text;
    backup_table text;
    latest_backup_ts text;
BEGIN
    -- Get the most recent backup timestamp
    SELECT backup_ts INTO latest_backup_ts
    FROM (
        SELECT split_part(tablename, '_', 3) || '_' || split_part(tablename, '_', 4) as backup_ts
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'backup_prod_%'
        ORDER BY split_part(tablename, '_', 3) || '_' || split_part(tablename, '_', 4) DESC
        LIMIT 1
    ) latest_backup;
    
    -- Restore each production table from its backup
    FOR table_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'prod_%'
    LOOP
        backup_table := 'backup_' || table_name || '_' || latest_backup_ts;
        
        -- Restore data from backup
        EXECUTE format('TRUNCATE TABLE %I', table_name);
        EXECUTE format('INSERT INTO %I SELECT * FROM %I', table_name, backup_table);
        
        RAISE NOTICE 'Restored % from backup', table_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Pre-migration safety checks and backup
DO $$
BEGIN
    -- Create backups before any migration
    PERFORM backup_prod_tables();
    
    -- Verify existing prod tables and their relationships
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'prod_%'
    ) THEN
        RAISE NOTICE 'No production tables found to backup';
        RETURN;
    END IF;
END
$$;

-- Post-migration verification
DO $$
BEGIN
    -- Verify data integrity after migration
    IF NOT verify_prod_data_integrity() THEN
        RAISE WARNING 'Data integrity check failed. Initiating rollback...';
        PERFORM rollback_to_backup();
        RAISE EXCEPTION 'Migration rolled back due to data loss';
    END IF;
END
$$;

-- Cleanup old backups (keep last 3 days)
DO $$
DECLARE
    old_backup text;
BEGIN
    FOR old_backup IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'backup_prod_%'
        AND split_part(tablename, '_', 3)::date < current_date - interval '3 days'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I', old_backup);
        RAISE NOTICE 'Dropped old backup: %', old_backup;
    END LOOP;
END
$$;
