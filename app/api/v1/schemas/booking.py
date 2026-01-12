"""Booking schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from models import BookingStatus


class BookingResponse(BaseModel):
    """Schema for booking response."""

    booking_id: uuid.UUID = Field(..., description="Unique booking identifier")
    booking_date_time: datetime = Field(..., description="Appointment date and time")
    booking_status: str = Field(..., description="Booking status")
    groomer_id: uuid.UUID = Field(..., description="Assigned groomer identifier")
    user_id: uuid.UUID = Field(..., description="User identifier")
    pet_id: uuid.UUID = Field(..., description="Pet identifier")
    rating: Decimal | None = Field(None, description="Customer rating")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class BookingCreate(BaseModel):
    """Schema for creating a new booking."""

    pet_id: uuid.UUID = Field(..., description="Pet identifier for the booking")
    booking_date_time: datetime = Field(..., description="Appointment date and time")
    groomer_id: uuid.UUID = Field(..., description="Assigned groomer identifier")
    booking_status: BookingStatus | None = Field(
        None, description="Booking status (defaults to pending)"
    )
    rating: Decimal | None = Field(
        None, ge=0, le=5, description="Customer rating (0-5)"
    )


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""

    booking_date_time: datetime | None = Field(
        None, description="Appointment date and time"
    )
    booking_status: BookingStatus | None = Field(
        None, description="Booking status"
    )
    groomer_id: uuid.UUID | None = Field(
        None, description="Assigned groomer identifier"
    )
    pet_id: uuid.UUID | None = Field(
        None, description="Pet identifier"
    )
    rating: Decimal | None = Field(
        None, ge=0, le=5, description="Customer rating (0-5)"
    )
