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

            # Create sample token reports first
            token_report_1 = TokenReportDB(
                mentions_purchasable_token=True,
                token_symbol="BASE1",
                token_chain="base",
                token_address="0x1234567890abcdef",
                is_listed_on_dex=True,
                trading_pairs=["BASE1/ETH", "BASE1/USDC"],
                confidence_score=8,
                reasoning="Sample Base token analysis"
            )
            session.add(token_report_1)

            token_report_2 = TokenReportDB(
                mentions_purchasable_token=True,
                token_symbol="SOL1",
                token_chain="solana",
                token_address="SOL123456789",
                is_listed_on_dex=True,
                trading_pairs=["SOL1/SOL", "SOL1/USDC"],
                confidence_score=7,
                reasoning="Sample Solana token analysis"
            )
            session.add(token_report_2)
            session.flush()  # Flush to get IDs

            # Create social media posts for each token report
            social_post_1 = SocialMediaPostDB(
                source="warpcast",
                post_id="base123",
                author_id="user456",
                author_username="base_enthusiast",
                author_display_name="Base Enthusiast",
                text="Check out this new Base token $BASE1 0x1234567890abcdef",
                original_timestamp=datetime.utcnow(),
                timestamp=datetime.utcnow(),
                reactions_count=15,
                replies_count=5,
                reposts_count=3,
                raw_data={"platform": "warpcast"},
                token_report_id=token_report_1.id
            )
            session.add(social_post_1)

            social_post_2 = SocialMediaPostDB(
                source="warpcast",
                post_id="sol123",
                author_id="user789",
                author_username="sol_enthusiast",
                author_display_name="Solana Enthusiast",
                text="New Solana gem $SOL1 SOL123456789",
                original_timestamp=datetime.utcnow(),
                timestamp=datetime.utcnow(),
                reactions_count=20,
                replies_count=8,
                reposts_count=5,
                raw_data={"platform": "warpcast"},
                token_report_id=token_report_2.id
            )
            session.add(social_post_2)

            # Create sample token opportunities with both relationships
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
                    report_id=report.id,
                    token_report_id=token_report_1.id  # Link to token report
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
                    report_id=report.id,
                    token_report_id=token_report_2.id  # Link to token report
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

    # Create sample social media posts and token reports
    with get_session() as session:
        try:
            # Create sample token report
            sample_token_report = TokenReportDB(
                mentions_purchasable_token=True,
                token_symbol="SAMPLE",
                token_chain="ethereum",
                token_address="0xsample",
                is_listed_on_dex=True,
                trading_pairs=["SAMPLE/ETH", "SAMPLE/USDT"],
                confidence_score=8,
                reasoning="Sample token analysis"
            )
            session.add(sample_token_report)
            session.flush()

            # Create sample social media post
            sample_social_post = SocialMediaPostDB(
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
                token_report_id=sample_token_report.id
            )
            session.add(sample_social_post)

            # Create SNEGEN token report
            snegen_token_report = TokenReportDB(
                mentions_purchasable_token=True,
                token_symbol="SNEGEN",
                token_chain="solana",
                token_address="SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj",
                is_listed_on_dex=True,
                trading_pairs=["SNEGEN/SOL", "SNEGEN/USDC"],
                confidence_score=9,
                reasoning="New Solana meme token with strong community engagement and growing trading volume"
            )
            session.add(snegen_token_report)
            session.flush()

            # Create SNEGEN social media post
            snegen_social_post = SocialMediaPostDB(
                source="warpcast",
                post_id="snegen_post_123",
                author_id="snegen_user",
                author_username="snegen_enthusiast",
                author_display_name="SNEGEN Enthusiast",
                text="$SNEGEN is taking off! The first meme token built for Solana's AI ecosystem. Already listed on multiple DEXes with growing liquidity. SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj",
                original_timestamp=datetime.utcnow(),
                timestamp=datetime.utcnow(),
                reactions_count=25,
                replies_count=12,
                reposts_count=8,
                raw_data={"platform": "warpcast", "verified": True},
                token_report_id=snegen_token_report.id
            )
            session.add(snegen_social_post)

            # Create SNEGEN alpha report
            snegen_report = AlphaReportDB(
                is_relevant=True,
                analysis="SNEGEN shows strong potential as the first meme token built for Solana's AI ecosystem. The token has gained significant traction in the Solana ecosystem, particularly among AI and meme token enthusiasts. With its growing liquidity and strong community engagement, SNEGEN represents an interesting opportunity in the intersection of AI and meme tokens on Solana.",
                message="Analysis of SNEGEN token opportunity",
                created_at=datetime.utcnow()
            )
            session.add(snegen_report)
            session.flush()

            # Add SNEGEN token opportunity linked to both alpha report and token report
            snegen_opportunity = TokenOpportunityDB(
                name="SNEGEN",
                chain=Chain.SOLANA,
                contract_address="SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj",
                market_cap=750000.0,
                community_score=8,
                safety_score=7,
                justification="First meme token focused on Solana's AI ecosystem with strong community growth. The project has shown impressive early traction with active trading on multiple DEXes and growing social media presence. Community engagement metrics are strong, and the unique positioning in the AI narrative space provides potential growth opportunities.",
                sources=["warpcast.com", "birdeye.so", "solscan.io"],
                recommendation="Buy",
                report_id=snegen_report.id,
                token_report_id=snegen_token_report.id
            )
            session.add(snegen_opportunity)
            
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
