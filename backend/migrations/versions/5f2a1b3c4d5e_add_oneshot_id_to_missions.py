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
    # Add oneshot_id column to missions table
    op.add_column('missions', sa.Column('oneshot_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_missions_oneshot_id', 'missions', 'generated_oneshots', ['oneshot_id'], ['id'])


def downgrade() -> None:
    # Remove oneshot_id column from missions table
    op.drop_constraint('fk_missions_oneshot_id', 'missions', type_='foreignkey')
    op.drop_column('missions', 'oneshot_id')
