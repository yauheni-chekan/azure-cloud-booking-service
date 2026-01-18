"""Groomer schemas."""

from decimal import Decimal

from pydantic import BaseModel, Field


class GroomerResponse(BaseModel):
    """Schema for groomer response from external service."""

    groomer_id: str = Field(..., description="Unique groomer identifier")
    name: str = Field(..., description="Groomer name")
    location: str = Field(..., description="Groomer location")
    specialization: str | None = Field(None, description="Groomer specialization type")
    rating: Decimal | None = Field(None, description="Groomer rating")

    class ConfigDict:
        """Pydantic configuration."""

        from_attributes = True
        extra = "allow"  # Allow extra fields from external service
