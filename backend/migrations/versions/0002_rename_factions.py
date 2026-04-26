"""Rename hex controlling_faction values to Collegium/Limes

Revision ID: 0002_rename_factions
Revises: 0001_initial
Create Date: 2026-04-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_rename_factions'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_TO_NEW = {
    'Inheritors': 'Limes',
    'Kathedral': 'Collegium',
    'Vastarei': 'Limes',
    'Alliance': 'Collegium',
    'Rim': 'Limes',
}

_NEW_TO_OLD = {
    'Collegium': 'Kathedral',
    'Limes': 'Inheritors',
}


def upgrade() -> None:
    conn = op.get_bind()
    for old, new in _OLD_TO_NEW.items():
        conn.execute(
            sa.text("UPDATE hexes SET controlling_faction = :new WHERE controlling_faction = :old"),
            {"new": new, "old": old},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for new, old in _NEW_TO_OLD.items():
        conn.execute(
            sa.text("UPDATE hexes SET controlling_faction = :old WHERE controlling_faction = :new"),
            {"old": old, "new": new},
        )
