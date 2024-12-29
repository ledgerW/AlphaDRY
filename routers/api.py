"""
API Router that combines query and generation endpoints.
Query endpoints are used to fetch data from the database.
Generation endpoints are used to generate new data using agents and chains.
"""

from fastapi import APIRouter
from .api_queries import router as query_router
from .api_generation import router as generation_router

# Create a combined router
router = APIRouter(prefix="/api")

# Include both routers
router.include_router(query_router)
router.include_router(generation_router)
