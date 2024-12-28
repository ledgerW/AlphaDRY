-- Check for any remaining duplicates in tokens table
SELECT chain, address, COUNT(*) as count
FROM dev_tokens
GROUP BY chain, address
HAVING COUNT(*) > 1;

-- Check the specific token that was causing issues
SELECT id, chain, address, symbol, name
FROM dev_tokens
WHERE chain = 'bsc' 
AND address = '0x8f0528ce5ef7b51152a59745befdd91d97091d2f';
