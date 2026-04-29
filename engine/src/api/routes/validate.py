"""Validate definition endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import ValidationError

from src.models.program_definition import ProgramDefinition

router = APIRouter(prefix="/validate-definition", tags=["definitions"])


@router.post("")
async def validate_definition(
    body: dict[str, Any],
) -> dict[str, Any]:
    try:
        ProgramDefinition.model_validate(body)
        return {"valid": True, "errors": []}
    except ValidationError as exc:
        errors = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        return {"valid": False, "errors": errors}
