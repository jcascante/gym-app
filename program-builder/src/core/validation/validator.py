"""Validation engine: checks hard/soft constraints on generated plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    HARD = "hard"
    SOFT = "soft"


@dataclass(frozen=True)
class ConstraintViolation:
    severity: Severity
    constraint: str
    key: str
    message: str
    actual: float | None = None
    limit: float | None = None


@dataclass
class ValidationResult:
    hard_violations: list[ConstraintViolation] = field(default_factory=list)
    soft_violations: list[ConstraintViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.hard_violations) == 0


class Validator:
    def check_max_weekly_volume(
        self,
        weekly_volume: dict[str, float],
        limits: dict[str, float],
    ) -> list[ConstraintViolation]:
        violations: list[ConstraintViolation] = []
        for key, limit in limits.items():
            actual = weekly_volume.get(key, 0)
            if actual > limit:
                violations.append(
                    ConstraintViolation(
                        severity=Severity.HARD,
                        constraint="max_weekly_volume",
                        key=key,
                        message=f"{key} volume {actual} exceeds max {limit}",
                        actual=actual,
                        limit=limit,
                    )
                )
        return violations

    def check_min_weekly_volume(
        self,
        weekly_volume: dict[str, float],
        limits: dict[str, float],
    ) -> list[ConstraintViolation]:
        violations: list[ConstraintViolation] = []
        for key, limit in limits.items():
            actual = weekly_volume.get(key, 0)
            if actual < limit:
                violations.append(
                    ConstraintViolation(
                        severity=Severity.HARD,
                        constraint="min_weekly_volume",
                        key=key,
                        message=f"{key} volume {actual} below min {limit}",
                        actual=actual,
                        limit=limit,
                    )
                )
        return violations

    def check_session_fatigue(
        self, fatigue: float, limit: float
    ) -> list[ConstraintViolation]:
        if fatigue > limit:
            return [
                ConstraintViolation(
                    severity=Severity.HARD,
                    constraint="max_session_fatigue",
                    key="session",
                    message=f"Session fatigue {fatigue} exceeds max {limit}",
                    actual=fatigue,
                    limit=limit,
                )
            ]
        return []

    def check_weekly_fatigue(
        self, fatigue: float, limit: float
    ) -> list[ConstraintViolation]:
        if fatigue > limit:
            return [
                ConstraintViolation(
                    severity=Severity.HARD,
                    constraint="max_weekly_fatigue",
                    key="week",
                    message=f"Weekly fatigue {fatigue} exceeds max {limit}",
                    actual=fatigue,
                    limit=limit,
                )
            ]
        return []

    def check_max_intense_minutes(
        self, intense_minutes: float, limit: float
    ) -> list[ConstraintViolation]:
        if intense_minutes > limit:
            return [
                ConstraintViolation(
                    severity=Severity.HARD,
                    constraint="max_intense_minutes",
                    key="intense_minutes",
                    message=(
                        f"Intense minutes {intense_minutes} exceeds "
                        f"max {limit}"
                    ),
                    actual=intense_minutes,
                    limit=limit,
                )
            ]
        return []

    def check_min_z2_minutes(
        self, z2_minutes: float, limit: float
    ) -> list[ConstraintViolation]:
        if z2_minutes < limit:
            return [
                ConstraintViolation(
                    severity=Severity.HARD,
                    constraint="min_z2_minutes",
                    key="z2_minutes",
                    message=f"Z2 minutes {z2_minutes} below min {limit}",
                    actual=z2_minutes,
                    limit=limit,
                )
            ]
        return []

    def check_soft_warnings(
        self, conditions: list[tuple[bool, str]]
    ) -> list[ConstraintViolation]:
        violations: list[ConstraintViolation] = []
        for triggered, message in conditions:
            if triggered:
                violations.append(
                    ConstraintViolation(
                        severity=Severity.SOFT,
                        constraint="soft_warning",
                        key="warning",
                        message=message,
                    )
                )
        return violations

    def validate_week(
        self,
        weekly_volume: dict[str, float],
        volume_limits_max: dict[str, float],
        volume_limits_min: dict[str, float],
        session_fatigues: list[float],
        session_fatigue_limit: float,
        weekly_fatigue_limit: float,
    ) -> ValidationResult:
        result = ValidationResult()

        result.hard_violations.extend(
            self.check_max_weekly_volume(weekly_volume, volume_limits_max)
        )
        result.hard_violations.extend(
            self.check_min_weekly_volume(weekly_volume, volume_limits_min)
        )

        for fatigue in session_fatigues:
            result.hard_violations.extend(
                self.check_session_fatigue(fatigue, session_fatigue_limit)
            )

        total_fatigue = sum(session_fatigues)
        result.hard_violations.extend(
            self.check_weekly_fatigue(total_fatigue, weekly_fatigue_limit)
        )

        return result
