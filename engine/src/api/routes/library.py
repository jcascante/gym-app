"""Exercise library endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.dependencies import get_exercise_library

router = APIRouter(prefix="/exercise-library", tags=["library"])


@router.get("")
async def get_library() -> dict[str, object]:
    library = get_exercise_library()
    return library.model_dump(mode="json")
