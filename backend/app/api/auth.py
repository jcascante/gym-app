"""
Authentication API routes.

Provides endpoints for user login with role-based authorization.
All endpoints include comprehensive OpenAPI documentation for Swagger UI.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token
)
from app.core.deps import get_current_user, get_current_user_check_password, get_subscription_admin_user
from app.models.user import User, UserRole
from app.models.subscription import Subscription
from app.schemas.user import UserResponse
from app.schemas.auth import TokenResponse, MessageResponse, PasswordChangeRequest, AdminResetPasswordRequest

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get access token",
    description="""
    Authenticate with email and password to receive a JWT access token.

    **Authentication Flow:**
    1. Submit email and password (use email in the username field)
    2. Receive access token with role and subscription context
    3. Include token in subsequent requests: `Authorization: Bearer {token}`

    **Security:**
    - Passwords are verified using bcrypt (slow hashing prevents brute force)
    - Tokens expire after 30 minutes (configurable)
    - Token includes user role and subscription information for authorization
    - Failed login attempts do not reveal whether user exists (prevents enumeration)

    **Usage in Swagger UI:**
    1. Click "Authorize" button at the top
    2. Enter your email in the "username" field (e.g., admin@testgym.com)
    3. Enter your password in the "password" field
    4. Click "Authorize" to save the token
    5. All protected endpoints will now include the token automatically
    """,
    responses={
        200: {
            "description": "Login successful, returns access token and user data",
        },
        401: {
            "description": "Invalid credentials or inactive account",
        },
        403: {
            "description": "Subscription suspended or cancelled",
        }
    },
    tags=["Authentication"]
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible login endpoint with role-based authentication.

    Accepts email in the 'username' field for OAuth2 compatibility.
    Returns JWT token with user role and subscription context.
    """
    # Query user by email (username field contains email)
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    # NOTE: Same error message for both cases to prevent user enumeration
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get subscription info (if user has one)
    subscription = None
    if user.subscription_id:
        subscription_result = await db.execute(
            select(Subscription).where(Subscription.id == user.subscription_id)
        )
        subscription = subscription_result.scalar_one_or_none()

        # Check subscription status
        if subscription and subscription.status.value != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription is {subscription.status.value}. Please contact support.",
            )

    # Update last login timestamp
    user.last_login_at = datetime.now()
    await db.commit()

    # Create access token with full context
    token_data = {
        "sub": user.email,
        "user_id": str(user.id),
        "role": user.role.value,
        "subscription_id": str(user.subscription_id) if user.subscription_id else None,
        "location_id": str(user.location_id) if user.location_id else None,
    }

    # Add subscription context if available
    if subscription:
        token_data.update({
            "subscription_type": subscription.subscription_type.value,
            "features": subscription.features,
            "limits": subscription.limits,
        })

    access_token = create_access_token(data=token_data)

    # Return token and user data
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user).model_dump(),
        password_must_be_changed=user.password_must_be_changed
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="""
    Get the profile information for the currently authenticated user.

    **Authentication Required:**
    This endpoint requires a valid JWT token in the Authorization header.

    **Returns:**
    - All user profile information except password
    - Includes role, subscription context, and location assignment

    **Note:**
    If password_must_be_changed is true, you must change your password before accessing this endpoint.
    """,
    responses={
        200: {
            "description": "Current user profile",
        },
        401: {
            "description": "Not authenticated or invalid token",
        },
        403: {
            "description": "Password must be changed",
        }
    },
    tags=["Authentication"]
)
async def get_me(
    current_user: User = Depends(get_current_user_check_password)
):
    """
    Get current authenticated user's profile.

    Uses the get_current_user_check_password dependency to ensure user is authenticated,
    account is active, and password has been changed if required.
    """
    return UserResponse.model_validate(current_user)


