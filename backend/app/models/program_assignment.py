"""
Program Assignment database model.

Defines the ProgramAssignment model for tracking when templates are assigned to clients.
"""
from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey, Index, Text, Boolean
from app.models.base import BaseModel, GUID
from app.models.subscription import JSONBType


class ProgramAssignment(BaseModel):
    """
    ProgramAssignment model representing template assignments to clients.

    When a coach assigns a template to a client, a ProgramAssignment is created.
    This tracks the relationship between the template, the client, and the
    actual program instance (which is a copy of the template with applied parameters).

    Attributes:
        subscription_id: Foreign key to subscription
        template_id: Foreign key to the original template
        client_id: Foreign key to the client (user)
        assigned_by: Foreign key to the coach who assigned
        program_id: Foreign key to the actual program instance (copy of template)
        assignment_parameters: JSONB with parameter values used
        start_date: When the program starts
        end_date: Calculated end date based on duration
        actual_end_date: When the client actually completed
        status: active, paused, completed, cancelled
        completion_percentage: Progress percentage (0.00 to 100.00)
        workouts_completed: Number of workouts completed
        workouts_total: Total workouts in program
        current_week: Current week number (1-based)
        current_day: Current day number (1-based)
        client_rating: Client's rating (0.00 to 5.00)
        client_feedback: Client's feedback text
        coach_notes: Coach's notes about assignment
        is_active: Soft delete flag

    Inherits from BaseModel:
        id: Primary key (UUID)
        created_at: When assignment was created
        created_by: User ID who created (coach)
        updated_at: Last modification timestamp
        updated_by: User ID who last updated

    Database Relationships:
        - Subscription (many-to-one)
        - Template (many-to-one with Program)
        - Client (many-to-one with User)
        - Assigned By (many-to-one with User)
        - Program Instance (many-to-one with Program)
    """
    __tablename__ = "program_assignments"

    # Subscription
    subscription_id = Column(
        GUID,
        ForeignKey('subscriptions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to subscription"
    )

    # Template and client
    template_id = Column(
        GUID,
        ForeignKey('programs.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        doc="Foreign key to the source template"
    )

    client_id = Column(
        GUID,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to the client (assigned to)"
    )

    assigned_by = Column(
        GUID,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        doc="Foreign key to the coach who assigned"
    )

    # Program instance (can be customized after assignment)
    program_id = Column(
        GUID,
        ForeignKey('programs.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to the actual program instance (copy of template)"
    )

    # Assignment parameters (values provided when creating from template)
    assignment_parameters = Column(
        JSONBType,
        nullable=False,
        doc="Parameter values: {goal: 'Bench 315 lbs', focus_lifts: [...], current_1rm: {...}}"
    )

    # Scheduling
    start_date = Column(
        Date,
        nullable=False,
        index=True,
        doc="Program start date"
    )

    end_date = Column(
        Date,
        nullable=True,
        doc="Calculated end date based on template duration"
    )

    actual_end_date = Column(
        Date,
        nullable=True,
        doc="When client actually completed the program"
    )

    # Status
    status = Column(
        String(50),
        default='active',
        nullable=False,
        index=True,
        doc="Status: active, paused, completed, cancelled"
    )

    completion_percentage = Column(
        Float,
        default=0.00,
        nullable=False,
        doc="Completion percentage (0.00 to 100.00)"
    )

    # Progress tracking
    workouts_completed = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of workouts completed"
    )

    workouts_total = Column(
        Integer,
        nullable=False,
        doc="Total number of workouts in program"
    )

    current_week = Column(
        Integer,
        default=1,
        nullable=False,
        doc="Current week number (1-based)"
    )

    current_day = Column(
        Integer,
        default=1,
        nullable=False,
        doc="Current day number (1-based)"
    )

    # Client feedback
    client_rating = Column(
        Float,
        nullable=True,
        doc="Client's rating (0.00 to 5.00)"
    )

    client_feedback = Column(
        Text,
        nullable=True,
        doc="Client's feedback text"
    )

    # Coach notes
    coach_notes = Column(
        Text,
        nullable=True,
        doc="Coach's notes about this assignment"
    )

    # Soft delete
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Soft delete flag"
    )

    # Composite indexes
    __table_args__ = (
        # Index for client's active assignments (unique name per table)
        Index('ix_program_assignments_client_active', 'client_id', 'is_active'),
        # Index for template usage tracking
        Index('ix_program_assignments_template', 'template_id'),
        # Index for subscription queries
        Index('ix_program_assignments_subscription', 'subscription_id'),
        # Index for status queries
        Index('ix_program_assignments_status_active', 'status', 'is_active'),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<ProgramAssignment(id={self.id}, client_id={self.client_id}, status='{self.status}')>"
