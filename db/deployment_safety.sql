-- Deployment Safety SQL
-- Run this in production to safely update database schema and triggers

-- 1. Create new trigger function (if not exists) that respects environment prefix
CREATE OR REPLACE FUNCTION notify_alpha_scout()
RETURNS TRIGGER AS $$
DECLARE
    payload json;
BEGIN
    -- Only proceed if mentions_purchasable_token is true
    IF NEW.mentions_purchasable_token = true THEN
        -- Create payload matching IsTokenReport format
        payload := json_build_object(
            'mentions_purchasable_token', NEW.mentions_purchasable_token,
            'token_symbol', NEW.token_symbol,
            'token_chain', NEW.token_chain,
            'token_address', NEW.token_address,
            'is_listed_on_dex', NEW.is_listed_on_dex,
            'trading_pairs', NEW.trading_pairs,
            'confidence_score', NEW.confidence_score,
            'reasoning', NEW.reasoning
        );

        -- Notify through Postgres NOTIFY
        PERFORM pg_notify('token_report_created', payload::text);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Safely drop existing trigger if it exists (using dynamic SQL to handle env prefix)
DO $$
DECLARE
    env_prefix text;
BEGIN
    -- Get environment prefix
    env_prefix := CASE 
        WHEN current_setting('app.deployment_env', TRUE) = 'production' THEN 'prod_'
        ELSE 'dev_'
    END;
    
    -- Drop existing trigger if it exists
    EXECUTE format('DROP TRIGGER IF EXISTS token_report_created ON %stoken_reports', env_prefix);
    
    -- Create new trigger with correct table prefix
    EXECUTE format('
        CREATE TRIGGER token_report_created
        AFTER INSERT ON %stoken_reports
        FOR EACH ROW
        EXECUTE FUNCTION notify_alpha_scout()', env_prefix);
END $$;

-- 3. Verify trigger creation
DO $$
DECLARE
    env_prefix text;
    trigger_exists boolean;
BEGIN
    -- Get environment prefix
    env_prefix := CASE 
        WHEN current_setting('app.deployment_env', TRUE) = 'production' THEN 'prod_'
        ELSE 'dev_'
    END;
    
    -- Check if trigger exists
    SELECT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'token_report_created'
        AND tgrelid = (env_prefix || 'token_reports')::regclass
    ) INTO trigger_exists;
    
    IF NOT trigger_exists THEN
        RAISE EXCEPTION 'Trigger creation failed';
    END IF;
END $$;
