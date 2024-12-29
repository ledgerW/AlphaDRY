"""fix_data_relationships

Revision ID: fix_data_relationships
Revises: 5267b6833cce
Create Date: 2024-12-28 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from db.connection import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = 'fix_data_relationships'
down_revision: Union[str, None] = '5267b6833cce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    prefix = get_env_prefix()
    conn = op.get_bind()

    # First ensure token_id columns exist in reports and opportunities tables
    reports_token_id_exists = conn.execute(
        text(f"""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{prefix}token_reports'
            AND column_name = 'token_id'
        )::boolean
        """)
    ).scalar()

    opps_token_id_exists = conn.execute(
        text(f"""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{prefix}token_opportunities'
            AND column_name = 'token_id'
        )::boolean
        """)
    ).scalar()

    if not reports_token_id_exists:
        op.add_column(f'{prefix}token_reports', 
            sa.Column('token_id', sa.Integer, nullable=True)
        )

    if not opps_token_id_exists:
        op.add_column(f'{prefix}token_opportunities',
            sa.Column('token_id', sa.Integer, nullable=True)
        )

    # Then ensure the tokens table exists and has the right structure
    tokens_exists = conn.execute(
        text(f"""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{prefix}tokens'
        )::boolean
        """)
    ).scalar()

    if not tokens_exists:
        # Create tokens table if it doesn't exist
        op.create_table(
            f'{prefix}tokens',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('symbol', sa.String, nullable=False, index=True),
            sa.Column('name', sa.String, nullable=False),
            sa.Column('chain', sa.String, nullable=False),
            sa.Column('address', sa.String, nullable=True, index=True),
            sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
        )

    # First ensure all addresses are lowercase
    conn.execute(text(f"""
    UPDATE {prefix}token_reports
    SET token_address = LOWER(token_address)
    WHERE token_address IS NOT NULL;

    UPDATE {prefix}token_opportunities
    SET contract_address = LOWER(contract_address)
    WHERE contract_address IS NOT NULL;
    """))

    # Drop unique constraint if it exists, using a more robust approach
    conn.execute(text(f"""
    DO $$
    BEGIN
        -- Attempt to drop the constraint if it exists
        BEGIN
            ALTER TABLE {prefix}tokens
            DROP CONSTRAINT IF EXISTS uq_{prefix}token_chain_address;
        EXCEPTION WHEN undefined_table THEN
            -- Table doesn't exist yet, which is fine
            NULL;
        END;
    END $$;
    """))

    # Create tokens from reports
    conn.execute(text(f"""
    INSERT INTO {prefix}tokens (symbol, name, chain, address, created_at)
    SELECT DISTINCT ON (token_chain, LOWER(token_address))
        COALESCE(token_symbol, '') as symbol,
        COALESCE(token_symbol, '') as name,
        token_chain as chain,
        LOWER(token_address) as address,
        CURRENT_TIMESTAMP as created_at
    FROM {prefix}token_reports
    WHERE token_chain IS NOT NULL 
    AND token_address IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM {prefix}tokens t
        WHERE t.chain = token_chain
        AND t.address = LOWER(token_address)
    );
    """))

    # Create tokens from opportunities
    conn.execute(text(f"""
    INSERT INTO {prefix}tokens (symbol, name, chain, address, created_at)
    SELECT DISTINCT ON (chain, LOWER(contract_address))
        COALESCE(name, '') as symbol,
        COALESCE(name, '') as name,
        chain,
        LOWER(contract_address) as address,
        CURRENT_TIMESTAMP as created_at
    FROM {prefix}token_opportunities
    WHERE chain IS NOT NULL 
    AND contract_address IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM {prefix}tokens t
        WHERE t.chain = chain
        AND t.address = LOWER(contract_address)
    );
    """))

    # Update relationships with tokens
    conn.execute(text(f"""
    UPDATE {prefix}token_reports r
    SET token_id = t.id
    FROM {prefix}tokens t
    WHERE r.token_chain = t.chain 
    AND LOWER(r.token_address) = t.address
    AND r.token_chain IS NOT NULL 
    AND r.token_address IS NOT NULL
    AND r.token_id IS NULL;

    UPDATE {prefix}token_opportunities o
    SET token_id = t.id
    FROM {prefix}tokens t
    WHERE o.chain = t.chain 
    AND LOWER(o.contract_address) = t.address
    AND o.chain IS NOT NULL 
    AND o.contract_address IS NOT NULL
    AND o.token_id IS NULL;
    """))

    # Note: Constraint management moved to remove_unintended_constraints migration

    # Now add foreign key constraints if they don't exist
    fk_reports_exists = conn.execute(
        text(f"""
        SELECT COUNT(1) FROM information_schema.table_constraints
        WHERE table_schema = 'public'
        AND table_name = '{prefix}token_reports'
        AND constraint_name = 'fk_{prefix}token_reports_token'
        """)
    ).scalar()
    
    fk_opps_exists = conn.execute(
        text(f"""
        SELECT COUNT(1) FROM information_schema.table_constraints
        WHERE table_schema = 'public'
        AND table_name = '{prefix}token_opportunities'
        AND constraint_name = 'fk_{prefix}token_opportunities_token'
        """)
    ).scalar()

    if not fk_reports_exists:
        op.create_foreign_key(
            f'fk_{prefix}token_reports_token',
            f'{prefix}token_reports',
            f'{prefix}tokens',
            ['token_id'],
            ['id'],
            ondelete='SET NULL'
        )

    if not fk_opps_exists:
        op.create_foreign_key(
            f'fk_{prefix}token_opportunities_token',
            f'{prefix}token_opportunities',
            f'{prefix}tokens',
            ['token_id'],
            ['id'],
            ondelete='SET NULL'
        )

def downgrade() -> None:
    prefix = get_env_prefix()
    conn = op.get_bind()
    
    # Drop foreign key constraints if they exist
    fk_reports_exists = conn.execute(
        text(f"""
        SELECT COUNT(1) FROM information_schema.table_constraints
        WHERE table_schema = 'public'
        AND table_name = '{prefix}token_reports'
        AND constraint_name = 'fk_{prefix}token_reports_token'
        """)
    ).scalar()
    
    fk_opps_exists = conn.execute(
        text(f"""
        SELECT COUNT(1) FROM information_schema.table_constraints
        WHERE table_schema = 'public'
        AND table_name = '{prefix}token_opportunities'
        AND constraint_name = 'fk_{prefix}token_opportunities_token'
        """)
    ).scalar()

    if fk_reports_exists:
        op.drop_constraint(
            f'fk_{prefix}token_reports_token',
            f'{prefix}token_reports',
            type_='foreignkey'
        )

    if fk_opps_exists:
        op.drop_constraint(
            f'fk_{prefix}token_opportunities_token',
            f'{prefix}token_opportunities',
            type_='foreignkey'
        )

    # Clear token_id references
    conn.execute(text(f"""
    UPDATE {prefix}token_reports SET token_id = NULL;
    UPDATE {prefix}token_opportunities SET token_id = NULL;
    """))
