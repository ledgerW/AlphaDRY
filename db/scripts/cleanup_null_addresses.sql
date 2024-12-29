-- Delete tokens with NULL addresses and return the deleted records for verification
DELETE FROM prod_tokens 
WHERE address IS NULL 
RETURNING id, chain, address, created_at;
