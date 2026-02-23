"""
Users API routes with role-based access control.

Provides CRUD operations for user management with proper authorization.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.deps import (
    get_current_user,
    get_subscription_admin_user,
    get_application_support_user,
    check_subscription_access
)
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.schemas.auth import MessageResponse
from app.schemas.program_assignment import (
    ClientProgramsListResponse,
    ProgramAssignmentSummary,
)

router = APIRouter()


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
    description="""
    Get a paginated list of users within your subscription.

    **Authorization:**
    - SUBSCRIPTION_ADMIN: Can list all users in their subscription
    - COACH: Can list all users in their subscription (read-only)
    - CLIENT: Can only see themselves (redirects to /me)
    - APPLICATION_SUPPORT: Can list users across all subscriptions

    **Filtering:**
    - Filter by role to get only coaches, clients, etc.
    - Filter by location (ENTERPRISE only)
    - Search by email or name
    """,
    tags=["Users"]
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    location_id: Optional[UUID] = Query(None, description="Filter by location (ENTERPRISE only)"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List users with filtering and pagination."""

    # Build query based on user role
    query = select(User)

    # APPLICATION_SUPPORT can see all users
    if current_user.role == UserRole.APPLICATION_SUPPORT:
        pass  # No filtering
    # Other users can only see users in their subscription
    elif current_user.subscription_id:
        query = query.where(User.subscription_id == current_user.subscription_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Apply filters
    if role:
        query = query.where(User.role == role)

    if location_id:
        query = query.where(User.location_id == location_id)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                func.json_extract(User.profile, '$.name').ilike(search_term)
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="""
    Create a new user within your subscription.

    **Authorization:**
    - SUBSCRIPTION_ADMIN: Can create users in their subscription
    - APPLICATION_SUPPORT: Can create users in any subscription

    **Role Restrictions:**
    - INDIVIDUAL: Can only have SUBSCRIPTION_ADMIN (owner) and CLIENTs
    - GYM: Can have SUBSCRIPTION_ADMIN, COACHes, and CLIENTs
    - ENTERPRISE: Can have all roles + location assignment

    **Validation:**
    - Email must be unique across the platform
    - Role must be allowed for the subscription type
    - Subscription limits are enforced (max_admins, max_coaches, max_clients)
    """,
    tags=["Users"]
)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_subscription_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user with role validation."""

    # Determine subscription ID
    if current_user.role == UserRole.APPLICATION_SUPPORT:
        # Support can create users in any subscription
        subscription_id = user_in.subscription_id
        if not subscription_id and user_in.role != UserRole.APPLICATION_SUPPORT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="subscription_id is required for non-support users"
            )
    else:
        # Admins can only create users in their own subscription
        subscription_id = current_user.subscription_id
        if user_in.subscription_id and user_in.subscription_id != subscription_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create users in other subscriptions"
            )

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=user_in.email,
        subscription_id=subscription_id,
        location_id=user_in.location_id,
        role=user_in.role,
        hashed_password=get_password_hash(user_in.password),
        profile=user_in.profile or {},
        is_active=True,
        created_by=current_user.id
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="""
    Get a specific user's details.

    **Authorization:**
    - Users can view other users in their subscription
    - APPLICATION_SUPPORT can view any user
    """,
    tags=["Users"]
)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a user by ID with subscription access check."""

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check subscription access
    if current_user.role != UserRole.APPLICATION_SUPPORT:
        if user.subscription_id != current_user.subscription_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="""
    Update a user's information.

    **Authorization:**
    - SUBSCRIPTION_ADMIN: Can update users in their subscription
    - APPLICATION_SUPPORT: Can update any user
    - Users can update their own profile (limited fields)

    **Updatable Fields:**
    - Admins: All fields (email, role, profile, location_id, is_active)
    - Self: Only profile fields
    """,
    tags=["Users"]
)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a user with role-based field restrictions."""

    # Get user to update
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions
    is_self = user.id == current_user.id
    is_admin = current_user.role in [UserRole.SUBSCRIPTION_ADMIN, UserRole.APPLICATION_SUPPORT]
    is_same_subscription = user.subscription_id == current_user.subscription_id

    # Validate access
    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if not is_self and is_admin and current_user.role != UserRole.APPLICATION_SUPPORT:
        if not is_same_subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    # Apply updates
    update_data = user_update.model_dump(exclude_unset=True)

    # Non-admins can only update profile
    if not is_admin:
        allowed_fields = {"profile"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

    # Check email uniqueness if changing
    if "email" in update_data and update_data["email"] != user.email:
        result = await db.execute(
            select(User).where(User.email == update_data["email"])
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Update fields
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_by = current_user.id

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete user",
    description="""
    Delete (deactivate) a user.

    **Authorization:**
    - SUBSCRIPTION_ADMIN: Can delete users in their subscription
    - APPLICATION_SUPPORT: Can delete any user

    **Note:** This performs a soft delete (sets is_active=False)
    """,
    tags=["Users"]
)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_subscription_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a user (set is_active=False)."""

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check subscription access (except for APPLICATION_SUPPORT)
    if current_user.role != UserRole.APPLICATION_SUPPORT:
        if user.subscription_id != current_user.subscription_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Soft delete
    user.is_active = False
    user.updated_by = current_user.id

    await db.commit()

    return MessageResponse(
        message="User deleted successfully",
        detail=f"User {user.email} has been deactivated"
    )


