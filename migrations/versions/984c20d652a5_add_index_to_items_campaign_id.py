"""Add index to items.campaign_id

Revision ID: 984c20d652a5
Revises:
Create Date: 2026-02-04 22:05:00.562383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '984c20d652a5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Manually adding the index creation
    op.create_index(op.f('ix_items_campaign_id'), 'items', ['campaign_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Manually removing the index
    op.drop_index(op.f('ix_items_campaign_id'), table_name='items')
