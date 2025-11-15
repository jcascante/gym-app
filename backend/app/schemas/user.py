"""
User Pydantic schemas for request/response validation.

These schemas define the structure of user data in API requests and responses,
providing automatic validation, serialization, and OpenAPI documentation.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole


class UserBase(BaseModel):
    """
    Base user schema with common fields.
    """
    email: EmailStr = Field(
        ...,
        description="User's email address (unique identifier)",
        examples=["john.doe@example.com"]
    )
    role: UserRole = Field(
        ...,
        description="User role (APPLICATION_SUPPORT, SUBSCRIPTION_ADMIN, COACH, CLIENT)",
        examples=[UserRole.CLIENT]
    )
    profile: Optional[Dict[str, Any]] = Field(
        None,
        description="User profile data (name, avatar, bio, phone, etc.)",
        examples=[{"name": "John Doe", "phone": "+1234567890"}]
    )


class UserCreate(UserBase):
    """
    Schema for user creation requests.

    Used by admins to create new users within their subscription.
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (minimum 8 characters)",
        examples=["SecurePassword123!"]
    )
    subscription_id: Optional[UUID] = Field(
        None,
        description="Subscription ID (null for APPLICATION_SUPPORT)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    location_id: Optional[UUID] = Field(
        None,
        description="Location ID (ENTERPRISE only)",
        examples=["660e8400-e29b-41d4-a716-446655440000"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "coach@example.com",
                "role": "COACH",
                "password": "SecurePassword123!",
                "subscription_id": "550e8400-e29b-41d4-a716-446655440000",
                "profile": {
                    "name": "Jane Smith",
                    "phone": "+1234567890",
                    "bio": "Certified personal trainer"
                }
            }
        }
    )


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.

    All fields are optional to allow partial updates.
    """
    email: Optional[EmailStr] = Field(
        None,
        description="New email address (must be unique)",
        examples=["newemail@example.com"]
    )
    role: Optional[UserRole] = Field(
        None,
        description="New role (admin only)",
        examples=[UserRole.COACH]
    )
    profile: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated profile data",
        examples=[{"name": "Jane Doe", "phone": "+9876543210"}]
    )
    location_id: Optional[UUID] = Field(
        None,
        description="Updated location ID (ENTERPRISE only)",
        examples=["660e8400-e29b-41d4-a716-446655440000"]
    )
    is_active: Optional[bool] = Field(
        None,
        description="Account active status (admin only)",
        examples=[True]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile": {
                    "name": "Jane Doe",
                    "phone": "+9876543210"
                }
            }
        }
    )


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.

    Includes all user fields except password.
    """
    id: UUID = Field(
        ...,
        description="Unique user ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    subscription_id: Optional[UUID] = Field(
        None,
        description="Subscription ID (null for APPLICATION_SUPPORT)",
        examples=["660e8400-e29b-41d4-a716-446655440000"]
    )
    location_id: Optional[UUID] = Field(
        None,
        description="Location ID (ENTERPRISE only)",
        examples=["770e8400-e29b-41d4-a716-446655440000"]
    )
    role: UserRole = Field(
        ...,
        description="User role",
        examples=[UserRole.CLIENT]
    )
    email: EmailStr = Field(
        ...,
        description="Email address",
        examples=["john.doe@example.com"]
    )
    profile: Optional[Dict[str, Any]] = Field(
        None,
        description="User profile data",
        examples=[{"name": "John Doe", "phone": "+1234567890"}]
    )
    is_active: bool = Field(
        ...,
        description="Whether the account is active",
        examples=[True]
    )
    last_login_at: Optional[datetime] = Field(
        None,
        description="Last login timestamp",
        examples=["2025-01-15T10:30:00"]
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
        examples=["2025-01-15T10:30:00"]
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
        examples=["2025-01-15T10:30:00"]
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "subscription_id": "660e8400-e29b-41d4-a716-446655440000",
                "location_id": None,
                "role": "CLIENT",
                "email": "john.doe@example.com",
                "profile": {
                    "name": "John Doe",
                    "phone": "+1234567890"
                },
                "is_active": True,
                "last_login_at": "2025-01-15T10:30:00",
                "created_at": "2025-01-15T10:30:00",
                "updated_at": "2025-01-15T10:30:00"
            }
        }
    )


class UserListResponse(BaseModel):
    """
    Schema for paginated user list responses.
    """
    users: list[UserResponse] = Field(
        ...,
        description="List of users",
        examples=[[]]
    )
    total: int = Field(
        ...,
        description="Total number of users matching the query",
        examples=[10]
    )
    skip: int = Field(
        ...,
        description="Number of users skipped",
        examples=[0]
    )
    limit: int = Field(
        ...,
        description="Maximum number of users returned",
        examples=[100]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [],
                "total": 10,
                "skip": 0,
                "limit": 100
            }
        }
    )
