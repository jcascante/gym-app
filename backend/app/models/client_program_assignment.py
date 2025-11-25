"""
Client Program Assignment database model.

Tracks which programs are assigned to which clients, including assignment status,
start/end dates, progress tracking, and completion.
"""
from sqlalchemy import Column, String, Boolean, Integer, Date, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, GUID
from datetime import date


class ClientProgramAssignment(BaseModel):
    """
    ClientProgramAssignment model representing program assignments to clients.

    This model tracks the assignment of workout programs to specific clients,
    including their progress, status, and completion.

    Attributes:
        subscription_id: Foreign key to subscription (for multi-tenant isolation)
        location_id: Foreign key to location (nullable, for enterprise multi-location)
        coach_id: Foreign key to coach who assigned the program
        client_id: Foreign key to client user
        program_id: Foreign key to the assigned program

        assignment_name: Optional custom name for this assignment (e.g., "Winter Bulk")
        start_date: When client should start the program
        end_date: Expected completion date (calculated from program duration)
        actual_completion_date: When client actually completed the program

        status: Current status (assigned, in_progress, completed, paused, cancelled)
        current_week: Which week the client is currently on (1-based)
        current_day: Which day within the week (1-based)

        is_active: Whether this assignment is currently active
        notes: Coach notes about this assignment

    Inherits from BaseModel:
        id: Primary key (UUID)
        created_at: When assignment was created
        created_by: User ID who created (audit trail)
        updated_at: Last modification timestamp
        updated_by: User ID who last updated

    Database Relationships:
        - client: Many-to-one with User
        - coach: Many-to-one with User
        - program: Many-to-one with Program
        - subscription: Many-to-one with Subscription
        - location: Many-to-one with Location (nullable)
    """
    __tablename__ = "client_program_assignments"

    # Multi-tenant fields
    subscription_id = Column(
        GUID,
        ForeignKey('subscriptions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to subscription (for multi-tenant isolation)"
    )

    location_id = Column(
        GUID,
        ForeignKey('locations.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="Foreign key to location (nullable, for enterprise multi-location)"
    )

    # Assignment relationships
    coach_id = Column(
        GUID,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,  # Null if coach is deleted
        index=True,
        doc="Coach who assigned this program"
    )

    client_id = Column(
        GUID,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Client user this program is assigned to"
    )

    program_id = Column(
        GUID,
        ForeignKey('programs.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Program that is assigned"
    )

    # Assignment metadata
    assignment_name = Column(
        String(255),
        nullable=True,
        doc="Optional custom name for this assignment (e.g., 'Winter Bulk')"
    )

    # Date tracking
    start_date = Column(
        Date,
        nullable=False,
        default=date.today,
        doc="When client should start the program"
    )

    end_date = Column(
        Date,
        nullable=True,
        doc="Expected completion date (calculated from program duration)"
    )

    actual_completion_date = Column(
        Date,
        nullable=True,
        doc="When client actually completed the program"
    )

    # Progress tracking
    status = Column(
        String(50),
        nullable=False,
        default="assigned",
        index=True,
        doc="Status: assigned, in_progress, completed, paused, cancelled"
    )

    current_week = Column(
        Integer,
        nullable=False,
        default=1,
        doc="Which week the client is currently on (1-based)"
    )

    current_day = Column(
        Integer,
        nullable=False,
        default=1,
        doc="Which day within the week (1-based)"
    )

    # Activity flag
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Whether this assignment is currently active"
    )

    # Notes
    notes = Column(
        Text,
        nullable=True,
        doc="Coach notes about this assignment"
    )

    # Relationships (define these after all models are loaded to avoid circular imports)
    # These will be added via back_populates in the respective models

    # Composite indexes for common queries
    __table_args__ = (
        # Index for finding active assignments for a client
        Index('ix_client_assignments_client_active', 'client_id', 'is_active', 'status'),
        # Index for finding all assignments by a coach
        Index('ix_client_assignments_coach', 'coach_id', 'is_active'),
        # Index for subscription isolation
        Index('ix_client_assignments_subscription', 'subscription_id', 'is_active'),
        # Index for location isolation (enterprise)
        Index('ix_client_assignments_location', 'location_id', 'is_active'),
        # Composite index for status queries
        Index('ix_client_assignments_status_dates', 'status', 'start_date', 'end_date'),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<ClientProgramAssignment(id={self.id}, client_id={self.client_id}, program_id={self.program_id}, status='{self.status}')>"

    @property
    def is_completed(self) -> bool:
        """Check if the assignment is completed."""
        return self.status == "completed" and self.actual_completion_date is not None

    @property
    def is_overdue(self) -> bool:
        """Check if the assignment is past its end date but not completed."""
        if self.end_date is None or self.is_completed:
            return False
        return date.today() > self.end_date

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage based on current week."""
        # This is a simple calculation - can be enhanced with actual workout completion
        # Assuming program duration is stored in the related Program model
        # For now, return 0 as placeholder
        return 0.0
