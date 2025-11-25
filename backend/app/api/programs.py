"""
Programs API endpoints

Provides three key endpoints:
1. GET /algorithms/{builder_type}/constants - Calculation constants for frontend
2. POST /preview - Calculate program preview without saving
3. POST / - Calculate and save program to database
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.program import (
    ProgramInputs,
    ProgramPreview,
    CalculationConstants,
    ProgramResponse
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
                        exercise_name=exercise_detail.exercise_name,
                        sets=exercise_detail.sets,
                        reps=exercise_detail.reps,
                        weight_lbs=exercise_detail.weight_lbs,
                        percentage_1rm=exercise_detail.percentage_1rm,
                        notes=exercise_detail.notes or "",
                        order=order,
                        created_by=current_user.id,
                        updated_by=current_user.id
                    )
                    db.add(program_day_exercise)

        # 6. Commit to database
        await db.commit()
        await db.refresh(program)

        # 7. Return ProgramResponse
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
# Additional endpoints (TODO - Phase 2)
# ============================================================================

# GET /programs - List all templates
# GET /programs/{id} - Get specific program with full details
# PUT /programs/{id} - Update program
# DELETE /programs/{id} - Delete/archive program
# POST /programs/{id}/duplicate - Duplicate template
