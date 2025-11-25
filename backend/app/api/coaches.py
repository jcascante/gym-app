"""
Coach-specific API endpoints.

These endpoints provide coach dashboard statistics and coach profile information.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.deps import get_coach_or_admin_user
from app.models.user import User
from app.models.coach_client_assignment import CoachClientAssignment
from app.models.client_program_assignment import ClientProgramAssignment
from app.models.program import Program
from pydantic import BaseModel

router = APIRouter(prefix="/coaches/me", tags=["Coach"])


class CoachStatsResponse(BaseModel):
    """Coach dashboard statistics"""
    total_clients: int
    active_clients: int
    total_programs: int
    active_programs: int

    class Config:
        from_attributes = True


@router.get("/stats", response_model=CoachStatsResponse)
async def get_coach_stats(
    current_user: User = Depends(get_coach_or_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics for the authenticated coach.

    Returns:
    - total_clients: Total number of clients assigned to this coach
    - active_clients: Number of currently active clients
    - total_programs: Total number of program templates created by this coach
    - active_programs: Number of active program assignments across all clients
    """

    # Count total clients assigned to this coach
    total_clients_result = await db.execute(
        select(func.count(CoachClientAssignment.id)).where(
            and_(
                CoachClientAssignment.coach_id == current_user.id,
                CoachClientAssignment.subscription_id == current_user.subscription_id,
                CoachClientAssignment.is_active == True
            )
        )
    )
    total_clients = total_clients_result.scalar_one()

    # Count active clients (clients with active status)
    # We'll use the same count for now since we don't have client status tracking yet
    active_clients = total_clients

    # Count total program templates created by this coach
    total_programs_result = await db.execute(
        select(func.count(Program.id)).where(
            and_(
                Program.created_by_user_id == current_user.id,
                Program.subscription_id == current_user.subscription_id,
                Program.is_template == True
            )
        )
    )
    total_programs = total_programs_result.scalar_one()

    # Count active program assignments across all clients
    # Active means: status is 'assigned' or 'in_progress' and is_active is True
    active_programs_result = await db.execute(
        select(func.count(ClientProgramAssignment.id)).where(
            and_(
                ClientProgramAssignment.coach_id == current_user.id,
                ClientProgramAssignment.subscription_id == current_user.subscription_id,
                ClientProgramAssignment.is_active == True,
                ClientProgramAssignment.status.in_(['assigned', 'in_progress'])
            )
        )
    )
    active_programs = active_programs_result.scalar_one()

    return CoachStatsResponse(
        total_clients=total_clients,
        active_clients=active_clients,
        total_programs=total_programs,
        active_programs=active_programs
    )
