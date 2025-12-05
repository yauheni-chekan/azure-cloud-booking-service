"""Booking model and status enum for the booking service."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base

if TYPE_CHECKING:
    from models import Pet, User


class BookingStatus(StrEnum):
    """Enumeration of possible booking statuses."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Booking(Base):
    """Booking model representing grooming appointments."""

    __tablename__ = "bookings"

    booking_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    booking_date_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    booking_status: Mapped[str] = mapped_column(String(20), default=BookingStatus.PENDING.value)
    groomer_id: Mapped[uuid.UUID] = mapped_column(index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    pet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pets.pet_id", ondelete="NO ACTION"), index=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(precision=3, scale=2))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="bookings", foreign_keys=[user_id])
    pet: Mapped["Pet"] = relationship(back_populates="bookings")

    def __repr__(self) -> str:
        """Return a string representation of the booking."""
        return f"Booking(booking_id={self.booking_id!r}, status={self.booking_status!r})"

    @property
    def status(self) -> BookingStatus:
        """Get the booking status as an enum."""
        return BookingStatus(self.booking_status)

    @status.setter
    def status(self, value: BookingStatus) -> None:
        """Set the booking status from an enum."""
        self.booking_status = value.value
