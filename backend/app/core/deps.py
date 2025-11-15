"""
Authentication and authorization dependencies for route protection.

These dependency functions are used with FastAPI's Depends() to inject
authenticated users into route handlers and enforce authorization rules based on
roles and subscription context.
"""
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_access_token
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.auth import TokenPayload


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    This is the primary authentication dependency. Use it to protect routes
    that require authentication.

    Returns:
        User: The authenticated user from the database with subscription context

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found
        HTTPException 401: If user account is inactive
        HTTPException 403: If subscription is suspended or cancelled
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and validate JWT token
        payload = decode_access_token(token)

        # Extract user data from token
        email: Optional[str] = payload.get("sub")
        user_id: Optional[str] = payload.get("user_id")

        if email is None or user_id is None:
            raise credentials_exception

        # Create token payload for validation
        token_data = TokenPayload(
            sub=email,
            user_id=user_id,
            subscription_id=payload.get("subscription_id"),
            location_id=payload.get("location_id"),
            role=payload.get("role", ""),
            subscription_type=payload.get("subscription_type"),
            features=payload.get("features"),
            limits=payload.get("limits"),
            exp=payload.get("exp"),
            iat=payload.get("iat")
        )

    except Exception:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == UUID(token_data.user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
        )

    # Check subscription status (except for APPLICATION_SUPPORT)
    if user.role != UserRole.APPLICATION_SUPPORT and user.subscription_id:
        subscription_result = await db.execute(
            select(Subscription).where(Subscription.id == user.subscription_id)
        )
        subscription = subscription_result.scalar_one_or_none()

        if subscription is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subscription not found",
            )

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription is {subscription.status.value}. Please contact support.",
            )

    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to restrict routes to specific user roles.

    Args:
        *allowed_roles: One or more UserRole values that are allowed access

    Returns:
        Dependency function that checks user role

    Example:
        ```python
        @router.post("/users")
        async def create_user(
            user_data: UserCreate,
            current_user: User = Depends(require_role(UserRole.SUBSCRIPTION_ADMIN, UserRole.APPLICATION_SUPPORT))
        ):
            # Only admins and support can create users
            pass
        ```
    """
    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(r.value for r in allowed_roles)}",
            )
        return current_user

    return check_role


async def get_application_support_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to restrict routes to APPLICATION_SUPPORT users only.

    APPLICATION_SUPPORT users have cross-subscription access for support/debugging.
    All access is logged for compliance.
    """
    if current_user.role != UserRole.APPLICATION_SUPPORT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. APPLICATION_SUPPORT role required.",
        )
    return current_user


async def get_subscription_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to restrict routes to SUBSCRIPTION_ADMIN users.

    SUBSCRIPTION_ADMIN users can manage their subscription and all users within it.
    """
    if current_user.role not in [UserRole.SUBSCRIPTION_ADMIN, UserRole.APPLICATION_SUPPORT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. SUBSCRIPTION_ADMIN role required.",
        )
    return current_user


async def get_coach_or_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to restrict routes to COACH or SUBSCRIPTION_ADMIN users.

    Used for routes that both coaches and admins should access (e.g., creating programs).
    """
    if current_user.role not in [UserRole.COACH, UserRole.SUBSCRIPTION_ADMIN, UserRole.APPLICATION_SUPPORT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. COACH or SUBSCRIPTION_ADMIN role required.",
        )
    return current_user


def check_subscription_access(user: User, resource_subscription_id: UUID) -> None:
    """
    Helper function to verify user has access to a resource's subscription.

    Args:
        user: Current authenticated user
        resource_subscription_id: Subscription ID of the resource being accessed

    Raises:
        HTTPException 403: If user doesn't have access to this subscription
    """
    # APPLICATION_SUPPORT can access any subscription
    if user.role == UserRole.APPLICATION_SUPPORT:
        return

    # Other users can only access their own subscription
    if user.subscription_id != resource_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Resource belongs to a different subscription.",
        )


def check_location_access(user: User, resource_location_id: Optional[UUID]) -> None:
    """
    Helper function to verify user has access to a resource's location (ENTERPRISE only).

    Args:
        user: Current authenticated user
        resource_location_id: Location ID of the resource being accessed

    Raises:
        HTTPException 403: If user doesn't have access to this location
    """
    # APPLICATION_SUPPORT and users without location assignment can access all locations
    if user.role == UserRole.APPLICATION_SUPPORT or user.location_id is None:
        return

    # Users with location assignment can only access their assigned location
    if resource_location_id and user.location_id != resource_location_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Resource belongs to a different location.",
        )


async def get_current_active_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Subscription:
    """
    Dependency to get the current user's active subscription.

    Returns:
        Subscription: The user's subscription

    Raises:
        HTTPException 403: If user has no subscription or it's not active
    """
    if current_user.role == UserRole.APPLICATION_SUPPORT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="APPLICATION_SUPPORT users don't have subscriptions",
        )

    if not current_user.subscription_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no subscription",
        )

    result = await db.execute(
        select(Subscription).where(Subscription.id == current_user.subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Subscription is {subscription.status.value}",
        )

    return subscription
