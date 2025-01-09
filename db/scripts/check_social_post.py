import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_session
from sqlalchemy import text

def check_social_post():
    """Check most recent social media post and its relationships"""
    with get_session() as session:
        # Get most recent post
        post = session.execute(text("""
            SELECT id, post_id, author_username, original_timestamp, created_at
            FROM prod_social_media_posts
            ORDER BY created_at DESC
            LIMIT 1
        """)).first()
        
        if post:
            print(f"\nFound most recent post:")
            print(f"Post ID: {post.id}")
            print(f"Original Post ID: {post.post_id}")
            print(f"Author: {post.author_username}")
            print(f"Original Timestamp: {post.original_timestamp}")
            print(f"Created At: {post.created_at}")
            
            # Check for associated token report and verify relationship
            token_report = session.execute(text("""
                SELECT 
                    tr.id, 
                    tr.token_symbol, 
                    tr.token_chain, 
                    tr.token_address, 
                    tr.created_at,
                    smp.token_report_id,
                    CASE 
                        WHEN tr.id = smp.token_report_id THEN true 
                        ELSE false 
                    END as relationship_valid
                FROM prod_token_reports tr
                JOIN prod_social_media_posts smp ON tr.id = smp.token_report_id
                WHERE smp.id = :post_id
            """), {'post_id': post.id}).first()
            
            if token_report:
                print("\nAssociated Token Report:")
                print(f"Report ID: {token_report.id}")
                print(f"Token Symbol: {token_report.token_symbol}")
                print(f"Chain: {token_report.token_chain}")
                print(f"Address: {token_report.token_address}")
                print(f"Created At: {token_report.created_at}")
                print(f"Social Post token_report_id: {token_report.token_report_id}")
                print(f"Relationship Valid: {token_report.relationship_valid}")
            else:
                print("\nNo associated token report found")
                
            # Check for any locks on the post
            locks = session.execute(text("""
                SELECT relation::regclass::text as table_name,
                       locktype,
                       mode,
                       granted
                FROM pg_locks l
                JOIN pg_stat_activity s
                ON l.pid = s.pid
                WHERE relation::regclass::text = 'prod_social_media_posts'
                AND page = (SELECT (ctid::text::point)[0]::integer 
                          FROM prod_social_media_posts 
                          WHERE id = :post_id)
            """), {'post_id': post.id}).fetchall()
            
            if locks:
                print("\nActive locks on this post:")
                for lock in locks:
                    print(f"Type: {lock.locktype}")
                    print(f"Mode: {lock.mode}")
                    print(f"Granted: {lock.granted}")
            else:
                print("\nNo active locks found on this post")
                
        else:
            print("\nNo posts found in prod_social_media_posts")
            
            # Check if sequence exists
            curr_val = session.execute(text("""
                SELECT last_value 
                FROM prod_social_media_posts_id_seq
            """)).scalar()
            
            print(f"\nCurrent sequence value: {curr_val}")

if __name__ == "__main__":
    check_social_post()  # Check the most recent post
