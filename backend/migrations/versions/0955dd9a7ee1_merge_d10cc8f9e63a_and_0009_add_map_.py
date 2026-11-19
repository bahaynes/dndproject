"""merge d10cc8f9e63a and 0009_add_map_routes

Revision ID: 0955dd9a7ee1
Revises: 0009_add_map_routes, d10cc8f9e63a
Create Date: 2026-11-19 15:48:27.336462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0955dd9a7ee1'
down_revision: Union[str, None] = ('0009_add_map_routes', 'd10cc8f9e63a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
