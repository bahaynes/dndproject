"""Replace xp/scrip with gold on mission_rewards

Revision ID: 0004_mission_rewards_gold
Revises: 0003_character_stats_gold
Create Date: 2026-04-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0004_mission_rewards_gold'
down_revision: Union[str, None] = '0003_character_stats_gold'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('mission_rewards') as batch_op:
        batch_op.add_column(sa.Column('gold', sa.Integer(), nullable=True))
        batch_op.drop_column('xp')
        batch_op.drop_column('scrip')


def downgrade() -> None:
    with op.batch_alter_table('mission_rewards') as batch_op:
        batch_op.add_column(sa.Column('scrip', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('xp', sa.Integer(), nullable=True))
        batch_op.drop_column('gold')
