"""Groomer API endpoints."""

import logging

import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas import GroomerResponse
from app.config import settings

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
    location: str | None = Query(None, description="Filter groomers by location"),
    specialization: str | None = Query(None, description="Filter groomers by specialization type"),
    min_rating: float | None = Query(
        None, ge=0, le=5, description="Minimum rating filter", alias="minRating"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
) -> list[GroomerResponse]:
    """Search for groomers by calling the external groomer service."""
    logger.info(
        "Searching groomers with filters - location: %s, specialization: %s, minRating: %s",
        location,
        specialization,
        min_rating,
    )

    # Build query parameters for the groomer service
    params = {
        "skip": skip,
        "limit": limit,
    }
    if location:
        params["location"] = location
    if specialization:
        params["specialization"] = specialization
    if min_rating is not None:
        params["min_rating"] = min_rating

    # Call the external groomer service
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            groomer_service_url = f"{settings.groomer_service_url}/api/v1/groomers"
            logger.info("Calling groomer service: %s with params: %s", groomer_service_url, params)

            response = await client.get(groomer_service_url, params=params)
            response.raise_for_status()
            groomers_data = response.json()

            return [GroomerResponse.model_validate(groomer) for groomer in groomers_data]

        except httpx.TimeoutException:
            logger.error("Timeout when calling groomer service")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Groomer service request timed out",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Error calling groomer service: %s - %s",
                e.response.status_code,
                e.response.text,
            )
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Groomer service endpoint not found",
                )
            elif e.response.status_code >= 500:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Groomer service is unavailable",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error from groomer service: {e.response.text}",
                )
        except Exception as e:
            logger.exception("Unexpected error calling groomer service: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to communicate with groomer service",
            )
