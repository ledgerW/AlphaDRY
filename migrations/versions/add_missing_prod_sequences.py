"""add_missing_prod_sequences

Revision ID: add_missing_prod_sequences
Revises: fix_alpha_reports_sequence
Create Date: 2024-12-31 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from database import get_env_prefix

# revision identifiers, used by Alembic.
revision: str = 'add_missing_prod_sequences'
down_revision: Union[str, None] = 'fix_alpha_reports_sequence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    prefix = get_env_prefix()
    print(f"Running migrations with {prefix} prefix")
    
    # Tables that need sequences
    tables = [
        'social_media_posts',
        'token_opportunities',
        'token_reports'
    ]
    
    for table in tables:
        # Create sequence if it doesn't exist
        op.execute(f'CREATE SEQUENCE IF NOT EXISTS "{prefix}{table}_id_seq"')
        
        # Set sequence as default and ownership
        op.execute(f"""
            ALTER TABLE {prefix}{table} ALTER COLUMN id SET DEFAULT nextval('{prefix}{table}_id_seq'::regclass);
            ALTER SEQUENCE {prefix}{table}_id_seq OWNED BY {prefix}{table}.id;
            SELECT setval('{prefix}{table}_id_seq', COALESCE((SELECT MAX(id) FROM {prefix}{table}), 0) + 1, false)
        """)

def downgrade() -> None:
    prefix = get_env_prefix()
    print(f"Rolling back migrations with {prefix} prefix")
    
    tables = [
        'social_media_posts',
        'token_opportunities',
        'token_reports'
    ]
    
    for table in tables:
        # Remove default value and sequence
        op.execute(f"""
            ALTER TABLE {prefix}{table} ALTER COLUMN id DROP DEFAULT;
            DROP SEQUENCE IF EXISTS "{prefix}{table}_id_seq";
        """)
