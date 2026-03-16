"""Business logic for saving and retrieving GeneratedPlan records."""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.generated_plan import GeneratedPlan


class GeneratedPlanService:

    @staticmethod
    async def create(
        db: AsyncSession,
        client_id: UUID,
        subscription_id: UUID,
        name: str,
        engine_program_id: str,
        engine_program_version: str,
        plan_data: dict,
        inputs_echo: Optional[dict] = None,
        notes: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> GeneratedPlan:
        plan = GeneratedPlan(
            client_id=client_id,
            subscription_id=subscription_id,
            name=name,
            engine_program_id=engine_program_id,
            engine_program_version=engine_program_version,
            plan_data=plan_data,
            inputs_echo=inputs_echo,
            notes=notes,
            created_by=created_by,
        )
        db.add(plan)
        await db.flush()
        return plan

    @staticmethod
    async def list_for_client(
        db: AsyncSession,
        client_id: UUID,
        include_inactive: bool = False,
    ) -> list[GeneratedPlan]:
        filters = [GeneratedPlan.client_id == client_id]
        if not include_inactive:
            filters.append(GeneratedPlan.is_active == True)  # noqa: E712
        result = await db.execute(
            select(GeneratedPlan)
            .where(and_(*filters))
            .order_by(GeneratedPlan.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        plan_id: UUID,
        client_id: UUID,
    ) -> Optional[GeneratedPlan]:
        result = await db.execute(
            select(GeneratedPlan).where(
                and_(
                    GeneratedPlan.id == plan_id,
                    GeneratedPlan.client_id == client_id,
                    GeneratedPlan.is_active == True,  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        plan: GeneratedPlan,
        updated_by: UUID,
        name: Optional[str] = None,
        notes: Optional[str] = None,
        plan_data: Optional[dict] = None,
    ) -> GeneratedPlan:
        if name is not None:
            plan.name = name
        if notes is not None:
            plan.notes = notes
        if plan_data is not None:
            plan.plan_data = plan_data
        plan.updated_by = updated_by
        await db.flush()
        return plan

    @staticmethod
    async def soft_delete(
        db: AsyncSession,
        plan: GeneratedPlan,
        updated_by: UUID,
    ) -> None:
        plan.is_active = False
        plan.updated_by = updated_by
        await db.flush()
