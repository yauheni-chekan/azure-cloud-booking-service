"""Pet schemas."""

import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class PetCreate(BaseModel):
    """Schema for creating a new pet."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Pet's name"
    )
    species: str = Field(
        ..., min_length=1, max_length=50, description="Pet species (e.g., Dog, Cat)"
    )
    breed: str | None = Field(
        None, max_length=100, description="Pet breed"
    )
    age: int | None = Field(
        None, ge=0, description="Pet age in years"
    )
    weight: Decimal | None = Field(
        None, ge=0, description="Pet weight in kg"
    )
    special_instructions: str | None = Field(
        None, description="Special care instructions for the pet"
    )


class PetResponse(BaseModel):
    """Schema for pet response."""

    pet_id: uuid.UUID = Field(..., description="Unique pet identifier")
    user_id: uuid.UUID = Field(..., description="Owner's user identifier")
    name: str = Field(..., description="Pet's name")
    species: str = Field(..., description="Pet species")
    breed: str | None = Field(None, description="Pet breed")
    age: int | None = Field(None, description="Pet age in years")
    weight: Decimal | None = Field(None, description="Pet weight in kg")
    special_instructions: str | None = Field(None, description="Special care instructions")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class PetUpdate(BaseModel):
    """Schema for updating a pet."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Pet's name"
    )
    species: str | None = Field(
        None, min_length=1, max_length=50, description="Pet species (e.g., Dog, Cat)"
    )
    breed: str | None = Field(
        None, max_length=100, description="Pet breed"
    )
    age: int | None = Field(
        None, ge=0, description="Pet age in years"
    )
    weight: Decimal | None = Field(
        None, ge=0, description="Pet weight in kg"
    )
    special_instructions: str | None = Field(
        None, description="Special care instructions for the pet"
    )
