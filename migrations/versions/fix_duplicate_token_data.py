"""fix duplicate token data

Revision ID: fix_duplicate_token_data
Revises: remove_unintended_constraints
Create Date: 2024-01-10 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from db.connection import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = 'fix_duplicate_token_data'
down_revision: Union[str, None] = 'remove_unintended_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    prefix = get_env_prefix()
    
    # First, let's identify and fix any duplicate tokens
    op.execute(text(f"""
    DO $$
    DECLARE
        duplicate_token RECORD;
        token_to_keep INTEGER;
    BEGIN
        -- Find any duplicates in the tokens table
        FOR duplicate_token IN (
            SELECT chain, address, array_agg(id) as ids, count(*) as cnt
            FROM {prefix}tokens
            WHERE chain = 'bsc' AND address = '0x8f0528ce5ef7b51152a59745befdd91d97091d2f'
            GROUP BY chain, address
            HAVING count(*) > 1
        ) LOOP
            -- Keep the token with the most relationships
            SELECT t.id INTO token_to_keep
            FROM {prefix}tokens t
            LEFT JOIN {prefix}token_reports tr ON tr.token_id = t.id
            LEFT JOIN {prefix}token_opportunities to2 ON to2.token_id = t.id
            WHERE t.chain = duplicate_token.chain 
            AND t.address = duplicate_token.address
            GROUP BY t.id
            ORDER BY COUNT(tr.id) + COUNT(to2.id) DESC, t.id
            LIMIT 1;

            -- Update relationships to point to the token we're keeping
            UPDATE {prefix}token_reports 
            SET token_id = token_to_keep
            WHERE token_id = ANY(duplicate_token.ids) 
            AND token_id != token_to_keep;

            UPDATE {prefix}token_opportunities 
            SET token_id = token_to_keep
            WHERE token_id = ANY(duplicate_token.ids)
            AND token_id != token_to_keep;

            -- Delete the duplicate tokens
            DELETE FROM {prefix}tokens 
            WHERE chain = duplicate_token.chain 
            AND address = duplicate_token.address
            AND id != token_to_keep;
        END LOOP;
    END $$;
    """))

    # Now verify no duplicates exist and recreate the unique constraint if needed
    op.execute(text(f"""
    DO $$
    BEGIN
        -- Drop the constraint if it exists (to be safe)
        ALTER TABLE {prefix}tokens 
        DROP CONSTRAINT IF EXISTS uq_{prefix}token_chain_address;

        -- Recreate the constraint
        ALTER TABLE {prefix}tokens
        ADD CONSTRAINT uq_{prefix}token_chain_address UNIQUE (chain, address);
    END $$;
    """))

def downgrade() -> None:
    # Cannot reliably restore duplicate data
    pass
