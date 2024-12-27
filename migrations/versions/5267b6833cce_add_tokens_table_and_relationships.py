"""add_tokens_table_and_relationships

Revision ID: 5267b6833cce
Revises: convert_chain_to_string
Create Date: 2024-12-27 17:14:22.806843

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from db.connection import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = '5267b6833cce'
down_revision: Union[str, None] = 'convert_chain_to_string'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    prefix = get_env_prefix()
    
    # Create tokens table
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

    # Add token_id to token_reports
    op.add_column(
        f'{prefix}token_reports',
        Column('token_id', Integer, ForeignKey(f'{prefix}tokens.id'), nullable=True)
    )
    
    # Add token_id to token_opportunities
    op.add_column(
        f'{prefix}token_opportunities',
        Column('token_id', Integer, ForeignKey(f'{prefix}tokens.id'), nullable=True)
    )


def downgrade() -> None:
    prefix = get_env_prefix()
    
    # Remove token_id from token_opportunities
    op.drop_column(f'{prefix}token_opportunities', 'token_id')
    
    # Remove token_id from token_reports
    op.drop_column(f'{prefix}token_reports', 'token_id')
    
    # Drop tokens table
    op.drop_table(f'{prefix}tokens')
