"""API v1 package."""

from fastapi import APIRouter

from . import health

# Create the main v1 router
router = APIRouter()

# Include sub-routers
router.include_router(health.router, tags=["health"])

__all__ = ["router"]
