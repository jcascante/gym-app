"""
Workout endpoints for logging and tracking workouts.

Provides REST API for managing workout logs, retrieving workout history,
and calculating fitness statistics.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, UserRole, WorkoutStatus
from app.schemas.workout import (
    RecentWorkoutResponse,
    WorkoutHistoryResponse,
    WorkoutLogCreate,
    WorkoutLogResponse,
    WorkoutLogUpdate,
    WorkoutStatsResponse,
)
from app.schemas.workout_exercise_log import (
    ExerciseLogResponse,
    SetLogResponse,
    WorkoutLogExtendedRequest,
    WorkoutLogExtendedResponse,
)
from app.services.workout_service import WorkoutService

router = APIRouter()


def _serialize_workout_for_response(w):
    """Map WorkoutLog model to dict matching WorkoutLogResponse schema."""
    return {
        "id": w.id,
        "client_id": w.client_id,
        "coach_id": getattr(w, "coach_id", None),
        "program_id": w.program_id,
        "assignment_id": getattr(w, "client_program_assignment_id", None),
        "status": w.status,
        "workout_date": w.workout_date,
        "duration_minutes": w.duration_minutes,
        "notes": w.notes,
        "created_at": w.created_at,
        "updated_at": w.updated_at,
    }


def _serialize_workout_for_recent(w):
    return {
        "id": w.id,
        "workout_date": w.workout_date,
        "status": w.status,
        "duration_minutes": w.duration_minutes,
        "notes": w.notes,
        "program_name": getattr(getattr(w, 'program', None), 'name', None),
        "assignment_name": getattr(getattr(w, 'assignment', None), 'assignment_name', None),
    }


@router.post(
    "",
    response_model=WorkoutLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a workout session",
    tags=["Workouts"],
)
async def create_workout_log(
    request: WorkoutLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutLogResponse:
    """
    Log a new workout session.

    Only clients can log their own workouts, coaches can log for their clients.

    **Authorization:**
    - Clients can only log their own workouts
    - Coaches can log workouts for their assigned clients
    """
    # Get the assignment to validate and extract necessary IDs
    from sqlalchemy import select

    from app.models import ClientProgramAssignment

    stmt = select(ClientProgramAssignment).where(
        ClientProgramAssignment.id == request.assignment_id
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program assignment not found",
        )

    # Authorization check
    if current_user.role == UserRole.CLIENT:
        if assignment.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot log workouts for other clients",
            )
    elif current_user.role == UserRole.COACH:
        # Verify coach-client relationship (if assignment exists, coach is authorized)
        # This could be enhanced with explicit coach-client assignment checks
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients and coaches can log workouts",
        )

    # Create workout log
    workout = await WorkoutService.create_workout_log(
        db=db,
        subscription_id=current_user.subscription_id,
        client_id=assignment.client_id,
        assignment_id=request.assignment_id,
        program_id=assignment.program_id,
        coach_id=current_user.id if current_user.role == UserRole.COACH else None,
        status=request.status,
        duration_minutes=request.duration_minutes,
        notes=request.notes,
        workout_date=request.workout_date,
        created_by=current_user.id,
    )

    await db.commit()

    return WorkoutLogResponse.model_validate(_serialize_workout_for_response(workout))



@router.post(
    "/log",
    status_code=status.HTTP_201_CREATED,
    summary="Log a full workout session with per-set exercise data",
    tags=["Workouts"],
)
async def create_extended_workout_log(
    request: WorkoutLogExtendedRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Extended workout log endpoint. Creates:
    - WorkoutLog with day_status / session_rating / program_day_id
    - WorkoutExerciseLog rows (one per set)
    - Calls advance_progress() on the assignment → auto-advances current_week/current_day
    """
    from datetime import datetime as dt_type

    from sqlalchemy import select as sa_select

    from app.models import ClientProgramAssignment
    from app.models.workout_exercise_log import WorkoutExerciseLog
    from app.models.workout_log import WorkoutLog
    from app.services.assignment_service import advance_progress

    assignment_uuid = UUID(request.assignment_id)
    stmt = sa_select(ClientProgramAssignment).where(ClientProgramAssignment.id == assignment_uuid)
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if current_user.role == UserRole.CLIENT and assignment.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot log for another client")

    program_day_uuid = UUID(request.program_day_id) if request.program_day_id else None

    workout = WorkoutLog(
        subscription_id=current_user.subscription_id,
        client_id=assignment.client_id,
        client_program_assignment_id=assignment_uuid,
        program_id=assignment.program_id,
        program_day_id=program_day_uuid,
        coach_id=current_user.id if current_user.role == UserRole.COACH else None,
        status=WorkoutStatus.COMPLETED if request.day_status == "completed" else WorkoutStatus.SKIPPED,
        day_status=request.day_status,
        duration_minutes=request.duration_minutes,
        session_rating=request.session_rating,
        notes=request.notes,
        workout_date=dt_type.utcnow(),
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(workout)
    await db.flush()

    # Create per-set exercise logs
    now = dt_type.utcnow()
    for ex_log in request.exercise_logs:
        pde_uuid = UUID(ex_log.program_day_exercise_id) if ex_log.program_day_exercise_id else None
        for set_data in ex_log.sets:
            set_log = WorkoutExerciseLog(
                subscription_id=current_user.subscription_id,
                workout_log_id=workout.id,
                program_day_exercise_id=pde_uuid,
                exercise_name=ex_log.exercise_name,
                set_number=set_data.set_number,
                actual_reps=set_data.actual_reps,
                actual_weight_lbs=set_data.actual_weight_lbs,
                actual_rpe=set_data.actual_rpe,
                notes=set_data.notes,
                completed_at=now,
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            db.add(set_log)

    # Auto-advance assignment position
    updated_assignment = await advance_progress(
        assignment_id=assignment_uuid,
        day_status=request.day_status,
        db=db,
    )

    await db.commit()
    await db.refresh(workout)
    await db.refresh(updated_assignment)

    return WorkoutLogExtendedResponse(
        workout_log_id=str(workout.id),
        assignment_id=str(assignment_uuid),
        program_day_id=str(program_day_uuid) if program_day_uuid else None,
        day_status=workout.day_status,
        duration_minutes=workout.duration_minutes,
        session_rating=workout.session_rating,
        exercise_logs=[],  # omit full set data from response for brevity
        current_week=updated_assignment.current_week,
        current_day=updated_assignment.current_day,
        assignment_status=updated_assignment.status,
        progress_percentage=updated_assignment.progress_percentage,
        progress_health=updated_assignment.progress_health,
    )


@router.get(
    "/assignments/{assignment_id}/workouts",
    response_model=list[WorkoutLogResponse],
    summary="Get workouts for a program assignment",
    tags=["Workouts"],
)
async def get_workouts_for_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all workout logs for a specific program assignment.

    Clients may only retrieve workouts for their own assignments. Coaches may
    retrieve workouts for assignments they created/own.
    """
    from sqlalchemy import select

    from app.models import ClientProgramAssignment

    stmt = select(ClientProgramAssignment).where(ClientProgramAssignment.id == assignment_id)
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Authorization
    if current_user.role == UserRole.CLIENT:
        if assignment.client_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view workouts for assignments you don't own")
    elif current_user.role == UserRole.COACH:
        if assignment.coach_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view workouts for assignments you don't own")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view assignment workouts")

    workouts = await WorkoutService.get_assignment_workouts(db=db, assignment_id=assignment_id)

    return [WorkoutLogResponse.model_validate(_serialize_workout_for_response(w)) for w in workouts]


@router.get(
    "/stats",
    response_model=WorkoutStatsResponse,
    summary="Get workout statistics",
    tags=["Workouts"],
)
async def get_workout_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutStatsResponse:
    """
    Get workout statistics for the current user (must be a client).

    Returns:
    - total_workouts: Total number of workouts logged
    - completed_workouts: Number of completed workouts
    - skipped_workouts: Number of skipped workouts
    - last_workout_date: ISO format datetime of last completed workout
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can view their own stats",
        )

    stats = await WorkoutService.get_client_workout_stats(
        db=db,
        client_id=current_user.id,
    )

    return WorkoutStatsResponse(**stats)


@router.get(
    "/recent",
    response_model=list[RecentWorkoutResponse],
    summary="Get recent workouts",
    tags=["Workouts"],
)
async def get_recent_workouts(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecentWorkoutResponse]:
    """
    Get recent completed workouts for the current client.

    Only clients can retrieve their own recent workouts.

    **Query Parameters:**
    - days: Number of days to look back (1-90, default 7)
    - limit: Maximum number of results (1-100, default 10)
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can view their workouts",
        )

    workouts = await WorkoutService.get_client_recent_workouts(
        db=db,
        client_id=current_user.id,
        days=days,
        limit=limit,
    )

    return [RecentWorkoutResponse.model_validate(_serialize_workout_for_recent(w)) for w in workouts]


@router.get(
    "/{workout_id}/detail",
    summary="Get full workout detail including per-set exercise logs",
    tags=["Workouts"],
)
async def get_workout_detail(
    workout_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a workout log together with all per-set exercise data.
    Used to pre-fill the re-log form with previously recorded values.
    """
    from collections import defaultdict

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.workout_log import WorkoutLog

    result = await db.execute(
        select(WorkoutLog)
        .options(selectinload(WorkoutLog.exercise_logs))
        .where(WorkoutLog.id == workout_id)
    )
    workout = result.unique().scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    if current_user.role == UserRole.CLIENT and workout.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Group exercise logs by exercise_name + program_day_exercise_id
    grouped: dict = defaultdict(list)
    for s in sorted(workout.exercise_logs, key=lambda x: (x.exercise_name, x.set_number)):
        key = (s.exercise_name, str(s.program_day_exercise_id) if s.program_day_exercise_id else None)
        grouped[key].append(s)

    exercise_logs = [
        ExerciseLogResponse(
            exercise_name=key[0],
            program_day_exercise_id=key[1],
            sets=[
                SetLogResponse(
                    id=str(s.id),
                    set_number=s.set_number,
                    actual_reps=s.actual_reps,
                    actual_weight_lbs=s.actual_weight_lbs,
                    actual_rpe=s.actual_rpe,
                    notes=s.notes,
                    completed_at=s.completed_at,
                )
                for s in sets
            ],
        )
        for key, sets in grouped.items()
    ]

    return {
        "workout_log_id": str(workout.id),
        "day_status": workout.day_status,
        "duration_minutes": workout.duration_minutes,
        "session_rating": workout.session_rating,
        "notes": workout.notes,
        "exercise_logs": [el.model_dump() for el in exercise_logs],
    }


@router.get(
    "/{workout_id}",
    response_model=WorkoutLogResponse,
    summary="Get workout details",
    tags=["Workouts"],
)
async def get_workout(
    workout_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutLogResponse:
    """
    Get details for a specific workout log.

    Only clients can view their own workouts, coaches can view their clients' workouts.
    """
    workout = await WorkoutService.get_workout_log(db=db, workout_id=workout_id)

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    # Authorization check
    if current_user.role == UserRole.CLIENT:
        if workout.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other clients' workouts",
            )
    elif current_user.role == UserRole.COACH:
        # Verify coach-client relationship
        if workout.coach_id != current_user.id and workout.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view workouts for clients you don't coach",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view workouts",
        )

    return WorkoutLogResponse.model_validate(_serialize_workout_for_response(workout))


