
"""drop warpcasts tables

Revision ID: drop_warpcasts_tables
Create Date: 2024-12-19
"""
from alembic import op

def upgrade():
    op.drop_table('dev_warpcasts')
    op.drop_table('prod_warpcasts')

def downgrade():
    pass  # We don't need to recreate the tables
