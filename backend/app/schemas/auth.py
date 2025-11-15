"""
Authentication Pydantic schemas for login and token management.

These schemas define the structure for authentication-related API requests and responses,
including login credentials, JWT tokens, and token payloads.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole
from app.models.subscription import SubscriptionType


class LoginRequest(BaseModel):
    """
    Schema for login requests.

    Accepts email and password for authentication.
    """
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john.doe@example.com"]
    )
    password: str = Field(
        ...,
        description="User's password",
        examples=["SecurePassword123!"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePassword123!"
            }
        }
    )


class TokenResponse(BaseModel):
    """
    Schema for successful login response.

    Returns JWT access token and user information with subscription context.
    The access_token should be included in subsequent requests
    in the Authorization header as: 'Bearer {access_token}'
    """
    access_token: str = Field(
        ...,
        description="JWT access token for authentication",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer' for JWT)",
        examples=["bearer"]
    )
    user: Dict[str, Any] = Field(
        ...,
        description="User information including role and subscription context",
        examples=[{
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "john.doe@example.com",
            "role": "CLIENT",
            "subscription_id": "660e8400-e29b-41d4-a716-446655440000",
            "location_id": None,
            "is_active": True
        }]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huLmRvZUBleGFtcGxlLmNvbSIsInVzZXJfaWQiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJyb2xlIjoiQ0xJRU5UIiwic3Vic2NyaXB0aW9uX2lkIjoiNjYwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAwIiwiZXhwIjoxNzA1MzI2MDAwfQ...",
                "token_type": "bearer",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "john.doe@example.com",
                    "role": "CLIENT",
                    "subscription_id": "660e8400-e29b-41d4-a716-446655440000",
                    "location_id": None,
                    "profile": {
                        "name": "John Doe",
                        "phone": "+1234567890"
                    },
                    "is_active": True,
                    "created_at": "2025-01-15T10:30:00",
                    "updated_at": "2025-01-15T10:30:00"
                }
            }
        }
    )


class TokenPayload(BaseModel):
    """
    Schema for decoded JWT token payload.

    Internal use for validating token contents.
    Includes user ID, role, subscription context, and permissions.
    """
    sub: str = Field(
        ...,
        description="Subject (user email from token)"
    )
    user_id: str = Field(
        ...,
        description="User ID from token (UUID string)"
    )
    subscription_id: Optional[str] = Field(
        None,
        description="Subscription ID (null for APPLICATION_SUPPORT)"
    )
    location_id: Optional[str] = Field(
        None,
        description="Location ID (ENTERPRISE only)"
    )
    role: str = Field(
        ...,
        description="User role"
    )
    subscription_type: Optional[str] = Field(
        None,
        description="Subscription type (INDIVIDUAL, GYM, ENTERPRISE)"
    )
    features: Optional[Dict[str, Any]] = Field(
        None,
        description="Subscription features enabled"
    )
    limits: Optional[Dict[str, Any]] = Field(
        None,
        description="Subscription resource limits"
    )
    exp: Optional[int] = Field(
        None,
        description="Token expiration timestamp (Unix epoch)"
    )
    iat: Optional[int] = Field(
        None,
        description="Token issued at timestamp (Unix epoch)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "john.doe@example.com",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "subscription_id": "660e8400-e29b-41d4-a716-446655440000",
                "location_id": None,
                "role": "CLIENT",
                "subscription_type": "GYM",
                "features": {
                    "multi_location": False,
                    "api_access": False
                },
                "limits": {
                    "max_coaches": 25,
                    "max_clients": 500
                },
                "exp": 1705326000,
                "iat": 1705324200
            }
        }
    )


class PasswordChangeRequest(BaseModel):
    """
    Schema for password change requests.

    Requires current password for security.
    """
    current_password: str = Field(
        ...,
        description="User's current password for verification",
        examples=["OldPassword123!"]
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (minimum 8 characters)",
        examples=["NewSecurePassword456!"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!"
            }
        }
    )


class MessageResponse(BaseModel):
    """
    Generic message response schema.

    Used for success/error messages without complex data.
    """
    message: str = Field(
        ...,
        description="Response message",
        examples=["Operation completed successfully"]
    )
    detail: Optional[str] = Field(
        None,
        description="Additional details about the response",
        examples=["User account has been successfully created"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
                "detail": "User account has been successfully created"
            }
        }
    )
