"""fix chain enum type

Revision ID: fix_chain_enum_type
Revises: fix_token_relationships
Create Date: 2024-12-20 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fix_chain_enum_type'
down_revision: Union[str, None] = 'drop_warpcasts_tables'  # Make this the first migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define enum values to match Chain enum in agents/models.py
# These must be lowercase to match the enum values
CHAIN_VALUES = ('ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 'solana')

def upgrade() -> None:
    # Fix chain column in both dev and prod tables
    for prefix in ['dev_', 'prod_']:
        table_name = f"{prefix}token_opportunities"
        enum_name = f'{prefix}chain_type'
        
        # Create connection
        conn = op.get_bind()
        
        # Check if enum type exists
        enum_exists = conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :enum_name)"),
            {"enum_name": enum_name}
        ).scalar()
        
        if not enum_exists:
            # Create enum type with lowercase values
            op.execute(
                text(f'CREATE TYPE {enum_name} AS ENUM {str(CHAIN_VALUES)}')
            )
        else:
            # If enum exists, try to update it to include all values
            # First get current values
            current_values = conn.execute(
                text("""
                    SELECT e.enumlabel
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = :enum_name
                """),
                {"enum_name": enum_name}
            ).scalars().all()
            
            # Add any missing values
            for value in CHAIN_VALUES:
                if value not in current_values:
                    op.execute(
                        text(f"ALTER TYPE {enum_name} ADD VALUE '{value}'")
                    )
        
        # Check if column exists
        column_exists = conn.execute(
            text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = :table_name AND column_name = 'chain'
            )
            """),
            {"table_name": table_name}
        ).scalar()
        
        if not column_exists:
            # Add chain column
            op.add_column(
                table_name,
                sa.Column(
                    'chain',
                    postgresql.ENUM(*CHAIN_VALUES, name=enum_name),
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
            text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = :table_name AND column_name = 'chain'
            )
            """),
            {"table_name": table_name}
        ).scalar()
        
        if column_exists:
            op.drop_column(table_name, 'chain')
        
        # Check if enum exists before trying to remove
        enum_exists = conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :enum_name)"),
            {"enum_name": enum_name}
        ).scalar()
        
        if enum_exists:
            op.execute(text(f'DROP TYPE IF EXISTS {enum_name}'))
