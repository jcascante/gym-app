"""
Exercise Library API endpoints.

Provides CRUD for the exercise library, supporting both global exercises
(visible to all subscriptions) and subscription-specific custom exercises.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.exercise import Exercise
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse,
    ExerciseListResponse,
)

router = APIRouter()


# ============================================================================
# GET /exercises — List exercises
# ============================================================================

@router.get(
    "",
    response_model=ExerciseListResponse,
    summary="List exercises",
    description="""
    List exercises available to the current user.

    Returns:
    - Global platform exercises (is_global=True)
    - Subscription-specific exercises for the user's subscription

    **Filters:**
    - search: Filter by name (case-insensitive substring)
    - category: Filter by category (compound, isolation, cardio, mobility)
    - muscle_group: Filter by muscle group (substring match in array)
    - equipment: Filter by equipment required
    - difficulty_level: Filter by difficulty
    """
)
async def list_exercises(
    search: Optional[str] = Query(None, description="Filter by name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    muscle_group: Optional[str] = Query(None, description="Filter by muscle group"),
    difficulty_level: Optional[str] = Query(None, description="Filter by difficulty"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExerciseListResponse:
    # Base filter: active exercises that are global OR belong to the user's subscription
    base_filter = and_(
        Exercise.is_active == True,
        or_(
            Exercise.is_global == True,
            Exercise.subscription_id == current_user.subscription_id,
        ),
    )

    query = select(Exercise).where(base_filter)

    if search:
        query = query.where(Exercise.name.ilike(f"%{search}%"))
    if category:
        query = query.where(Exercise.category == category)
    if difficulty_level:
        query = query.where(Exercise.difficulty_level == difficulty_level)
    # muscle_group is a JSON array; use ilike on the cast for SQLite compatibility
    if muscle_group:
        query = query.where(
            func.cast(Exercise.muscle_groups, type_=None).ilike(f"%{muscle_group}%")
        )

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Exercise.name).offset(offset).limit(limit)
    exercises = (await db.execute(query)).scalars().all()

    return ExerciseListResponse(
        exercises=[ExerciseResponse.model_validate(e) for e in exercises],
        total=total,
        count=len(exercises),
        offset=offset,
        limit=limit,
    )


# ============================================================================
# GET /exercises/{exercise_id} — Get single exercise
# ============================================================================

@router.get(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Get exercise by ID",
)
async def get_exercise(
    exercise_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    result = await db.execute(
        select(Exercise).where(
            and_(
                Exercise.id == exercise_id,
                Exercise.is_active == True,
                or_(
                    Exercise.is_global == True,
                    Exercise.subscription_id == current_user.subscription_id,
                ),
            )
        )
    )
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return ExerciseResponse.model_validate(exercise)


# ============================================================================
# POST /exercises — Create exercise
# ============================================================================

@router.post(
    "",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom exercise",
    description="""
    Create a custom exercise for the current subscription.

    **Permissions:**
    - COACH / SUBSCRIPTION_ADMIN: Can create subscription-specific exercises
    - APPLICATION_SUPPORT: Can create global exercises (is_global=True)
    """
)
async def create_exercise(
    data: ExerciseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    # Only admins and coaches can create exercises
    if current_user.role not in (UserRole.COACH, UserRole.SUBSCRIPTION_ADMIN, UserRole.APPLICATION_SUPPORT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only coaches and admins can create exercises",
        )

    is_global = current_user.role == UserRole.APPLICATION_SUPPORT
    subscription_id = None if is_global else current_user.subscription_id

    exercise = Exercise(
        subscription_id=subscription_id,
        name=data.name,
        description=data.description,
        category=data.category,
        muscle_groups=data.muscle_groups or [],
        equipment=data.equipment or [],
        video_url=data.video_url,
        thumbnail_url=data.thumbnail_url,
        is_bilateral=data.is_bilateral,
        is_timed=data.is_timed,
        default_rest_seconds=data.default_rest_seconds,
        difficulty_level=data.difficulty_level,
        is_global=is_global,
        is_verified=is_global,  # Global exercises created by support are auto-verified
        is_active=True,
        created_by=current_user.id,
        updated_by=current_user.id,
    )

    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)

    return ExerciseResponse.model_validate(exercise)


# ============================================================================
# PATCH /exercises/{exercise_id} — Update exercise
# ============================================================================

@router.patch(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Update an exercise",
)
async def update_exercise(
    exercise_id: UUID,
    data: ExerciseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    result = await db.execute(
        select(Exercise).where(
            and_(
                Exercise.id == exercise_id,
                or_(
                    # Subscription exercise: owner subscription can edit
                    Exercise.subscription_id == current_user.subscription_id,
                    # Global exercise: only APPLICATION_SUPPORT can edit
                    and_(
                        Exercise.is_global == True,
                        current_user.role == UserRole.APPLICATION_SUPPORT,
                    ),
                ),
            )
        )
    )
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found or not editable",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exercise, field, value)
    exercise.updated_by = current_user.id

    await db.commit()
    await db.refresh(exercise)

    return ExerciseResponse.model_validate(exercise)


# ============================================================================
# DELETE /exercises/{exercise_id} — Soft-delete exercise
# ============================================================================

@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete (deactivate) an exercise",
)
async def delete_exercise(
    exercise_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Exercise).where(
            and_(
                Exercise.id == exercise_id,
                Exercise.is_active == True,
                or_(
                    Exercise.subscription_id == current_user.subscription_id,
                    and_(
                        Exercise.is_global == True,
                        current_user.role == UserRole.APPLICATION_SUPPORT,
                    ),
                ),
            )
        )
    )
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found or not deletable",
        )

    exercise.is_active = False
    exercise.updated_by = current_user.id
    await db.commit()

    return {"message": "Exercise deactivated successfully"}
