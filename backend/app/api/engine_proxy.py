"""
Engine proxy endpoints — forwards CLIENT requests to TrainGen Engine.
Adds auth gate; no persistence here.
"""
from typing import Any
from fastapi import APIRouter, Depends
from app.core.deps import get_client_user
from app.models.user import User
from app.services import engine_client

router = APIRouter(prefix="/engine", tags=["TrainGen Engine"])


@router.get("/program-definitions")
async def list_program_definitions(
    _: User = Depends(get_client_user),
) -> list[dict]:
    return await engine_client.list_program_definitions()


@router.get("/program-definitions/{program_id}")
async def get_program_definition(
    program_id: str,
    _: User = Depends(get_client_user),
) -> dict:
    return await engine_client.get_program_definition(program_id)


@router.post("/generate")
async def generate_plan(
    payload: dict[str, Any],
    _: User = Depends(get_client_user),
) -> dict:
    return await engine_client.generate_plan(payload)


@router.post("/exercises/alternatives")
async def get_exercise_alternatives(
    payload: dict[str, Any],
    _: User = Depends(get_client_user),
) -> dict:
    return await engine_client.get_exercise_alternatives(payload)


@router.post("/plans/apply-overrides")
async def apply_overrides(
    payload: dict[str, Any],
    _: User = Depends(get_client_user),
) -> dict:
    return await engine_client.apply_overrides(payload)
