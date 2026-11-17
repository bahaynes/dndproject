"""Add hex proposal and night-of hex selection columns to sessions

Revision ID: 0007_session_first_hex_proposals
Revises: 0006_add_xp_columns
Create Date: 2026-11-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0007_session_first_hex_proposals'
down_revision: Union[str, None] = '0006_add_xp_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('game_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confirmed_hex_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_game_sessions_confirmed_hex_id', 'hexes', ['confirmed_hex_id'], ['id'])

    with op.batch_alter_table('session_proposals', schema=None) as batch_op:
        batch_op.alter_column('mission_id', existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column('hex_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_session_proposals_hex_id', 'hexes', ['hex_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('session_proposals', schema=None) as batch_op:
        batch_op.drop_constraint('fk_session_proposals_hex_id', type_='foreignkey')
        batch_op.drop_column('hex_id')
        batch_op.alter_column('mission_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('game_sessions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_game_sessions_confirmed_hex_id', type_='foreignkey')
        batch_op.drop_column('confirmed_hex_id')
