-- Check if tables exist and their structure
SELECT table_name, column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name IN ('prod_token_reports', 'prod_token_opportunities', 'prod_tokens')
ORDER BY table_name, ordinal_position;

-- Check sample data from token_reports
SELECT symbol, chain, address 
FROM prod_token_reports 
LIMIT 5;

-- Check sample data from token_opportunities
SELECT symbol, chain, address 
FROM prod_token_opportunities 
LIMIT 5;
