"""
Program template browsing and client self-service start flow.

GET  /programs/templates                    — list engine + coach templates
GET  /programs/templates/{id}               — template detail
POST /programs/templates/{id}/preview       — dry-run generation
POST /programs/templates/{id}/start         — generate copy + assign to self
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.program import Program, ProgramDay, ProgramWeek
from app.models.user import User
from app.schemas.program import (
    DayDetail,
    ExerciseDetail,
    ProgramDetailResponse,
    WeekDetail,
)
from app.schemas.program_self_start import (
    SelfStartRequest,
    SelfStartResponse,
    TemplateListItem,
    TemplateListResponse,
)
from app.services import engine_client

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /programs/templates
# ---------------------------------------------------------------------------


@router.get("/", response_model=TemplateListResponse, summary="List available program templates")
async def list_templates(
    source: str | None = None,  # "engine" | "coach" | None (all)
    difficulty: str | None = None,
    duration_weeks: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns both engine-defined programs and coach-created templates visible
    to the current user's subscription.
    """
    items: list[TemplateListItem] = []

    # --- Engine templates ---
    if source in (None, "engine"):
        try:
            engine_defs = await engine_client.list_program_definitions()
        except HTTPException:
            engine_defs = []

        for defn in engine_defs:
            dw = defn.get("duration_weeks") or defn.get("weeks")
            dpw = defn.get("days_per_week") or defn.get("days")
            if duration_weeks and dw != duration_weeks:
                continue
            if difficulty and defn.get("difficulty_level") != difficulty:
                continue
            items.append(
                TemplateListItem(
                    id=str(defn.get("id") or defn.get("program_id", "")),
                    source="engine",
                    name=defn.get("name", ""),
                    description=defn.get("description"),
                    program_type=defn.get("program_type"),
                    difficulty_level=defn.get("difficulty_level"),
                    duration_weeks=dw or 0,
                    days_per_week=dpw or 0,
                    tags=defn.get("tags", []),
                    times_assigned=defn.get("times_assigned", 0),
                )
            )

    # --- Coach templates (subscription-scoped + public) ---
    if source in (None, "coach"):
        query = (
            select(Program)
            .where(
                and_(
                    Program.is_template == True,
                    Program.archived_at.is_(None),
                    or_(
                        Program.subscription_id == current_user.subscription_id,
                        Program.is_public == True,
                    ),
                )
            )
            .order_by(Program.created_at.desc())
        )
        if difficulty:
            query = query.where(Program.difficulty_level == difficulty)
        if duration_weeks:
            query = query.where(Program.duration_weeks == duration_weeks)

        result = await db.execute(query)
        programs = result.scalars().all()

        for p in programs:
            items.append(
                TemplateListItem(
                    id=str(p.id),
                    source="coach",
                    name=p.name,
                    description=p.description,
                    program_type=p.program_type,
                    difficulty_level=p.difficulty_level,
                    duration_weeks=p.duration_weeks,
                    days_per_week=p.days_per_week,
                    tags=p.tags or [],
                    times_assigned=p.times_assigned or 0,
                )
            )

    return TemplateListResponse(templates=items, total=len(items))


# ---------------------------------------------------------------------------
# GET /programs/templates/{id}
# ---------------------------------------------------------------------------


@router.get("/{template_id}", summary="Template detail")
async def get_template(
    template_id: str,
    source: str = "coach",  # "engine" | "coach"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    For engine templates: proxies to TrainGen Engine definition detail.
    For coach templates: returns full program tree from DB.
    """
    if source == "engine":
        return await engine_client.get_program_definition(template_id)

    from uuid import UUID

    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid template ID")

    result = await db.execute(
        select(Program)
        .options(
            selectinload(Program.weeks)
            .selectinload(ProgramWeek.days)
            .selectinload(ProgramDay.exercises)
        )
        .where(
            and_(
                Program.id == template_uuid,
                Program.is_template == True,
                Program.archived_at.is_(None),
                or_(
                    Program.subscription_id == current_user.subscription_id,
                    Program.is_public == True,
                ),
            )
        )
    )
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    weeks = []
    for week in sorted(program.weeks, key=lambda w: w.week_number):
        days = []
        for day in sorted(week.days, key=lambda d: d.day_number):
            exercises = [
                ExerciseDetail(
                    id=str(ex.id),
                    exercise_name=ex.exercise_name or "",
                    sets=ex.sets,
                    reps=ex.reps or ex.reps_target or 0,
                    weight_lbs=ex.weight_lbs or ex.load_value,
                    percentage_1rm=int(ex.percentage_1rm) if ex.percentage_1rm else None,
                    notes=ex.notes or "",
                )
                for ex in sorted(day.exercises, key=lambda e: (e.exercise_order or 0))
            ]
            days.append(
                DayDetail(
                    day_number=day.day_number,
                    name=day.name,
                    suggested_day_of_week=(
                        str(day.suggested_day_of_week) if day.suggested_day_of_week else None
                    ),
                    exercises=exercises,
                )
            )
        weeks.append(
            WeekDetail(week_number=week.week_number, name=week.name or f"Week {week.week_number}", days=days)
        )

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
        weeks=weeks,
    )


# ---------------------------------------------------------------------------
# POST /programs/templates/{id}/preview
# ---------------------------------------------------------------------------


@router.post("/{template_id}/preview", summary="Dry-run program generation")
async def preview_template(
    template_id: str,
    body: SelfStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dry-run: call the engine or internal generator and return the full program
    structure without persisting anything.
    """
    if body.source == "engine":
        payload = dict(body.inputs)
        if body.movements:
            payload.setdefault("movements", body.movements)
        payload.setdefault("program_id", template_id)
        return await engine_client.generate_plan(payload)

    # Coach template preview: load template and return its current structure
    return await get_template(template_id=template_id, source="coach", db=db, current_user=current_user)


# ---------------------------------------------------------------------------
# POST /programs/templates/{id}/start
# ---------------------------------------------------------------------------


@router.post(
    "/{template_id}/start",
    response_model=SelfStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate program copy and assign to self",
)
async def start_template(
    template_id: str,
    body: SelfStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a full copy of the program (engine or coach template),
    creates a ClientProgramAssignment for the current user, and schedules days.
    """
    from datetime import date as date_type

    from app.services.assignment_service import self_start_program

    start_date = body.start_date or date_type.today()

    inputs = dict(body.inputs)
    if body.movements:
        inputs.setdefault("movements", body.movements)

    assignment = await self_start_program(
        source=body.source,
        template_id=template_id,
        inputs=inputs,
        start_date=start_date,
        current_user=current_user,
        db=db,
        assignment_name=body.assignment_name,
    )

    await db.commit()
    await db.refresh(assignment)

    return SelfStartResponse(
        assignment_id=str(assignment.id),
        program_id=str(assignment.program_id),
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        status=assignment.status,
    )
