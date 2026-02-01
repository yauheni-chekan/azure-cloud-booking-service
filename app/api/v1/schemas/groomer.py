"""Groomer schemas."""

from pydantic import BaseModel, ConfigDict, Field


class GroomerResponse(BaseModel):
    """Schema for groomer response from external service (GroomerRead)."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    groomer_id: str = Field(..., description="Unique groomer identifier")
    first_name: str = Field(..., description="Groomer's first name")
    last_name: str = Field(..., description="Groomer's last name")
    location: str = Field(..., description="Groomer location")
    specialization: str | None = Field(None, description="Groomer specialization type")
    status: str = Field(..., description="Groomer status")
    rating: float = Field(..., description="Groomer rating")
    review_count: int = Field(..., description="Number of reviews")
    complaint_count: int = Field(..., description="Number of complaints")
    total_bookings_count: int = Field(..., description="Total number of bookings")
