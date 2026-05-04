"""Native Lambda handler — production execution path.

Dispatches on event["operation"]:
  generate              → pipeline.generate(PlanRequest)
  list_definitions      → list all loaded ProgramDefinitions
  get_definition        → get one ProgramDefinition by program_id
  get_library           → full ExerciseLibrary
  get_exercise_alternatives → alternatives for one exercise
  apply_overrides       → swap exercises in a generated plan
  validate_definition   → validate a definition dict
"""

from __future__ import annotations

import copy
import json
from typing import Any

from pydantic import ValidationError

from src.api.dependencies import (
    get_definition_by_id,
    get_exercise_library,
    get_program_definitions,
)
from src.core.pipeline import Pipeline
from src.models.exercise_alternatives import (
    ExerciseAlternative,
    ExerciseAlternativesRequest,
)
from src.models.generated_plan import GeneratedPlan
from src.models.plan_overrides import (
    AppliedOverride,
    ApplyOverridesRequest,
    ApplyOverridesResponse,
    RejectedOverride,
)
from src.models.plan_request import PlanRequest
from src.models.program_definition import ProgramDefinition


def _ok(body: Any) -> dict[str, Any]:
    return {"statusCode": 200, "body": body}


def _err(status: int, message: str) -> dict[str, Any]:
    return {"statusCode": status, "body": {"error": message}}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    operation = event.get("operation")
    payload: dict[str, Any] = event.get("payload", {})

    if operation == "generate":
        try:
            request = PlanRequest.model_validate(payload)
        except ValidationError as exc:
            return _err(422, str(exc))

        defn = get_definition_by_id(request.program_id)
        if defn is None:
            return _err(404, f"Program '{request.program_id}' not found")

        library = get_exercise_library()
        pipeline = Pipeline(library, defn)
        return _ok(pipeline.generate(request))

    if operation == "list_definitions":
        defs = get_program_definitions()
        return _ok([
            {
                "program_id": d.program_id,
                "version": d.version,
                "name": d.name,
                "description": d.description,
                "category": d.category,
                "tags": d.tags,
                "days_per_week": {
                    "min": d.template.days_per_week.min,
                    "max": d.template.days_per_week.max,
                },
                "weeks": {"min": d.template.weeks.min, "max": d.template.weeks.max},
            }
            for d in defs.values()
        ])

    if operation == "get_definition":
        program_id = payload.get("program_id")
        if not program_id:
            return _err(400, "payload.program_id is required")
        defn = get_definition_by_id(program_id)
        if defn is None:
            return _err(404, f"Program '{program_id}' not found")
        return _ok(defn.model_dump(mode="json"))

    if operation == "get_library":
        library = get_exercise_library()
        return _ok(library.model_dump(mode="json"))

    if operation == "get_exercise_alternatives":
        try:
            body = ExerciseAlternativesRequest.model_validate(payload)
        except ValidationError as exc:
            return _err(422, str(exc))

        library = get_exercise_library()
        exercise_index = {ex.id: ex for ex in library.exercises}
        original = exercise_index.get(body.exercise_id)
        if original is None:
            return _err(404, f"Exercise '{body.exercise_id}' not found")

        exclude_set = set(body.exclude_ids)
        original_patterns = set(original.patterns)
        swap_group_matches: list[ExerciseAlternative] = []
        pattern_matches: list[ExerciseAlternative] = []

        for ex in library.exercises:
            if ex.id == body.exercise_id or ex.id in exclude_set:
                continue
            if ex.equipment and not set(ex.equipment).issubset(set(body.athlete_equipment)):
                continue
            if body.restrictions and set(ex.contraindications) & set(body.restrictions):
                continue
            if original.swap_group and ex.swap_group == original.swap_group:
                swap_group_matches.append(ExerciseAlternative(
                    id=ex.id, name=ex.name, patterns=ex.patterns, tags=ex.tags,
                    swap_group=ex.swap_group, fatigue_cost=ex.fatigue_cost,
                    match_reason="swap_group",
                ))
            elif set(ex.patterns) & original_patterns:
                pattern_matches.append(ExerciseAlternative(
                    id=ex.id, name=ex.name, patterns=ex.patterns, tags=ex.tags,
                    swap_group=ex.swap_group, fatigue_cost=ex.fatigue_cost,
                    match_reason="pattern_match",
                ))

        alternatives = (swap_group_matches + pattern_matches)[: body.limit]
        return _ok({
            "original_exercise_id": body.exercise_id,
            "alternatives": [a.model_dump(mode="json") for a in alternatives],
        })

    if operation == "apply_overrides":
        try:
            body = ApplyOverridesRequest.model_validate(payload)
        except ValidationError as exc:
            return _err(422, str(exc))

        try:
            plan = GeneratedPlan.model_validate(body.plan)
        except ValidationError as exc:
            return _err(422, str(exc))

        library = get_exercise_library()
        exercise_index = {ex.id: ex for ex in library.exercises}

        block_lookup: dict[str, tuple[str, str]] = {}
        for week in plan.weeks:
            for session in week.sessions:
                for block in session.blocks:
                    block_lookup[block.block_id] = (block.exercise.id, block.exercise.name)

        applied: list[AppliedOverride] = []
        rejected: list[RejectedOverride] = []
        plan_dict = copy.deepcopy(body.plan)

        for override in body.overrides:
            if override.block_id not in block_lookup:
                rejected.append(RejectedOverride(
                    block_id=override.block_id, new_exercise_id=override.new_exercise_id,
                    reason="block_not_found",
                ))
                continue
            if override.new_exercise_id not in exercise_index:
                rejected.append(RejectedOverride(
                    block_id=override.block_id, new_exercise_id=override.new_exercise_id,
                    reason="exercise_not_found",
                ))
                continue

            original_id, original_name = block_lookup[override.block_id]
            original_ex = exercise_index.get(original_id)
            new_ex = exercise_index[override.new_exercise_id]

            if original_ex is not None:
                same_swap = original_ex.swap_group and new_ex.swap_group == original_ex.swap_group
                shares_pattern = bool(set(new_ex.patterns) & set(original_ex.patterns))
                if not same_swap and not shares_pattern:
                    rejected.append(RejectedOverride(
                        block_id=override.block_id, new_exercise_id=override.new_exercise_id,
                        reason="incompatible_exercise",
                    ))
                    continue

            for week_d in plan_dict["weeks"]:
                for session_d in week_d["sessions"]:
                    for block_d in session_d["blocks"]:
                        if block_d["block_id"] == override.block_id:
                            block_d["exercise"]["id"] = new_ex.id
                            block_d["exercise"]["name"] = new_ex.name

            applied.append(AppliedOverride(
                block_id=override.block_id,
                original_exercise_id=original_id, original_exercise_name=original_name,
                new_exercise_id=new_ex.id, new_exercise_name=new_ex.name,
            ))
            block_lookup[override.block_id] = (new_ex.id, new_ex.name)

        response = ApplyOverridesResponse(plan=plan_dict, applied=applied, rejected=rejected)
        return _ok(response.model_dump(mode="json"))

    if operation == "validate_definition":
        try:
            ProgramDefinition.model_validate(payload)
            return _ok({"valid": True, "errors": []})
        except ValidationError as exc:
            errors = [
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in exc.errors()
            ]
            return _ok({"valid": False, "errors": errors})

    return _err(400, f"Unknown operation: {operation!r}")
