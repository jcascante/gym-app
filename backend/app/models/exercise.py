"""
Exercise database model.

Defines the Exercise Library for storing exercises (global and subscription-specific).
"""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index, Text
from app.models.base import BaseModel, GUID
from app.models.subscription import JSONBType


class Exercise(BaseModel):
    """
    Exercise model representing exercises in the library.

    Exercises can be:
    1. Global (is_global=True, subscription_id=None) - Available to all subscriptions
    2. Subscription-specific (is_global=False, subscription_id set) - Only for specific gym

    Attributes:
        subscription_id: Foreign key to subscription (null for global exercises)
        created_by: User who created this exercise (null for global exercises)
        name: Exercise name (e.g., "Back Squat", "Kettlebell Press")
        description: Optional description of the exercise
        category: Exercise category (compound, isolation, cardio, mobility)
        muscle_groups: JSONB array of muscle groups targeted
        equipment: JSONB array of equipment required
        video_url: Optional URL to instructional video
        thumbnail_url: Optional URL to thumbnail image
        is_bilateral: Whether exercise is bilateral (true) or unilateral (false)
        is_timed: Whether exercise is timed (planks, cardio) vs rep-based
        default_rest_seconds: Default rest period between sets
        difficulty_level: Difficulty (beginner, intermediate, advanced, elite)
        progression_exercises: JSONB array of UUIDs for easier/harder variations
        is_global: Whether this is a platform-wide exercise
        is_verified: Whether exercise has been quality-checked by platform
        is_active: Soft delete flag

    Inherits from BaseModel:
        id: Primary key (UUID)
        created_at: When exercise was created
        created_by: User ID who created (audit trail)
        updated_at: Last modification timestamp
        updated_by: User ID who last updated

    Database Relationships:
        - Subscription (many-to-one)
        - User (many-to-one, creator)
    """
    __tablename__ = "exercises_library"

    # Subscription and creator
    subscription_id = Column(
        GUID,
        ForeignKey('subscriptions.id', ondelete='CASCADE'),
        nullable=True,  # Null for global exercises
        index=True,
        doc="Foreign key to subscription (null for global exercises)"
    )

    # Exercise metadata
    name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Exercise name (e.g., 'Back Squat', 'Kettlebell Press')"
    )

    description = Column(
        Text,
        nullable=True,
        doc="Exercise description and form cues"
    )

    category = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Exercise category: compound, isolation, cardio, mobility"
    )

    muscle_groups = Column(
        JSONBType,
        default=list,
        nullable=False,
        doc="Muscle groups targeted (e.g., ['chest', 'triceps', 'shoulders'])"
    )

    equipment = Column(
        JSONBType,
        default=list,
        nullable=False,
        doc="Equipment required (e.g., ['barbell', 'bench'])"
    )

    # Media
    video_url = Column(
        String(500),
        nullable=True,
        doc="URL to instructional video"
    )

    thumbnail_url = Column(
        String(500),
        nullable=True,
        doc="URL to thumbnail image"
    )

    # Exercise parameters
    is_bilateral = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether exercise is bilateral (false for single-leg/single-arm)"
    )

    is_timed = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether exercise is timed (true for planks, cardio)"
    )

    default_rest_seconds = Column(
        Integer,
        default=90,
        nullable=False,
        doc="Default rest period between sets in seconds"
    )

    # Difficulty and progression
    difficulty_level = Column(
        String(50),
        nullable=True,
        doc="Difficulty level: beginner, intermediate, advanced, elite"
    )

    progression_exercises = Column(
        JSONBType,
        default=list,
        nullable=False,
        doc="Array of exercise UUIDs representing easier/harder variations"
    )

    # Usage and curation
    is_global = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this is a platform-wide exercise (APPLICATION_SUPPORT only)"
    )

    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether exercise has been quality-checked by platform"
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
        # Index for subscription exercises
        Index('ix_exercises_subscription_active', 'subscription_id', 'is_active'),
        # Index for global exercises
        Index('ix_exercises_global_active', 'is_global', 'is_active'),
        # Index for category searches
        Index('ix_exercises_category', 'category'),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Exercise(id={self.id}, name='{self.name}', category='{self.category}')>"
