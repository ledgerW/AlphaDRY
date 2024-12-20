"""convert chain to string

Revision ID: convert_chain_to_string
Revises: fix_chain_enum_type
Create Date: 2024-12-20 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'convert_chain_to_string'
down_revision: Union[str, None] = 'fix_chain_enum_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Convert chain column in both dev and prod tables
    for prefix in ['dev_', 'prod_']:
        table_name = f"{prefix}token_opportunities"
        enum_name = f'{prefix}chain_type'
        temp_column = 'chain_new'
        
        # Create connection
        conn = op.get_bind()
        
        # Add temporary string column
        op.add_column(
            table_name,
            sa.Column(temp_column, sa.String(), nullable=True)
        )
        
        # Copy data from enum column to string column, converting to lowercase
        op.execute(
            text(f'UPDATE {table_name} SET {temp_column} = LOWER(chain::text)')
        )
        
        # Drop the enum column
        op.drop_column(table_name, 'chain')
        
        # Rename temporary column to chain
        op.alter_column(
            table_name,
            temp_column,
            new_column_name='chain',
            nullable=False
        )
        
        # Drop the enum type
        op.execute(text(f'DROP TYPE IF EXISTS {enum_name}'))

def downgrade() -> None:
    # Convert chain column back to enum in both dev and prod tables
    for prefix in ['dev_', 'prod_']:
        table_name = f"{prefix}token_opportunities"
        enum_name = f'{prefix}chain_type'
        temp_column = 'chain_new'
        
        # Create the enum type
        op.execute(
            text(f"CREATE TYPE {enum_name} AS ENUM ('ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 'solana')")
        )
        
        # Add temporary enum column
        op.add_column(
            table_name,
            sa.Column(temp_column, postgresql.ENUM('ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 'solana', name=enum_name), nullable=True)
        )
        
        # Copy data from string column to enum column
        op.execute(
            text(f'UPDATE {table_name} SET {temp_column} = chain::text::{enum_name}')
        )
        
        # Drop the string column
        op.drop_column(table_name, 'chain')
        
        # Rename temporary column to chain
        op.alter_column(
            table_name,
            temp_column,
            new_column_name='chain',
            nullable=False
        )
