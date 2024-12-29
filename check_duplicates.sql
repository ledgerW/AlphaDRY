-- Check for any remaining duplicates in tokens table
SELECT chain, address, COUNT(*) as count
FROM prod_tokens
GROUP BY chain, address
HAVING COUNT(*) > 1;

-- Check for duplicates in token reports
SELECT token_chain, token_address, COUNT(*) as count
FROM prod_token_reports
GROUP BY token_chain, token_address
HAVING COUNT(*) > 1;

-- Check for duplicates in token opportunities
SELECT chain, contract_address, COUNT(*) as count
FROM prod_token_opportunities
WHERE contract_address IS NOT NULL
GROUP BY chain, contract_address
HAVING COUNT(*) > 1;
