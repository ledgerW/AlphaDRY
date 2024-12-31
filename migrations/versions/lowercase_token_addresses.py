"""lowercase token addresses

Revision ID: lowercase_token_addresses
Revises: lowercase_chain_values
Create Date: 2024-01-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'lowercase_token_addresses'
down_revision = 'lowercase_chain_values'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Convert all token addresses to lowercase across different tables
    op.execute(text("""
        -- Convert addresses in tokens table
        UPDATE tokens 
        SET address = LOWER(address) 
        WHERE address IS NOT NULL;
        
        -- Convert contract_addresses in token_opportunities table
        UPDATE token_opportunities 
        SET contract_address = LOWER(contract_address) 
        WHERE contract_address IS NOT NULL;
        
        -- Convert token_addresses in token_reports table
        UPDATE token_reports 
        SET token_address = LOWER(token_address) 
        WHERE token_address IS NOT NULL;
    """))

def downgrade() -> None:
    # No downgrade path needed since case conversion is one-way
    pass
