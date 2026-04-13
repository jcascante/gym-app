"""
Assignment service — program self-service flow, scheduling, and progress tracking.

Three main responsibilities:
  1. schedule_program_days()  — set scheduled_date on every ProgramDay at assignment time
  2. self_start_program()     — engine or coach-template → full copy + assignment
  3. advance_progress()       — called after every workout log to auto-advance position
"""
from __future__ import annotations

import copy
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client_program_assignment import ClientProgramAssignment
from app.models.program import Program, ProgramDay, ProgramDayExercise, ProgramWeek
from app.models.user import User

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DAY_NAME_TO_ISO = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    # numeric strings (1-7, Mon=1 convention)
    "1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6,
}


def _compute_scheduled_date(start_date: date, suggested_day_of_week: Any) -> date | None:
    """
    Return the first calendar date >= start_date that falls on the suggested weekday.

    suggested_day_of_week can be:
      - an int 1-7 (1=Monday) as stored in ProgramDay
      - a string name like "monday"
      - None → returns None
    """
    if suggested_day_of_week is None:
        return None

    try:
        raw = str(suggested_day_of_week).lower().strip()
        iso_weekday = _DAY_NAME_TO_ISO.get(raw)
        if iso_weekday is None:
            # Try parsing as zero-based int directly
            iso_weekday = int(suggested_day_of_week) % 7
    except (TypeError, ValueError):
        return None

    days_ahead = (iso_weekday - start_date.weekday()) % 7
    return start_date + timedelta(days=days_ahead)


