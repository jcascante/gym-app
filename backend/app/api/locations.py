"""
Locations API routes for ENTERPRISE subscriptions.

Provides CRUD operations for location management.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import (
    get_current_user,
    get_subscription_admin_user,
    check_subscription_access
)
from app.models.user import User, UserRole
from app.models.location import Location
from app.models.subscription import Subscription, SubscriptionType
from app.schemas.auth import MessageResponse
from pydantic import BaseModel, Field, ConfigDict

router = APIRouter()


# Location Schemas (inline for simplicity)
class LocationBase(BaseModel):
    name: str = Field(..., max_length=255)
    address: Optional[dict] = None
    contact_info: Optional[dict] = None
    settings: Optional[dict] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[dict] = None
    contact_info: Optional[dict] = None
    settings: Optional[dict] = None
    is_active: Optional[bool] = None


class LocationResponse(LocationBase):
    id: UUID
    subscription_id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


@router.get(
    "",
    response_model=list[LocationResponse],
    summary="List locations",
    description="""
    Get locations for a subscription.

    **Authorization:**
    - SUBSCRIPTION_ADMIN: Can list locations in their subscription
    - COACH/CLIENT: Can list locations in their subscription (read-only)
    - APPLICATION_SUPPORT: Can list locations in any subscription

    **Note:** Only applies to ENTERPRISE subscriptions with multi_location feature.
    """,
    tags=["Locations"]
)
async def list_locations(
    subscription_id: Optional[UUID] = Query(None, description="Filter by subscription (APPLICATION_SUPPORT only)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List locations with filtering."""

    # Determine which subscription to query
    if current_user.role == UserRole.APPLICATION_SUPPORT:
        if not subscription_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="subscription_id required for APPLICATION_SUPPORT"
            )
        target_subscription_id = subscription_id
    else:
        if not current_user.subscription_id:
            return []
        target_subscription_id = current_user.subscription_id

    # Build query
    query = select(Location).where(Location.subscription_id == target_subscription_id)

    if is_active is not None:
        query = query.where(Location.is_active == is_active)

    result = await db.execute(query)
    locations = result.scalars().all()

    return [LocationResponse.model_validate(loc) for loc in locations]


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create location",
    description="""
    Create a new location for an ENTERPRISE subscription.

    **Authorization:**
    - SUBSCRIPTION_ADMIN: Can create locations in their subscription
    - APPLICATION_SUPPORT: Can create locations in any subscription

    **Requirements:**
    - Subscription must be ENTERPRISE type
    - Subscription must have multi_location feature enabled
    """,
    tags=["Locations"]
)
async def create_location(
    location_in: LocationCreate,
    subscription_id: Optional[UUID] = Query(None, description="Subscription ID (APPLICATION_SUPPORT only)"),
    current_user: User = Depends(get_subscription_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new location."""

    # Determine subscription
    if current_user.role == UserRole.APPLICATION_SUPPORT:
        if not subscription_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="subscription_id required"
            )
        target_subscription_id = subscription_id
    else:
        target_subscription_id = current_user.subscription_id

    # Verify subscription exists and is ENTERPRISE
    result = await db.execute(
        select(Subscription).where(Subscription.id == target_subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    if subscription.subscription_type != SubscriptionType.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Locations are only available for ENTERPRISE subscriptions"
        )

    if not subscription.features.get("multi_location", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multi-location feature not enabled for this subscription"
        )

    # Create location
    location = Location(
        subscription_id=target_subscription_id,
        name=location_in.name,
        address=location_in.address,
        contact_info=location_in.contact_info,
        settings=location_in.settings or {},
        is_active=True,
        created_by=current_user.id
    )

    db.add(location)
    await db.commit()
    await db.refresh(location)

    return LocationResponse.model_validate(location)


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Get location",
    description="""
    Get location details.

    **Authorization:**
    - Users can view locations in their subscription
    - APPLICATION_SUPPORT can view any location
    """,
    tags=["Locations"]
)
async def get_location(
    location_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get location by ID."""

    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Check access
    check_subscription_access(current_user, location.subscription_id)

    return LocationResponse.model_validate(location)


@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Update location",
    description="""
    Update location details.

    **Authorization:**
    - SUBSCRIPTION_ADMIN: Can update locations in their subscription
    - APPLICATION_SUPPORT: Can update any location
    """,
    tags=["Locations"]
)
async def update_location(
    location_id: UUID,
    location_update: LocationUpdate,
    current_user: User = Depends(get_subscription_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update location."""

    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Check access
    check_subscription_access(current_user, location.subscription_id)

    # Apply updates
    update_data = location_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(location, field, value)

    location.updated_by = current_user.id

    await db.commit()
    await db.refresh(location)

    return LocationResponse.model_validate(location)


@router.delete(
    "/{location_id}",
    response_model=MessageResponse,
    summary="Delete location",
    description="""
    Delete a location (soft delete - sets is_active=False).

    **Authorization:**
    - SUBSCRIPTION_ADMIN: Can delete locations in their subscription
    - APPLICATION_SUPPORT: Can delete any location
    """,
    tags=["Locations"]
)
async def delete_location(
    location_id: UUID,
    current_user: User = Depends(get_subscription_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a location."""

    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Check access
    check_subscription_access(current_user, location.subscription_id)

    # Soft delete
    location.is_active = False
    location.updated_by = current_user.id

    await db.commit()

    return MessageResponse(
        message="Location deleted successfully",
        detail=f"Location '{location.name}' has been deactivated"
    )
