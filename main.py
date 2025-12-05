"""Azure Cloud Booking Service - Example usage of SQLAlchemy models."""

import logging
import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from models import (
    Booking,
    BookingStatus,
    Pet,
    User,
)
from service import DatabaseManager, create_engine_from_connection_string

load_dotenv()

time_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt=time_format,
)
logger = logging.getLogger("Booking Service Demo")


def create_users(session: Session) -> None:
    """Create new users."""
    u1 = User(first_name="John", last_name="Doe", email="john.doe@example.com", phone="+1-555-123-4567")
    u2 = User(first_name="Jane", last_name="Smith", email="jane.smith@example.com", phone="+1-555-987-6543")
    u3 = User(first_name="Jim", last_name="Beam", email="jim.beam@example.com", phone="+1-555-123-7890")
    session.add_all([u1, u2, u3])
    session.flush()
    logger.info("Created users: %s", [u1, u2, u3])
    return u1, u2, u3


def create_pets(session: Session, users: list[User]) -> None:
    """Create new pets."""
    p1 = Pet(
        user_id=users[0].user_id,
        name="Buddy",
        breed="Golden Retriever",
        species="Dog",
        age=3,
        weight=Decimal("30.5"),
        special_instructions="Friendly but nervous around loud noises",
    )
    p2 = Pet(
        user_id=users[1].user_id,
        name="Max",
        breed="Labrador",
        species="Dog",
        age=5,
        weight=Decimal("35.2"),
        special_instructions="Loves to play fetch",
    )
    p3 = Pet(
        user_id=users[2].user_id,
        name="Whiskers",
        breed="Siamese",
        species="Cat",
        age=2,
        weight=Decimal("4.5"),
        special_instructions="Prefers quiet environments",
    )
    session.add_all([p1, p2, p3])
    session.flush()
    logger.info("Created pets: %s", [p1, p2, p3])
    return p1, p2, p3


def create_bookings(session: Session, pets: list[Pet]) -> None:
    """Create new bookings."""
    b1 = Booking(
        booking_date_time=datetime(2025, 12, 15, 10, 0, 0, tzinfo=UTC),
        booking_status=BookingStatus.CONFIRMED,
        groomer_id=uuid.uuid4(),
        user_id=pets[0].user_id,
        pet_id=pets[0].pet_id,
    )
    b2 = Booking(
        booking_date_time=datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC),
        booking_status=BookingStatus.CONFIRMED,
        groomer_id=uuid.uuid4(),
        user_id=pets[1].user_id,
        pet_id=pets[1].pet_id,
    )
    b3 = Booking(
        booking_date_time=datetime(2025, 12, 17, 10, 0, 0, tzinfo=UTC),
        booking_status=BookingStatus.CONFIRMED,
        groomer_id=uuid.uuid4(),
        user_id=pets[2].user_id,
        pet_id=pets[2].pet_id,
    )
    session.add_all([b1, b2, b3])
    session.flush()
    logger.info("Created bookings: %s", [b1, b2, b3])
    return b1, b2, b3


def main() -> None:
    """Demonstrate usage of the booking service models."""
    # Example connection string for Azure SQL Database
    # WARNING: Never hardcode credentials in production - use environment variables!
    connection_string = os.getenv("DB_CONNECTION_STRING")
    if not connection_string:
        message = "DB_CONNECTION_STRING environment variable is not set"
        logger.error(message)
        raise ValueError(message)

    # Create the database engine
    engine = create_engine_from_connection_string(connection_string)
    logger.info("Created engine for database connection")
    # Initialize the database manager
    db = DatabaseManager(engine)
    logger.info("Initialized database manager")
    # Create all tables
    db.create_tables()
    logger.info("Created all tables")
    # Example: Creating records using the session scope
    with db.session_scope() as session:
        u1, u2, u3 = create_users(session)
        p1, p2, p3 = create_pets(session, [u1, u2, u3])
        create_bookings(session, [p1, p2, p3])

    logger.info("Reading data from database")
    with db.session_scope() as session:
        users = session.query(User).all()
        pets = session.query(Pet).all()
        bookings = session.query(Booking).all()
        logger.info("Users:\n\t%s", "\n\t".join(str(user) for user in users))
        logger.info("Pets:\n\t%s", "\n\t".join(str(pet) for pet in pets))
        logger.info("Bookings:\n\t%s", "\n\t".join(str(booking) for booking in bookings))

    logger.info("Deleting data from database")
    with db.session_scope() as session:
        session.query(Booking).delete()
        session.query(Pet).delete()
        session.query(User).delete()
        session.commit()
        logger.info("Deleted all data from database")
    logger.info("Dropping tables from database")

    db.drop_tables()
    logger.info("Dropped all tables from database")


if __name__ == "__main__":
    main()
