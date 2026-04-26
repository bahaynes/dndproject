"""Replace xp/scrip with gold on character_stats

Revision ID: 0003_character_stats_gold
Revises: 0002_rename_factions
Create Date: 2026-04-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003_character_stats_gold'
down_revision: Union[str, None] = '0002_rename_factions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('character_stats') as batch_op:
        batch_op.add_column(sa.Column('gold', sa.Integer(), nullable=False, server_default='0'))
        batch_op.drop_column('xp')
        batch_op.drop_column('scrip')


def downgrade() -> None:
    with op.batch_alter_table('character_stats') as batch_op:
        batch_op.add_column(sa.Column('scrip', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('xp', sa.Integer(), nullable=False, server_default='0'))
        batch_op.drop_column('gold')
