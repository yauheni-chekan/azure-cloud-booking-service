"""User API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas import (
    BookingResponse,
    PetCreate,
    PetResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.database import db
from app.services.unified_log_queue import get_unified_log_sender
from models import Booking, BookingStatus, Pet, User

router = APIRouter(prefix="/users", tags=["users"])

# Initialize unified log sender
unified_log_sender = get_unified_log_sender()


@router.get(
    "",
    summary="Get All Users",
    description="Retrieve all users from the database",
    response_description="List of all users",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
async def get_users() -> list[UserResponse]:
    """Get all users."""
    with db.session_scope() as session:
        users = session.query(User).all()
        return [UserResponse.model_validate(user) for user in users]


@router.get(
    "/{user_id}",
    summary="Get User by ID",
    description="Retrieve a user by their unique identifier",
    response_description="User details",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user(user_id: uuid.UUID) -> UserResponse:
    """Get a user by their ID."""
    with db.session_scope() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        return UserResponse.model_validate(user)


@router.post(
    "",
    summary="Create User",
    description="Create a new user in the database",
    response_description="Created user details",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user_data: UserCreate) -> UserResponse:
    """Create a new user."""
    with db.session_scope() as session:
        # Check if email already exists
        existing_user = session.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_data.email} already exists",
            )

        # Create new user
        new_user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
        )
        session.add(new_user)
        session.flush()
        if unified_log_sender:
            await unified_log_sender.send(
                level="info",
                event="booking_service.user_created",
                message=f"User {new_user.email} created successfully",
            )
        return UserResponse.model_validate(new_user)


@router.put(
    "/{user_id}",
    summary="Update User",
    description="Update a user's information by their ID",
    response_description="Updated user details",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user(user_id: uuid.UUID, user_data: UserUpdate) -> UserResponse:
    """Update a user by their ID."""
    with db.session_scope() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        # Check if email is being updated and if it already exists
        if user_data.email and user_data.email != user.email:
            existing_user = session.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with email {user_data.email} already exists",
                )

        # Update fields if provided
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.phone is not None:
            user.phone = user_data.phone

        session.flush()
        if unified_log_sender:
            await unified_log_sender.send(
                level="info",
                event="booking_service.user_updated",
                message=f"User {user.email} updated successfully",
            )
        return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    summary="Delete User",
    description="Delete a user by their ID",
    response_description="Deleted user details",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_user(user_id: uuid.UUID) -> UserResponse:
    """Delete a user by their ID."""
    with db.session_scope() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        user_response = UserResponse.model_validate(user)
        session.delete(user)
        session.flush()
        if unified_log_sender:
            await unified_log_sender.send(
                level="info",
                event="booking_service.user_deleted",
                message=f"User {user.email} deleted successfully",
            )
        return user_response


@router.get(
    "/{user_id}/bookings",
    summary="Get User Bookings",
    description="Retrieve all bookings for a specific user, optionally filtered by status",
    response_description="List of user bookings",
    response_model=list[BookingResponse],
    status_code=status.HTTP_200_OK,
)
async def get_user_bookings(
    user_id: uuid.UUID,
    booking_status: BookingStatus | None = Query(
        None,
        description="Filter bookings by status",
        alias="status",
    ),
) -> list[BookingResponse]:
    """Get all bookings for a user, optionally filtered by status."""
    with db.session_scope() as session:
        # Verify user exists
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        # Query bookings
        query = session.query(Booking).filter(Booking.user_id == user_id)
        if booking_status:
            query = query.filter(Booking.booking_status == booking_status.value)

        bookings = query.all()
        return [BookingResponse.model_validate(booking) for booking in bookings]


@router.post(
    "/{user_id}/pets",
    summary="Add Pet Profile",
    description="Create a new pet profile for a user",
    response_description="Created pet details",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pet(user_id: uuid.UUID, pet_data: PetCreate) -> PetResponse:
    """Add a pet profile for a user."""
    with db.session_scope() as session:
        # Verify user exists
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        # Create new pet
        new_pet = Pet(
            user_id=user_id,
            name=pet_data.name,
            species=pet_data.species,
            breed=pet_data.breed,
            age=pet_data.age,
            weight=pet_data.weight,
            special_instructions=pet_data.special_instructions,
        )
        session.add(new_pet)
        session.flush()
        if unified_log_sender:
            await unified_log_sender.send(
                level="info",
                event="booking_service.pet_created",
                message=f"Pet {new_pet.name} created successfully",
            )
        return PetResponse.model_validate(new_pet)


@router.get(
    "/{user_id}/pets",
    summary="Get User Pets",
    description="Retrieve all pets for a specific user",
    response_description="List of user pets",
    response_model=list[PetResponse],
    status_code=status.HTTP_200_OK,
)
async def get_user_pets(user_id: uuid.UUID) -> list[PetResponse]:
    """Get all pets for a user."""
    with db.session_scope() as session:
        # Verify user exists
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        # Query pets
        pets = session.query(Pet).filter(Pet.user_id == user_id).all()
        return [PetResponse.model_validate(pet) for pet in pets]
