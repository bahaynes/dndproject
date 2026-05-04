"""Add hidden flag and hint to mission rewards

Revision ID: 0005_add_hidden_rewards
Revises: 0004_mission_rewards_gold
Create Date: 2024-04-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_add_hidden_rewards'
down_revision: Union[str, None] = '0004_mission_rewards_gold'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('mission_rewards', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_hidden', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('hint', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('mission_rewards', schema=None) as batch_op:
        batch_op.drop_column('hint')
        batch_op.drop_column('is_hidden')
