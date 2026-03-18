"""Replace fuel/crystals/credits with single Essence resource

Revision ID: 0002_essence_resource
Revises: 0001_initial
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0002_essence_resource'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ships: drop fuel/max_fuel/crystals/credits, add essence
    op.add_column('ships', sa.Column('essence', sa.Integer(), nullable=False, server_default='0'))
    op.drop_column('ships', 'fuel')
    op.drop_column('ships', 'max_fuel')
    op.drop_column('ships', 'crystals')
    op.drop_column('ships', 'credits')

    # Ledger entries: drop 4 delta columns, add essence_delta
    op.add_column('ledger_entries', sa.Column('essence_delta', sa.Integer(), nullable=False, server_default='0'))
    op.drop_column('ledger_entries', 'fuel_delta')
    op.drop_column('ledger_entries', 'crystal_delta')
    op.drop_column('ledger_entries', 'credit_delta')
    op.drop_column('ledger_entries', 'xp_delta')


def downgrade() -> None:
    # Restore ledger delta columns
    op.add_column('ledger_entries', sa.Column('xp_delta', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ledger_entries', sa.Column('credit_delta', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ledger_entries', sa.Column('crystal_delta', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ledger_entries', sa.Column('fuel_delta', sa.Integer(), nullable=False, server_default='0'))
    op.drop_column('ledger_entries', 'essence_delta')

    # Restore ship columns
    op.add_column('ships', sa.Column('credits', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ships', sa.Column('crystals', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('ships', sa.Column('max_fuel', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('ships', sa.Column('fuel', sa.Integer(), nullable=False, server_default='100'))
    op.drop_column('ships', 'essence')
