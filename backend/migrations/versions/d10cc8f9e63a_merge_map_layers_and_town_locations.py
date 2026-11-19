"""merge map_layers and town_locations

Revision ID: d10cc8f9e63a
Revises: 0008_add_map_layers, 0008_add_town_locations
Create Date: 2026-11-19 15:27:59.589650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd10cc8f9e63a'
down_revision: Union[str, None] = ('0008_add_map_layers', '0008_add_town_locations')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
