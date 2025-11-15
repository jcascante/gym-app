"""
AuditLog database model.

Defines the audit_log table for tracking all user actions and data changes.
Immutable append-only log for compliance and debugging.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Enum as SQLEnum
import enum
from app.models.base import BaseModel, GUID, get_utc_now
from app.models.subscription import JSONBType


class AuditAction(str, enum.Enum):
    """Audit action types."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS = "ACCESS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PASSWORD_RESET = "PASSWORD_RESET"
    ROLE_CHANGE = "ROLE_CHANGE"


class AuditLog(BaseModel):
    """
    AuditLog model for tracking all user actions and data changes.

    This is an immutable append-only log for compliance and debugging.
    Never update or delete audit log entries.

    Attributes:
        subscription_id: Foreign key to subscription (nullable for platform-level events)
        location_id: Foreign key to location (nullable)
        user_id: Foreign key to user who performed the action (nullable for system events)
        action: Type of action performed (CREATE, UPDATE, DELETE, LOGIN, etc.)
        entity_type: Type of entity affected (e.g., 'user', 'subscription', 'workout')
        entity_id: UUID of the affected entity
        changes: JSONB field with before/after state for UPDATE, full record for CREATE/DELETE
        ip_address: IP address of the request
        user_agent: User agent string from the request
        timestamp: Timestamp of the event (defaults to created_at)
        metadata: JSONB field for additional context (reason, request_id, etc.)

    Note: This model inherits from BaseModel but doesn't use created_by/updated_by
    since audit logs should never be updated or associated with a creator.
    """
    __tablename__ = "audit_log"

    subscription_id = Column(
        GUID,
        ForeignKey('subscriptions.id', ondelete='SET NULL'),
        nullable=True,  # Null for platform-level events
        index=True,
        doc="Foreign key to subscription (null for platform-level events)"
    )

    location_id = Column(
        GUID,
        ForeignKey('locations.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="Foreign key to location (nullable)"
    )

    user_id = Column(
        GUID,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,  # Null for system events
        index=True,
        doc="Foreign key to user who performed the action (null for system events)"
    )

    action = Column(
        SQLEnum(AuditAction, name='audit_action_enum', native_enum=False),
        nullable=False,
        index=True,
        doc="Type of action performed"
    )

    entity_type = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Type of entity affected (e.g., 'user', 'subscription', 'workout')"
    )

    entity_id = Column(
        GUID,
        nullable=True,  # Null for some events like LOGIN
        index=True,
        doc="UUID of the affected entity"
    )

    changes = Column(
        JSONBType,
        nullable=True,
        doc="Before/after state for UPDATE, full record for CREATE/DELETE"
    )

    ip_address = Column(
        String(45),  # IPv6 max length
        nullable=True,
        doc="IP address of the request"
    )

    user_agent = Column(
        String(500),
        nullable=True,
        doc="User agent string from the request"
    )

    timestamp = Column(
        DateTime,
        default=get_utc_now,
        nullable=False,
        index=True,
        doc="Timestamp of the event"
    )

    extra_metadata = Column(
        JSONBType,
        nullable=True,
        doc="Additional context (reason, request_id, etc.)"
    )

    # Composite indexes for common queries
    __table_args__ = (
        # Index for querying user's actions
        Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        # Index for querying subscription's audit trail
        Index('ix_audit_subscription_timestamp', 'subscription_id', 'timestamp'),
        # Index for querying by action type
        Index('ix_audit_action_timestamp', 'action', 'timestamp'),
        # Index for querying by entity
        Index('ix_audit_entity', 'entity_type', 'entity_id', 'timestamp'),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<AuditLog(id={self.id}, action={self.action}, entity_type='{self.entity_type}', user_id={self.user_id}, timestamp={self.timestamp})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary (for logging/debugging)."""
        return {
            "id": str(self.id),
            "subscription_id": str(self.subscription_id) if self.subscription_id else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action.value if self.action else None,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "extra_metadata": self.extra_metadata,
        }
