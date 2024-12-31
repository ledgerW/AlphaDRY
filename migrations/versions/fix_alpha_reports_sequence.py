"""fix_alpha_reports_sequence

Revision ID: fix_alpha_reports_sequence
Revises: 084ce25df2a2
Create Date: 2024-12-31 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_alpha_reports_sequence'
down_revision: Union[str, None] = ('084ce25df2a2',)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create sequence
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'prod_alpha_reports_id_seq') THEN
                CREATE SEQUENCE prod_alpha_reports_id_seq;
            END IF;
        END $$;
    """)
    
    # Set sequence ownership and default
    op.execute("""
        ALTER TABLE prod_alpha_reports ALTER COLUMN id SET DEFAULT nextval('prod_alpha_reports_id_seq');
        ALTER SEQUENCE prod_alpha_reports_id_seq OWNED BY prod_alpha_reports.id;
    """)
    
    # Initialize sequence value
    op.execute("""
        SELECT setval('prod_alpha_reports_id_seq', COALESCE((SELECT MAX(id) FROM prod_alpha_reports), 0) + 1, false);
    """)

def downgrade() -> None:
    # Remove default value and sequence
    op.execute("""
        ALTER TABLE prod_alpha_reports ALTER COLUMN id DROP DEFAULT;
        DROP SEQUENCE IF EXISTS prod_alpha_reports_id_seq;
    """)
