
import asyncio
from datetime import datetime
from routers.api_models import SocialMediaInput
from routers.api_generation import analyze_social_post

async def test_analyze():
    # Create a test social media input
    test_input = SocialMediaInput(
        text="Check out $SNEGEN on Solana! SNGNZYxdKvH4ZuVGZTtBVHDhTGEBhXtQJeqoJKBqEYj",
        source="warpcast",
        author_id="test_user",
        author_username="test_user",
        author_display_name="Test User",
        post_id="test_123",
        original_timestamp=datetime.utcnow(),
        reactions_count=5,
        replies_count=2,
        reposts_count=1
    )
    
    # Test the function
    try:
        result = await analyze_social_post(test_input)
        print("Analysis result:", result)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_analyze())
