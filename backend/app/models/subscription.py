"""
Subscription database model.

Defines the Subscription table structure representing the top-level tenant entity.
Each subscription represents an individual coach, gym, or enterprise customer.
"""
from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator, Text
import enum
import json
from app.models.base import BaseModel


class SubscriptionType(str, enum.Enum):
    """Subscription tier types."""
    INDIVIDUAL = "INDIVIDUAL"
    GYM = "GYM"
    ENTERPRISE = "ENTERPRISE"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status values."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class JSONBType(TypeDecorator):
    """
    Platform-independent JSONB type.

    Uses PostgreSQL's JSONB when available, otherwise uses Text with JSON serialization.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            return json.loads(value)


class Subscription(BaseModel):
    """
    Subscription model representing the top-level tenant entity.

    Attributes:
        name: Subscription name (e.g., "PowerFit Gym", "Maria's Coaching")
        subscription_type: Tier type (INDIVIDUAL, GYM, ENTERPRISE)
        status: Current status (ACTIVE, SUSPENDED, CANCELLED)
        features: JSONB field with feature flags (multi_location, api_access, etc.)
        limits: JSONB field with resource limits (max_coaches, max_clients, etc.)
        billing_info: JSONB field with billing information

    Inherits from BaseModel:
        id: Primary key (UUID)
        created_at: Timestamp of creation
        created_by: User who created the subscription (nullable for system-created)
        updated_at: Timestamp of last update
        updated_by: User who last updated the subscription
    """
    __tablename__ = "subscriptions"

    name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Subscription name (e.g., 'PowerFit Gym', 'Maria's Coaching')"
    )

    subscription_type = Column(
        SQLEnum(SubscriptionType, name='subscription_type_enum', native_enum=False),
        nullable=False,
        index=True,
        doc="Subscription tier (INDIVIDUAL, GYM, ENTERPRISE)"
    )

    status = Column(
        SQLEnum(SubscriptionStatus, name='subscription_status_enum', native_enum=False),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        index=True,
        doc="Current subscription status"
    )

    features = Column(
        JSONBType,
        nullable=False,
        default=dict,
        doc="Feature flags (e.g., {'multi_location': true, 'api_access': false})"
    )

    limits = Column(
        JSONBType,
        nullable=False,
        default=dict,
        doc="Resource limits (e.g., {'max_coaches': 25, 'max_clients': 500})"
    )

    billing_info = Column(
        JSONBType,
        nullable=True,
        doc="Billing information (payment method, billing cycle, etc.)"
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Subscription(id={self.id}, name='{self.name}', type={self.subscription_type}, status={self.status})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary (for logging/debugging)."""
        return {
            "id": str(self.id),
            "name": self.name,
            "subscription_type": self.subscription_type.value if self.subscription_type else None,
            "status": self.status.value if self.status else None,
            "features": self.features,
            "limits": self.limits,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
