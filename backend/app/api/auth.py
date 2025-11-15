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
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.subscription import Subscription
from app.schemas.user import UserResponse
from app.schemas.auth import TokenResponse, MessageResponse

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
        user=UserResponse.model_validate(user).model_dump()
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
    """,
    responses={
        200: {
            "description": "Current user profile",
        },
        401: {
            "description": "Not authenticated or invalid token",
        }
    },
    tags=["Authentication"]
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.

    Uses the get_current_user dependency to ensure user is authenticated
    and account is active.
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
    """,
    responses={
        200: {
            "description": "Authentication successful",
        },
        401: {
            "description": "Not authenticated",
        }
    },
    tags=["Authentication"]
)
async def test_auth(
    current_user: User = Depends(get_current_user)
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
