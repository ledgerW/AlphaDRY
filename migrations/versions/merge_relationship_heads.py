"""merge relationship heads

Revision ID: merge_relationship_heads
Revises: fix_data_relationships, fix_token_relationships
Create Date: 2024-01-05 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_relationship_heads'
down_revision: Union[str, Sequence[str]] = ('fix_data_relationships', 'fix_token_relationships')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass  # This migration just merges the heads

def downgrade() -> None:
    pass