async def _load_template_tree(template_id: UUID, subscription_id: UUID, db: AsyncSession) -> Program:
    """Load a coach-created template with its full week/day/exercise tree."""
    result = await db.execute(
        select(Program)
        .options(
            selectinload(Program.weeks)
            .selectinload(ProgramWeek.days)
            .selectinload(ProgramDay.exercises)
        )
        .where(
            Program.id == template_id,
            Program.subscription_id == subscription_id,
            Program.is_template == True,
            Program.archived_at.is_(None),
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


async def _copy_program_tree(
    template: Program,
    current_user: User,
    db: AsyncSession,
    override_name: str | None = None,
) -> Program:
    """Deep-copy a template program tree into new is_template=False rows."""
    client_program = Program(
        subscription_id=current_user.subscription_id,
        created_by_user_id=current_user.id,
        name=override_name or template.name,
        description=template.description,
        builder_type=template.builder_type,
        algorithm_version=template.algorithm_version,
        input_data=copy.deepcopy(template.input_data),
        calculated_data=copy.deepcopy(template.calculated_data),
        is_template=False,
        is_public=False,
        status="published",
        parent_template_id=template.id,
        duration_weeks=template.duration_weeks,
        days_per_week=template.days_per_week,
        program_type=template.program_type,
        difficulty_level=template.difficulty_level,
        tags=copy.deepcopy(template.tags),
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(client_program)
    await db.flush()

    for week in sorted(template.weeks, key=lambda w: w.week_number):
        new_week = ProgramWeek(
            program_id=client_program.id,
            subscription_id=current_user.subscription_id,
            week_number=week.week_number,
            name=week.name,
            description=week.description,
            notes=week.notes,
            focus_area=week.focus_area,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        db.add(new_week)
        await db.flush()

        for day in sorted(week.days, key=lambda d: d.day_number):
            new_day = ProgramDay(
                program_week_id=new_week.id,
                subscription_id=current_user.subscription_id,
                day_number=day.day_number,
                name=day.name,
                description=day.description,
                day_type=day.day_type,
                suggested_day_of_week=day.suggested_day_of_week,
                estimated_duration_minutes=day.estimated_duration_minutes,
                warm_up_notes=day.warm_up_notes,
                cool_down_notes=day.cool_down_notes,
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            db.add(new_day)
            await db.flush()

            for ex in sorted(day.exercises, key=lambda e: (e.exercise_order or 0)):
                new_ex = ProgramDayExercise(
                    program_day_id=new_day.id,
                    subscription_id=current_user.subscription_id,
                    exercise_name=ex.exercise_name,
                    exercise_order=ex.exercise_order,
                    sets=ex.sets,
                    reps=ex.reps,
                    reps_min=ex.reps_min,
                    reps_max=ex.reps_max,
                    reps_target=ex.reps_target,
                    load_type=ex.load_type,
                    load_value=ex.load_value,
                    load_unit=ex.load_unit,
                    weight_lbs=ex.weight_lbs,
                    tempo=ex.tempo,
                    rest_seconds=ex.rest_seconds,
                    duration_seconds=ex.duration_seconds,
                    rpe_target=ex.rpe_target,
                    percentage_1rm=ex.percentage_1rm,
                    notes=ex.notes,
                    coaching_cues=ex.coaching_cues,
                    created_by=current_user.id,
                    updated_by=current_user.id,
                )
                db.add(new_ex)

    return client_program


async def _materialize_engine_plan(
    engine_response: dict,
    engine_program_id: str,
    current_user: User,
    db: AsyncSession,
    override_name: str | None = None,
) -> Program:
    """
    Materialize a TrainGen Engine generate_plan() response into Program tree rows.

    Expected engine response shape (mirrors StrengthProgramGenerator preview):
    {
      "name": "...",
      "description": "...",
      "duration_weeks": 8,
      "days_per_week": 4,
      "program_type": "strength",
      "difficulty_level": "intermediate",
      "weeks": [
        {
          "week_number": 1,
          "name": "...",
          "days": [
            {
              "day_number": 1,
              "name": "...",
              "suggested_day_of_week": 1,
              "exercises": [
                {
                  "exercise_name": "Squat",
                  "sets": 5,
                  "reps": 5,
                  "weight_lbs": 225.0,
                  "rpe_target": 8.0,
                  "coaching_cues": "...",
                  "notes": "..."
                }
              ]
            }
          ]
        }
      ]
    }
    """
    duration_weeks = engine_response.get("duration_weeks", len(engine_response.get("weeks", [])))
    days_per_week = engine_response.get("days_per_week", 0)
    if not days_per_week and engine_response.get("weeks"):
        days_per_week = max(len(w.get("days", [])) for w in engine_response["weeks"])

    program = Program(
        subscription_id=current_user.subscription_id,
        created_by_user_id=current_user.id,
        name=override_name or engine_response.get("name", "Engine Program"),
        description=engine_response.get("description"),
        program_type=engine_response.get("program_type"),
        difficulty_level=engine_response.get("difficulty_level"),
        builder_type="engine",
        is_template=False,
        is_public=False,
        status="published",
        duration_weeks=duration_weeks,
        days_per_week=days_per_week,
        engine_program_id=engine_program_id,
        engine_program_version=engine_response.get("version"),
        input_data=engine_response.get("input_data"),
        calculated_data=engine_response.get("calculated_data"),
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(program)
    await db.flush()

    for week_data in engine_response.get("weeks", []):
        week = ProgramWeek(
            program_id=program.id,
            subscription_id=current_user.subscription_id,
            week_number=week_data["week_number"],
            name=week_data.get("name"),
            description=week_data.get("description"),
            focus_area=week_data.get("focus_area"),
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        db.add(week)
        await db.flush()

        for day_data in week_data.get("days", []):
            day = ProgramDay(
                program_week_id=week.id,
                subscription_id=current_user.subscription_id,
                day_number=day_data["day_number"],
                name=day_data.get("name", f"Day {day_data['day_number']}"),
                description=day_data.get("description"),
                day_type=day_data.get("day_type"),
                suggested_day_of_week=day_data.get("suggested_day_of_week"),
                estimated_duration_minutes=day_data.get("estimated_duration_minutes"),
                warm_up_notes=day_data.get("warm_up_notes"),
                cool_down_notes=day_data.get("cool_down_notes"),
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            db.add(day)
            await db.flush()

            for order, ex_data in enumerate(day_data.get("exercises", []), start=1):
                ex = ProgramDayExercise(
                    program_day_id=day.id,
                    subscription_id=current_user.subscription_id,
                    exercise_name=ex_data.get("exercise_name", ""),
                    exercise_order=ex_data.get("exercise_order", order),
                    sets=ex_data.get("sets", 1),
                    reps=ex_data.get("reps"),
                    reps_target=ex_data.get("reps_target") or ex_data.get("reps"),
                    reps_min=ex_data.get("reps_min"),
                    reps_max=ex_data.get("reps_max"),
                    weight_lbs=ex_data.get("weight_lbs"),
                    load_value=ex_data.get("load_value") or ex_data.get("weight_lbs"),
                    load_type=ex_data.get("load_type", "fixed_weight"),
                    load_unit=ex_data.get("load_unit", "lbs"),
                    rpe_target=ex_data.get("rpe_target"),
                    percentage_1rm=ex_data.get("percentage_1rm"),
                    rest_seconds=ex_data.get("rest_seconds"),
                    notes=ex_data.get("notes", ""),
                    coaching_cues=ex_data.get("coaching_cues"),
                    created_by=current_user.id,
                    updated_by=current_user.id,
                )
                db.add(ex)

    return program


# ---------------------------------------------------------------------------
# Engine plan format converter
# ---------------------------------------------------------------------------

def _extract_exercise_from_block(block: dict) -> dict:
    """Convert an EngineBlock (from saved plan_data) to a flat exercise dict."""
    name = (block.get("exercise") or {}).get("name", "Exercise")
    prescription = block.get("prescription") or {}

    sets = 1
    reps = None
    weight_lbs = None
    rpe_target = None
    notes = ""

    if "top_set" in prescription:
        # StrengthPrescription: top_set + optional backoff sets
        top = prescription["top_set"]
        backoffs = prescription.get("backoff") or []
        sets = top.get("sets", 1) + sum(b.get("sets", 0) for b in backoffs)
        reps = top.get("reps")
        load_kg = top.get("load_kg")
        if load_kg:
            weight_lbs = round(load_kg * 2.205, 1)
        rpe_target = top.get("target_rpe")
    elif "reps_range" in prescription:
        # RepsRangePrescription
        sets = prescription.get("sets", 3)
        rr = prescription.get("reps_range") or [8, 12]
        reps = rr[0] if rr else 8
        target_rir = prescription.get("target_rir", 2)
        rpe_target = round(10 - target_rir, 1)
    elif "work" in prescription and "intervals" in (prescription.get("work") or {}):
        # ConditioningIntervalsPrescription
        work = prescription["work"]
        sets = work.get("intervals", 1)
        notes = f"{work.get('seconds_each', 0)}s work / {prescription.get('rest_seconds', 0)}s rest"
    elif "duration_minutes" in prescription:
        # ConditioningSteadyPrescription
        notes = f"{prescription.get('duration_minutes', 0)} min steady state"

    return {
        "exercise_name": name,
        "sets": sets,
        "reps": reps,
        "weight_lbs": weight_lbs,
        "rpe_target": rpe_target,
        "notes": notes,
    }


def _convert_engine_plan_for_materialization(plan_data: dict) -> dict:
    """
    Convert engine's GeneratedPlan blob (weeks[].sessions[].blocks[])
    to the format _materialize_engine_plan() expects (weeks[].days[].exercises[]).
    """
    raw_weeks = plan_data.get("weeks") or []
    weeks = []
    for week_data in raw_weeks:
        sessions = week_data.get("sessions") or []
        days = []
        for session in sessions:
            exercises = [_extract_exercise_from_block(b) for b in (session.get("blocks") or [])]
            days.append({
                "day_number": session.get("day", len(days) + 1),
                "name": f"Day {session.get('day', len(days) + 1)}",
                "exercises": exercises,
            })
        weeks.append({
            "week_number": week_data.get("week", len(weeks) + 1),
            "days": days,
        })

    duration_weeks = len(weeks)
    days_per_week = max((len(w["days"]) for w in weeks), default=0)

    return {
        "name": plan_data.get("program_id", "My Program"),
        "duration_weeks": duration_weeks,
        "days_per_week": days_per_week,
        "weeks": weeks,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def schedule_program_days(program_id: UUID, start_date: date, db: AsyncSession) -> None:
    """
    Compute and set scheduled_date on every ProgramDay in the program.

    Days within week N are scheduled starting at start_date + (N-1)*7 days,
    then snapped forward to the suggested_day_of_week if one is set.
    """
    result = await db.execute(
        select(ProgramWeek)
        .options(selectinload(ProgramWeek.days))
        .where(ProgramWeek.program_id == program_id)
        .order_by(ProgramWeek.week_number)
    )
    weeks = result.scalars().all()

    for week in weeks:
        week_start = start_date + timedelta(weeks=week.week_number - 1)
        for day in sorted(week.days, key=lambda d: d.day_number):
            if day.suggested_day_of_week is not None:
                day.scheduled_date = _compute_scheduled_date(week_start, day.suggested_day_of_week)
            else:
                # Fall back to sequential days from week start
                day.scheduled_date = week_start + timedelta(days=day.day_number - 1)

    await db.flush()


async def self_start_program(
    source: str,  # "engine" | "coach"
    template_id: str,
    inputs: dict,
    start_date: date,
    current_user: User,
    db: AsyncSession,
    assignment_name: str | None = None,
) -> ClientProgramAssignment:
    """
    Generate a full program copy for the current user and create an assignment.

    source="engine":
      - Calls engine_client.generate_plan(inputs)
      - Materializes engine response → Program tree (is_template=False)
      - Sets engine_program_id / engine_program_version on Program

    source="coach":
      - Loads coach template by template_id from DB
      - Deep-copies Program tree (is_template=False)

    In both cases:
      - Creates ClientProgramAssignment
      - Calls schedule_program_days()
    """
    from app.services import engine_client

    subscription_id = current_user.subscription_id
    template_uuid = UUID(template_id)

    if source == "engine":
        engine_response = await engine_client.generate_plan(inputs)
        program = await _materialize_engine_plan(
            engine_response=engine_response,
            engine_program_id=template_id,
            current_user=current_user,
            db=db,
            override_name=assignment_name,
        )
    elif source == "coach":
        template = await _load_template_tree(template_uuid, subscription_id, db)
        program = await _copy_program_tree(
            template=template,
            current_user=current_user,
            db=db,
            override_name=assignment_name,
        )
        # Increment usage counter on the template
        template.times_assigned = (template.times_assigned or 0) + 1
    else:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source '{source}'. Must be 'engine' or 'coach'.",
        )

    end_date = start_date + timedelta(weeks=program.duration_weeks)

    assignment = ClientProgramAssignment(
        subscription_id=subscription_id,
        location_id=current_user.location_id,
        coach_id=None,  # Self-started — no coach
        client_id=current_user.id,
        program_id=program.id,
        assignment_name=assignment_name,
        start_date=start_date,
        end_date=end_date,
        status="assigned",
        current_week=1,
        current_day=1,
        workouts_completed=0,
        workouts_skipped=0,
        is_active=True,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(assignment)
    await db.flush()

    await schedule_program_days(program.id, start_date, db)

    return assignment


async def start_saved_plan(
    plan_id: UUID,
    start_date: date,
    current_user: User,
    db: AsyncSession,
    assignment_name: str | None = None,
) -> ClientProgramAssignment:
    """
    Materialize a saved GeneratedPlan blob into Program rows and create an assignment.

    Converts engine's sessions/blocks format → materialization format → DB rows.
    Links GeneratedPlan.assignment_id back to the new assignment.
    """
    from app.models.generated_plan import GeneratedPlan

    result = await db.execute(
        select(GeneratedPlan).where(
            GeneratedPlan.id == plan_id,
            GeneratedPlan.client_id == current_user.id,
            GeneratedPlan.is_active == True,  # noqa: E712
        )
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        from fastapi import HTTPException
        from fastapi import status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Plan not found")

    if plan.assignment_id is not None:
        from fastapi import HTTPException
        from fastapi import status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="This plan has already been started",
        )

    materialization_data = _convert_engine_plan_for_materialization(plan.plan_data)

    program = await _materialize_engine_plan(
        engine_response=materialization_data,
        engine_program_id=plan.engine_program_id,
        current_user=current_user,
        db=db,
        override_name=assignment_name or plan.name,
    )
    program.engine_program_version = plan.engine_program_version

    end_date = start_date + timedelta(weeks=program.duration_weeks)

    assignment = ClientProgramAssignment(
        subscription_id=current_user.subscription_id,
        location_id=current_user.location_id,
        coach_id=None,
        client_id=current_user.id,
        program_id=program.id,
        assignment_name=assignment_name or plan.name,
        start_date=start_date,
        end_date=end_date,
        status="assigned",
        current_week=1,
        current_day=1,
        workouts_completed=0,
        workouts_skipped=0,
        is_active=True,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(assignment)
    await db.flush()

    await schedule_program_days(program.id, start_date, db)

    plan.assignment_id = assignment.id
    plan.updated_by = current_user.id
    await db.flush()

    return assignment


async def advance_progress(
    assignment_id: UUID,
    day_status: str,  # "completed" | "skipped" | "partial"
    db: AsyncSession,
) -> ClientProgramAssignment:
    """
    Called after every workout log.

    1. Increments workouts_completed or workouts_skipped
    2. Determines next position (day++, or week++ if last day of week)
    3. If past last week → marks assignment completed
    4. Persists and returns updated assignment (with program loaded for progress calc)
    """
    from sqlalchemy.orm import joinedload

    result = await db.execute(
        select(ClientProgramAssignment)
        .options(joinedload(ClientProgramAssignment.program))  # type: ignore[attr-defined]
        .where(ClientProgramAssignment.id == assignment_id)
    )
    assignment = result.unique().scalar_one_or_none()
    if assignment is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # 1. Update counters
    if day_status in ("completed", "partial"):
        assignment.workouts_completed = (assignment.workouts_completed or 0) + 1
    else:
        assignment.workouts_skipped = (assignment.workouts_skipped or 0) + 1

    # 2. Advance position
    program = assignment.program
    if assignment.current_day < program.days_per_week:
        assignment.current_day += 1
    else:
        # End of week — move to next week
        assignment.current_week += 1
        assignment.current_day = 1

    # 3. Check completion
    if assignment.current_week > program.duration_weeks:
        from datetime import datetime
        assignment.status = "completed"
        assignment.actual_completion_date = datetime.utcnow().date()

    assignment.updated_by = assignment.client_id  # client is the actor

    await db.flush()
    return assignment
