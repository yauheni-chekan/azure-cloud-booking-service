"""Health check schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


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
