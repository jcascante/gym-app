"""
CoachClientAssignment database model.

Defines the coach-client relationship for GYM and ENTERPRISE subscriptions.
Tracks which coaches are assigned to which clients.
"""
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Index
from app.models.base import BaseModel, GUID, get_utc_now


class CoachClientAssignment(BaseModel):
    """
    CoachClientAssignment model for tracking coach-client relationships.

    Only applies to GYM and ENTERPRISE subscriptions.
    Individual subscriptions don't use this - the admin coaches all clients directly.

    Attributes:
        subscription_id: Foreign key to parent subscription
        location_id: Foreign key to location (nullable, ENTERPRISE only)
        coach_id: Foreign key to coach user
        client_id: Foreign key to client user
        assigned_at: Timestamp when the assignment was made
        is_active: Whether the assignment is active

    Inherits from BaseModel:
        id: Primary key (UUID)
        created_at: Timestamp of creation
        created_by: User who created the assignment
        updated_at: Timestamp of last update
        updated_by: User who last updated the assignment
    """
    __tablename__ = "coach_client_assignments"

    subscription_id = Column(
        GUID,
        ForeignKey('subscriptions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to parent subscription"
    )

    location_id = Column(
        GUID,
        ForeignKey('locations.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="Foreign key to location (ENTERPRISE only)"
    )

    coach_id = Column(
        GUID,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to coach user"
    )

    client_id = Column(
        GUID,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to client user"
    )

    assigned_at = Column(
        DateTime,
        default=get_utc_now,
        nullable=False,
        doc="Timestamp when the assignment was made"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the assignment is active"
    )

    # Composite indexes for common queries
    __table_args__ = (
        # Index for finding all clients of a coach
        Index('ix_coach_client_assignments_coach_active', 'coach_id', 'is_active'),
        # Index for finding the coach of a client
        Index('ix_coach_client_assignments_client_active', 'client_id', 'is_active'),
        # Index for subscription-level queries
        Index('ix_coach_client_assignments_subscription_active', 'subscription_id', 'is_active'),
        # Index for location-level queries (ENTERPRISE)
        Index('ix_coach_client_assignments_location_active', 'location_id', 'is_active'),
        # Unique constraint to prevent duplicate active assignments
        Index('ix_coach_client_assignments_unique', 'coach_id', 'client_id', 'is_active', unique=True),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<CoachClientAssignment(id={self.id}, coach_id={self.coach_id}, client_id={self.client_id}, is_active={self.is_active})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary (for logging/debugging)."""
        return {
            "id": str(self.id),
            "subscription_id": str(self.subscription_id),
            "location_id": str(self.location_id) if self.location_id else None,
            "coach_id": str(self.coach_id),
            "client_id": str(self.client_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
