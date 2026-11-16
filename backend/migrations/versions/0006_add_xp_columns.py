"""Add xp columns to character_stats and mission_rewards

Revision ID: 0006_add_xp_columns
Revises: 0005_add_hidden_rewards
Create Date: 2026-11-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_add_xp_columns'
down_revision: Union[str, None] = '0005_add_hidden_rewards'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('character_stats', schema=None) as batch_op:
        batch_op.add_column(sa.Column('xp', sa.Integer(), server_default='0', nullable=False))

    with op.batch_alter_table('mission_rewards', schema=None) as batch_op:
        batch_op.add_column(sa.Column('xp', sa.Integer(), server_default='0', nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('mission_rewards', schema=None) as batch_op:
        batch_op.drop_column('xp')

    with op.batch_alter_table('character_stats', schema=None) as batch_op:
        batch_op.drop_column('xp')
