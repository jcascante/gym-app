"""
Assignment management endpoints.

GET  /workouts/assignments/{id}/today      — today's prescribed workout
PATCH /workouts/assignments/{id}/progress  — coach manual progress override
PATCH /workouts/assignments/{id}/feedback  — client submits rating + feedback
GET  /workouts/assignments/{id}            — current assignment state
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.client_program_assignment import ClientProgramAssignment
from app.models.program import ProgramDay, ProgramWeek
from app.models.user import User, UserRole
from app.models.workout_log import WorkoutLog
from app.schemas.program_self_start import (
    AssignmentResponse,
    DayLogSummary,
    ExercisePrescription,
    FeedbackRequest,
    ProgressOverrideRequest,
    TodayWorkoutResponse,
)

router = APIRouter()


async def _get_assignment(
    assignment_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> ClientProgramAssignment:
    """Load assignment + program, enforcing ownership or coach access."""
    result = await db.execute(
        select(ClientProgramAssignment)
        .options(selectinload(ClientProgramAssignment.program))  # type: ignore[attr-defined]
        .where(
            and_(
                ClientProgramAssignment.id == assignment_id,
                ClientProgramAssignment.subscription_id == current_user.subscription_id,
            )
        )
    )
    assignment = result.unique().scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    is_owner = str(assignment.client_id) == str(current_user.id)
    is_coach_or_admin = current_user.role in (
        UserRole.COACH,
        UserRole.SUBSCRIPTION_ADMIN,
        UserRole.APPLICATION_SUPPORT,
    )
    if not (is_owner or is_coach_or_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return assignment


def _assignment_response(assignment: ClientProgramAssignment) -> AssignmentResponse:
    return AssignmentResponse(
        id=str(assignment.id),
        program_id=str(assignment.program_id),
        client_id=str(assignment.client_id),
        assignment_name=assignment.assignment_name,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        status=assignment.status,
        current_week=assignment.current_week,
        current_day=assignment.current_day,
        workouts_completed=assignment.workouts_completed or 0,
        workouts_skipped=assignment.workouts_skipped or 0,
        progress_percentage=assignment.progress_percentage,
        progress_health=assignment.progress_health,
        client_rating=assignment.client_rating,
        client_feedback=assignment.client_feedback,
    )


# ---------------------------------------------------------------------------
# GET /workouts/assignments/{id}/today
# ---------------------------------------------------------------------------


@router.get("/{assignment_id}/today", response_model=TodayWorkoutResponse)
async def get_today_workout(
    assignment_id: UUID,
    week: int | None = Query(None, ge=1, description="Week number to load (defaults to current)"),
    day: int | None = Query(None, ge=1, description="Day number to load (defaults to current)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a ProgramDay with all exercises as prescribed.
    Defaults to current_week/current_day on the assignment.
    Pass ?week=X&day=Y to load any specific day (e.g. to log a missed session).
    """
    assignment = await _get_assignment(assignment_id, current_user, db)
    program = assignment.program

    target_week = week if week is not None else assignment.current_week
    target_day = day if day is not None else assignment.current_day

    # Find the ProgramDay matching target_week / target_day
    result = await db.execute(
        select(ProgramDay)
        .options(selectinload(ProgramDay.exercises), selectinload(ProgramDay.week))
        .join(ProgramWeek, ProgramDay.program_week_id == ProgramWeek.id)
        .where(
            and_(
                ProgramWeek.program_id == program.id,
                ProgramWeek.week_number == target_week,
                ProgramDay.day_number == target_day,
            )
        )
    )
    day = result.unique().scalar_one_or_none()

    program_day = day  # rename to avoid shadowing the query param
    if not program_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No day found for week {target_week}, day {target_day}",
        )

    exercises = [
        ExercisePrescription(
            id=str(ex.id),
            exercise_name=ex.exercise_name or "",
            sets=ex.sets,
            reps=ex.reps or ex.reps_target,
            reps_target=ex.reps_target,
            weight_lbs=ex.weight_lbs or ex.load_value,
            rpe_target=ex.rpe_target,
            percentage_1rm=ex.percentage_1rm,
            rest_seconds=ex.rest_seconds,
            notes=ex.notes,
            coaching_cues=ex.coaching_cues,
            exercise_order=ex.exercise_order,
        )
        for ex in sorted(program_day.exercises, key=lambda e: (e.exercise_order or 0))
    ]

    return TodayWorkoutResponse(
        assignment_id=str(assignment.id),
        program_day_id=str(program_day.id),
        week_number=target_week,
        day_number=target_day,
        day_name=program_day.name,
        exercises=exercises,
        current_week=assignment.current_week,
        current_day=assignment.current_day,
        progress_percentage=assignment.progress_percentage,
        progress_health=assignment.progress_health,
    )


