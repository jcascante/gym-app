"""
WorkoutExerciseLog model — one row per set logged during a workout session.
"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import GUID, BaseModel


class WorkoutExerciseLog(BaseModel):
    """
    Tracks each set performed during a workout session.

    One row per set so real training data is preserved:
    e.g., set 1: 225 lbs RPE 7, set 2: 215 lbs RPE 9.
    """

    __tablename__ = "workout_exercise_logs"

    subscription_id = Column(
        GUID,
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    workout_log_id = Column(
        GUID,
        ForeignKey("workout_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Nullable — free-form workouts may not have a program day exercise
    program_day_exercise_id = Column(
        GUID,
        ForeignKey("program_day_exercises.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Denormalized for display (exercise may be renamed/deleted later)
    exercise_name = Column(String(255), nullable=False)

    set_number = Column(Integer, nullable=False)
    actual_reps = Column(Integer, nullable=True)
    actual_weight_lbs = Column(Float, nullable=True)
    actual_rpe = Column(Float, nullable=True)  # 1.0–10.0
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=False)

    # Relationships
    workout_log = relationship(
        "WorkoutLog",
        back_populates="exercise_logs",
    )

    __table_args__ = (
        Index("ix_workout_exercise_logs_workout", "workout_log_id"),
        Index("ix_workout_exercise_logs_subscription", "subscription_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<WorkoutExerciseLog(workout_log_id={self.workout_log_id}, "
            f"exercise='{self.exercise_name}', set={self.set_number})>"
        )
