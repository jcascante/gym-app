"""GeneratedPlan — stores a TrainGen Engine plan blob linked to a client."""
from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Index
from app.models.base import BaseModel, GUID
from app.models.subscription import JSONBType


class GeneratedPlan(BaseModel):
    __tablename__ = "generated_plans"

    subscription_id = Column(
        GUID,
        ForeignKey('subscriptions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    client_id = Column(
        GUID,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)

    engine_program_id = Column(String(100), nullable=False)
    engine_program_version = Column(String(50), nullable=False)

    inputs_echo = Column(JSONBType, nullable=True)
    plan_data = Column(JSONBType, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        Index('ix_generated_plans_client_active', 'client_id', 'is_active'),
        Index('ix_generated_plans_subscription_client', 'subscription_id', 'client_id'),
    )
