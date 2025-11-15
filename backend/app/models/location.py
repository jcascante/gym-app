"""
Location database model.

Defines the Location table structure for ENTERPRISE subscriptions.
Represents physical locations within a multi-location subscription.
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Index
from app.models.base import BaseModel, GUID
from app.models.subscription import JSONBType


class Location(BaseModel):
    """
    Location model for ENTERPRISE subscriptions.

    Attributes:
        subscription_id: Foreign key to parent subscription
        name: Location name (e.g., "Downtown Branch", "West Side Location")
        address: JSONB field with address details (street, city, state, zip, country)
        contact_info: JSONB field with contact details (phone, email, manager_name)
        settings: JSONB field with location-specific configuration
        is_active: Whether the location is active (soft delete capability)

    Inherits from BaseModel:
        id: Primary key (UUID)
        created_at: Timestamp of creation
        created_by: User who created the location
        updated_at: Timestamp of last update
        updated_by: User who last updated the location
    """
    __tablename__ = "locations"

    subscription_id = Column(
        GUID,
        ForeignKey('subscriptions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to parent subscription"
    )

    name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Location name (e.g., 'Downtown Branch')"
    )

    address = Column(
        JSONBType,
        nullable=True,
        doc="Address details (street, city, state, zip, country)"
    )

    contact_info = Column(
        JSONBType,
        nullable=True,
        doc="Contact information (phone, email, manager_name)"
    )

    settings = Column(
        JSONBType,
        nullable=True,
        default=dict,
        doc="Location-specific configuration"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the location is active (false = soft deleted)"
    )

    # Composite indexes for common queries
    __table_args__ = (
        # Index for active locations within a subscription
        Index('ix_locations_subscription_active', 'subscription_id', 'is_active'),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Location(id={self.id}, name='{self.name}', subscription_id={self.subscription_id}, is_active={self.is_active})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary (for logging/debugging)."""
        return {
            "id": str(self.id),
            "subscription_id": str(self.subscription_id),
            "name": self.name,
            "address": self.address,
            "contact_info": self.contact_info,
            "settings": self.settings,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
