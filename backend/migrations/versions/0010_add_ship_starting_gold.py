"""Add starting_gold to ships table

Revision ID: 0010_add_ship_starting_gold
Revises: 0955dd9a7ee1
Create Date: 2026-11-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0010_add_ship_starting_gold'
down_revision: Union[str, None] = '0955dd9a7ee1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('ships', schema=None) as batch_op:
        batch_op.add_column(sa.Column('starting_gold', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('ships', schema=None) as batch_op:
        batch_op.drop_column('starting_gold')
