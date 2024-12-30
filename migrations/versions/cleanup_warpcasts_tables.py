"""cleanup warpcasts tables

Revision ID: cleanup_warpcasts_tables
Create Date: 2024-12-30
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'cleanup_warpcasts_tables'
down_revision = 'drop_warpcasts_tables'  # Points to the previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Drop tables for both dev and prod environments
    for prefix in ['dev_', 'prod_']:
        op.drop_table(f'{prefix}warpcasts')

    # Drop any backup tables
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        DECLARE
            backup_table text;
        BEGIN
            FOR backup_table IN 
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename LIKE 'backup_prod_warpcasts_%'
            LOOP
                EXECUTE format('DROP TABLE IF EXISTS %I', backup_table);
                RAISE NOTICE 'Dropped backup table: %', backup_table;
            END LOOP;
        END
        $$;
    """))

def downgrade():
    # Recreate tables for both dev and prod environments if needed to rollback
    for prefix in ['dev_', 'prod_']:
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
