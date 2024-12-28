
"""lowercase chain values

Revision ID: lowercase_chain_values
Revises: fix_data_relationships
Create Date: 2024-12-28 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
from sqlalchemy import text
from db.connection import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = 'lowercase_chain_values'
down_revision: Union[str, None] = 'fix_data_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    prefix = get_env_prefix()
    # Update chain values to lowercase
    op.execute(
        text(f"""
        UPDATE {prefix}tokens 
        SET chain = LOWER(chain)
        WHERE chain != LOWER(chain)
        """)
    )

def downgrade() -> None:
    # No downgrade needed since we want to maintain lowercase values
    pass
