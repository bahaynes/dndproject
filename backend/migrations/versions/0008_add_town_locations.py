"""Add town_locations JSON column to ships table

Revision ID: 0008_add_town_locations
Revises: 0007_session_first_hex_proposals
Create Date: 2026-11-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0008_add_town_locations'
down_revision: Union[str, None] = '0007_session_first_hex_proposals'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('ships', schema=None) as batch_op:
        batch_op.add_column(sa.Column('town_locations', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('ships', schema=None) as batch_op:
        batch_op.drop_column('town_locations')
