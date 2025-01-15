import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import get_session
from sqlalchemy import text

def fix_social_post_relationships():
    """Fix missing relationships between social media posts and token reports"""
    with get_session() as session:
        try:
            # Start transaction
            session.begin()
            
            # Find posts that have token reports but missing token_report_id
            results = session.execute(text("""
                SELECT smp.id as post_id,
                       smp.post_id as original_post_id,
                       tr.id as report_id
                FROM prod_social_media_posts smp
                JOIN prod_token_reports tr ON tr.id = (
                    SELECT tr2.id
                    FROM prod_token_reports tr2
                    JOIN prod_social_media_posts smp2 ON smp2.post_id = smp.post_id
                    WHERE smp2.token_report_id = tr2.id
                    ORDER BY tr2.created_at DESC
                    LIMIT 1
                )
                WHERE smp.token_report_id IS NULL
                ORDER BY tr.created_at DESC
            """)).fetchall()
            
            if not results:
                print("No orphaned relationships found")
                return
                
            print(f"Found {len(results)} posts with missing relationships")
            
            # Update each post with its token report ID
            for result in results:
                print(f"\nFixing relationship for post {result.original_post_id}")
                
                # Update the relationship using the post's database id
                session.execute(text("""
                    UPDATE prod_social_media_posts
                    SET token_report_id = :report_id
                    WHERE id = :post_id
                    RETURNING id, post_id, token_report_id
                """), {
                    'report_id': result.report_id,
                    'post_id': result.post_id
                })
                
                # Verify the update
                updated = session.execute(text("""
                    SELECT smp.id, 
                           smp.post_id,
                           smp.token_report_id,
                           tr.id as report_id
                    FROM prod_social_media_posts smp
                    JOIN prod_token_reports tr ON tr.id = smp.token_report_id
                    WHERE smp.id = :post_id
                """), {
                    'post_id': result.post_id
                }).first()
                
                if updated and updated.token_report_id == result.report_id:
                    print(f"Successfully updated post {updated.post_id} with token_report_id {updated.token_report_id}")
                else:
                    print(f"Failed to update post {result.original_post_id}")
                    session.rollback()
                    return
            
            # Commit all changes
            session.commit()
            print("\nSuccessfully fixed all relationships")
            
        except Exception as e:
            session.rollback()
            print(f"Error fixing relationships: {str(e)}")
            raise

if __name__ == "__main__":
    fix_social_post_relationships()
