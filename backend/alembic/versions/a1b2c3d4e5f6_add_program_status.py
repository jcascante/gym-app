"""add program status

Revision ID: a1b2c3d4e5f6
Revises: 3dbdba4eec75
Create Date: 2026-02-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '3dbdba4eec75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('programs', sa.Column('status', sa.String(20), nullable=True))
    op.create_index('ix_programs_status', 'programs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_programs_status', table_name='programs')
    op.drop_column('programs', 'status')
