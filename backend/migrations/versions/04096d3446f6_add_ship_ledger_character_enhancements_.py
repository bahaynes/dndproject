"""Add ship ledger character enhancements session result

Revision ID: 04096d3446f6
Revises: c3d4e5f6a7b8
Create Date: 2026-03-14 20:01:37.242010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '04096d3446f6'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_tables(conn) -> set:
    return set(Inspector.from_engine(conn).get_table_names())


def _existing_columns(conn, table: str) -> set:
    return {c['name'] for c in Inspector.from_engine(conn).get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()
    tables = _existing_tables(conn)

    if 'ships' not in tables:
        op.create_table('ships',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('campaign_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('level', sa.Integer(), nullable=False),
            sa.Column('fuel', sa.Integer(), nullable=False),
            sa.Column('max_fuel', sa.Integer(), nullable=False),
            sa.Column('crystals', sa.Integer(), nullable=False),
            sa.Column('credits', sa.Integer(), nullable=False),
            sa.Column('motd', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('campaign_id')
        )
        op.create_index(op.f('ix_ships_id'), 'ships', ['id'], unique=False)

    if 'ledger_entries' not in tables:
        op.create_table('ledger_entries',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('campaign_id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.Integer(), nullable=True),
            sa.Column('event_type', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=False),
            sa.Column('fuel_delta', sa.Integer(), nullable=False),
            sa.Column('crystal_delta', sa.Integer(), nullable=False),
            sa.Column('credit_delta', sa.Integer(), nullable=False),
            sa.Column('xp_delta', sa.Integer(), nullable=False),
            sa.Column('ship_snapshot', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
            sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_ledger_entries_id'), 'ledger_entries', ['id'], unique=False)

    char_cols = _existing_columns(conn, 'characters')
    for col_name, col_def in [
        ('class_name',         sa.Column('class_name', sa.String(), nullable=True)),
        ('level',              sa.Column('level', sa.Integer(), nullable=False, server_default='1')),
        ('status',             sa.Column('status', sa.String(), nullable=False, server_default='Active')),
        ('date_of_death',      sa.Column('date_of_death', sa.DateTime(), nullable=True)),
        ('missions_completed', sa.Column('missions_completed', sa.Integer(), nullable=False, server_default='0')),
    ]:
        if col_name not in char_cols:
            op.add_column('characters', col_def)

    session_cols = _existing_columns(conn, 'game_sessions')
    for col_name, col_def in [
        ('result',          sa.Column('result', sa.String(), nullable=True)),
        ('fuel_burned',     sa.Column('fuel_burned', sa.Integer(), nullable=False, server_default='0')),
        ('crystals_earned', sa.Column('crystals_earned', sa.Integer(), nullable=False, server_default='0')),
        ('credits_earned',  sa.Column('credits_earned', sa.Integer(), nullable=False, server_default='0')),
    ]:
        if col_name not in session_cols:
            op.add_column('game_sessions', col_def)


def downgrade() -> None:
    op.drop_column('game_sessions', 'credits_earned')
    op.drop_column('game_sessions', 'crystals_earned')
    op.drop_column('game_sessions', 'fuel_burned')
    op.drop_column('game_sessions', 'result')
    op.drop_column('characters', 'missions_completed')
    op.drop_column('characters', 'date_of_death')
    op.drop_column('characters', 'status')
    op.drop_column('characters', 'level')
    op.drop_column('characters', 'class_name')
    op.drop_index(op.f('ix_ledger_entries_id'), table_name='ledger_entries')
    op.drop_table('ledger_entries')
    op.drop_index(op.f('ix_ships_id'), table_name='ships')
    op.drop_table('ships')
