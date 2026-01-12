"""API v1 package."""

from fastapi import APIRouter

from . import health
from .booking import router as booking_router
from .groomer import router as groomer_router
from .pet import router as pet_router
from .user import router as user_router

# Create the main v1 router
router = APIRouter()

# Include sub-routers
router.include_router(health.router, tags=["health"])
router.include_router(user_router, tags=["users"])
router.include_router(pet_router, tags=["pets"])
router.include_router(booking_router, tags=["bookings"])
router.include_router(groomer_router, tags=["groomers"])

__all__ = ["router"]
