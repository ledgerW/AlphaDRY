"""add chain column to token opportunities

Revision ID: 0507e8573ab9
Revises: 
Create Date: 2024-12-19 16:18:35.267690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from agents.models import Chain

# revision identifiers, used by Alembic.
revision: str = '0507e8573ab9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add chain column to both dev and prod tables if they exist
    for prefix in ['dev_', 'prod_']:
        table_name = f"{prefix}token_opportunities"
        
        # Check if table exists before trying to add column
        if op.get_bind().dialect.has_table(op.get_bind(), table_name):
            op.add_column(
                table_name,
                sa.Column(
                    'chain',
                    sa.Enum(Chain, name=f'{prefix}chain_type'),
                    nullable=True
                )
            )


def downgrade() -> None:
    # Remove chain column from both dev and prod tables if they exist
    for prefix in ['dev_', 'prod_']:
        table_name = f"{prefix}token_opportunities"
        
        # Check if table exists before trying to remove column
        if op.get_bind().dialect.has_table(op.get_bind(), table_name):
            op.drop_column(table_name, 'chain')
            op.execute(f'DROP TYPE IF EXISTS {prefix}chain_type')
