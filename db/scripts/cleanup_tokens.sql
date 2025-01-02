
BEGIN;

-- Create temp table to track which tokens will be deleted and their replacements
CREATE TEMP TABLE token_mapping (
    old_token_id INT,
    new_token_id INT
);

-- Identify duplicates and map them to the most recently created token
WITH duplicates AS (
    SELECT DISTINCT ON (LOWER(chain), LOWER(address))
           id as keep_id,
           chain,
           address,
           created_at,
           ARRAY(
               SELECT t2.id 
               FROM prod_tokens t2 
               WHERE LOWER(t2.chain) = LOWER(t1.chain) 
               AND LOWER(t2.address) = LOWER(t1.address)
               AND t2.id != t1.id
           ) as ids_to_remove
    FROM prod_tokens t1
    WHERE address IS NOT NULL
    ORDER BY LOWER(chain), LOWER(address), created_at DESC
)
INSERT INTO token_mapping (old_token_id, new_token_id)
SELECT unnest(ids_to_remove), keep_id
FROM duplicates
WHERE array_length(ids_to_remove, 1) > 0;

-- Update relationships before deleting tokens
UPDATE prod_token_reports
SET token_id = tm.new_token_id
FROM token_mapping tm
WHERE token_id = tm.old_token_id;

UPDATE prod_token_opportunities
SET token_id = tm.new_token_id
FROM token_mapping tm
WHERE token_id = tm.old_token_id;

-- Delete the duplicate tokens
DELETE FROM prod_tokens t
USING token_mapping tm
WHERE t.id = tm.old_token_id;

-- Now safely convert remaining chain values to lowercase
UPDATE prod_tokens
SET chain = LOWER(chain);

DROP TABLE token_mapping;

-- Verify results
SELECT chain, LOWER(address) as address, COUNT(*)
FROM prod_tokens
WHERE address IS NOT NULL
GROUP BY chain, LOWER(address)
HAVING COUNT(*) > 1;

COMMIT;
