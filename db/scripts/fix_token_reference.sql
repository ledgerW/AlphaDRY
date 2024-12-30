-- Fix dangling token references for both dev and prod environments
DO $$
BEGIN
    -- Clean up prod_token_reports references
    UPDATE prod_token_reports
    SET token_id = NULL
    WHERE token_id IS NOT NULL
    AND token_id NOT IN (SELECT id FROM prod_tokens);
    
    RAISE NOTICE 'Cleaned up dangling references in prod_token_reports';
    
    -- Clean up prod_token_opportunities references
    UPDATE prod_token_opportunities
    SET token_id = NULL
    WHERE token_id IS NOT NULL
    AND token_id NOT IN (SELECT id FROM prod_tokens);
    
    RAISE NOTICE 'Cleaned up dangling references in prod_token_opportunities';
    
    -- Clean up dev_token_reports references
    UPDATE dev_token_reports
    SET token_id = NULL
    WHERE token_id IS NOT NULL
    AND token_id NOT IN (SELECT id FROM dev_tokens);
    
    RAISE NOTICE 'Cleaned up dangling references in dev_token_reports';
    
    -- Clean up dev_token_opportunities references
    UPDATE dev_token_opportunities
    SET token_id = NULL
    WHERE token_id IS NOT NULL
    AND token_id NOT IN (SELECT id FROM dev_tokens);
    
    RAISE NOTICE 'Cleaned up dangling references in dev_token_opportunities';
END
$$;

-- Verify no dangling references remain
DO $$
DECLARE
    dangling_count integer;
BEGIN
    -- Check prod_token_reports
    SELECT COUNT(*) INTO dangling_count
    FROM prod_token_reports
    WHERE token_id IS NOT NULL
    AND token_id NOT IN (SELECT id FROM prod_tokens);
    
    IF dangling_count > 0 THEN
        RAISE EXCEPTION 'Found % dangling references in prod_token_reports', dangling_count;
    END IF;
    
    -- Check prod_token_opportunities
    SELECT COUNT(*) INTO dangling_count
    FROM prod_token_opportunities
    WHERE token_id IS NOT NULL
    AND token_id NOT IN (SELECT id FROM prod_tokens);
    
    IF dangling_count > 0 THEN
        RAISE EXCEPTION 'Found % dangling references in prod_token_opportunities', dangling_count;
    END IF;
    
    -- Check dev_token_reports
    SELECT COUNT(*) INTO dangling_count
    FROM dev_token_reports
    WHERE token_id IS NOT NULL
    AND token_id NOT IN (SELECT id FROM dev_tokens);
    
    IF dangling_count > 0 THEN
        RAISE EXCEPTION 'Found % dangling references in dev_token_reports', dangling_count;
    END IF;
    
    -- Check dev_token_opportunities
    SELECT COUNT(*) INTO dangling_count
    FROM dev_token_opportunities
    WHERE token_id IS NOT NULL
    AND token_id NOT IN (SELECT id FROM dev_tokens);
    
    IF dangling_count > 0 THEN
        RAISE EXCEPTION 'Found % dangling references in dev_token_opportunities', dangling_count;
    END IF;
    
    RAISE NOTICE 'All token references verified clean';
END
$$;
