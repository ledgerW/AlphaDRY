"""
This module is maintained for backward compatibility.
All database functionality has been moved to the db package.
New code should import directly from the db package.
"""

from db import (
    # Connection
    get_engine,
    get_env_prefix,
    get_session,
    
    # Models
    SQLModel,
    AlphaReportDB,
    TokenOpportunityDB,
    SocialMediaPostDB,
    TokenReportDB,
    TokenDB,
    
    # Operations
    create_alpha_report,
    get_alpha_report,
    get_all_alpha_reports,
    create_social_media_post,
    create_token_report,
    get_or_create_token,
    
    # Utils
    create_db_and_tables,
    reset_db,
    tables_exist
)

# Re-export everything
__all__ = [
    'get_engine',
    'get_env_prefix',
    'get_session',
    'SQLModel',
    'AlphaReportDB',
    'TokenOpportunityDB',
    'SocialMediaPostDB',
    'TokenReportDB',
    'TokenDB',
    'create_alpha_report',
    'get_alpha_report',
    'get_all_alpha_reports',
    'create_social_media_post',
    'create_token_report',
    'get_or_create_token',
    'create_db_and_tables',
    'reset_db',
    'tables_exist'
]

if __name__ == "__main__":
    create_db_and_tables()
