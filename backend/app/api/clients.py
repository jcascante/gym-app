"""
Client management API endpoints for coaches.

These endpoints allow coaches to manage their assigned clients,
including creating new clients, viewing client lists, and updating client profiles.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.deps import get_current_user, get_coach_or_admin_user
from app.models.user import User, UserRole
from app.models.coach_client_assignment import CoachClientAssignment
from app.schemas.client import (
    CreateClientRequest,
    CreateClientResponse,
    ClientListResponse,
    ClientSummary,
    ClientDetailResponse,
    ClientProfileUpdate,
    UpdateOneRepMaxRequest,
    OneRepMaxResponse,
)
from app.schemas.program_assignment import (
    ClientProgramsListResponse,
    ProgramAssignmentSummary,
)
from app.core.security import get_password_hash
import secrets
import string

router = APIRouter(prefix="/coaches/me/clients", tags=["Client Management"])


def generate_random_password(length: int = 12) -> str:
    """Generate a secure random password for new clients."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


@router.post("", response_model=CreateClientResponse, status_code=status.HTTP_201_CREATED)
async def create_or_find_client(
    request: CreateClientRequest,
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new client or find existing client by email.

    If client with this email already exists:
    - Return existing client info with is_new=False
    - Create coach-client assignment if not already assigned

    If client doesn't exist:
    - Create new client account with generated password
    - Create coach-client assignment
    - Optionally send welcome email (TODO: implement email sending)

    **Required permissions**: COACH or SUBSCRIPTION_ADMIN
    """
    # Check if user with this email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # Client already exists
        # Verify they're a client (not a coach or admin)
        if existing_user.role != UserRole.CLIENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with this email exists but has role {existing_user.role.value}. Cannot add as client."
            )

        # Check if already assigned to this coach
        assignment_result = await db.execute(
            select(CoachClientAssignment).where(
                and_(
                    CoachClientAssignment.coach_id == current_user.id,
                    CoachClientAssignment.client_id == existing_user.id,
                    CoachClientAssignment.is_active == True
                )
            )
        )
        existing_assignment = assignment_result.scalar_one_or_none()

        if not existing_assignment:
            # Create coach-client assignment
            assignment = CoachClientAssignment(
                subscription_id=current_user.subscription_id,
                location_id=current_user.location_id,
                coach_id=current_user.id,
                client_id=existing_user.id,
                is_active=True,
            )
            assignment.created_by = current_user.id
            db.add(assignment)
            await db.commit()

        # Extract name from profile
        profile = existing_user.profile or {}
        basic_info = profile.get('basic_info', {})
        first_name = basic_info.get('first_name', request.first_name)
        last_name = basic_info.get('last_name', request.last_name)
        name = f"{first_name} {last_name}"

        # Check profile completeness
        profile_complete = all([
            basic_info.get('first_name'),
            basic_info.get('last_name'),
            profile.get('training_preferences', {}).get('available_days_per_week'),
        ])

        return CreateClientResponse(
            client_id=existing_user.id,
            email=existing_user.email,
            name=name,
            is_new=False,
            profile_complete=profile_complete,
            already_assigned=existing_assignment is not None
        )

    # Client doesn't exist - create new client
    # Generate random password
    temp_password = generate_random_password()

    # Create user profile with basic info
    profile = {
        "basic_info": {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "phone_number": request.phone_number,
        }
    }

    # Create new client user
    new_client = User(
        subscription_id=current_user.subscription_id,
        location_id=current_user.location_id,
        role=UserRole.CLIENT,
        email=request.email,
        hashed_password=get_password_hash(temp_password),
        profile=profile,
        is_active=True,
        password_must_be_changed=True,  # Force password change on first login
    )
    new_client.created_by = current_user.id
    db.add(new_client)
    await db.flush()  # Get client ID

    # Create coach-client assignment
    assignment = CoachClientAssignment(
        subscription_id=current_user.subscription_id,
        location_id=current_user.location_id,
        coach_id=current_user.id,
        client_id=new_client.id,
        is_active=True,
    )
    assignment.created_by = current_user.id
    db.add(assignment)

    await db.commit()
    await db.refresh(new_client)

    # TODO: Send welcome email with credentials if send_welcome_email is True
    # This would include:
    # - Login URL
    # - Email (username)
    # - Temporary password
    # - Instructions to change password on first login

    return CreateClientResponse(
        client_id=new_client.id,
        email=new_client.email,
        name=f"{request.first_name} {request.last_name}",
        is_new=True,
        profile_complete=False,  # New clients haven't completed profile yet
        already_assigned=False
    )


@router.get("", response_model=ClientListResponse)
async def list_my_clients(
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, inactive, new"),
    search: Optional[str] = Query(None, description="Search by name or email"),
):
    """
    Get list of all clients assigned to current coach.

    Returns summary view of each client with key stats for the coach dashboard.

    **Required permissions**: COACH or SUBSCRIPTION_ADMIN
    """
    # Build base query for coach's clients
    query = (
        select(User, CoachClientAssignment.assigned_at)
        .join(CoachClientAssignment, User.id == CoachClientAssignment.client_id)
        .where(
            and_(
                CoachClientAssignment.coach_id == current_user.id,
                CoachClientAssignment.is_active == True,
                User.is_active == True,
            )
        )
    )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            User.email.ilike(search_term)
            # TODO: Add name search once we index profile fields
        )

    # Execute query
    result = await db.execute(query)
    clients_data = result.all()

    # Build client summaries
    clients = []
    for user, assigned_at in clients_data:
        profile = user.profile or {}
        basic_info = profile.get('basic_info', {})
        training_exp = profile.get('training_experience', {})

        first_name = basic_info.get('first_name', 'Unknown')
        last_name = basic_info.get('last_name', 'Client')
        name = f"{first_name} {last_name}"

        # Check profile completeness
        profile_complete = all([
            basic_info.get('first_name'),
            basic_info.get('last_name'),
            profile.get('training_preferences', {}).get('available_days_per_week'),
        ])

        # Check if has 1RMs
        has_one_rep_maxes = len(training_exp.get('one_rep_maxes', {})) > 0

        # Determine status
        # TODO: Calculate from actual workout logs and program assignments
        client_status = "new" if not profile_complete else "active"

        # Apply status filter
        if status_filter and client_status != status_filter:
            continue

        # Count active programs for this client
        from app.models.client_program_assignment import ClientProgramAssignment
        active_programs_result = await db.execute(
            select(func.count(ClientProgramAssignment.id)).where(
                and_(
                    ClientProgramAssignment.client_id == user.id,
                    ClientProgramAssignment.is_active == True,
                    ClientProgramAssignment.status.in_(['assigned', 'in_progress'])
                )
            )
        )
        active_programs_count = active_programs_result.scalar_one()

        clients.append(
            ClientSummary(
                id=user.id,
                email=user.email,
                first_name=first_name,
                last_name=last_name,
                name=name,
                profile_photo=None,  # TODO: Add profile photo support
                active_programs=active_programs_count,
                last_workout=None,  # TODO: Get from workout_logs table
                status=client_status,
                profile_complete=profile_complete,
                has_one_rep_maxes=has_one_rep_maxes,
                assigned_at=assigned_at,
            )
        )

    # Sort by assigned_at (most recent first)
    clients.sort(key=lambda x: x.assigned_at, reverse=True)

    return ClientListResponse(
        clients=clients,
        total=len(clients)
    )


@router.get("/{client_id}", response_model=ClientDetailResponse)
async def get_client_detail(
    client_id: UUID,
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific client.

    Includes full profile, assignment info, and stats.

    **Required permissions**: COACH or SUBSCRIPTION_ADMIN (must be assigned to this client)
    """
    # Verify coach-client relationship
    assignment_result = await db.execute(
        select(CoachClientAssignment).where(
            and_(
                CoachClientAssignment.coach_id == current_user.id,
                CoachClientAssignment.client_id == client_id,
                CoachClientAssignment.is_active == True
            )
        )
    )
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or not assigned to you"
        )

    # Get client user
    result = await db.execute(
        select(User).where(User.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Get actual stats from program_assignments table
    from app.models.client_program_assignment import ClientProgramAssignment

    # Count active programs
    active_programs_result = await db.execute(
        select(func.count(ClientProgramAssignment.id)).where(
            and_(
                ClientProgramAssignment.client_id == client_id,
                ClientProgramAssignment.is_active == True,
                ClientProgramAssignment.status.in_(['assigned', 'in_progress'])
            )
        )
    )
    active_programs_count = active_programs_result.scalar_one()

    # Count completed programs
    completed_programs_result = await db.execute(
        select(func.count(ClientProgramAssignment.id)).where(
            and_(
                ClientProgramAssignment.client_id == client_id,
                ClientProgramAssignment.status == 'completed'
            )
        )
    )
    completed_programs_count = completed_programs_result.scalar_one()

    return ClientDetailResponse(
        id=client.id,
        email=client.email,
        profile=client.profile,
        is_active=client.is_active,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.created_by,
        active_programs=active_programs_count,
        completed_programs=completed_programs_count,
        total_workouts=0,  # TODO: Implement when workout logging is added
        last_workout=None,  # TODO: Implement when workout logging is added
        last_login_at=client.last_login_at,
        created_at=client.created_at,
    )


@router.patch("/{client_id}/profile", response_model=ClientDetailResponse)
async def update_client_profile(
    client_id: UUID,
    profile_update: ClientProfileUpdate,
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update client profile information.

    Coach can update any part of the client's profile. All fields are optional
    to allow partial updates.

    **Required permissions**: COACH or SUBSCRIPTION_ADMIN (must be assigned to this client)
    """
    # Verify coach-client relationship
    assignment_result = await db.execute(
        select(CoachClientAssignment).where(
            and_(
                CoachClientAssignment.coach_id == current_user.id,
                CoachClientAssignment.client_id == client_id,
                CoachClientAssignment.is_active == True
            )
        )
    )
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or not assigned to you"
        )

    # Get client user
    result = await db.execute(
        select(User).where(User.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Update profile (merge with existing)
    current_profile = client.profile or {}

    # Update each section if provided
    if profile_update.basic_info:
        current_profile['basic_info'] = profile_update.basic_info.model_dump(exclude_none=True)

    if profile_update.anthropometrics:
        current_profile['anthropometrics'] = profile_update.anthropometrics.model_dump(exclude_none=True)

    if profile_update.training_experience:
        current_profile['training_experience'] = profile_update.training_experience.model_dump(exclude_none=True)

    if profile_update.fitness_goals:
        current_profile['fitness_goals'] = profile_update.fitness_goals.model_dump(exclude_none=True)

    if profile_update.health_info:
        current_profile['health_info'] = profile_update.health_info.model_dump(exclude_none=True)

    if profile_update.training_preferences:
        current_profile['training_preferences'] = profile_update.training_preferences.model_dump(exclude_none=True)

    if profile_update.notes:
        current_profile['notes'] = profile_update.notes

    client.profile = current_profile
    client.updated_by = current_user.id

    await db.commit()
    await db.refresh(client)

    return ClientDetailResponse(
        id=client.id,
        email=client.email,
        profile=client.profile,
        is_active=client.is_active,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.created_by,
        active_programs=0,  # TODO
        completed_programs=0,  # TODO
        total_workouts=0,  # TODO
        last_workout=None,  # TODO
        last_login_at=client.last_login_at,
        created_at=client.created_at,
    )


@router.put("/{client_id}/one-rep-max", response_model=OneRepMaxResponse)
async def update_client_one_rep_max(
    client_id: UUID,
    request: UpdateOneRepMaxRequest,
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add or update a client's 1RM for a specific exercise.

    This is used during program building or when testing new maxes.
    Coach-verified 1RMs are marked as verified=True.

    **Required permissions**: COACH or SUBSCRIPTION_ADMIN (must be assigned to this client)
    """
    # Verify coach-client relationship
    assignment_result = await db.execute(
        select(CoachClientAssignment).where(
            and_(
                CoachClientAssignment.coach_id == current_user.id,
                CoachClientAssignment.client_id == client_id,
                CoachClientAssignment.is_active == True
            )
        )
    )
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or not assigned to you"
        )

    # Get client user
    result = await db.execute(
        select(User).where(User.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Update 1RM in profile
    current_profile = client.profile or {}
    training_exp = current_profile.get('training_experience', {})
    one_rep_maxes = training_exp.get('one_rep_maxes', {})

    # Add or update 1RM
    one_rep_maxes[request.exercise_name] = {
        "weight": request.weight,
        "unit": request.unit,
        "tested_date": request.tested_date.isoformat(),
        "verified": request.verified,
    }

    training_exp['one_rep_maxes'] = one_rep_maxes
    current_profile['training_experience'] = training_exp
    client.profile = current_profile
    client.updated_by = current_user.id

    await db.commit()
    await db.refresh(client)

    return OneRepMaxResponse(
        client_id=client.id,
        exercise_name=request.exercise_name,
        weight=request.weight,
        unit=request.unit,
        tested_date=request.tested_date,
        verified=request.verified,
        updated_at=client.updated_at,
    )


@router.get("/{client_id}/programs", response_model=ClientProgramsListResponse)
async def get_client_programs(
    client_id: UUID,
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status: assigned, in_progress, completed, paused, cancelled"),
):
    """
    Get all programs assigned to a specific client.

    Returns list of program assignments with status, progress, and metadata.

    **Required permissions**: COACH or SUBSCRIPTION_ADMIN (must be assigned to this client)
    """
    from app.models.client_program_assignment import ClientProgramAssignment
    from app.models.program import Program

    # Verify coach-client relationship
    assignment_result = await db.execute(
        select(CoachClientAssignment).where(
            and_(
                CoachClientAssignment.coach_id == current_user.id,
                CoachClientAssignment.client_id == client_id,
                CoachClientAssignment.is_active == True
            )
        )
    )
    coach_assignment = assignment_result.scalar_one_or_none()

    if not coach_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or not assigned to you"
        )

    # Get client user
    result = await db.execute(
        select(User).where(User.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Build query for program assignments
    query = select(ClientProgramAssignment).where(
        ClientProgramAssignment.client_id == client_id
    )

    # Apply status filter if provided
    if status_filter:
        query = query.where(ClientProgramAssignment.status == status_filter)

    # Execute query
    result = await db.execute(query.order_by(ClientProgramAssignment.created_at.desc()))
    assignments = result.scalars().all()

    # Build program summaries
    program_summaries = []
    active_count = 0
    completed_count = 0

    for assignment in assignments:
        # Get program details
        program_result = await db.execute(
            select(Program).where(Program.id == assignment.program_id)
        )
        program = program_result.scalar_one_or_none()

        if not program:
            continue  # Skip if program was deleted

        # Get coach name
        coach_result = await db.execute(
            select(User).where(User.id == assignment.coach_id)
        )
        coach = coach_result.scalar_one_or_none()
        coach_profile = coach.profile or {} if coach else {}
        coach_basic_info = coach_profile.get("basic_info", {})
        coach_name = f"{coach_basic_info.get('first_name', 'Unknown')} {coach_basic_info.get('last_name', 'Coach')}"

        # Calculate progress
        progress_percentage = ((assignment.current_week - 1) / program.duration_weeks * 100) if program.duration_weeks > 0 else 0.0

        # Count active and completed
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
            current_week=assignment.current_week,
            current_day=assignment.current_day,
            progress_percentage=progress_percentage,
            is_active=assignment.is_active,
            assigned_at=assignment.created_at,
            assigned_by_name=coach_name
        ))

    # Build client name
    client_profile = client.profile or {}
    basic_info = client_profile.get("basic_info", {})
    client_name = f"{basic_info.get('first_name', 'Unknown')} {basic_info.get('last_name', 'Client')}"

    return ClientProgramsListResponse(
        client_id=client.id,
        client_name=client_name,
        programs=program_summaries,
        total=len(program_summaries),
        active_count=active_count,
        completed_count=completed_count
    )


@router.delete("/{client_id}/programs/{assignment_id}")
async def remove_program_assignment(
    client_id: UUID,
    assignment_id: UUID,
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove/deactivate a program assignment from a client.

    This does NOT delete the program template, only the assignment to the client.

    **Required permissions**: COACH or SUBSCRIPTION_ADMIN (must be assigned to this client)
    """
    from app.models.client_program_assignment import ClientProgramAssignment

    # Verify coach-client relationship
    assignment_result = await db.execute(
        select(CoachClientAssignment).where(
            and_(
                CoachClientAssignment.coach_id == current_user.id,
                CoachClientAssignment.client_id == client_id,
                CoachClientAssignment.is_active == True
            )
        )
    )
    coach_assignment = assignment_result.scalar_one_or_none()

    if not coach_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or not assigned to you"
        )

    # Find the program assignment
    program_assignment_result = await db.execute(
        select(ClientProgramAssignment).where(
            and_(
                ClientProgramAssignment.id == assignment_id,
                ClientProgramAssignment.client_id == client_id
            )
        )
    )
    program_assignment = program_assignment_result.scalar_one_or_none()

    if not program_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program assignment not found"
        )

    # Deactivate the assignment (soft delete)
    program_assignment.is_active = False
    program_assignment.status = 'cancelled'
    program_assignment.updated_by = current_user.id

    await db.commit()

    return {"message": "Program assignment removed successfully"}


@router.delete("/{client_id}")
async def remove_client_assignment(
    client_id: UUID,
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove client assignment (unassign client from this coach).

    This does NOT delete the client's account, only the coach-client relationship.

    **Required permissions**: COACH or SUBSCRIPTION_ADMIN
    """
    # Find assignment
    result = await db.execute(
        select(CoachClientAssignment).where(
            and_(
                CoachClientAssignment.coach_id == current_user.id,
                CoachClientAssignment.client_id == client_id,
                CoachClientAssignment.is_active == True
            )
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client assignment not found"
        )

    # Deactivate assignment (soft delete)
    assignment.is_active = False
    assignment.updated_by = current_user.id

    await db.commit()

    return {"message": "Client assignment removed successfully"}
