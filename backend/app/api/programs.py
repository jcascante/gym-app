"""
Programs API endpoints

Provides three key endpoints:
1. GET /algorithms/{builder_type}/constants - Calculation constants for frontend
2. POST /preview - Calculate program preview without saving
3. POST / - Calculate and save program to database
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.program import (
    ProgramInputs,
    ProgramPreview,
    CalculationConstants,
    ProgramResponse,
    ProgramListResponse,
    ProgramDetailResponse,
    WeekDetail,
    DayDetail,
    ExerciseDetail,
    GenerateForClientRequest,
    GenerateForClientResponse,
    UpdateExerciseRequest,
    UpdateExerciseResponse,
    PublishProgramResponse,
)
from app.schemas.program_assignment import AssignProgramRequest, AssignProgramResponse
from app.services.strength_program_generator import StrengthProgramGenerator

router = APIRouter()


# ============================================================================
# GET Calculation Constants
# ============================================================================

@router.get(
    "/algorithms/{builder_type}/constants",
    response_model=CalculationConstants,
    summary="Get calculation constants for a program builder",
    description="""
    Returns the calculation constants (lookup tables, formulas) for a specific
    program builder type.

    **Purpose**: Frontend fetches these on mount to ensure its preview
    calculations match the backend's calculations exactly.

    **Usage**:
    1. Frontend loads program builder page
    2. Fetches constants: GET /api/v1/programs/algorithms/strength_linear_5x5/constants
    3. Uses returned tables for preview calculations
    4. When user saves, backend recalculates using same constants

    This ensures frontend preview matches saved program exactly.

    **Supported builder types**:
    - `strength_linear_5x5` - Linear progression strength program

    **Returns**:
    - Algorithm version
    - Weekly jump lookup table
    - Ramp-up lookup table
    - Protocol (sets/reps) by week
    """
)
async def get_calculation_constants(
    builder_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get calculation constants for frontend to mirror backend calculations.
    """
    if builder_type != "strength_linear_5x5":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown builder type: {builder_type}. "
                   f"Supported types: strength_linear_5x5"
        )

    # Return constants from generator (single source of truth)
    return StrengthProgramGenerator.get_constants()


# ============================================================================
# POST Preview Program
# ============================================================================

@router.post(
    "/preview",
    response_model=ProgramPreview,
    summary="Preview program calculations without saving",
    description="""
    Calculate and return program structure without saving to database.

    **Use cases**:
    1. **Validation**: Frontend can call this to validate its calculations
       against backend
    2. **Preview**: Show user final program before committing to save
    3. **Testing**: Verify calculations are correct before assigning to clients

    **Flow**:
    1. User completes program builder wizard (frontend)
    2. Frontend shows preview using client-side calculations
    3. (Optional) Frontend calls this endpoint to validate preview
    4. If preview looks good, user clicks "Save"
    5. Frontend calls POST /programs to save

    **Returns**: Full program structure with all weeks/days/exercises calculated
    """
)
async def preview_program(
    inputs: ProgramInputs,
    current_user: User = Depends(get_current_user)
):
    """
    Generate program preview without saving.
    """
    try:
        preview = StrengthProgramGenerator.generate_preview(inputs)
        return preview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate program preview: {str(e)}"
        )


# ============================================================================
# POST Create Program
# ============================================================================

