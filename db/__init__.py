"""
Database package for DryAlpha project.
This module provides a clean interface to the database functionality
while maintaining backward compatibility with the original database.py.
"""

from .connection import get_engine, get_env_prefix
from .models.base import get_session
from .models.alpha import AlphaReportDB, TokenOpportunityDB
from .models.token import TokenDB
from .models.social import SocialMediaPostDB, TokenReportDB
from .operations.alpha import (
    create_alpha_report,
    get_alpha_report,
    get_all_alpha_reports
)
from .operations.social import (
    create_social_media_post,
    create_token_report
)
from .operations.token import get_or_create_token
from .utils import (
    create_db_and_tables,
    reset_db,
    tables_exist
)

# For backward compatibility
from sqlmodel import SQLModel

__all__ = [
    # Connection
    'get_engine',
    'get_env_prefix',
    'get_session',
    
    # Models
    'SQLModel',
    'AlphaReportDB',
    'TokenOpportunityDB',
    'SocialMediaPostDB',
    'TokenReportDB',
    'TokenDB',
    
    # Operations
    'create_alpha_report',
    'get_alpha_report',
    'get_all_alpha_reports',
    'create_social_media_post',
    'create_token_report',
    'get_or_create_token',
    
    # Utils
    'create_db_and_tables',
    'reset_db',
    'tables_exist'
]
