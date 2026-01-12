"""Base class for SQLAlchemy models (Azure SQL only)."""

import uuid
from typing import ClassVar

from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map: ClassVar[dict] = {
        uuid.UUID: UNIQUEIDENTIFIER,
    }
