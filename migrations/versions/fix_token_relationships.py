"""fix token relationships

Revision ID: fix_token_relationships
Revises: drop_warpcasts_tables
Create Date: 2024-12-19 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_token_relationships'
down_revision: str = '5267b6833cce'  # Make this run after tokens table creation
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add foreign key constraint for both dev and prod
    for prefix in ['dev_', 'prod_']:
        try:
            # Try to create foreign key constraint
            op.create_foreign_key(
                f'{prefix}fk_token_opportunities_token_report',
                f'{prefix}token_opportunities',
                f'{prefix}token_reports',
                ['token_report_id'],
                ['id'],
                ondelete='SET NULL'  # Allow token reports to be deleted without affecting opportunities
            )
        except Exception as e:
            print(f"Warning: Could not create foreign key for {prefix}token_opportunities: {str(e)}")

def downgrade() -> None:
    # Remove the constraints
    for prefix in ['dev_', 'prod_']:
        try:
            op.drop_constraint(
                f'{prefix}fk_token_opportunities_token_report',
                f'{prefix}token_opportunities',
                type_='foreignkey'
            )
        except Exception as e:
            print(f"Warning: Could not drop foreign key for {prefix}token_opportunities: {str(e)}")
