"""remove unintended constraints

Revision ID: remove_unintended_constraints
Revises: fix_data_relationships
Create Date: 2024-01-10 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from db.connection import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = 'remove_unintended_constraints'
down_revision: Union[str, None] = 'fix_data_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    prefix = get_env_prefix()  # This will return either 'dev_' or 'prod_'
    
    # First check if there are any unintended unique constraints
    op.execute(text(f"""
    DO $$
    DECLARE
        r record;
    BEGIN
        -- Drop any unintended unique constraints on token_reports
        FOR r IN (
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = 'public'
            AND tc.table_name = '{prefix}token_reports'
            AND tc.constraint_type = 'UNIQUE'
            AND kcu.column_name IN ('token_chain', 'token_address')
        ) LOOP
            EXECUTE 'ALTER TABLE {prefix}token_reports DROP CONSTRAINT ' || quote_ident(r.constraint_name);
        END LOOP;

        -- Drop any unintended unique constraints on token_opportunities
        FOR r IN (
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = 'public'
            AND tc.table_name = '{prefix}token_opportunities'
            AND tc.constraint_type = 'UNIQUE'
            AND kcu.column_name IN ('chain', 'contract_address')
        ) LOOP
            EXECUTE 'ALTER TABLE {prefix}token_opportunities DROP CONSTRAINT ' || quote_ident(r.constraint_name);
        END LOOP;
    END $$;
    """))

    # Ensure the tokens table has its intended unique constraint
    op.execute(text(f"""
    DO $$
    BEGIN
        -- First try to drop the constraint if it exists
        BEGIN
            ALTER TABLE {prefix}tokens
            DROP CONSTRAINT IF EXISTS uq_{prefix}token_chain_address;
        EXCEPTION WHEN undefined_table THEN
            NULL;
        END;

        -- Now add the constraint back
        BEGIN
            ALTER TABLE {prefix}tokens
            ADD CONSTRAINT uq_{prefix}token_chain_address UNIQUE (chain, address);
        EXCEPTION WHEN duplicate_table THEN
            -- Constraint already exists, which is fine
            NULL;
        END;
    END $$;
    """))

def downgrade() -> None:
    # We don't want to recreate any unintended constraints
    pass
