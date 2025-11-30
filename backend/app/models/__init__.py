"""
Models package.

Exports all database models for easy importing.
"""
from app.models.base import BaseModel, GUID, get_utc_now
from app.models.subscription import Subscription, SubscriptionType, SubscriptionStatus, JSONBType
from app.models.location import Location
from app.models.user import User, UserRole
from app.models.coach_client_assignment import CoachClientAssignment
from app.models.client_program_assignment import ClientProgramAssignment
from app.models.audit_log import AuditLog, AuditAction
from app.models.program import Program, ProgramWeek, ProgramDay, ProgramDayExercise
from app.models.exercise import Exercise
from app.models.program_assignment import ProgramAssignment

__all__ = [
    "BaseModel",
    "GUID",
    "get_utc_now",
    "JSONBType",
    "Subscription",
    "SubscriptionType",
    "SubscriptionStatus",
    "Location",
    "User",
    "UserRole",
    "CoachClientAssignment",
    "ClientProgramAssignment",
    "AuditLog",
    "AuditAction",
    "Program",
    "ProgramWeek",
    "ProgramDay",
    "ProgramDayExercise",
    "Exercise",
    "ProgramAssignment",
]
