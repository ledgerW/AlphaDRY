
-- First, convert all chain values to lowercase
UPDATE prod_tokens
SET chain = LOWER(chain);

-- Create temp table to track which tokens will be deleted and their replacements
CREATE TEMP TABLE token_mapping (
    old_token_id INT,
    new_token_id INT
);

-- Identify duplicates and decide which ones to keep (most recently created)
WITH duplicates AS (
    SELECT MIN(id) as keep_id,
           array_agg(id) as all_ids
    FROM prod_tokens
    WHERE address IS NOT NULL
    GROUP BY LOWER(chain), LOWER(address)
    HAVING COUNT(*) > 1
)
INSERT INTO token_mapping
SELECT unnest(all_ids) as old_token_id,
       keep_id as new_token_id
FROM duplicates
WHERE unnest(all_ids) != keep_id;

-- Update token reports to point to the surviving tokens
UPDATE prod_token_reports
SET token_id = tm.new_token_id
FROM token_mapping tm
WHERE token_id = tm.old_token_id;

-- Update token opportunities to point to the surviving tokens
UPDATE prod_token_opportunities
SET token_id = tm.new_token_id
FROM token_mapping tm
WHERE token_id = tm.old_token_id;

-- Delete the duplicate tokens
DELETE FROM prod_tokens t
USING token_mapping tm
WHERE t.id = tm.old_token_id;

-- Drop the temporary table
DROP TABLE token_mapping;

-- Verify results
SELECT chain, LOWER(address) as address, COUNT(*)
FROM prod_tokens
WHERE address IS NOT NULL
GROUP BY chain, LOWER(address)
HAVING COUNT(*) > 1;
