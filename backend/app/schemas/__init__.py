"""
Pydantic schemas for request/response validation.
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
)
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
)
from app.schemas.program import (
    MovementInput,
    ProgramInputs,
    ProgramPreview,
    ProgramResponse,
    ProgramDetailResponse,
    CalculationConstants,
)
from app.schemas.client import (
    CreateClientRequest,
    CreateClientResponse,
    ClientProfile,
    ClientProfileUpdate,
    ClientSummary,
    ClientListResponse,
    ClientDetailResponse,
    UpdateOneRepMaxRequest,
    OneRepMaxResponse,
)
from app.schemas.program_assignment import (
    AssignProgramRequest,
    AssignProgramResponse,
    ProgramAssignmentSummary,
    ClientProgramsListResponse,
    UpdateAssignmentStatusRequest,
    UpdateAssignmentStatusResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    # Auth
    "LoginRequest",
    "TokenResponse",
    # Subscription
    "SubscriptionCreate",
    "SubscriptionUpdate",
    "SubscriptionResponse",
    # Program
    "MovementInput",
    "ProgramInputs",
    "ProgramPreview",
    "ProgramResponse",
    "ProgramDetailResponse",
    "CalculationConstants",
    # Client
    "CreateClientRequest",
    "CreateClientResponse",
    "ClientProfile",
    "ClientProfileUpdate",
    "ClientSummary",
    "ClientListResponse",
    "ClientDetailResponse",
    "UpdateOneRepMaxRequest",
    "OneRepMaxResponse",
    # Program Assignment
    "AssignProgramRequest",
    "AssignProgramResponse",
    "ProgramAssignmentSummary",
    "ClientProgramsListResponse",
    "UpdateAssignmentStatusRequest",
    "UpdateAssignmentStatusResponse",
]
