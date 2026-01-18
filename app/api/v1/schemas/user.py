"""User schemas."""

import uuid

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""

    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    phone: str | None = Field(None, max_length=20, description="User's phone number")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    first_name: str | None = Field(
        None, min_length=1, max_length=100, description="User's first name"
    )
    last_name: str | None = Field(
        None, min_length=1, max_length=100, description="User's last name"
    )
    email: EmailStr | None = Field(None, description="User's email address")
    phone: str | None = Field(None, max_length=20, description="User's phone number")


class UserResponse(UserBase):
    """Schema for user response."""

    user_id: uuid.UUID = Field(..., description="Unique user identifier")
    bookings_taken: int = Field(0, description="Number of bookings taken by the user")

    class ConfigDict:
        """Pydantic configuration."""

        from_attributes = True
