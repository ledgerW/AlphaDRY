"""fix token address cases

Revision ID: fix_token_address_cases
Revises: merge_relationship_heads
Create Date: 2024-12-28 22:37:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_token_address_cases'
down_revision: Union[str, None] = ('merge_relationship_heads', 'lowercase_chain_values')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # First identify and delete duplicate Base token entries, keeping the one with most relationships
    op.execute("""
        WITH token_counts AS (
            SELECT t.id,
                   t.address,
                   t.chain,
                   COUNT(DISTINCT tr.id) + COUNT(DISTINCT to2.id) as rel_count,
                   ROW_NUMBER() OVER (PARTITION BY LOWER(t.address), t.chain ORDER BY COUNT(DISTINCT tr.id) + COUNT(DISTINCT to2.id) DESC, t.id) as rn
            FROM prod_tokens t
            LEFT JOIN prod_token_reports tr ON tr.token_id = t.id
            LEFT JOIN prod_token_opportunities to2 ON to2.token_id = t.id
            WHERE t.address LIKE '0x%'
            GROUP BY t.id, t.address, t.chain
        ),
        to_delete AS (
            SELECT id 
            FROM token_counts 
            WHERE rn > 1
        )
        DELETE FROM prod_tokens
        WHERE id IN (SELECT id FROM to_delete)
        RETURNING id;
    """)
    
    # Then update remaining Base token addresses to lowercase
    op.execute("""
        UPDATE prod_tokens
        SET address = LOWER(address)
        WHERE address LIKE '0x%';
    """)
    
    # Update any token opportunities that were pointing to deleted tokens
    op.execute("""
        UPDATE prod_token_opportunities o
        SET token_id = t.id
        FROM prod_tokens t
        WHERE o.contract_address LIKE '0x%'
        AND LOWER(o.contract_address) = t.address
        AND o.chain = t.chain
        AND o.token_id IS NULL;
    """)
    
    # Update any token reports that were pointing to deleted tokens
    op.execute("""
        UPDATE prod_token_reports r
        SET token_id = t.id
        FROM prod_tokens t
        WHERE r.token_address LIKE '0x%'
        AND LOWER(r.token_address) = t.address
        AND r.token_chain = t.chain
        AND r.token_id IS NULL;
    """)

def downgrade() -> None:
    # Cannot reliably restore original case of addresses
    pass
