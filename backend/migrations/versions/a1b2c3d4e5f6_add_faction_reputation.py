"""add faction reputation

Revision ID: a1b2c3d4e5f6
Revises: 5f2a1b3c4d5e
Create Date: 2026-03-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5f2a1b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'faction_reputations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('faction_name', sa.String(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('level >= -5 AND level <= 5', name='reputation_level_range'),
    )
    op.create_index('ix_faction_reputations_id', 'faction_reputations', ['id'])

    op.create_table(
        'faction_reputation_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reputation_id', sa.Integer(), sa.ForeignKey('faction_reputations.id'), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('game_sessions.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_faction_reputation_events_id', 'faction_reputation_events', ['id'])


def downgrade() -> None:
    op.drop_index('ix_faction_reputation_events_id', 'faction_reputation_events')
    op.drop_table('faction_reputation_events')
    op.drop_index('ix_faction_reputations_id', 'faction_reputations')
    op.drop_table('faction_reputations')
