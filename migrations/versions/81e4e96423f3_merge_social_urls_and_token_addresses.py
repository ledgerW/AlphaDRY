"""merge_social_urls_and_token_addresses

Revision ID: 81e4e96423f3
Revises: lowercase_token_addresses
Create Date: 2025-01-06 18:30:32.757615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81e4e96423f3'
down_revision: Union[str, None] = 'lowercase_token_addresses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
