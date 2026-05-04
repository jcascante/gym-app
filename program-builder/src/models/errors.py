from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class ErrorType(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    REPAIR_FAILED = "REPAIR_FAILED"
    EXPRESSION_ERROR = "EXPRESSION_ERROR"
    SELECTOR_ERROR = "SELECTOR_ERROR"
    NOT_FOUND = "NOT_FOUND"


class EngineError(BaseModel):
    type: ErrorType
    message: str
    details: dict[str, Any] = {}
