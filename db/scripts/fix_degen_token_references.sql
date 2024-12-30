-- Update DEGEN token references to point to the correct token ID
DO $$
BEGIN
    -- Update token reports for DEGEN to point to the correct token
    UPDATE prod_token_reports
    SET token_id = 13
    WHERE token_id = 25
    AND token_symbol = 'DEGEN'
    AND token_chain = 'Base';
    
    RAISE NOTICE 'Updated DEGEN token references in prod_token_reports';
END
$$;
