"""Health check endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.api.v1.schemas import HealthResponse
from app.config import settings

router = APIRouter()


@router.get(
    "/health",
    summary="Health Check",
    description="Check the health status of the service",
    response_description="Service health information",
)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns the current health status of the service along with
    service metadata and timestamp.

    :return: HealthResponse with service status information
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
    )
