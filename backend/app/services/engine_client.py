"""
Client for the Program Builder.

Dispatches to one of two transports selected by ENGINE_INVOCATION_MODE:
  http   — async HTTP (docker-compose / local dev)
  lambda — AWS Lambda direct invoke (production)
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

# ── HTTP transport (local dev) ──────────────────────────────────────────────


async def _http(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{settings.ENGINE_URL}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(method, url, **kwargs)
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Program Builder is unreachable",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Program Builder timed out",
            )

    if response.status_code == 200:
        return response.json()

    try:
        error_body = response.json()
    except Exception:
        error_body = {"detail": response.text}

    raise HTTPException(
        status_code=response.status_code,
        detail=error_body.get("detail", "Program Builder error"),
    )


# ── Lambda transport (production) ───────────────────────────────────────────


def _invoke_lambda(operation: str, payload: dict[str, Any]) -> Any:
    import boto3  # imported lazily — not installed in local dev
    import botocore.exceptions

    client = boto3.client("lambda", region_name=settings.ENGINE_LAMBDA_REGION)
    event = {"operation": operation, "payload": payload}

    try:
        response = client.invoke(
            FunctionName=settings.ENGINE_LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(event),
        )
    except botocore.exceptions.ClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Program Builder invocation failed: {exc.response['Error']['Message']}",
        ) from exc

    if response.get("FunctionError"):
        raw = json.loads(response["Payload"].read())
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Program Builder error: {raw.get('errorMessage', 'unknown error')}",
        )

    result: dict[str, Any] = json.loads(response["Payload"].read())
    status_code_val: int = result.get("statusCode", 200)

    if status_code_val != 200:
        body = result.get("body", {})
        error_msg = body.get("error", "Program Builder error") if isinstance(body, dict) else str(body)
        raise HTTPException(status_code=status_code_val, detail=error_msg)

    return result["body"]


def _lambda(operation: str, payload: dict[str, Any] | None = None) -> Any:
    return _invoke_lambda(operation, payload or {})


# ── Public API ───────────────────────────────────────────────────────────────


async def list_program_definitions() -> list[dict]:
    if settings.ENGINE_INVOCATION_MODE == "lambda":
        return _lambda("list_definitions")
    return await _http("GET", "/api/v1/program-definitions")


async def get_program_definition(program_id: str) -> dict:
    if settings.ENGINE_INVOCATION_MODE == "lambda":
        return _lambda("get_definition", {"program_id": program_id})
    return await _http("GET", f"/api/v1/program-definitions/{program_id}")


async def generate_plan(payload: dict) -> dict:
    if settings.ENGINE_INVOCATION_MODE == "lambda":
        return _lambda("generate", payload)
    return await _http("POST", "/api/v1/generate", json=payload)


async def get_exercise_alternatives(payload: dict) -> dict:
    if settings.ENGINE_INVOCATION_MODE == "lambda":
        return _lambda("get_exercise_alternatives", payload)
    return await _http("POST", "/api/v1/exercises/alternatives", json=payload)


async def apply_overrides(payload: dict) -> dict:
    if settings.ENGINE_INVOCATION_MODE == "lambda":
        return _lambda("apply_overrides", payload)
    return await _http("POST", "/api/v1/plans/apply-overrides", json=payload)
