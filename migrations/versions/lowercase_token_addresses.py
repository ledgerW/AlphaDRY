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
down_revision = 'add_missing_prod_sequences'
branch_labels = None
depends_on = None

def upgrade() -> None:
    from database import get_env_prefix
    prefix = get_env_prefix()
    
    # Convert addresses to lowercase only for non-Solana chains
    # Update tokens table
    op.execute(text(f"""
        UPDATE {prefix}tokens t
        SET address = LOWER(address) 
        WHERE address IS NOT NULL 
        AND LOWER(t.chain) != 'solana';
    """))
    
    # Update token_opportunities table
    op.execute(text(f"""
        UPDATE {prefix}token_opportunities o
        SET contract_address = LOWER(contract_address) 
        WHERE contract_address IS NOT NULL 
        AND LOWER(o.chain) != 'solana';
    """))
    
    # Update token_reports table - join with tokens to get chain info
    op.execute(text(f"""
        UPDATE {prefix}token_reports r
        SET token_address = LOWER(token_address) 
        FROM {prefix}tokens t
        WHERE r.token_address IS NOT NULL 
        AND r.token_address = t.address
        AND LOWER(t.chain) != 'solana';
    """))

def downgrade() -> None:
    # No downgrade path needed since case conversion is one-way
    pass
