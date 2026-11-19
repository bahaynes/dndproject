"""Merge heads and add routes JSON column to hex_maps

Revision ID: 0009_add_map_routes
Revises: 0008_add_map_layers, 0008_add_town_locations
Create Date: 2026-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_add_map_routes'
down_revision: Union[str, Sequence[str], None] = ('0008_add_map_layers', '0008_add_town_locations')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('hex_maps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('routes', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('hex_maps', schema=None) as batch_op:
        batch_op.drop_column('routes')
