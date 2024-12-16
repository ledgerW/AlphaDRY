from datetime import datetime
from sqlmodel import SQLModel
from sqlalchemy import text
from typing import Dict, Any
from .connection import get_engine, get_env_prefix, tables_exist
from .models.alpha import AlphaReportDB, TokenOpportunityDB
from .models.social import SocialMediaPostDB, TokenReportDB
from .models.warpcast import get_model
from .models.base import get_session
from agents.models import Chain

def populate_dev_data():
    """Populate development tables with dummy data."""
    if get_env_prefix() != "dev_":
        return

    # Create alpha reports and opportunities in a separate transaction
    with get_session() as session:
        try:
            # Create a sample alpha report
            report = AlphaReportDB(
                is_relevant=True,
                analysis="This is a sample analysis of market opportunities",
                message="Sample input message"
            )
            session.add(report)
            session.flush()

            # Create sample token opportunities
            opportunities = [
                TokenOpportunityDB(
                    name="Sample Token 1",
                    chain=Chain.BASE,
                    contract_address="0x1234567890abcdef",
                    market_cap=1000000.0,
                    community_score=8,
                    safety_score=7,
                    justification="Strong community and solid fundamentals",
                    sources=["source1.com", "source2.com"],
                    recommendation="Buy",
                    report_id=report.id
                ),
                TokenOpportunityDB(
                    name="Sample Token 2",
                    chain=Chain.SOLANA,
                    contract_address="SOL123456789",
                    market_cap=500000.0,
                    community_score=6,
                    safety_score=8,
                    justification="Innovative technology with growing adoption",
                    sources=["source3.com", "source4.com"],
                    recommendation="Hold",
                    report_id=report.id
                )
            ]
            for opp in opportunities:
                session.add(opp)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error creating alpha reports: {e}")

    # Create warpcast data in a separate transaction
    with get_session() as session:
        try:
            Model = get_model()
            warpcast = Model(
                raw_cast={"sample": "data"},
                hash="sample_hash_123",
                username="test_user",
                user_fid=12345,
                text="This is a sample warpcast message",
                timestamp=datetime.utcnow(),
                replies=5,
                reactions=10,
                recasts=3,
                pulled_from_user="sample_puller"
            )
            session.add(warpcast)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error creating warpcast: {e}")

    # Create sample social media post and token report
    with get_session() as session:
        try:
            # Create token report
            token_report = TokenReportDB(
                mentions_purchasable_token=True,
                token_symbol="SAMPLE",
                token_chain="ethereum",
                token_address="0xsample",
                is_listed_on_dex=True,
                trading_pairs=["SAMPLE/ETH", "SAMPLE/USDT"],
                confidence_score=8,
                reasoning="Sample token analysis"
            )
            session.add(token_report)
            session.flush()

            # Create social media post
            social_post = SocialMediaPostDB(
                source="warpcast",
                post_id="sample123",
                author_id="user123",
                author_username="test_user",
                author_display_name="Test User",
                text="Check out this new token $SAMPLE",
                original_timestamp=datetime.utcnow(),
                timestamp=datetime.utcnow(),
                reactions_count=5,
                replies_count=2,
                reposts_count=1,
                raw_data={"sample": "data"},
                token_report_id=token_report.id
            )
            session.add(social_post)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error creating sample social media data: {e}")

def reset_db():
    """Drop all tables and recreate them with fresh dummy data."""
    engine = get_engine()
    env_prefix = get_env_prefix()
    
    # Drop tables in correct order to handle dependencies
    with engine.begin() as conn:
        # Drop tables first
        conn.execute(text(f"DROP TABLE IF EXISTS {env_prefix}token_opportunities CASCADE"))
        conn.execute(text(f"DROP TABLE IF EXISTS {env_prefix}alpha_reports CASCADE"))
        conn.execute(text(f"DROP TABLE IF EXISTS {env_prefix}warpcasts CASCADE"))
        conn.execute(text(f"DROP TABLE IF EXISTS {env_prefix}social_media_posts CASCADE"))
        conn.execute(text(f"DROP TABLE IF EXISTS {env_prefix}token_reports CASCADE"))
        
        # Only drop the enum type if we're in dev environment
        if env_prefix == "dev_":
            conn.execute(text("DROP TYPE IF EXISTS chain CASCADE"))
    
    # Recreate tables
    SQLModel.metadata.create_all(engine)
    populate_dev_data()

def create_db_and_tables(force_reset: bool = False):
    """Create database tables if they don't exist and populate dev data."""
    if force_reset:
        reset_db()
    elif not tables_exist():
        engine = get_engine()
        try:
            SQLModel.metadata.create_all(engine)
            populate_dev_data()
        except Exception as e:
            print(f"Warning: Some tables already exist - {str(e)}")

if __name__ == "__main__":
    create_db_and_tables()
