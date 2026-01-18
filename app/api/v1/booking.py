"""Booking API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas import BookingCreate, BookingResponse, BookingUpdate
from app.services import db, log_sender
from models import Booking, BookingStatus, Pet, User

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    summary="Create New Booking",
    description="Create a new booking for a pet",
    response_description="Created booking details",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(booking_data: BookingCreate) -> BookingResponse:
    """Create a new booking."""
    with db.session_scope() as session:
        # Verify pet exists and get user_id from pet
        pet = session.query(Pet).filter(Pet.pet_id == booking_data.pet_id).first()
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pet with ID {booking_data.pet_id} not found",
            )

        # Verify user exists
        user = session.query(User).filter(User.user_id == pet.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {pet.user_id} not found",
            )

        # Create new booking
        new_booking = Booking(
            pet_id=booking_data.pet_id,
            user_id=pet.user_id,
            booking_date_time=booking_data.booking_date_time,
            groomer_id=booking_data.groomer_id,
            booking_status=(
                booking_data.booking_status.value
                if booking_data.booking_status
                else BookingStatus.PENDING.value
            ),
            rating=booking_data.rating,
        )
        session.add(new_booking)
        session.flush()
        if log_sender:
            await log_sender.send(
                level="info",
                event="booking_service.booking_created",
                message=f"Booking {new_booking.booking_id} created successfully",
            )
        return BookingResponse.model_validate(new_booking)


@router.get(
    "/{booking_id}",
    summary="Get Booking Details",
    description="Retrieve a booking by its unique identifier",
    response_description="Booking details",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_booking(booking_id: uuid.UUID) -> BookingResponse:
    """Get a booking by its ID."""
    with db.session_scope() as session:
        booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with ID {booking_id} not found",
            )
        return BookingResponse.model_validate(booking)


@router.put(
    "/{booking_id}",
    summary="Update Booking",
    description="Update a booking's information by its ID",
    response_description="Updated booking details",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
)
async def update_booking(booking_id: uuid.UUID, booking_data: BookingUpdate) -> BookingResponse:
    """Update a booking by its ID."""
    with db.session_scope() as session:
        booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with ID {booking_id} not found",
            )

        # Update fields if provided (using model_dump to get only explicitly set fields)
        update_data = booking_data.model_dump(exclude_unset=True)

        if "booking_date_time" in update_data:
            booking.booking_date_time = update_data["booking_date_time"]
        if "booking_status" in update_data:
            # Handle BookingStatus enum conversion
            status_value = update_data["booking_status"]
            if isinstance(status_value, BookingStatus):
                booking.booking_status = status_value.value
            else:
                # Pydantic validates enum, so this should be safe
                booking.booking_status = str(status_value)
        if "groomer_id" in update_data:
            booking.groomer_id = update_data["groomer_id"]
        if "pet_id" in update_data:
            # Verify new pet exists
            pet = session.query(Pet).filter(Pet.pet_id == update_data["pet_id"]).first()
            if not pet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Pet with ID {update_data['pet_id']} not found",
                )
            booking.pet_id = update_data["pet_id"]
            booking.user_id = pet.user_id  # Update user_id when pet changes
        if "rating" in update_data:
            booking.rating = update_data["rating"]

        session.flush()
        if log_sender:
            await log_sender.send(
                level="info",
                event="booking_service.booking_updated",
                message=f"Booking {booking.booking_id} updated successfully",
            )
        return BookingResponse.model_validate(booking)


@router.delete(
    "/{booking_id}",
    summary="Cancel Booking",
    description="Cancel (delete) a booking by its ID",
    response_description="Cancelled booking details",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
)
async def cancel_booking(booking_id: uuid.UUID) -> BookingResponse:
    """Cancel (delete) a booking by its ID."""
    with db.session_scope() as session:
        booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with ID {booking_id} not found",
            )
        booking_response = BookingResponse.model_validate(booking)
        session.delete(booking)
        session.flush()
        if log_sender:
            await log_sender.send(
                level="info",
                event="booking_service.booking_cancelled",
                message=f"Booking {booking_id} cancelled successfully",
            )
        return booking_response
