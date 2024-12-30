-- Fix dangling token references for both dev and prod environments
DO $$
DECLARE
    prefix text;
BEGIN
    -- Handle both dev and prod environments
    FOR prefix IN ARRAY ARRAY['dev_', 'prod_'] LOOP
        -- Clean up token_reports references if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = prefix || 'token_reports'
        ) THEN
            EXECUTE format('
                UPDATE %s%s
                SET token_id = NULL
                WHERE token_id IS NOT NULL
                AND token_id NOT IN (SELECT id FROM %stokens)',
                prefix, 'token_reports', prefix
            );
            RAISE NOTICE 'Cleaned up dangling references in %stoken_reports', prefix;
        END IF;
        
        -- Clean up token_opportunities references if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = prefix || 'token_opportunities'
        ) THEN
            EXECUTE format('
                UPDATE %s%s
                SET token_id = NULL
                WHERE token_id IS NOT NULL
                AND token_id NOT IN (SELECT id FROM %stokens)',
                prefix, 'token_opportunities', prefix
            );
            RAISE NOTICE 'Cleaned up dangling references in %stoken_opportunities', prefix;
        END IF;
        
        -- Clean up social_media_posts references if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = prefix || 'social_media_posts'
        ) THEN
            EXECUTE format('
                UPDATE %s%s
                SET token_id = NULL
                WHERE token_id IS NOT NULL
                AND token_id NOT IN (SELECT id FROM %stokens)',
                prefix, 'social_media_posts', prefix
            );
            RAISE NOTICE 'Cleaned up dangling references in %ssocial_media_posts', prefix;
        END IF;
        
        -- Clean up alpha_reports references if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = prefix || 'alpha_reports'
        ) THEN
            EXECUTE format('
                UPDATE %s%s
                SET token_id = NULL
                WHERE token_id IS NOT NULL
                AND token_id NOT IN (SELECT id FROM %stokens)',
                prefix, 'alpha_reports', prefix
            );
            RAISE NOTICE 'Cleaned up dangling references in %salpha_reports', prefix;
        END IF;
    END LOOP;
END
$$;

-- Verify no dangling references remain
DO $$
DECLARE
    prefix text;
    dangling_count integer;
BEGIN
    FOR prefix IN ARRAY ARRAY['dev_', 'prod_'] LOOP
        -- Check token_reports if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = prefix || 'token_reports'
        ) THEN
            EXECUTE format('
                SELECT COUNT(*) FROM %s%s
                WHERE token_id IS NOT NULL
                AND token_id NOT IN (SELECT id FROM %stokens)',
                prefix, 'token_reports', prefix
            ) INTO dangling_count;
            
            IF dangling_count > 0 THEN
                RAISE EXCEPTION 'Found % dangling references in %stoken_reports', dangling_count, prefix;
            END IF;
        END IF;
        
        -- Check token_opportunities if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = prefix || 'token_opportunities'
        ) THEN
            EXECUTE format('
                SELECT COUNT(*) FROM %s%s
                WHERE token_id IS NOT NULL
                AND token_id NOT IN (SELECT id FROM %stokens)',
                prefix, 'token_opportunities', prefix
            ) INTO dangling_count;
            
            IF dangling_count > 0 THEN
                RAISE EXCEPTION 'Found % dangling references in %stoken_opportunities', dangling_count, prefix;
            END IF;
        END IF;
        
        -- Check social_media_posts if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = prefix || 'social_media_posts'
        ) THEN
            EXECUTE format('
                SELECT COUNT(*) FROM %s%s
                WHERE token_id IS NOT NULL
                AND token_id NOT IN (SELECT id FROM %stokens)',
                prefix, 'social_media_posts', prefix
            ) INTO dangling_count;
            
            IF dangling_count > 0 THEN
                RAISE EXCEPTION 'Found % dangling references in %ssocial_media_posts', dangling_count, prefix;
            END IF;
        END IF;
        
        -- Check alpha_reports if table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = prefix || 'alpha_reports'
        ) THEN
            EXECUTE format('
                SELECT COUNT(*) FROM %s%s
                WHERE token_id IS NOT NULL
                AND token_id NOT IN (SELECT id FROM %stokens)',
                prefix, 'alpha_reports', prefix
            ) INTO dangling_count;
            
            IF dangling_count > 0 THEN
                RAISE EXCEPTION 'Found % dangling references in %salpha_reports', dangling_count, prefix;
            END IF;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'All token references verified clean';
END
$$;
