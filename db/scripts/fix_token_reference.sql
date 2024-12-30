-- Fix dangling token references for both dev and prod environments
DO $$
DECLARE
    prefix text;
BEGIN
    -- Handle both dev and prod environments
    FOR prefix IN ('dev_', 'prod_') LOOP
        -- Clean up token_reports references
        EXECUTE format('
            UPDATE %Itoken_reports
            SET token_id = NULL
            WHERE token_id IS NOT NULL
            AND token_id NOT IN (SELECT id FROM %Itokens)',
            prefix, prefix
        );
        
        RAISE NOTICE 'Cleaned up dangling references in %token_reports', prefix;
        
        -- Clean up token_opportunities references
        EXECUTE format('
            UPDATE %Itoken_opportunities
            SET token_id = NULL
            WHERE token_id IS NOT NULL
            AND token_id NOT IN (SELECT id FROM %Itokens)',
            prefix, prefix
        );
        
        RAISE NOTICE 'Cleaned up dangling references in %token_opportunities', prefix;
        
        -- Clean up any other tables that might reference tokens
        EXECUTE format('
            UPDATE %Isocial_media_posts
            SET token_id = NULL
            WHERE token_id IS NOT NULL
            AND token_id NOT IN (SELECT id FROM %Itokens)',
            prefix, prefix
        );
        
        RAISE NOTICE 'Cleaned up dangling references in %social_media_posts', prefix;
        
        -- Clean up alpha_reports references if they exist
        EXECUTE format('
            UPDATE %Ialpha_reports
            SET token_id = NULL
            WHERE token_id IS NOT NULL
            AND token_id NOT IN (SELECT id FROM %Itokens)',
            prefix, prefix
        );
        
        RAISE NOTICE 'Cleaned up dangling references in %alpha_reports', prefix;
    END LOOP;
END
$$;

-- Verify no dangling references remain
DO $$
DECLARE
    prefix text;
    dangling_count integer;
BEGIN
    FOR prefix IN ('dev_', 'prod_') LOOP
        -- Check token_reports
        EXECUTE format('
            SELECT COUNT(*) FROM %Itoken_reports
            WHERE token_id IS NOT NULL
            AND token_id NOT IN (SELECT id FROM %Itokens)',
            prefix, prefix
        ) INTO dangling_count;
        
        IF dangling_count > 0 THEN
            RAISE EXCEPTION 'Found % dangling references in %token_reports', dangling_count, prefix;
        END IF;
        
        -- Check token_opportunities
        EXECUTE format('
            SELECT COUNT(*) FROM %Itoken_opportunities
            WHERE token_id IS NOT NULL
            AND token_id NOT IN (SELECT id FROM %Itokens)',
            prefix, prefix
        ) INTO dangling_count;
        
        IF dangling_count > 0 THEN
            RAISE EXCEPTION 'Found % dangling references in %token_opportunities', dangling_count, prefix;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'All token references verified clean';
END
$$;
