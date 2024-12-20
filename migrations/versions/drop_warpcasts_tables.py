"""drop warpcasts tables

Revision ID: drop_warpcasts_tables
Create Date: 2024-12-19
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'drop_warpcasts_tables'
down_revision = '0507e8573ab9'  # Points to the previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Create tables for both dev and prod environments
    for prefix in ['dev_', 'prod_']:
        # First create the warpcasts table to ensure it exists
        op.create_table(f'{prefix}warpcasts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('raw_cast', sa.JSON(), nullable=True),
            sa.Column('hash', sa.String(), nullable=True),
            sa.Column('username', sa.String(), nullable=True),
            sa.Column('user_fid', sa.Integer(), nullable=True),
            sa.Column('text', sa.String(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('replies', sa.Integer(), nullable=True),
            sa.Column('reactions', sa.Integer(), nullable=True),
            sa.Column('recasts', sa.Integer(), nullable=True),
            sa.Column('pulled_from_user', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

def downgrade():
    # Drop tables for both dev and prod environments
    for prefix in ['dev_', 'prod_']:
        op.drop_table(f'{prefix}warpcasts')
