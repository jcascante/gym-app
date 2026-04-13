"""
Workout Log database model.

Tracks individual workout sessions for clients, including completion status,
exercise performance data, and session notes for progress tracking.
"""
import enum

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import GUID, BaseModel


class WorkoutStatus(str, enum.Enum):
    """Workout session status."""
    COMPLETED = "completed"
    SKIPPED = "skipped"
    SCHEDULED = "scheduled"


class WorkoutLog(BaseModel):
    """
    WorkoutLog model representing individual workout sessions.

    This model tracks when a client completes (or skips) a workout session,
    including performance data for exercises performed and coach/client notes.

    Attributes:
        subscription_id: Foreign key to subscription (for multi-tenant isolation)
        client_program_assignment_id: Foreign key to the program assignment this workout belongs to
        client_id: Foreign key to the client performing the workout
        coach_id: Foreign key to coach who assigned this workout (for reference)
        program_id: Foreign key to the program this workout is part of

        workout_date: Date/time of the workout session
        status: Workout status (completed, skipped, scheduled)
        duration_minutes: How long the workout took (if completed)
        notes: Client notes about how they felt, any modifications, issues, etc.

    Inherits from BaseModel:
        id: Primary key (UUID)
        created_at: When log entry was created
        created_by: User ID who created (audit trail)
        updated_at: Last modification timestamp
        updated_by: User ID who last updated

    Database Relationships:
        - client: Many-to-one with User
        - coach: Many-to-one with User
        - program: Many-to-one with Program
        - assignment: Many-to-one with ClientProgramAssignment
        - exercise_logs: One-to-many with ExerciseLog (cascade delete)
        - subscription: Many-to-one with Subscription
    """
    __tablename__ = "workout_logs"

    # Foreign keys
    subscription_id = Column(
        GUID,
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_program_assignment_id = Column(
        GUID,
        ForeignKey("client_program_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coach_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    program_id = Column(
        GUID,
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Link to the specific program day this session covers
    program_day_id = Column(
        GUID,
        ForeignKey("program_days.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Workout session data
    workout_date = Column(
        DateTime,
        nullable=False,
        index=True,
    )
    status = Column(
        SQLEnum(WorkoutStatus),
        default=WorkoutStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    duration_minutes = Column(
        String,  # Store as string to preserve flexibility (null if skipped, number if completed)
        nullable=True,
    )

    # Explicit day status — more precise than overloading WorkoutStatus
    day_status = Column(
        String(20),
        nullable=True,
        index=True,
        doc="completed | skipped | partial",
    )

    session_rating = Column(
        Integer,
        nullable=True,
        doc="Client self-rating of the session (1–5)",
    )

    notes = Column(
        Text,
        nullable=True,
    )

    # Relationships
    client = relationship(
        "User",
        foreign_keys=[client_id],
        backref="workouts_logged",
        lazy="joined",
    )
    coach = relationship(
        "User",
        foreign_keys=[coach_id],
        backref="client_workouts_monitored",
        lazy="joined",
    )
    program = relationship(
        "Program",
        backref="workout_logs",
        lazy="joined",
    )
    assignment = relationship(
        "ClientProgramAssignment",
        backref="workout_logs",
        lazy="joined",
    )
    subscription = relationship(
        "Subscription",
        backref="workout_logs",
        lazy="joined",
    )
    exercise_logs = relationship(
        "WorkoutExerciseLog",
        back_populates="workout_log",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_workout_logs_client_date", "client_id", "workout_date"),
        Index("idx_workout_logs_assignment_date", "client_program_assignment_id", "workout_date"),
        Index("idx_workout_logs_subscription_date", "subscription_id", "workout_date"),
    )

    def __repr__(self) -> str:
        return f"<WorkoutLog(id={self.id}, client_id={self.client_id}, workout_date={self.workout_date}, status={self.status})>"
