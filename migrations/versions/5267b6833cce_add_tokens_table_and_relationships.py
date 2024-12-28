"""add_tokens_table_and_relationships

Revision ID: 5267b6833cce
Revises: convert_chain_to_string
Create Date: 2024-12-27 17:14:22.806843

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint, text
from db.connection import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = '5267b6833cce'
down_revision: Union[str, None] = 'convert_chain_to_string'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    prefix = get_env_prefix()
    conn = op.get_bind()
    
    # Check if tokens table exists
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
            Column('id', Integer, primary_key=True),
            Column('symbol', String, nullable=False, index=True),
            Column('name', String, nullable=False),
            Column('chain', String, nullable=False),
            Column('address', String, nullable=True, index=True),
            Column('created_at', DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            UniqueConstraint('chain', 'address', name=f'uq_{prefix}token_chain_address')
        )

    # Check if token_id columns exist
    token_reports_has_token_id = conn.execute(
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
    
    token_opps_has_token_id = conn.execute(
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

    # Add token_id columns if they don't exist
    if not token_reports_has_token_id:
        op.add_column(
            f'{prefix}token_reports',
            Column('token_id', Integer, nullable=True)
        )
    
    if not token_opps_has_token_id:
        op.add_column(
            f'{prefix}token_opportunities',
            Column('token_id', Integer, nullable=True)
        )

    # Check if foreign key constraints exist
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

    # Add foreign key constraints if they don't exist
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
    
    # Check if token_id columns exist before dropping
    token_reports_has_token_id = conn.execute(
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
    
    token_opps_has_token_id = conn.execute(
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

    if token_opps_has_token_id:
        op.drop_column(f'{prefix}token_opportunities', 'token_id')
    
    if token_reports_has_token_id:
        op.drop_column(f'{prefix}token_reports', 'token_id')
    
    # Check if tokens table exists before dropping
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
    
    if tokens_exists:
        op.drop_table(f'{prefix}tokens')
