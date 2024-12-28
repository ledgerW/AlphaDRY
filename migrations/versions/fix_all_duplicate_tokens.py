"""fix all duplicate tokens

Revision ID: fix_all_duplicate_tokens
Revises: fix_duplicate_token_data
Create Date: 2024-01-10 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from db.connection import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = 'fix_all_duplicate_tokens'
down_revision: Union[str, None] = 'fix_duplicate_token_data'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    prefix = get_env_prefix()

    # First find and handle duplicates
    op.execute(text(f"""
        WITH duplicates AS (
            SELECT chain, address, array_agg(id) as ids
            FROM {prefix}tokens
            WHERE address IS NOT NULL
            GROUP BY chain, address
            HAVING count(*) > 1
        ),
        tokens_to_keep AS (
            SELECT DISTINCT ON (t.chain, t.address) 
                t.id as keep_id,
                t.chain,
                t.address,
                d.ids as duplicate_ids
            FROM {prefix}tokens t
            JOIN duplicates d ON t.chain = d.chain AND t.address = d.address
            LEFT JOIN {prefix}token_reports tr ON tr.token_id = t.id
            LEFT JOIN {prefix}token_opportunities to2 ON to2.token_id = t.id
            GROUP BY t.id, t.chain, t.address, t.created_at, d.ids
            ORDER BY t.chain, t.address, COUNT(tr.id) + COUNT(to2.id) DESC, t.created_at ASC
        )
        UPDATE {prefix}token_reports tr
        SET token_id = tk.keep_id
        FROM tokens_to_keep tk
        WHERE tr.token_id = ANY(tk.duplicate_ids)
        AND tr.token_id != tk.keep_id;
    """))

    # Update token opportunities
    op.execute(text(f"""
        WITH duplicates AS (
            SELECT chain, address, array_agg(id) as ids
            FROM {prefix}tokens
            WHERE address IS NOT NULL
            GROUP BY chain, address
            HAVING count(*) > 1
        ),
        tokens_to_keep AS (
            SELECT DISTINCT ON (t.chain, t.address) 
                t.id as keep_id,
                t.chain,
                t.address,
                d.ids as duplicate_ids
            FROM {prefix}tokens t
            JOIN duplicates d ON t.chain = d.chain AND t.address = d.address
            LEFT JOIN {prefix}token_reports tr ON tr.token_id = t.id
            LEFT JOIN {prefix}token_opportunities to2 ON to2.token_id = t.id
            GROUP BY t.id, t.chain, t.address, t.created_at, d.ids
            ORDER BY t.chain, t.address, COUNT(tr.id) + COUNT(to2.id) DESC, t.created_at ASC
        )
        UPDATE {prefix}token_opportunities to2
        SET token_id = tk.keep_id
        FROM tokens_to_keep tk
        WHERE to2.token_id = ANY(tk.duplicate_ids)
        AND to2.token_id != tk.keep_id;
    """))

    # Delete duplicate tokens
    op.execute(text(f"""
        WITH duplicates AS (
            SELECT chain, address, array_agg(id) as ids
            FROM {prefix}tokens
            WHERE address IS NOT NULL
            GROUP BY chain, address
            HAVING count(*) > 1
        ),
        tokens_to_keep AS (
            SELECT DISTINCT ON (t.chain, t.address) 
                t.id as keep_id,
                t.chain,
                t.address,
                d.ids as duplicate_ids
            FROM {prefix}tokens t
            JOIN duplicates d ON t.chain = d.chain AND t.address = d.address
            LEFT JOIN {prefix}token_reports tr ON tr.token_id = t.id
            LEFT JOIN {prefix}token_opportunities to2 ON to2.token_id = t.id
            GROUP BY t.id, t.chain, t.address, t.created_at, d.ids
            ORDER BY t.chain, t.address, COUNT(tr.id) + COUNT(to2.id) DESC, t.created_at ASC
        )
        DELETE FROM {prefix}tokens t
        USING tokens_to_keep tk
        WHERE t.chain = tk.chain 
        AND t.address = tk.address
        AND t.id != tk.keep_id;
    """))

    # Ensure addresses are lowercase
    op.execute(text(f"""
        UPDATE {prefix}tokens
        SET address = LOWER(address)
        WHERE address IS NOT NULL
        AND address != LOWER(address);
    """))

    # Drop and recreate unique constraint
    op.execute(text(f"""
        ALTER TABLE {prefix}tokens 
        DROP CONSTRAINT IF EXISTS uq_{prefix}token_chain_address;
    """))

    op.execute(text(f"""
        ALTER TABLE {prefix}tokens
        ADD CONSTRAINT uq_{prefix}token_chain_address UNIQUE (chain, address);
    """))

    # Drop any unique constraints on token_reports and token_opportunities
    op.execute(text(f"""
        SELECT format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I;',
            tc.table_name,
            tc.constraint_name
        )
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public'
        AND tc.table_name IN ('{prefix}token_reports', '{prefix}token_opportunities')
        AND tc.constraint_type = 'UNIQUE'
        AND kcu.column_name IN ('token_chain', 'token_address', 'chain', 'contract_address');
    """))

def downgrade() -> None:
    # Cannot reliably restore duplicate data
    pass
