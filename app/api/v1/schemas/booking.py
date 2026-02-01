"""Booking schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from models import BookingStatus


class BookingResponse(BaseModel):
    """Schema for booking response."""

    model_config = ConfigDict(from_attributes=True)

    booking_id: uuid.UUID = Field(..., description="Unique booking identifier")
    booking_date_time: datetime = Field(..., description="Appointment date and time")
    booking_status: str = Field(..., description="Booking status")
    groomer_id: uuid.UUID = Field(..., description="Assigned groomer identifier")
    user_id: uuid.UUID = Field(..., description="User identifier")
    pet_id: uuid.UUID = Field(..., description="Pet identifier")
    rating: Decimal | None = Field(None, description="Customer rating")


class BookingCreate(BaseModel):
    """Schema for creating a new booking."""
    model_config = ConfigDict(from_attributes=True)

    pet_id: uuid.UUID = Field(..., description="Pet identifier for the booking")
    booking_date_time: datetime = Field(..., description="Appointment date and time")
    groomer_id: uuid.UUID = Field(..., description="Assigned groomer identifier")
    booking_status: BookingStatus | None = Field(
        None, description="Booking status (defaults to pending)"
    )


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""
    model_config = ConfigDict(from_attributes=True)
    booking_date_time: datetime | None = Field(None, description="Appointment date and time")
    booking_status: BookingStatus | None = Field(None, description="Booking status")
    groomer_id: uuid.UUID | None = Field(None, description="Assigned groomer identifier")
    pet_id: uuid.UUID | None = Field(None, description="Pet identifier")


class BookingReviewCreate(BaseModel):
    """Schema for creating a review for a booking."""
    model_config = ConfigDict(from_attributes=True)
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(None, max_length=500, description="Optional review comment")
