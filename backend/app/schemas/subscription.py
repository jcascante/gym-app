"""
Subscription Pydantic schemas for request/response validation.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.subscription import SubscriptionType, SubscriptionStatus


class SubscriptionBase(BaseModel):
    """
    Base subscription schema with common fields.
    """
    name: str = Field(
        ...,
        max_length=255,
        description="Subscription name (e.g., 'PowerFit Gym', 'Maria's Coaching')",
        examples=["PowerFit Gym"]
    )
    subscription_type: SubscriptionType = Field(
        ...,
        description="Subscription tier (INDIVIDUAL, GYM, ENTERPRISE)",
        examples=[SubscriptionType.GYM]
    )
    features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Feature flags enabled for this subscription",
        examples=[{"multi_location": False, "api_access": False}]
    )
    limits: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resource limits for this subscription",
        examples=[{"max_coaches": 25, "max_clients": 500, "storage_gb": 50}]
    )


class SubscriptionCreate(SubscriptionBase):
    """
    Schema for subscription creation requests.
    """
    billing_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Billing information (payment method, billing cycle, etc.)",
        examples=[{"payment_method": "card", "billing_cycle": "monthly"}]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "PowerFit Gym",
                "subscription_type": "GYM",
                "features": {
                    "multi_location": False,
                    "api_access": False,
                    "white_label": False
                },
                "limits": {
                    "max_admins": 5,
                    "max_coaches": 25,
                    "max_clients": 500,
                    "storage_gb": 50
                },
                "billing_info": {
                    "payment_method": "card",
                    "billing_cycle": "monthly"
                }
            }
        }
    )


class SubscriptionUpdate(BaseModel):
    """
    Schema for updating subscription.
    """
    name: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated subscription name",
        examples=["PowerFit Gym - Downtown"]
    )
    subscription_type: Optional[SubscriptionType] = Field(
        None,
        description="Updated subscription tier",
        examples=[SubscriptionType.ENTERPRISE]
    )
    status: Optional[SubscriptionStatus] = Field(
        None,
        description="Updated subscription status",
        examples=[SubscriptionStatus.ACTIVE]
    )
    features: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated feature flags",
        examples=[{"multi_location": True, "api_access": True}]
    )
    limits: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated resource limits",
        examples=[{"max_coaches": 50, "max_clients": 1000}]
    )
    billing_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated billing information",
        examples=[{"payment_method": "card", "billing_cycle": "annual"}]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subscription_type": "ENTERPRISE",
                "features": {
                    "multi_location": True,
                    "api_access": True
                }
            }
        }
    )


class SubscriptionResponse(BaseModel):
    """
    Schema for subscription data in API responses.
    """
    id: UUID = Field(
        ...,
        description="Unique subscription ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    name: str = Field(
        ...,
        description="Subscription name",
        examples=["PowerFit Gym"]
    )
    subscription_type: SubscriptionType = Field(
        ...,
        description="Subscription tier",
        examples=[SubscriptionType.GYM]
    )
    status: SubscriptionStatus = Field(
        ...,
        description="Subscription status",
        examples=[SubscriptionStatus.ACTIVE]
    )
    features: Dict[str, Any] = Field(
        ...,
        description="Feature flags",
        examples=[{"multi_location": False, "api_access": False}]
    )
    limits: Dict[str, Any] = Field(
        ...,
        description="Resource limits",
        examples=[{"max_coaches": 25, "max_clients": 500}]
    )
    billing_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Billing information",
        examples=[{"payment_method": "card", "billing_cycle": "monthly"}]
    )
    created_at: datetime = Field(
        ...,
        description="Subscription creation timestamp",
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
                "name": "PowerFit Gym",
                "subscription_type": "GYM",
                "status": "ACTIVE",
                "features": {
                    "multi_location": False,
                    "api_access": False,
                    "white_label": False
                },
                "limits": {
                    "max_admins": 5,
                    "max_coaches": 25,
                    "max_clients": 500,
                    "storage_gb": 50
                },
                "billing_info": {
                    "payment_method": "card",
                    "billing_cycle": "monthly"
                },
                "created_at": "2025-01-15T10:30:00",
                "updated_at": "2025-01-15T10:30:00"
            }
        }
    )