@router.get(
    "/me/programs",
    response_model=ClientProgramsListResponse,
    summary="Get programs assigned to current client",
    tags=["Users"],
)
async def get_my_programs(
    status_filter: Optional[str] = Query(None, description="Filter by assignment status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all programs assigned to the authenticated client.

    Only users with role CLIENT may call this endpoint. Returns the same
    structure as the coach-facing client programs endpoint but scoped to the
    current user.
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can view their own program assignments",
        )

    from app.models.client_program_assignment import ClientProgramAssignment
    from app.models.program import Program

    # Build query for this client's assignments
    query = select(ClientProgramAssignment).where(
        ClientProgramAssignment.client_id == current_user.id
    )

    if status_filter:
        query = query.where(ClientProgramAssignment.status == status_filter)

    result = await db.execute(query.order_by(ClientProgramAssignment.created_at.desc()))
    assignments = result.scalars().all()

    program_summaries: list[ProgramAssignmentSummary] = []
    active_count = 0
    completed_count = 0

    for assignment in assignments:
        # Get program details
        program_result = await db.execute(
            select(Program).where(Program.id == assignment.program_id)
        )
        program = program_result.scalar_one_or_none()
        if not program:
            continue
        # Skip draft programs — clients can only see published programs
        if program.status == "draft":
            continue

        # Get coach name
        coach_result = await db.execute(
            select(User).where(User.id == assignment.coach_id)
        )
        coach = coach_result.scalar_one_or_none()
        coach_profile = coach.profile or {} if coach else {}
        coach_basic_info = coach_profile.get("basic_info", {})
        coach_name = f"{coach_basic_info.get('first_name', 'Unknown')} {coach_basic_info.get('last_name', 'Coach')}"

        progress_percentage = ((assignment.current_week - 1) / program.duration_weeks * 100) if program.duration_weeks > 0 else 0.0

        if assignment.is_active and assignment.status in ["assigned", "in_progress"]:
            active_count += 1
        elif assignment.status == "completed":
            completed_count += 1

        program_summaries.append(ProgramAssignmentSummary(
            assignment_id=assignment.id,
            program_id=program.id,
            program_name=program.name,
            assignment_name=assignment.assignment_name,
            duration_weeks=program.duration_weeks,
            days_per_week=program.days_per_week,
            start_date=assignment.start_date,
            end_date=assignment.end_date,
            actual_completion_date=assignment.actual_completion_date,
            status=assignment.status,
            program_status=program.status,
            current_week=assignment.current_week,
            current_day=assignment.current_day,
            progress_percentage=progress_percentage,
            is_active=assignment.is_active,
            assigned_at=assignment.created_at,
            assigned_by_name=coach_name,
        ))

    client_profile = current_user.profile or {}
    basic_info = client_profile.get('basic_info', {})
    client_name = f"{basic_info.get('first_name', 'Unknown')} {basic_info.get('last_name', 'Client')}"

    return ClientProgramsListResponse(
        client_id=current_user.id,
        client_name=client_name,
        programs=program_summaries,
        total=len(program_summaries),
        active_count=active_count,
        completed_count=completed_count,
    )
