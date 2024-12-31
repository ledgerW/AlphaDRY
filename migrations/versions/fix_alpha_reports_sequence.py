"""fix_alpha_reports_sequence

Revision ID: fix_alpha_reports_sequence
Revises: merge_token_and_warpcast_heads
Create Date: 2024-12-31 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from database import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = 'fix_alpha_reports_sequence'
down_revision: Union[str, None] = ('merge_token_and_warpcast_heads',)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    prefix = get_env_prefix()
    print(f"Running migrations with {prefix} prefix")
    
    # Create sequence if it doesn't exist
    op.execute(f'CREATE SEQUENCE IF NOT EXISTS "{prefix}alpha_reports_id_seq"')
    
    # Set sequence as default and ownership
    op.execute(f"""
        ALTER TABLE {prefix}alpha_reports ALTER COLUMN id SET DEFAULT nextval('{prefix}alpha_reports_id_seq'::regclass);
        ALTER SEQUENCE {prefix}alpha_reports_id_seq OWNED BY {prefix}alpha_reports.id;
        SELECT setval('{prefix}alpha_reports_id_seq', COALESCE((SELECT MAX(id) FROM {prefix}alpha_reports), 0) + 1, false)
    """)

def downgrade() -> None:
    prefix = get_env_prefix()
    print(f"Rolling back migrations with {prefix} prefix")
    
    # Remove default value and sequence
    op.execute(f"""
        ALTER TABLE {prefix}alpha_reports ALTER COLUMN id DROP DEFAULT;
        DROP SEQUENCE IF EXISTS "{prefix}alpha_reports_id_seq";
    """)
