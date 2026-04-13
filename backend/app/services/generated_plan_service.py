"""Business logic for saving and retrieving GeneratedPlan records."""
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
        inputs_echo: dict | None = None,
        notes: str | None = None,
        created_by: UUID | None = None,
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
        unstarted_only: bool = False,
    ) -> list[GeneratedPlan]:
        filters = [GeneratedPlan.client_id == client_id]
        if not include_inactive:
            filters.append(GeneratedPlan.is_active == True)  # noqa: E712
        if unstarted_only:
            filters.append(GeneratedPlan.assignment_id.is_(None))
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
    ) -> GeneratedPlan | None:
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
        name: str | None = None,
        notes: str | None = None,
        plan_data: dict | None = None,
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
