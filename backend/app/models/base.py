from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
import uuid as uuid_pkg
from app.core.database import Base


def get_utc_now():
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    CHAR(36) and stores as stringified UUIDs.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid_pkg.UUID):
                return str(uuid_pkg.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid_pkg.UUID):
                value = uuid_pkg.UUID(value)
            return value


class BaseModel(Base):
    """
    Base model with common fields for all models.
    Includes audit trail fields (created_at/by, updated_at/by).

    Note: created_by and updated_by are GUID fields without foreign key constraints
    to avoid circular dependencies. The application layer should ensure referential integrity.
    """
    __abstract__ = True

    id = Column(GUID, primary_key=True, index=True, default=uuid4)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    created_by = Column(GUID, nullable=True, doc="ID of user who created this record")
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    updated_by = Column(GUID, nullable=True, doc="ID of user who last updated this record")
