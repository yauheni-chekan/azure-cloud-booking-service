"""Groomer API endpoints."""

import logging
from decimal import Decimal

from fastapi import APIRouter, Query, status

from app.api.v1.schemas import GroomerResponse

router = APIRouter(prefix="/groomers", tags=["groomers"])
logger = logging.getLogger(__name__)


@router.get(
    "/search",
    summary="Search Groomers",
    description="Search for groomers by location, specialization, and minimum rating",
    response_description="List of matching groomers",
    response_model=list[GroomerResponse],
    status_code=status.HTTP_200_OK,
)
async def search_groomers(
    location: str | None = Query(None, description="Filter groomers by location", alias="location"),
    specialization: str | None = Query(
        None, description="Filter groomers by specialization type", alias="specialization"
    ),
    min_rating: Decimal | None = Query(
        None, ge=0, le=5, description="Minimum rating filter", alias="minRating"
    ),
) -> list[GroomerResponse]:
    """Search for groomers - returns mock data for now."""
    logger.info(
        "Searching groomers with filters - location: %s, specialization: %s, minRating: %s",
        location,
        specialization,
        min_rating,
    )

    # Mock groomer data
    mock_groomers = [
        {
            "groomer_id": "groomer-001",
            "name": "Sarah Johnson",
            "location": "New York",
            "specialization": "Dog",
            "rating": Decimal("4.8"),
        },
        {
            "groomer_id": "groomer-002",
            "name": "Mike Chen",
            "location": "Los Angeles",
            "specialization": "Cat",
            "rating": Decimal("4.5"),
        },
        {
            "groomer_id": "groomer-003",
            "name": "Emily Rodriguez",
            "location": "New York",
            "specialization": "Dog",
            "rating": Decimal("4.9"),
        },
        {
            "groomer_id": "groomer-004",
            "name": "David Kim",
            "location": "Chicago",
            "specialization": "Small Pets",
            "rating": Decimal("4.2"),
        },
        {
            "groomer_id": "groomer-005",
            "name": "Lisa Thompson",
            "location": "Los Angeles",
            "specialization": "Dog",
            "rating": Decimal("4.7"),
        },
        {
            "groomer_id": "groomer-006",
            "name": "James Wilson",
            "location": "Miami",
            "specialization": "Cat",
            "rating": Decimal("4.6"),
        },
        {
            "groomer_id": "groomer-007",
            "name": "Maria Garcia",
            "location": "New York",
            "specialization": "Small Pets",
            "rating": Decimal("4.4"),
        },
        {
            "groomer_id": "groomer-008",
            "name": "Robert Brown",
            "location": "Seattle",
            "specialization": "Dog",
            "rating": Decimal("4.3"),
        },
    ]

    # Apply filters
    filtered_groomers = mock_groomers

    if location:
        filtered_groomers = [
            g for g in filtered_groomers if g["location"].lower() == location.lower()
        ]

    if specialization:
        filtered_groomers = [
            g for g in filtered_groomers if g["specialization"].lower() == specialization.lower()
        ]

    if min_rating is not None:
        filtered_groomers = [g for g in filtered_groomers if g["rating"] >= min_rating]

    logger.info("Returning %d groomers matching filters", len(filtered_groomers))
    return [GroomerResponse.model_validate(groomer) for groomer in filtered_groomers]
