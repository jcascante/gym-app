"""
CLIENT-facing saved generated plan endpoints.
All routes scoped to the authenticated CLIENT user.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_client_user
from app.models.user import User
from app.schemas.generated_plan import (
    GeneratedPlanCreate,
    GeneratedPlanResponse,
    GeneratedPlanSummary,
    GeneratedPlanUpdate,
)
from app.services.generated_plan_service import GeneratedPlanService

router = APIRouter(prefix="/me/plans", tags=["My Generated Plans"])


@router.post("", response_model=GeneratedPlanResponse, status_code=status.HTTP_201_CREATED)
async def save_plan(
    body: GeneratedPlanCreate,
    current_user: User = Depends(get_client_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await GeneratedPlanService.create(
        db=db,
        client_id=current_user.id,
        subscription_id=current_user.subscription_id,
        name=body.name,
        engine_program_id=body.engine_program_id,
        engine_program_version=body.engine_program_version,
        plan_data=body.plan_data,
        inputs_echo=body.inputs_echo,
        notes=body.notes,
        created_by=current_user.id,
    )
    await db.commit()
    await db.refresh(plan)
    return GeneratedPlanResponse.model_validate(plan)


@router.get("", response_model=list[GeneratedPlanSummary])
async def list_my_plans(
    current_user: User = Depends(get_client_user),
    db: AsyncSession = Depends(get_db),
):
    plans = await GeneratedPlanService.list_for_client(db=db, client_id=current_user.id)
    return [GeneratedPlanSummary.model_validate(p) for p in plans]


@router.get("/{plan_id}", response_model=GeneratedPlanResponse)
async def get_my_plan(
    plan_id: UUID,
    current_user: User = Depends(get_client_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await GeneratedPlanService.get_by_id(
        db=db, plan_id=plan_id, client_id=current_user.id
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return GeneratedPlanResponse.model_validate(plan)


@router.patch("/{plan_id}", response_model=GeneratedPlanResponse)
async def update_my_plan(
    plan_id: UUID,
    body: GeneratedPlanUpdate,
    current_user: User = Depends(get_client_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await GeneratedPlanService.get_by_id(
        db=db, plan_id=plan_id, client_id=current_user.id
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    plan = await GeneratedPlanService.update(
        db=db,
        plan=plan,
        updated_by=current_user.id,
        name=body.name,
        notes=body.notes,
        plan_data=body.plan_data,
    )
    await db.commit()
    await db.refresh(plan)
    return GeneratedPlanResponse.model_validate(plan)


@router.delete("/{plan_id}")
async def delete_my_plan(
    plan_id: UUID,
    current_user: User = Depends(get_client_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await GeneratedPlanService.get_by_id(
        db=db, plan_id=plan_id, client_id=current_user.id
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    await GeneratedPlanService.soft_delete(db=db, plan=plan, updated_by=current_user.id)
    await db.commit()
    return {"deleted": True}
