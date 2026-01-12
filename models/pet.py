"""Pet model for the booking service."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base

if TYPE_CHECKING:
    from models import Booking, User


class Pet(Base):
    """Pet model representing pets owned by users."""

    __tablename__ = "pets"

    pet_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    breed: Mapped[str | None] = mapped_column(String(100))
    species: Mapped[str] = mapped_column(String(50))
    age: Mapped[int | None] = mapped_column()
    weight: Mapped[Decimal | None] = mapped_column(Numeric(precision=10, scale=2))
    special_instructions: Mapped[str | None] = mapped_column(Text)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="pets")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="pet")

    def __repr__(self) -> str:
        """Represent the pet model as a string."""
        return f"Pet(pet_id={self.pet_id!r}, name={self.name!r}, species={self.species!r})"
