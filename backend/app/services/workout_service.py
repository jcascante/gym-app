"""
Workout service for managing workout logs and statistics.

Provides business logic for logging workouts, retrieving workout history,
and calculating fitness statistics.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from app.models import WorkoutLog, WorkoutStatus, ClientProgramAssignment
from uuid import UUID


class WorkoutService:
    """Service for managing workout logs and statistics."""

    @staticmethod
    async def create_workout_log(
        db: AsyncSession,
        subscription_id: UUID,
        client_id: UUID,
        assignment_id: UUID,
        program_id: UUID,
        coach_id: Optional[UUID] = None,
        status: WorkoutStatus = WorkoutStatus.COMPLETED,
        duration_minutes: Optional[str] = None,
        notes: Optional[str] = None,
        workout_date: Optional[datetime] = None,
        created_by: Optional[UUID] = None,
    ) -> WorkoutLog:
        """
        Create a new workout log entry.

        Args:
            db: Database session
            subscription_id: Subscription ID
            client_id: Client who performed the workout
            assignment_id: Program assignment this workout belongs to
            program_id: Program ID
            coach_id: Coach who assigned the program (optional)
            status: Workout status (completed, skipped, scheduled)
            duration_minutes: Duration of workout in minutes
            notes: Notes about the workout
            workout_date: Date/time of workout (defaults to now)
            created_by: User ID creating the log

        Returns:
            Created WorkoutLog object
        """
        if workout_date is None:
            workout_date = datetime.utcnow()

        workout_log = WorkoutLog(
            subscription_id=subscription_id,
            client_id=client_id,
            client_program_assignment_id=assignment_id,
            program_id=program_id,
            coach_id=coach_id,
            status=status,
            duration_minutes=duration_minutes,
            notes=notes,
            workout_date=workout_date,
            created_by=created_by,
            updated_by=created_by,
        )

        db.add(workout_log)
        await db.flush()
        return workout_log

    @staticmethod
    async def get_workout_log(
        db: AsyncSession,
        workout_id: UUID,
    ) -> Optional[WorkoutLog]:
        """
        Get a specific workout log by ID.

        Args:
            db: Database session
            workout_id: Workout log ID

        Returns:
            WorkoutLog object or None if not found
        """
        stmt = select(WorkoutLog).where(WorkoutLog.id == workout_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_client_workout_history(
        db: AsyncSession,
        client_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[WorkoutStatus] = None,
    ) -> tuple[List[WorkoutLog], int]:
        """
        Get workout history for a client.

        Args:
            db: Database session
            client_id: Client ID
            limit: Maximum number of results
            offset: Pagination offset
            status_filter: Optional filter by status

        Returns:
            Tuple of (workout logs, total count)
        """
        where_clause = WorkoutLog.client_id == client_id
        if status_filter:
            where_clause = and_(where_clause, WorkoutLog.status == status_filter)

        # Get total count
        count_stmt = select(func.count(WorkoutLog.id)).where(where_clause)
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0

        # Get paginated results
        stmt = (
            select(WorkoutLog)
            .where(where_clause)
            .order_by(desc(WorkoutLog.workout_date))
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        workouts = result.scalars().all()

        return workouts, total_count

    @staticmethod
    async def get_client_recent_workouts(
        db: AsyncSession,
        client_id: UUID,
        days: int = 7,
        limit: int = 10,
    ) -> List[WorkoutLog]:
        """
        Get recent workouts for a client within specified days.

        Args:
            db: Database session
            client_id: Client ID
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of WorkoutLog objects
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = (
            select(WorkoutLog)
            .where(
                and_(
                    WorkoutLog.client_id == client_id,
                    WorkoutLog.workout_date >= cutoff_date,
                )
            )
            .order_by(desc(WorkoutLog.workout_date))
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_client_workout_stats(
        db: AsyncSession,
        client_id: UUID,
    ) -> dict:
        """
        Calculate workout statistics for a client.

        Args:
            db: Database session
            client_id: Client ID

        Returns:
            Dictionary with stats: total_workouts, completed_workouts, skipped_workouts, last_workout_date
        """
        # Count total workouts
        total_stmt = select(func.count(WorkoutLog.id)).where(WorkoutLog.client_id == client_id)
        total_result = await db.execute(total_stmt)
        total_workouts = total_result.scalar() or 0

        # Count completed workouts
        completed_stmt = select(func.count(WorkoutLog.id)).where(
            and_(
                WorkoutLog.client_id == client_id,
                WorkoutLog.status == WorkoutStatus.COMPLETED,
            )
        )
        completed_result = await db.execute(completed_stmt)
        completed_workouts = completed_result.scalar() or 0

        # Count skipped workouts
        skipped_stmt = select(func.count(WorkoutLog.id)).where(
            and_(
                WorkoutLog.client_id == client_id,
                WorkoutLog.status == WorkoutStatus.SKIPPED,
            )
        )
        skipped_result = await db.execute(skipped_stmt)
        skipped_workouts = skipped_result.scalar() or 0

        # Get last workout date
        last_workout_stmt = (
            select(WorkoutLog.workout_date)
            .where(
                and_(
                    WorkoutLog.client_id == client_id,
                    WorkoutLog.status == WorkoutStatus.COMPLETED,
                )
            )
            .order_by(desc(WorkoutLog.workout_date))
            .limit(1)
        )
        last_workout_result = await db.execute(last_workout_stmt)
        last_workout = last_workout_result.scalar_one_or_none()

        return {
            "total_workouts": total_workouts,
            "completed_workouts": completed_workouts,
            "skipped_workouts": skipped_workouts,
            "last_workout_date": last_workout.isoformat() if last_workout else None,
        }

    @staticmethod
    async def update_workout_log(
        db: AsyncSession,
        workout_id: UUID,
        status: Optional[WorkoutStatus] = None,
        duration_minutes: Optional[str] = None,
        notes: Optional[str] = None,
        updated_by: Optional[UUID] = None,
    ) -> Optional[WorkoutLog]:
        """
        Update a workout log.

        Args:
            db: Database session
            workout_id: Workout log ID
            status: New status
            duration_minutes: New duration
            notes: New notes
            updated_by: User ID updating the log

        Returns:
            Updated WorkoutLog or None if not found
        """
        workout = await WorkoutService.get_workout_log(db, workout_id)
        if not workout:
            return None

        if status is not None:
            workout.status = status
        if duration_minutes is not None:
            workout.duration_minutes = duration_minutes
        if notes is not None:
            workout.notes = notes
        if updated_by is not None:
            workout.updated_by = updated_by

        await db.flush()
        return workout

    @staticmethod
    async def delete_workout_log(
        db: AsyncSession,
        workout_id: UUID,
    ) -> bool:
        """
        Delete a workout log.

        Args:
            db: Database session
            workout_id: Workout log ID

        Returns:
            True if deleted, False if not found
        """
        workout = await WorkoutService.get_workout_log(db, workout_id)
        if not workout:
            return False

        await db.delete(workout)
        await db.flush()
        return True

    @staticmethod
    async def get_assignment_workouts(
        db: AsyncSession,
        assignment_id: UUID,
        limit: int = 50,
    ) -> List[WorkoutLog]:
        """
        Get all workouts for a program assignment.

        Args:
            db: Database session
            assignment_id: Program assignment ID
            limit: Maximum number of results

        Returns:
            List of WorkoutLog objects
        """
        stmt = (
            select(WorkoutLog)
            .where(WorkoutLog.client_program_assignment_id == assignment_id)
            .order_by(desc(WorkoutLog.workout_date))
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()
