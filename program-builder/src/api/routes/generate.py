"""Plan generation endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_definition_by_id, get_exercise_library
from src.core.pipeline import Pipeline
from src.models.plan_request import PlanRequest  # noqa: TC001

router = APIRouter(tags=["generate"])


@router.post("/generate")
async def generate_plan(request: PlanRequest) -> dict[str, Any]:
    defn = get_definition_by_id(request.program_id)
    if defn is None:
        raise HTTPException(
            status_code=404,
            detail=f"Program '{request.program_id}' not found",
        )

    library = get_exercise_library()
    pipeline = Pipeline(library, defn)
    plan = pipeline.generate(request)
    return plan
