-- Function to notify about new token reports
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

-- Create trigger to execute function after insert
DROP TRIGGER IF EXISTS token_report_created ON dev_token_reports;
CREATE TRIGGER token_report_created
    AFTER INSERT ON dev_token_reports
    FOR EACH ROW
    EXECUTE FUNCTION notify_alpha_scout();
