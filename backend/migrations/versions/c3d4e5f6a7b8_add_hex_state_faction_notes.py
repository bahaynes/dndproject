"""add hex_state, controlling_faction, player_notes to hexes

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hexes', sa.Column('hex_state', sa.String(), nullable=True, server_default='wilderness'))
    op.add_column('hexes', sa.Column('controlling_faction', sa.String(), nullable=True))
    op.add_column('hexes', sa.Column('player_notes', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('hexes', 'player_notes')
    op.drop_column('hexes', 'controlling_faction')
    op.drop_column('hexes', 'hex_state')
