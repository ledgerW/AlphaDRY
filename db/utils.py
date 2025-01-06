from datetime import datetime, timedelta
from sqlmodel import SQLModel
from sqlalchemy import text
from typing import Dict, Any, List
from .connection import get_engine, get_env_prefix, tables_exist
from .models.alpha import AlphaReportDB, TokenOpportunityDB
from .models.token import TokenDB
from .models.social import SocialMediaPostDB, TokenReportDB
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
            
            # Create SNEGEN token with DEX screener data (on Solana)
            snegen_token = session.query(TokenDB).filter(
                TokenDB.chain == Chain.SOLANA,
                TokenDB.address == "SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj"
            ).first()
            if not snegen_token:
                snegen_token = TokenDB(
                    symbol="SNEGEN",
                    name="SNEGEN Token",
                    chain=Chain.SOLANA,
                    address="SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj",
                    website_url="https://snegen.xyz",
                    twitter_url="https://twitter.com/snegen_xyz",
                    telegram_url="https://t.me/snegen_community",
                    image_url="https://raw.githubusercontent.com/snegen/brand/main/logo.png",
                    token_created_at=datetime.utcnow() - timedelta(days=30)  # Created 30 days ago
                )
                session.add(snegen_token)

            token_2 = session.query(TokenDB).filter(
                TokenDB.chain == Chain.SOLANA,
                TokenDB.address == "SOL123456789"
            ).first()
            if not token_2:
                token_2 = TokenDB(
                    symbol="SOL1",
                    name="Solana Token 1",
                    chain=Chain.SOLANA,
                    address="SOL123456789"
                )
                session.add(token_2)
            
            session.flush()  # Get IDs for the tokens

            # Create sample token reports
            token_report_1 = TokenReportDB(
                mentions_purchasable_token=True,
                token_symbol="BASE1",
                token_chain="base",
                token_address="0x1234567890abcdef",
                is_listed_on_dex=True,
                trading_pairs=["BASE1/ETH", "BASE1/USDC"],
                confidence_score=8,
                reasoning="Sample Base token analysis",
                token_id=token_1.id
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
                reasoning="Sample Solana token analysis",
                token_id=token_2.id
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
                    token_report_id=token_report_1.id,  # Link to token report
                    token_id=token_1.id  # Link to token
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
                    token_report_id=token_report_2.id,  # Link to token report
                    token_id=token_2.id  # Link to token
                )
            ]
            for opp in opportunities:
                session.add(opp)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error creating alpha reports: {e}")

    # Create sample social media posts and token reports
    with get_session() as session:
        try:
            # Create or get sample token
            sample_token = session.query(TokenDB).filter(
                TokenDB.chain == Chain.ETHEREUM,
                TokenDB.address == "0xsample"
            ).first()
            if not sample_token:
                sample_token = TokenDB(
                    symbol="SAMPLE",
                    name="Sample Token",
                    chain=Chain.ETHEREUM,
                    address="0xsample"
                )
                session.add(sample_token)
                session.flush()

            # Create sample token report
            sample_token_report = TokenReportDB(
                mentions_purchasable_token=True,
                token_symbol="SAMPLE",
                token_chain="ethereum",
                token_address="0xsample",
                is_listed_on_dex=True,
                trading_pairs=["SAMPLE/ETH", "SAMPLE/USDT"],
                confidence_score=8,
                reasoning="Sample token analysis",
                token_id=sample_token.id
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

            # Create or get SNEGEN token
            snegen_token = session.query(TokenDB).filter(
                TokenDB.chain == Chain.SOLANA,
                TokenDB.address == "SNGNZYxdKvH4ZuVGZTtBVHDhXtQJeqoJKBqEYj"
            ).first()
            if not snegen_token:
                snegen_token = TokenDB(
                    symbol="SNEGEN",
                    name="SNEGEN",
                    chain=Chain.SOLANA,
                    address="SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj"
                )
                session.add(snegen_token)
                session.flush()

            # Create SNEGEN token report
            snegen_token_report = TokenReportDB(
                mentions_purchasable_token=True,
                token_symbol="SNEGEN",
                token_chain="solana",
                token_address="SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj",
                is_listed_on_dex=True,
                trading_pairs=["SNEGEN/SOL", "SNEGEN/USDC"],
                confidence_score=9,
                reasoning="New Solana meme token with strong community engagement and growing trading volume",
                token_id=snegen_token.id
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
                token_report_id=snegen_token_report.id,
                token_id=snegen_token.id
            )
            session.add(snegen_opportunity)
            
            # Create 3 additional social media posts with token reports for SNEGEN
            base_time = datetime.utcnow()
            for i in range(3):
                post_time = base_time - timedelta(hours=i)
                # Create additional social media posts
                additional_post = SocialMediaPostDB(
                    source="warpcast",
                    post_id=f"snegen_test_{i}_{post_time.timestamp()}",
                    author_id=f"test_author_{i}",
                    author_username=f"snegen_fan_{i}",
                    author_display_name=f"SNEGEN Fan {i+1}",
                    text=f"$SNEGEN is revolutionizing Solana's AI ecosystem! Test post {i+1} #SolanaAI",
                    original_timestamp=post_time,
                    timestamp=post_time,
                    reactions_count=15 + i,
                    replies_count=7 + i,
                    reposts_count=4 + i,
                    raw_data={"platform": "warpcast", "verified": True}
                )
                session.add(additional_post)
                session.flush()
                
                # Create token reports for each post
                additional_report = TokenReportDB(
                    mentions_purchasable_token=True,
                    token_symbol="SNEGEN",
                    token_chain="solana",
                    token_address="SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj",
                    is_listed_on_dex=True,
                    trading_pairs=["SNEGEN/SOL", "SNEGEN/USDC"],
                    confidence_score=85 + i,
                    reasoning=f"Test report {i+1}: SNEGEN continues to show strong growth in the Solana AI ecosystem",
                    token_id=snegen_token.id,
                    social_media_post=additional_post
                )
                session.add(additional_report)
            
            # Create an additional token opportunity for SNEGEN
            additional_opportunity = TokenOpportunityDB(
                name="SNEGEN AI Integration",
                chain=Chain.SOLANA,
                contract_address="SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj",
                market_cap=800000.0,
                community_score=9,
                safety_score=8,
                justification="SNEGEN is expanding its AI capabilities with new integrations and partnerships",
                sources=["warpcast.com", "solscan.io"],
                recommendation="Strong Buy",
                token_id=snegen_token.id
            )
            session.add(additional_opportunity)
            
            # Create HIGHER token
            higher_token = TokenDB(
                symbol="HIGHER",
                name="HIGHER Token",
                chain=Chain.BASE,
                address="0x0578d8A44db98B23BF096A382e016e29a5Ce0ffe",
                created_at=datetime.utcnow()
            )
            session.add(higher_token)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error creating sample social media data: {e}")

def reset_db():
    """Drop all tables and recreate them with fresh dummy data."""
    engine = get_engine()
    env_prefix = get_env_prefix()
    
    print(f"Current environment prefix: {env_prefix}")
    
    if env_prefix != "dev_":
        raise ValueError("reset_db() can only be used in development environment")
    
    try:
        if "prod_" in str(engine.url):
            raise ValueError("CRITICAL SAFETY ERROR: Attempting to reset database with production connection string")
            
        print("Starting database reset...")
        # Drop tables in correct order to handle dependencies
        with engine.begin() as conn:
            print("Checking for active connections...")
            # Only terminate connections to dev tables
            result = conn.execute(text("""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = current_database()
                AND pid != pg_backend_pid()
                AND state != 'idle'
                AND application_name = 'dev'
            """))
            print(f"Terminated {result.rowcount} development connections")
            
            # Get all dev tables
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                AND tablename LIKE 'dev_%'
            """))
            dev_tables = [row[0] for row in result.fetchall()]
            print(f"Found dev tables: {dev_tables}")
            
            # Drop dev tables in correct order
            tables_to_drop = [
                "dev_token_opportunities",
                "dev_alpha_reports",
                "dev_social_media_posts",
                "dev_token_reports",
                "dev_tokens"
            ]
            
            for table in tables_to_drop:
                if table in dev_tables:
                    print(f"Dropping table {table}")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            print("Dropping enum type...")
            # Drop the enum type
            conn.execute(text("DROP TYPE IF EXISTS chain CASCADE"))
        
        print("Recreating tables...")
        # Recreate tables
        SQLModel.metadata.create_all(engine)
        print("Populating development data...")
        populate_dev_data()
        print("Database reset complete")
    except Exception as e:
        print(f"Error resetting database: {e}")
        raise

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
