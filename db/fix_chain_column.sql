-- Create Chain enum type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chain') THEN
        CREATE TYPE chain AS ENUM (
            'ethereum',
            'polygon',
            'arbitrum',
            'optimism',
            'base',
            'solana'
        );
    END IF;
END $$;

-- Add chain column to prod_token_opportunities if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'prod_token_opportunities' 
        AND column_name = 'chain'
    ) THEN
        -- First add the column as nullable
        ALTER TABLE prod_token_opportunities 
        ADD COLUMN chain chain;
        
        -- Then update existing rows with ethereum
        UPDATE prod_token_opportunities 
        SET chain = normalize_chain('ethereum');
        
        -- Finally make it not null
        ALTER TABLE prod_token_opportunities 
        ALTER COLUMN chain SET NOT NULL;
    END IF;
END $$;
