"""Program definition endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_definition_by_id, get_program_definitions

router = APIRouter(prefix="/program-definitions", tags=["definitions"])


@router.get("")
async def list_definitions() -> list[dict[str, object]]:
    defs = get_program_definitions()
    return [
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
    ]


@router.get("/{program_id}")
async def get_definition(program_id: str) -> dict[str, object]:
    defn = get_definition_by_id(program_id)
    if defn is None:
        raise HTTPException(status_code=404, detail="Program not found")
    return defn.model_dump(mode="json")
