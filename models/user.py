"""User model for the booking service."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base

if TYPE_CHECKING:
    from models import Booking, Pet


class User(Base):
    """User model representing customers in the booking system."""

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    bookings_taken: Mapped[int] = mapped_column(default=0)

    # Relationships
    pets: Mapped[list["Pet"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[Booking.user_id]",
    )

    def __repr__(self) -> str:
        """Represent the user model as a string."""
        return f"User(user_id={self.user_id!r}, email={self.email!r})"