@router.get(
    "/test-auth",
    response_model=MessageResponse,
    summary="Test authentication",
    description="""
    Simple endpoint to test if authentication is working correctly.

    **Purpose:**
    - Verify JWT token is being sent correctly
    - Confirm token validation is working
    - Test that protected routes are properly secured
    - Display user role and subscription info

    **Note:**
    If password_must_be_changed is true, you must change your password before accessing this endpoint.
    """,
    responses={
        200: {
            "description": "Authentication successful",
        },
        401: {
            "description": "Not authenticated",
        },
        403: {
            "description": "Password must be changed",
        }
    },
    tags=["Authentication"]
)
async def test_auth(
    current_user: User = Depends(get_current_user_check_password)
):
    """
    Test endpoint to verify authentication is working.

    Returns a message with the current user's information.
    """
    profile_name = current_user.profile.get("name") if current_user.profile else "User"
    return MessageResponse(
        message=f"Authentication working! Hello {profile_name}",
        detail=f"Role: {current_user.role.value}, Email: {current_user.email}"
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change user password",
    description="""
    Change the current user's password.

    **Requirements:**
    - Must provide current password for verification
    - New password must be at least 8 characters
    - User must be authenticated

    **Use Cases:**
    - Regular password changes for security
    - **First-time login**: New clients created by coaches must change their temporary password
    - Password reset after security concern

    **Important for New Clients:**
    When a coach creates a new client account, a random temporary password is generated.
    The client must use this endpoint to change their password on first login.
    The `password_must_be_changed` flag in the login response indicates this requirement.
    """,
    responses={
        200: {
            "description": "Password changed successfully",
        },
        401: {
            "description": "Current password is incorrect",
        },
        400: {
            "description": "New password doesn't meet requirements",
        }
    },
    tags=["Authentication"]
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password for the authenticated user.

    Verifies current password before allowing change.
    Sets password_must_be_changed to False after successful change.
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Validate new password is different from current
    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    current_user.password_must_be_changed = False  # Clear the flag
    current_user.updated_by = current_user.id

    await db.commit()

    return MessageResponse(
        message="Password changed successfully",
        detail="You can now access all features with your new password"
    )


@router.post(
    "/admin/reset-password",
    response_model=MessageResponse,
    summary="Admin: Reset user password",
    description="""
    Reset a user's password (Admin/Support only).

    **Required permissions**: APPLICATION_SUPPORT or SUBSCRIPTION_ADMIN

    **Use Cases:**
    - User forgot their password and needs a manual reset
    - Emergency password reset by support staff
    - Account recovery

    **Important:**
    - Sets a temporary password that the user will be forced to change on next login
    - Only admins within the same subscription can reset passwords (except APPLICATION_SUPPORT)
    - APPLICATION_SUPPORT can reset passwords for any user
    - The `force_password_change` flag (default: true) ensures user must change the temporary password

    **Security:**
    - New password must meet minimum requirements (8+ characters)
    - User receives `password_must_be_changed=true` flag
    - User cannot access other endpoints until password is changed
    - Admin should communicate the temporary password to user securely
    """,
    responses={
        200: {
            "description": "Password reset successfully",
        },
        401: {
            "description": "Not authenticated",
        },
        403: {
            "description": "Insufficient permissions (not admin/support)",
        },
        404: {
            "description": "User not found",
        }
    },
    tags=["Authentication", "Admin"]
)
async def admin_reset_password(
    request: AdminResetPasswordRequest,
    current_user: User = Depends(get_subscription_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to reset a user's password.

    Only APPLICATION_SUPPORT and SUBSCRIPTION_ADMIN users can access this.
    Admins can only reset passwords for users in their own subscription
    (except APPLICATION_SUPPORT who can reset any user's password).
    """
    # Find the target user
    result = await db.execute(
        select(User).where(User.email == request.user_email)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {request.user_email}",
        )

    # Check subscription access (except for APPLICATION_SUPPORT)
    if current_user.role != UserRole.APPLICATION_SUPPORT:
        if target_user.subscription_id != current_user.subscription_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot reset password for users in different subscriptions",
            )

    # Prevent resetting APPLICATION_SUPPORT passwords unless you are APPLICATION_SUPPORT
    if target_user.role == UserRole.APPLICATION_SUPPORT and current_user.role != UserRole.APPLICATION_SUPPORT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only APPLICATION_SUPPORT can reset APPLICATION_SUPPORT passwords",
        )

    # Update password
    target_user.hashed_password = get_password_hash(request.new_password)
    target_user.password_must_be_changed = request.force_password_change
    target_user.updated_by = current_user.id

    await db.commit()

    # Build response message
    force_change_msg = " User must change password on next login." if request.force_password_change else ""

    return MessageResponse(
        message=f"Password reset successfully for {target_user.email}",
        detail=f"New temporary password has been set.{force_change_msg} Please communicate the password to the user securely."
    )
