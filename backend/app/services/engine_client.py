"""
Async HTTP client for the TrainGen Engine.
All methods are thin wrappers that normalize errors.
The engine is stateless and requires no auth headers.
"""
import httpx
from typing import Any
from fastapi import HTTPException, status
from app.core.config import settings


async def _engine_request(method: str, path: str, **kwargs) -> Any:
    url = f"{settings.ENGINE_URL}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(method, url, **kwargs)
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TrainGen Engine is unreachable",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="TrainGen Engine timed out",
            )

    if response.status_code == 200:
        return response.json()

    try:
        error_body = response.json()
    except Exception:
        error_body = {"detail": response.text}

    raise HTTPException(
        status_code=response.status_code,
        detail=error_body.get("detail", "Engine error"),
    )


async def list_program_definitions() -> list[dict]:
    return await _engine_request("GET", "/api/v1/program-definitions")


async def get_program_definition(program_id: str) -> dict:
    return await _engine_request("GET", f"/api/v1/program-definitions/{program_id}")


async def generate_plan(payload: dict) -> dict:
    return await _engine_request("POST", "/api/v1/generate", json=payload)


async def get_exercise_alternatives(payload: dict) -> dict:
    return await _engine_request("POST", "/api/v1/exercises/alternatives", json=payload)


async def apply_overrides(payload: dict) -> dict:
    return await _engine_request("POST", "/api/v1/plans/apply-overrides", json=payload)
