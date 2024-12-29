"""merge_all_heads

Revision ID: 084ce25df2a2
Revises: lowercase_chain_values, merge_relationship_heads, remove_unintended_constraints
Create Date: 2024-12-29 16:53:23.340795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '084ce25df2a2'
down_revision: Union[str, None] = ('lowercase_chain_values', 'merge_relationship_heads', 'remove_unintended_constraints')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