@router.post(
    "/",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and save program",
    description="""
    Calculate program from inputs and save to database as template.

    **Backend is source of truth**: Even if frontend sends pre-calculated data,
    backend will re-calculate using its own algorithm to ensure consistency.

    **What gets stored**:
    - Original input data (1RMs, rep tests, target weights)
    - Calculated data (weekly jumps, ramp-up percentages)
    - Algorithm version used
    - Full program structure (weeks/days/exercises)

    **After saving**:
    - Program can be viewed in template library
    - Program can be assigned to clients
    - Program can be edited or duplicated

    **Permissions**:
    - SUBSCRIPTION_ADMIN: Can create templates for subscription
    - COACH (GYM/ENTERPRISE): Can create own templates
    """
)
async def create_program(
    inputs: ProgramInputs,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create program from inputs (calculates and saves).
    """
    try:
        # Import models here to avoid circular imports
        from app.models.program import Program, ProgramWeek, ProgramDay, ProgramDayExercise

        # 1. Generate preview using StrengthProgramGenerator (backend is source of truth)
        preview = StrengthProgramGenerator.generate_preview(inputs)

        # 2. Create Program model instance
        program = Program(
            subscription_id=current_user.subscription_id,
            created_by_user_id=current_user.id,
            name=inputs.name or f"{inputs.duration_weeks}-Week {inputs.builder_type.replace('_', ' ').title()}",
            description=inputs.description,
            builder_type=inputs.builder_type,
            algorithm_version=preview.algorithm_version,
            input_data=preview.input_data,
            calculated_data={
                name: calc.model_dump()
                for name, calc in preview.calculated_data.items()
            },
            is_template=inputs.is_template,
            is_public=False,  # Default to private
            duration_weeks=inputs.duration_weeks,
            days_per_week=inputs.days_per_week,
            created_by=current_user.id,
            updated_by=current_user.id
        )

        db.add(program)
        await db.flush()  # Get program.id without committing

        # 3. Create ProgramWeek instances
        for week_detail in preview.weeks:
            program_week = ProgramWeek(
                program_id=program.id,
                subscription_id=current_user.subscription_id,
                week_number=week_detail.week_number,
                name=week_detail.name,
                created_by=current_user.id,
                updated_by=current_user.id
            )
            db.add(program_week)
            await db.flush()  # Get program_week.id

            # 4. Create ProgramDay instances
            for day_detail in week_detail.days:
                program_day = ProgramDay(
                    program_week_id=program_week.id,
                    subscription_id=current_user.subscription_id,
                    day_number=day_detail.day_number,
                    name=day_detail.name,
                    suggested_day_of_week=day_detail.suggested_day_of_week,
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                db.add(program_day)
                await db.flush()  # Get program_day.id

                # 5. Create ProgramDayExercise instances
                for order, exercise_detail in enumerate(day_detail.exercises):
                    program_day_exercise = ProgramDayExercise(
                        program_day_id=program_day.id,
                        subscription_id=current_user.subscription_id,
                        exercise_name=exercise_detail.exercise_name,
                        exercise_order=order + 1,
                        sets=exercise_detail.sets,
                        reps=exercise_detail.reps,
                        reps_target=exercise_detail.reps,
                        weight_lbs=exercise_detail.weight_lbs,
                        load_value=exercise_detail.weight_lbs,
                        load_unit="lbs",
                        load_type="fixed_weight",
                        percentage_1rm=exercise_detail.percentage_1rm,
                        notes=exercise_detail.notes or "",
                        created_by=current_user.id,
                        updated_by=current_user.id
                    )
                    db.add(program_day_exercise)

        # 6. If client_id provided, create a client-specific draft + assignment
        assignment_id = None
        if inputs.client_id:
            from uuid import UUID
            from datetime import timedelta, date as date_type
            from app.models.client_program_assignment import ClientProgramAssignment

            program.is_template = False
            program.status = "draft"

            client_uuid = UUID(inputs.client_id)
            start_date = date_type.today()
            end_date = start_date + timedelta(weeks=inputs.duration_weeks)

            client_assignment = ClientProgramAssignment(
                subscription_id=current_user.subscription_id,
                location_id=current_user.location_id,
                coach_id=current_user.id,
                client_id=client_uuid,
                program_id=program.id,
                start_date=start_date,
                end_date=end_date,
                status="assigned",
                current_week=1,
                current_day=1,
                is_active=True,
                created_by=current_user.id,
                updated_by=current_user.id
            )
            db.add(client_assignment)
            await db.flush()
            assignment_id = str(client_assignment.id)

        # 7. Commit to database
        await db.commit()
        await db.refresh(program)

        # 8. Return ProgramResponse
        return ProgramResponse(
            id=str(program.id),
            subscription_id=str(program.subscription_id) if program.subscription_id else None,
            created_by_user_id=str(program.created_by_user_id) if program.created_by_user_id else None,
            name=program.name,
            description=program.description,
            builder_type=program.builder_type,
            algorithm_version=program.algorithm_version,
            duration_weeks=program.duration_weeks,
            days_per_week=program.days_per_week,
            is_template=program.is_template,
            is_public=program.is_public,
            status=program.status,
            assignment_id=assignment_id,
            created_at=program.created_at.isoformat(),
            updated_at=program.updated_at.isoformat()
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create program: {str(e)}"
        )


# ============================================================================
# POST Assign Program to Client
# ============================================================================

@router.post(
    "/{program_id}/assign",
    response_model=AssignProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign program to a client",
    description="""
    Assign an existing program to a client.

    **What happens**:
    1. Creates a ClientProgramAssignment record
    2. Calculates end date based on program duration
    3. Sets initial status to "assigned"
    4. Client can now see and track this program

    **Permissions**:
    - COACH: Can assign to their assigned clients only
    - SUBSCRIPTION_ADMIN: Can assign to any client in subscription

    **After assignment**:
    - Client sees program in their programs list
    - Coach can track client's progress
    - Workouts can be logged against this assignment
    """
)
async def assign_program_to_client(
    program_id: str,
    request: AssignProgramRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a program to a client."""
    from uuid import UUID
    from datetime import timedelta, date
    from app.models.program import Program
    from app.models.coach_client_assignment import CoachClientAssignment
    from app.models.client_program_assignment import ClientProgramAssignment
    from sqlalchemy import select, and_

    # Convert string UUID to UUID object
    try:
        program_uuid = UUID(program_id)
        client_uuid = UUID(str(request.client_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )

    # 1. Verify program exists and belongs to current user's subscription
    result = await db.execute(
        select(Program).where(
            and_(
                Program.id == program_uuid,
                Program.subscription_id == current_user.subscription_id
            )
        )
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found or not accessible"
        )

    # 2. Verify coach-client relationship (coaches can only assign to their clients)
    if current_user.role.value == "COACH":
        result = await db.execute(
            select(CoachClientAssignment).where(
                and_(
                    CoachClientAssignment.coach_id == current_user.id,
                    CoachClientAssignment.client_id == client_uuid,
                    CoachClientAssignment.is_active == True
                )
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign programs to your assigned clients"
            )

    # 3. Get client user for response
    from app.models.user import User as UserModel
    result = await db.execute(
        select(UserModel).where(UserModel.id == client_uuid)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # 4. Calculate end date based on program duration
    start_date = request.start_date or date.today()
    end_date = start_date + timedelta(weeks=program.duration_weeks)

    # 5. Create assignment
    assignment = ClientProgramAssignment(
        subscription_id=current_user.subscription_id,
        location_id=current_user.location_id,
        coach_id=current_user.id,
        client_id=client_uuid,
        program_id=program_uuid,
        assignment_name=request.assignment_name,
        start_date=start_date,
        end_date=end_date,
        status="assigned",
        current_week=1,
        current_day=1,
        is_active=True,
        notes=request.notes,
        created_by=current_user.id,
        updated_by=current_user.id
    )

    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    # 6. Build response
    client_profile = client.profile or {}
    basic_info = client_profile.get("basic_info", {})
    client_name = f"{basic_info.get('first_name', 'Unknown')} {basic_info.get('last_name', 'Client')}"

    return AssignProgramResponse(
        assignment_id=assignment.id,
        program_id=program.id,
        program_name=program.name,
        client_id=client.id,
        client_name=client_name,
        assignment_name=assignment.assignment_name,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        status=assignment.status,
        created_at=assignment.created_at
    )


# ============================================================================
# GET List Programs
# ============================================================================

@router.get(
    "/",
    response_model=ProgramListResponse,
    summary="List programs",
    description="List all programs (templates) for the current subscription."
)
async def list_programs(
    is_template: bool = True,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List programs for the coach's subscription."""
    from app.models.program import Program
    from sqlalchemy import select, and_, func

    query = select(Program).where(
        and_(
            Program.subscription_id == current_user.subscription_id,
            Program.archived_at.is_(None)
        )
    )
    if is_template:
        query = query.where(Program.is_template == True)
    else:
        query = query.where(Program.is_template == False)
    if search:
        query = query.where(Program.name.ilike(f"%{search}%"))

    query = query.order_by(Program.created_at.desc())

    result = await db.execute(query)
    programs = result.scalars().all()

    return ProgramListResponse(
        programs=[
            ProgramResponse(
                id=str(p.id),
                subscription_id=str(p.subscription_id) if p.subscription_id else None,
                created_by_user_id=str(p.created_by_user_id) if p.created_by_user_id else None,
                name=p.name,
                description=p.description,
                builder_type=p.builder_type,
                algorithm_version=p.algorithm_version,
                duration_weeks=p.duration_weeks,
                days_per_week=p.days_per_week,
                is_template=p.is_template,
                is_public=p.is_public,
                times_assigned=p.times_assigned or 0,
                status=p.status,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat()
            )
            for p in programs
        ],
        total=len(programs)
    )


# ============================================================================
# GET Program Detail
# ============================================================================

@router.get(
    "/{program_id}",
    response_model=ProgramDetailResponse,
    summary="Get program with full details",
    description="Get a specific program including all weeks, days, and exercises."
)
async def get_program(
    program_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full program structure."""
    from uuid import UUID
    from app.models.program import Program, ProgramWeek, ProgramDay, ProgramDayExercise
    from sqlalchemy import select, and_
    from sqlalchemy.orm import selectinload

    try:
        program_uuid = UUID(program_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format")

    result = await db.execute(
        select(Program)
        .options(
            selectinload(Program.weeks)
            .selectinload(ProgramWeek.days)
            .selectinload(ProgramDay.exercises)
        )
        .where(
            and_(
                Program.id == program_uuid,
                Program.subscription_id == current_user.subscription_id,
                Program.archived_at.is_(None)
            )
        )
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    weeks = []
    for week in sorted(program.weeks, key=lambda w: w.week_number):
        days = []
        for day in sorted(week.days, key=lambda d: d.day_number):
            exercises = []
            for ex in sorted(day.exercises, key=lambda e: (e.exercise_order or 0)):
                exercises.append(ExerciseDetail(
                    id=str(ex.id),
                    exercise_name=ex.exercise_name or "",
                    sets=ex.sets,
                    reps=ex.reps or ex.reps_target or 0,
                    weight_lbs=ex.weight_lbs or ex.load_value,
                    percentage_1rm=int(ex.percentage_1rm) if ex.percentage_1rm else None,
                    notes=ex.notes or ""
                ))
            days.append(DayDetail(
                day_number=day.day_number,
                name=day.name,
                suggested_day_of_week=str(day.suggested_day_of_week) if day.suggested_day_of_week else None,
                exercises=exercises
            ))
        weeks.append(WeekDetail(
            week_number=week.week_number,
            name=week.name or f"Week {week.week_number}",
            days=days
        ))

    return ProgramDetailResponse(
        id=str(program.id),
        subscription_id=str(program.subscription_id) if program.subscription_id else None,
        created_by_user_id=str(program.created_by_user_id) if program.created_by_user_id else None,
        name=program.name,
        description=program.description,
        builder_type=program.builder_type,
        algorithm_version=program.algorithm_version,
        duration_weeks=program.duration_weeks,
        days_per_week=program.days_per_week,
        is_template=program.is_template,
        is_public=program.is_public,
        times_assigned=program.times_assigned or 0,
        status=program.status,
        created_at=program.created_at.isoformat(),
        updated_at=program.updated_at.isoformat(),
        input_data=program.input_data or {},
        calculated_data=program.calculated_data or {},
        weeks=weeks
    )


# ============================================================================
# DELETE Program (archive)
# ============================================================================

@router.delete(
    "/{program_id}",
    status_code=status.HTTP_200_OK,
    summary="Archive a program",
    description="Soft-delete a program. Fails if the program has active client assignments."
)
async def delete_program(
    program_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a program (soft delete)."""
    from uuid import UUID
    from datetime import datetime
    from app.models.program import Program
    from app.models.client_program_assignment import ClientProgramAssignment
    from sqlalchemy import select, and_

    try:
        program_uuid = UUID(program_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format")

    result = await db.execute(
        select(Program).where(
            and_(
                Program.id == program_uuid,
                Program.subscription_id == current_user.subscription_id,
                Program.archived_at.is_(None)
            )
        )
    )
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    # Draft programs: cancel linked assignment and archive in one go
    if program.status == "draft":
        draft_assignment_result = await db.execute(
            select(ClientProgramAssignment).where(
                ClientProgramAssignment.program_id == program_uuid
            )
        )
        draft_assignment = draft_assignment_result.scalar_one_or_none()
        if draft_assignment:
            draft_assignment.status = "cancelled"
            draft_assignment.is_active = False
            draft_assignment.updated_by = current_user.id
        program.archived_at = datetime.utcnow().isoformat()
        await db.commit()
        return {"message": "Draft program discarded successfully"}

    # Cancel all active assignments before archiving
    active_assignments_result = await db.execute(
        select(ClientProgramAssignment).where(
            and_(
                ClientProgramAssignment.program_id == program_uuid,
                ClientProgramAssignment.is_active == True
            )
        )
    )
    active_assignments = active_assignments_result.scalars().all()
    for assignment in active_assignments:
        assignment.status = "cancelled"
        assignment.is_active = False
        assignment.updated_by = current_user.id

    program.archived_at = datetime.utcnow().isoformat()
    await db.commit()
    return {"message": "Program archived successfully"}


# ============================================================================
# POST Generate Client Program from Template
# ============================================================================

@router.post(
    "/{template_id}/generate-for-client",
    response_model=GenerateForClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a client-specific draft program from a template",
)
async def generate_for_client(
    template_id: str,
    request: GenerateForClientRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a personalized draft program for a client from a template."""
    from uuid import UUID
    from datetime import timedelta, date as date_type
    from app.models.program import Program, ProgramWeek, ProgramDay, ProgramDayExercise
    from app.models.coach_client_assignment import CoachClientAssignment
    from app.models.client_program_assignment import ClientProgramAssignment
    from app.models.user import User as UserModel
    from app.schemas.program import ProgramInputs, MovementInput
    from sqlalchemy import select, and_

    try:
        template_uuid = UUID(template_id)
        client_uuid = UUID(request.client_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format")

    # 1. Verify template exists and belongs to this subscription
    result = await db.execute(
        select(Program).where(
            and_(
                Program.id == template_uuid,
                Program.subscription_id == current_user.subscription_id,
                Program.is_template == True,
                Program.archived_at.is_(None)
            )
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # 2. Verify coach-client relationship
    if current_user.role.value == "COACH":
        coach_result = await db.execute(
            select(CoachClientAssignment).where(
                and_(
                    CoachClientAssignment.coach_id == current_user.id,
                    CoachClientAssignment.client_id == client_uuid,
                    CoachClientAssignment.is_active == True
                )
            )
        )
        if not coach_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only generate programs for your assigned clients"
            )

    # 3. Get client for naming
    client_result = await db.execute(select(UserModel).where(UserModel.id == client_uuid))
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    client_profile = client.profile or {}
    basic_info = client_profile.get("basic_info", {})
    client_name = f"{basic_info.get('first_name', 'Unknown')} {basic_info.get('last_name', 'Client')}"

    # 4. Build ProgramInputs from template + client params
    movements = [
        MovementInput(
            name=m.name,
            one_rm=m.one_rm,
            max_reps_at_80_percent=m.max_reps_at_80_percent,
            target_weight=m.target_weight
        )
        for m in request.movements
    ]
    program_inputs = ProgramInputs(
        builder_type=template.builder_type or "strength_linear_5x5",
        name=None,
        description=None,
        movements=movements,
        duration_weeks=template.duration_weeks,
        days_per_week=template.days_per_week,
        is_template=False,
    )

    # 5. Generate preview
    try:
        preview = StrengthProgramGenerator.generate_preview(program_inputs)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to generate program: {str(e)}")

    # 6. Create client Program record (draft)
    client_program = Program(
        subscription_id=current_user.subscription_id,
        created_by_user_id=current_user.id,
        name=f"{template.name} — {client_name}",
        description=template.description,
        builder_type=template.builder_type,
        algorithm_version=preview.algorithm_version,
        input_data=preview.input_data,
        calculated_data={name: calc.model_dump() for name, calc in preview.calculated_data.items()},
        is_template=False,
        is_public=False,
        status="draft",
        parent_template_id=template.id,
        duration_weeks=template.duration_weeks,
        days_per_week=template.days_per_week,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    db.add(client_program)
    await db.flush()

    # 7. Create week/day/exercise tree
    for week_detail in preview.weeks:
        program_week = ProgramWeek(
            program_id=client_program.id,
            subscription_id=current_user.subscription_id,
            week_number=week_detail.week_number,
            name=week_detail.name,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        db.add(program_week)
        await db.flush()

        for day_detail in week_detail.days:
            program_day = ProgramDay(
                program_week_id=program_week.id,
                subscription_id=current_user.subscription_id,
                day_number=day_detail.day_number,
                name=day_detail.name,
                suggested_day_of_week=day_detail.suggested_day_of_week,
                created_by=current_user.id,
                updated_by=current_user.id
            )
            db.add(program_day)
            await db.flush()

            for order, exercise_detail in enumerate(day_detail.exercises):
                program_day_exercise = ProgramDayExercise(
                    program_day_id=program_day.id,
                    subscription_id=current_user.subscription_id,
                    exercise_name=exercise_detail.exercise_name,
                    exercise_order=order + 1,
                    sets=exercise_detail.sets,
                    reps=exercise_detail.reps,
                    reps_target=exercise_detail.reps,
                    weight_lbs=exercise_detail.weight_lbs,
                    load_value=exercise_detail.weight_lbs,
                    load_unit="lbs",
                    load_type="fixed_weight",
                    percentage_1rm=exercise_detail.percentage_1rm,
                    notes=exercise_detail.notes or "",
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                db.add(program_day_exercise)

    # 8. Create assignment record
    start_date = request.start_date or date_type.today()
    end_date = start_date + timedelta(weeks=template.duration_weeks)
    assignment = ClientProgramAssignment(
        subscription_id=current_user.subscription_id,
        location_id=current_user.location_id,
        coach_id=current_user.id,
        client_id=client_uuid,
        program_id=client_program.id,
        start_date=start_date,
        end_date=end_date,
        status="assigned",
        current_week=1,
        current_day=1,
        is_active=True,
        notes=request.notes,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    db.add(assignment)

    # 9. Increment template usage counter
    template.times_assigned = (template.times_assigned or 0) + 1

    await db.commit()
    await db.refresh(client_program)
    await db.refresh(assignment)

    return GenerateForClientResponse(
        program_id=str(client_program.id),
        assignment_id=str(assignment.id),
        client_id=str(client_uuid),
        status="draft"
    )


# ============================================================================
# PATCH Exercise in Draft Program
# ============================================================================

@router.patch(
    "/{program_id}/exercises/{exercise_id}",
    response_model=UpdateExerciseResponse,
    summary="Update a single exercise in a draft program",
)
async def update_program_exercise(
    program_id: str,
    exercise_id: str,
    request: UpdateExerciseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Partially update an exercise in a draft program."""
    from uuid import UUID
    from datetime import datetime
    from app.models.program import Program, ProgramDayExercise
    from app.models.program import ProgramDay, ProgramWeek
    from sqlalchemy import select, and_

    try:
        program_uuid = UUID(program_id)
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format")

    # Verify program is a draft in this subscription
    prog_result = await db.execute(
        select(Program).where(
            and_(
                Program.id == program_uuid,
                Program.subscription_id == current_user.subscription_id,
                Program.is_template == False,
                Program.status == "draft",
                Program.archived_at.is_(None)
            )
        )
    )
    program = prog_result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft program not found")

    # Load exercise (verify it belongs to this program via join)
    ex_result = await db.execute(
        select(ProgramDayExercise)
        .join(ProgramDay, ProgramDayExercise.program_day_id == ProgramDay.id)
        .join(ProgramWeek, ProgramDay.program_week_id == ProgramWeek.id)
        .where(
            and_(
                ProgramDayExercise.id == exercise_uuid,
                ProgramWeek.program_id == program_uuid
            )
        )
    )
    exercise = ex_result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found in this program")

    # Apply partial updates
    if request.sets is not None:
        exercise.sets = request.sets
    if request.reps is not None:
        exercise.reps = request.reps
    if request.reps_target is not None:
        exercise.reps_target = request.reps_target
    if request.weight_lbs is not None:
        exercise.weight_lbs = request.weight_lbs
    if request.load_value is not None:
        exercise.load_value = request.load_value
    if request.notes is not None:
        exercise.notes = request.notes
    exercise.updated_by = current_user.id

    await db.commit()
    await db.refresh(exercise)

    return UpdateExerciseResponse(
        exercise_id=str(exercise.id),
        sets=exercise.sets,
        reps=exercise.reps,
        reps_target=exercise.reps_target,
        weight_lbs=exercise.weight_lbs,
        load_value=exercise.load_value,
        notes=exercise.notes,
        updated_at=exercise.updated_at.isoformat()
    )


# ============================================================================
# POST Publish Draft Program
# ============================================================================

@router.post(
    "/{program_id}/publish",
    response_model=PublishProgramResponse,
    summary="Publish a draft program (makes it visible to the client)",
)
async def publish_program(
    program_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publish a draft program so the client can see it."""
    from uuid import UUID
    from datetime import datetime
    from app.models.program import Program
    from sqlalchemy import select, and_

    try:
        program_uuid = UUID(program_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format")

    result = await db.execute(
        select(Program).where(
            and_(
                Program.id == program_uuid,
                Program.subscription_id == current_user.subscription_id,
                Program.is_template == False,
                Program.status == "draft",
                Program.archived_at.is_(None)
            )
        )
    )
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft program not found")

    published_at = datetime.utcnow().isoformat()
    program.status = "published"
    program.updated_by = current_user.id
    await db.commit()

    return PublishProgramResponse(
        program_id=str(program.id),
        status="published",
        published_at=published_at
    )
