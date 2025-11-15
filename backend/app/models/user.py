"""
User database model.

Defines the User table structure with authentication, profile, and role fields.
Includes unique constraints and indexes for optimal query performance.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, Enum as SQLEnum
import enum
from app.models.base import BaseModel, GUID
from app.models.subscription import JSONBType


class UserRole(str, enum.Enum):
    """User role types."""
    APPLICATION_SUPPORT = "APPLICATION_SUPPORT"
    SUBSCRIPTION_ADMIN = "SUBSCRIPTION_ADMIN"
    COACH = "COACH"
    CLIENT = "CLIENT"


class User(BaseModel):
    """
    User model representing authenticated users in the system.

    Attributes:
        subscription_id: Foreign key to subscription (null for APPLICATION_SUPPORT)
        location_id: Foreign key to location (nullable, ENTERPRISE only)
        role: User role (APPLICATION_SUPPORT, SUBSCRIPTION_ADMIN, COACH, CLIENT)
        email: Unique email address used for authentication
        hashed_password: Bcrypt hashed password (never store plain text)
        profile: JSONB field with profile data (name, avatar, bio, etc.)
        is_active: Whether the user account is active (soft delete capability)
        last_login_at: Timestamp of last successful login

    Inherits from BaseModel:
        id: Primary key (UUID)
        created_at: Timestamp of account creation
        created_by: User who created this account (nullable for self-registration)
        updated_at: Timestamp of last update
        updated_by: User who last updated this account

    Database Constraints:
        - email: unique, indexed, not nullable
        - Composite indexes for common queries (subscription + role, etc.)
    """
    __tablename__ = "users"

    # Subscription and location
    subscription_id = Column(
        GUID,
        ForeignKey('subscriptions.id', ondelete='CASCADE'),
        nullable=True,  # Null for APPLICATION_SUPPORT
        index=True,
        doc="Foreign key to subscription (null for APPLICATION_SUPPORT)"
    )

    location_id = Column(
        GUID,
        ForeignKey('locations.id', ondelete='SET NULL'),
        nullable=True,  # Null for users without location assignment
        index=True,
        doc="Foreign key to location (ENTERPRISE only)"
    )

    # Role
    role = Column(
        SQLEnum(UserRole, name='user_role_enum', native_enum=False),
        nullable=False,
        index=True,
        doc="User role (APPLICATION_SUPPORT, SUBSCRIPTION_ADMIN, COACH, CLIENT)"
    )

    # Authentication fields
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User's email address (unique identifier)"
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password"
    )

    # Profile fields (JSONB for flexibility)
    profile = Column(
        JSONBType,
        nullable=True,
        default=dict,
        doc="User profile data (name, avatar, bio, phone, etc.)"
    )

    # Status flags
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the account is active (false = soft deleted)"
    )

    last_login_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp of last successful login"
    )

    # Composite indexes for common queries
    __table_args__ = (
        # Index for login queries (email + active status check)
        Index('ix_users_email_active', 'email', 'is_active'),
        # Index for subscription + role queries
        Index('ix_users_subscription_role', 'subscription_id', 'role'),
        # Index for subscription + active status
        Index('ix_users_subscription_active', 'subscription_id', 'is_active'),
        # Index for location + role (ENTERPRISE queries)
        Index('ix_users_location_role', 'location_id', 'role'),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User(id={self.id}, email='{self.email}', role={self.role}, is_active={self.is_active})>"

    def to_dict(self) -> dict:
        """
        Convert model to dictionary (for logging/debugging).

        Note: Never include hashed_password in dict representations.
        Use schemas for API responses instead.
        """
        return {
            "id": str(self.id),
            "subscription_id": str(self.subscription_id) if self.subscription_id else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "role": self.role.value if self.role else None,
            "email": self.email,
            "profile": self.profile,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
