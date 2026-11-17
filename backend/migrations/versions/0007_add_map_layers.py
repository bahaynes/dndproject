"""Add map layer columns to hex_maps

Revision ID: 0007_add_map_layers
Revises: 0006_add_xp_columns
Create Date: 2026-11-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_add_map_layers'
down_revision: Union[str, None] = '0006_add_xp_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('hex_maps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('topo_image_key', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('satellite_image_key', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('layer_bounds', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('source_region', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('hex_maps', schema=None) as batch_op:
        batch_op.drop_column('source_region')
        batch_op.drop_column('layer_bounds')
        batch_op.drop_column('satellite_image_key')
        batch_op.drop_column('topo_image_key')
