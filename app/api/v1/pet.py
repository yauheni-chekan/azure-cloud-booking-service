"""Pet API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas import PetResponse, PetUpdate
from app.services.database import db
from models import Pet

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get(
    "/{pet_id}",
    summary="Get Pet Details",
    description="Retrieve a pet by its unique identifier",
    response_description="Pet details",
    response_model=PetResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pet(pet_id: uuid.UUID) -> PetResponse:
    """Get a pet by its ID."""
    with db.session_scope() as session:
        pet = session.query(Pet).filter(Pet.pet_id == pet_id).first()
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pet with ID {pet_id} not found",
            )
        return PetResponse.model_validate(pet)


@router.put(
    "/{pet_id}",
    summary="Update Pet Profile",
    description="Update a pet's information by its ID",
    response_description="Updated pet details",
    response_model=PetResponse,
    status_code=status.HTTP_200_OK,
)
async def update_pet(pet_id: uuid.UUID, pet_data: PetUpdate) -> PetResponse:
    """Update a pet by its ID."""
    with db.session_scope() as session:
        pet = session.query(Pet).filter(Pet.pet_id == pet_id).first()
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pet with ID {pet_id} not found",
            )

        # Update fields if provided (using model_dump to get only explicitly set fields)
        update_data = pet_data.model_dump(exclude_unset=True)
        
        if "name" in update_data:
            pet.name = update_data["name"]
        if "species" in update_data:
            pet.species = update_data["species"]
        if "breed" in update_data:
            pet.breed = update_data["breed"]
        if "age" in update_data:
            pet.age = update_data["age"]
        if "weight" in update_data:
            pet.weight = update_data["weight"]
        if "special_instructions" in update_data:
            pet.special_instructions = update_data["special_instructions"]

        session.flush()
        return PetResponse.model_validate(pet)


@router.delete(
    "/{pet_id}",
    summary="Delete Pet Profile",
    description="Delete a pet by its ID",
    response_description="Deleted pet details",
    response_model=PetResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_pet(pet_id: uuid.UUID) -> PetResponse:
    """Delete a pet by its ID."""
    with db.session_scope() as session:
        pet = session.query(Pet).filter(Pet.pet_id == pet_id).first()
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pet with ID {pet_id} not found",
            )
        pet_response = PetResponse.model_validate(pet)
        session.delete(pet)
        session.flush()
        return pet_response
