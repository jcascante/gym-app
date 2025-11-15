"""
Subscriptions API routes with role-based access control.

Provides CRUD operations for subscription management.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.deps import (
    get_current_user,
    get_application_support_user,
    check_subscription_access
)
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionType, SubscriptionStatus
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.schemas.auth import MessageResponse

router = APIRouter()


@router.get(
    "",
    response_model=list[SubscriptionResponse],
    summary="List subscriptions",
    description="""
    Get a list of subscriptions.

    **Authorization:**
    - APPLICATION_SUPPORT: Can list all subscriptions
    - SUBSCRIPTION_ADMIN: Can only see their own subscription
    """,
    tags=["Subscriptions"]
)
async def list_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    subscription_type: Optional[SubscriptionType] = Query(None, description="Filter by type"),
    status: Optional[SubscriptionStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List subscriptions with filtering."""

    query = select(Subscription)

    # Non-support users can only see their own subscription
    if current_user.role != UserRole.APPLICATION_SUPPORT:
        if not current_user.subscription_id:
            return []
        query = query.where(Subscription.id == current_user.subscription_id)

    # Apply filters
    if subscription_type:
        query = query.where(Subscription.subscription_type == subscription_type)

    if status:
        query = query.where(Subscription.status == status)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    subscriptions = result.scalars().all()

    return [SubscriptionResponse.model_validate(sub) for sub in subscriptions]


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create subscription",
    description="""
    Create a new subscription.

    **Authorization:**
    - APPLICATION_SUPPORT only

    This creates the top-level tenant entity. After creation, you can create
    a SUBSCRIPTION_ADMIN user for the new subscription.
    """,
    tags=["Subscriptions"]
)
async def create_subscription(
    subscription_in: SubscriptionCreate,
    current_user: User = Depends(get_application_support_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new subscription (APPLICATION_SUPPORT only)."""

    # Check if name already exists
    result = await db.execute(
        select(Subscription).where(Subscription.name == subscription_in.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription name already exists"
        )

    # Create subscription
    subscription = Subscription(
        name=subscription_in.name,
        subscription_type=subscription_in.subscription_type,
        status=SubscriptionStatus.ACTIVE,
        features=subscription_in.features,
        limits=subscription_in.limits,
        billing_info=subscription_in.billing_info,
        created_by=current_user.id
    )

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return SubscriptionResponse.model_validate(subscription)


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get subscription",
    description="""
    Get subscription details.

    **Authorization:**
    - APPLICATION_SUPPORT: Can view any subscription
    - SUBSCRIPTION_ADMIN: Can only view their own subscription
    """,
    tags=["Subscriptions"]
)
async def get_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get subscription by ID."""

    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Check access
    check_subscription_access(current_user, subscription_id)

    return SubscriptionResponse.model_validate(subscription)


@router.patch(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Update subscription",
    description="""
    Update subscription settings.

    **Authorization:**
    - APPLICATION_SUPPORT: Can update any subscription (all fields)
    - SUBSCRIPTION_ADMIN: Can update their own subscription (limited fields)

    **Updatable by SUBSCRIPTION_ADMIN:**
    - name, billing_info

    **Updatable by APPLICATION_SUPPORT:**
    - All fields including subscription_type, status, features, limits
    """,
    tags=["Subscriptions"]
)
async def update_subscription(
    subscription_id: UUID,
    subscription_update: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update subscription."""

    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Check access
    check_subscription_access(current_user, subscription_id)

    # Apply updates
    update_data = subscription_update.model_dump(exclude_unset=True)

    # Non-support users have limited update permissions
    if current_user.role != UserRole.APPLICATION_SUPPORT:
        allowed_fields = {"name", "billing_info"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

    # Update fields
    for field, value in update_data.items():
        setattr(subscription, field, value)

    subscription.updated_by = current_user.id

    await db.commit()
    await db.refresh(subscription)

    return SubscriptionResponse.model_validate(subscription)


@router.delete(
    "/{subscription_id}",
    response_model=MessageResponse,
    summary="Delete subscription",
    description="""
    Delete a subscription (sets status to CANCELLED).

    **Authorization:**
    - APPLICATION_SUPPORT only

    **Note:** This cancels the subscription and cascades to all users/locations.
    """,
    tags=["Subscriptions"]
)
async def delete_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_application_support_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a subscription (APPLICATION_SUPPORT only)."""

    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Set status to CANCELLED
    subscription.status = SubscriptionStatus.CANCELLED
    subscription.updated_by = current_user.id

    await db.commit()

    return MessageResponse(
        message="Subscription cancelled successfully",
        detail=f"Subscription '{subscription.name}' has been cancelled"
    )
