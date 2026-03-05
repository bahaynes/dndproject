"""add oneshot_id to missions

Revision ID: 5f2a1b3c4d5e
Revises: 43d88e4142dc
Create Date: 2026-02-08 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f2a1b3c4d5e'
down_revision: Union[str, None] = '43d88e4142dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add oneshot_id column to missions table.
    # FK constraint omitted — SQLite does not support ALTER TABLE ADD CONSTRAINT.
    # The relationship is enforced at the ORM level.
    op.add_column('missions', sa.Column('oneshot_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('missions', 'oneshot_id')
