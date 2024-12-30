"""merge token and warpcast heads

Revision ID: merge_token_and_warpcast_heads
Revises: cleanup_warpcasts_tables, 084ce25df2a2
Create Date: 2024-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_token_and_warpcast_heads'
down_revision: Union[str, None] = ('cleanup_warpcasts_tables', '084ce25df2a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
