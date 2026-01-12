"""Health check endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(
        ...,
        description="Health status of the service",
        examples=["healthy"],
    )
    service: str = Field(
        ...,
        description="Service name",
        examples=["azure-cloud-booking-service"],
    )
    version: str = Field(
        ...,
        description="Service version",
        examples=["0.1.0"],
    )
    timestamp: datetime = Field(
        ...,
        description="Current server timestamp in UTC",
    )


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
