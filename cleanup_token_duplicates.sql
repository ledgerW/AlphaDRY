-- Delete duplicate tokens, keeping only the most recently created one
WITH duplicates AS (
    SELECT LOWER(chain) as lchain, LOWER(address) as laddress, COUNT(*) 
    FROM prod_tokens 
    WHERE address IS NOT NULL 
    GROUP BY LOWER(chain), LOWER(address)
    HAVING COUNT(*) > 1
),
to_delete AS (
    SELECT t.id
    FROM prod_tokens t
    JOIN duplicates d ON LOWER(t.chain) = d.lchain AND LOWER(t.address) = d.laddress
    WHERE t.id NOT IN (
        -- Keep the most recently created token for each chain/address pair
        SELECT DISTINCT ON (LOWER(t2.chain), LOWER(t2.address)) t2.id
        FROM prod_tokens t2
        JOIN duplicates d2 ON LOWER(t2.chain) = d2.lchain AND LOWER(t2.address) = d2.laddress
        ORDER BY LOWER(t2.chain), LOWER(t2.address), t2.created_at DESC
    )
)
DELETE FROM prod_tokens 
WHERE id IN (SELECT id FROM to_delete)
RETURNING id, chain, address;
