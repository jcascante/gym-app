"""
Pydantic schemas for request/response validation.
"""
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
)
from app.schemas.client import (
    ClientDetailResponse,
    ClientListResponse,
    ClientProfile,
    ClientProfileUpdate,
    ClientSummary,
    CreateClientRequest,
    CreateClientResponse,
    OneRepMaxResponse,
    UpdateOneRepMaxRequest,
)
from app.schemas.program import (
    CalculationConstants,
    MovementInput,
    ProgramDetailResponse,
    ProgramInputs,
    ProgramPreview,
    ProgramResponse,
)
from app.schemas.program_assignment import (
    AssignProgramRequest,
    AssignProgramResponse,
    ClientProgramsListResponse,
    ProgramAssignmentSummary,
    UpdateAssignmentStatusRequest,
    UpdateAssignmentStatusResponse,
)
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
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
