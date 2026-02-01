"""Booking API endpoints."""

import logging
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas import (
    BookingCreate,
    BookingResponse,
    BookingReviewCreate,
    BookingUpdate,
)
from app.config import settings
from app.services import db, log_sender
from models import Booking, BookingStatus, Pet, User

router = APIRouter(prefix="/bookings", tags=["bookings"])
logger = logging.getLogger(__name__)


async def increment_groomer_booking_count(groomer_id: uuid.UUID) -> None:
    """Increment the booking count for a groomer in the groomer service.

    :param groomer_id: The groomer's UUID
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            groomer_service_url = (
                f"{settings.groomer_service_url}/api/v1/groomers/"
                f"{groomer_id}/increment-booking-count"
            )
            logger.info("Incrementing booking count for groomer: %s", groomer_service_url)
            response = await client.post(groomer_service_url)
            response.raise_for_status()
            logger.info("Successfully incremented booking count for groomer %s", groomer_id)
        except httpx.TimeoutException:
            logger.warning(
                "Timeout when incrementing booking count for groomer %s", groomer_id
            )
            raise
        except httpx.HTTPStatusError as e:
            logger.warning(
                "Error incrementing booking count for groomer %s: %s - %s",
                groomer_id,
                e.response.status_code,
                e.response.text,
            )
            raise
        except Exception as e:
            logger.exception("Unexpected error incrementing booking count: %s", str(e))
            raise


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
    # Validate booking date is in the future
    now = datetime.now(UTC)
    booking_datetime = booking_data.booking_date_time
    if booking_datetime.tzinfo is None:
        # If timezone-naive, assume UTC
        booking_datetime = booking_datetime.replace(tzinfo=UTC)
    elif booking_datetime.tzinfo != UTC:
        # Convert to UTC for comparison
        booking_datetime = booking_datetime.astimezone(UTC)

    if booking_datetime <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking date and time must be in the future",
        )

    # Verify groomer exists via groomer service
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            groomer_service_url = (
                f"{settings.groomer_service_url}/api/v1/groomers/"
                f"{booking_data.groomer_id}"
            )
            logger.info("Validating groomer exists: %s", groomer_service_url)
            response = await client.get(groomer_service_url)
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Groomer with ID {booking_data.groomer_id} not found",
                )
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.error("Timeout when validating groomer with groomer service")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Groomer service request timed out while validating groomer",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Error validating groomer with groomer service: %s - %s",
                e.response.status_code,
                e.response.text,
            )
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Groomer with ID {booking_data.groomer_id} not found",
                )
            elif e.response.status_code >= 500:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Groomer service is unavailable",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error from groomer service: {e.response.text}",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Unexpected error validating groomer: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to communicate with groomer service",
            )

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

        # Check for time conflict - verify groomer is not already booked at this time
        conflicting_booking = (
            session.query(Booking)
            .filter(
                Booking.groomer_id == booking_data.groomer_id,
                Booking.booking_date_time == booking_data.booking_date_time,
                Booking.booking_status.notin_(
                    [BookingStatus.CANCELLED.value, BookingStatus.NO_SHOW.value]
                ),
            )
            .first()
        )
        if conflicting_booking:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Groomer {booking_data.groomer_id} is already booked at "
                    f"{booking_data.booking_date_time}"
                ),
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
        )
        session.add(new_booking)
        session.flush()
        session.refresh(new_booking)  # Refresh to ensure all attributes are loaded

        # Increment groomer's booking count in groomer service
        try:
            await increment_groomer_booking_count(booking_data.groomer_id)
        except Exception as e:
            logger.exception("Failed to increment groomer booking count: %s", str(e))
            # Don't fail the booking creation if increment fails
            # Log the error but continue

        if log_sender:
            await log_sender.send(
                level="info",
                event="booking_service.booking_created",
                message=f"Booking {new_booking.booking_id} created successfully",
            )
        return BookingResponse.model_validate(new_booking)


@router.get(
    "",
    summary="Get All Bookings",
    description="Retrieve all bookings with optional filtering by groomer and status",
    response_description="List of bookings",
    response_model=list[BookingResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_bookings(
    groomer_id: uuid.UUID | None = Query(None, description="Filter by groomer ID"),
    booking_status: BookingStatus | None = Query(
        None, description="Filter by booking status", alias="status"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
) -> list[BookingResponse]:
    """Get all bookings with optional filtering."""
    with db.session_scope() as session:
        query = session.query(Booking)

        # Apply filters if provided
        if groomer_id:
            query = query.filter(Booking.groomer_id == groomer_id)
        if booking_status:
            query = query.filter(Booking.booking_status == booking_status.value)

        # Order by booking date (most recent first) and apply pagination
        bookings = (
            query.order_by(Booking.booking_date_time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [BookingResponse.model_validate(booking) for booking in bookings]


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
            booking.booking_status = status_value.value
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
        booking_response = BookingResponse.model_validate(booking, from_attributes=True)
        session.delete(booking)
        session.flush()
        if log_sender:
            await log_sender.send(
                level="info",
                event="booking_service.booking_cancelled",
                message=f"Booking {booking_id} cancelled successfully",
            )
        return booking_response


@router.post(
    "/{booking_id}/review",
    summary="Submit Booking Review",
    description="Submit a review for a completed booking to the groomer service",
    response_description="Review submission confirmation",
    status_code=status.HTTP_201_CREATED,
)
async def submit_booking_review(
    booking_id: uuid.UUID, review_data: BookingReviewCreate
) -> dict:
    """Submit a review for a booking.

    This endpoint retrieves the booking details and forwards the review
    to the groomer service.

    :param booking_id: The booking UUID to review
    :param review_data: Review data including rating and optional comment
    :return: Confirmation of review submission
    :raises HTTPException: 404 if booking not found, 400 if booking not completed
    """
    with db.session_scope() as session:
        # Get the booking
        booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with ID {booking_id} not found",
            )

        # Verify booking is completed
        if booking.booking_status != BookingStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot review booking with status '{booking.booking_status}'. "
                "Only completed bookings can be reviewed.",
            )

        # Prepare review data for groomer service
        review_payload = {
            "booking_id": str(booking.booking_id),
            "user_id": str(booking.user_id),
            "rating": review_data.rating,
            "comment": review_data.comment,
        }

        # Submit review to groomer service
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                groomer_review_url = (
                    f"{settings.groomer_service_url}/api/v1/groomers/"
                    f"{booking.groomer_id}/reviews"
                )
                logger.info(
                    "Submitting review to groomer service: %s with payload: %s",
                    groomer_review_url,
                    review_payload,
                )
                response = await client.post(groomer_review_url, json=review_payload)
                response.raise_for_status()
                review_response = response.json()
                logger.info(
                    "Successfully submitted review for booking %s to groomer %s",
                    booking_id,
                    booking.groomer_id,
                )

                if log_sender:
                    await log_sender.send(
                        level="info",
                        event="booking_service.review_submitted",
                        message=f"Review submitted for booking {booking_id}",
                    )

                return {
                    "message": "Review submitted successfully",
                    "booking_id": str(booking_id),
                    "groomer_id": str(booking.groomer_id),
                    "review": review_response,
                }

            except httpx.TimeoutException:
                logger.error("Timeout when submitting review to groomer service")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Groomer service request timed out while submitting review",
                )
            except httpx.HTTPStatusError as e:
                logger.error(
                    "Error submitting review to groomer service: %s - %s",
                    e.response.status_code,
                    e.response.text,
                )
                if e.response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Groomer with ID {booking.groomer_id} not found in groomer service",
                    )
                elif e.response.status_code >= 500:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Groomer service is unavailable",
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Error from groomer service: {e.response.text}",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Unexpected error submitting review: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to communicate with groomer service",
                )
