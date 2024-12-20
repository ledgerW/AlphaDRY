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