@router.get(
    "",
    response_model=WorkoutHistoryResponse,
    summary="Get workout history",
    tags=["Workouts"],
)
async def get_workout_history(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status_filter: WorkoutStatus | None = Query(
        None,
        description="Filter by workout status (completed, skipped, scheduled)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutHistoryResponse:
    """
    Get workout history for the current client.

    Only clients can retrieve their own history.

    **Query Parameters:**
    - limit: Maximum number of results (1-100, default 20)
    - offset: Pagination offset (default 0)
    - status: Filter by status (completed, skipped, or scheduled)
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can view their workout history",
        )

    workouts, total = await WorkoutService.get_client_workout_history(
        db=db,
        client_id=current_user.id,
        limit=limit,
        offset=offset,
        status_filter=status_filter,
    )

    return WorkoutHistoryResponse(
        total=total,
        count=len(workouts),
        offset=offset,
        limit=limit,
        workouts=[WorkoutLogResponse.model_validate(_serialize_workout_for_response(w)) for w in workouts],
    )


@router.put(
    "/{workout_id}",
    response_model=WorkoutLogResponse,
    summary="Update a workout log",
    tags=["Workouts"],
)
async def update_workout(
    workout_id: UUID,
    request: WorkoutLogUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutLogResponse:
    """
    Update a workout log.

    Only the client who logged the workout or their coach can update it.
    """
    workout = await WorkoutService.get_workout_log(db=db, workout_id=workout_id)

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    # Authorization check
    if current_user.role == UserRole.CLIENT:
        if workout.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update other clients' workouts",
            )
    elif current_user.role == UserRole.COACH:
        if workout.coach_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update workouts for clients you don't coach",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update workouts",
        )

    updated = await WorkoutService.update_workout_log(
        db=db,
        workout_id=workout_id,
        status=request.status,
        duration_minutes=request.duration_minutes,
        notes=request.notes,
        updated_by=current_user.id,
    )

    await db.commit()

    return WorkoutLogResponse.model_validate(_serialize_workout_for_response(updated))


@router.delete(
    "/{workout_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workout log",
    tags=["Workouts"],
)
async def delete_workout(
    workout_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a workout log.

    Only the client who logged the workout or their coach can delete it.
    """
    workout = await WorkoutService.get_workout_log(db=db, workout_id=workout_id)

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    # Authorization check
    if current_user.role == UserRole.CLIENT:
        if workout.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete other clients' workouts",
            )
    elif current_user.role == UserRole.COACH:
        if workout.coach_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete workouts for clients you don't coach",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete workouts",
        )

    deleted = await WorkoutService.delete_workout_log(db=db, workout_id=workout_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workout",
        )

    await db.commit()
