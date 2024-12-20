"""fix chain enum type

Revision ID: fix_chain_enum_type
Revises: fix_token_relationships
Create Date: 2024-12-20 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from agents.models import Chain

# revision identifiers, used by Alembic.
revision: str = 'fix_chain_enum_type'
down_revision: Union[str, None] = 'fix_token_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix chain column in both dev and prod tables
    for prefix in ['dev_', 'prod_']:
        table_name = f"{prefix}token_opportunities"
        enum_name = f'{prefix}chain_type'
        
        # Create connection
        conn = op.get_bind()
        
        # Check if enum type exists
        enum_exists = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = %s)",
            (enum_name,)
        ).scalar()
        
        if not enum_exists:
            # Create enum type
            enum_values = [e.value for e in Chain]
            op.execute(
                f'CREATE TYPE {enum_name} AS ENUM {str(tuple(enum_values))}'
            )
        
        # Check if column exists
        column_exists = conn.execute(
            """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = 'chain'
            )
            """,
            (table_name,)
        ).scalar()
        
        if not column_exists:
            # Add chain column
            op.add_column(
                table_name,
                sa.Column(
                    'chain',
                    sa.Enum(Chain, name=enum_name),
                    nullable=True
                )
            )


def downgrade() -> None:
    # Remove chain column from both dev and prod tables if they exist
    for prefix in ['dev_', 'prod_']:
        table_name = f"{prefix}token_opportunities"
        enum_name = f'{prefix}chain_type'
        
        conn = op.get_bind()
        
        # Check if column exists before trying to remove
        column_exists = conn.execute(
            """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = 'chain'
            )
            """,
            (table_name,)
        ).scalar()
        
        if column_exists:
            op.drop_column(table_name, 'chain')
        
        # Check if enum exists before trying to remove
        enum_exists = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = %s)",
            (enum_name,)
        ).scalar()
        
        if enum_exists:
            op.execute(f'DROP TYPE IF EXISTS {enum_name}')