# ---------------------------------------------------------------------------
# GET /workouts/assignments/{id}/logs
# ---------------------------------------------------------------------------


@router.get("/{assignment_id}/logs", response_model=list[DayLogSummary])
async def get_assignment_logs(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all workout logs for this assignment, one entry per logged day.
    Used to show per-day completion status in the program view.
    """
    await _get_assignment(assignment_id, current_user, db)  # auth check

    result = await db.execute(
        select(WorkoutLog)
        .join(ProgramDay, WorkoutLog.program_day_id == ProgramDay.id, isouter=True)
        .join(ProgramWeek, ProgramDay.program_week_id == ProgramWeek.id, isouter=True)
        .where(WorkoutLog.client_program_assignment_id == assignment_id)
        .order_by(WorkoutLog.workout_date)
    )
    logs = result.scalars().all()

    return [
        DayLogSummary(
            workout_log_id=str(log.id),
            program_day_id=str(log.program_day_id) if log.program_day_id else None,
            day_status=log.day_status or log.status.value,
            workout_date=log.workout_date.isoformat(),
        )
        for log in logs
    ]


# ---------------------------------------------------------------------------
# GET /workouts/assignments/{id}
# ---------------------------------------------------------------------------


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Current state of an assignment."""
    assignment = await _get_assignment(assignment_id, current_user, db)
    return _assignment_response(assignment)


# ---------------------------------------------------------------------------
# PATCH /workouts/assignments/{id}/progress  (coach override)
# ---------------------------------------------------------------------------


@router.patch("/{assignment_id}/progress", response_model=AssignmentResponse)
async def override_progress(
    assignment_id: UUID,
    body: ProgressOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Coach manual override of current_week / current_day / status."""
    if current_user.role not in (
        UserRole.COACH,
        UserRole.SUBSCRIPTION_ADMIN,
        UserRole.APPLICATION_SUPPORT,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coaches only")

    assignment = await _get_assignment(assignment_id, current_user, db)

    if body.current_week is not None:
        assignment.current_week = body.current_week
    if body.current_day is not None:
        assignment.current_day = body.current_day
    if body.status is not None:
        assignment.status = body.status
    assignment.updated_by = current_user.id

    await db.commit()
    await db.refresh(assignment)
    return _assignment_response(assignment)


# ---------------------------------------------------------------------------
# PATCH /workouts/assignments/{id}/feedback  (client)
# ---------------------------------------------------------------------------


@router.patch("/{assignment_id}/feedback", response_model=AssignmentResponse)
async def submit_feedback(
    assignment_id: UUID,
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Client submits overall program rating and free-text feedback."""
    assignment = await _get_assignment(assignment_id, current_user, db)

    # Only the client themselves can submit feedback
    if str(assignment.client_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the client can submit feedback")

    if body.client_rating is not None:
        assignment.client_rating = body.client_rating
    if body.client_feedback is not None:
        assignment.client_feedback = body.client_feedback
    assignment.updated_by = current_user.id

    await db.commit()
    await db.refresh(assignment)
    return _assignment_response(assignment)
