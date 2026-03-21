"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('discord_guild_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('dm_role_id', sa.String(), nullable=True),
        sa.Column('player_role_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('discord_guild_id'),
    )
    op.create_index(op.f('ix_campaigns_id'), 'campaigns', ['id'], unique=False)
    op.create_index(op.f('ix_campaigns_discord_guild_id'), 'campaigns', ['discord_guild_id'], unique=True)

    # users without the active_character_id FK yet (circular dep with characters)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('discord_id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='player'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('active_character_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_discord_id'), 'users', ['discord_id'], unique=False)

    op.create_table('characters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('character_sheet_url', sa.String(), nullable=True),
        sa.Column('class_name', sa.String(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(), nullable=False, server_default='Active'),
        sa.Column('date_of_death', sa.DateTime(), nullable=True),
        sa.Column('missions_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_characters_id'), 'characters', ['id'], unique=False)
    op.create_index(op.f('ix_characters_name'), 'characters', ['name'], unique=False)
    op.create_index(op.f('ix_characters_owner_id'), 'characters', ['owner_id'], unique=False)

    # Now add the FK from users.active_character_id -> characters.id
    op.create_foreign_key(
        'fk_users_active_character_id', 'users', 'characters',
        ['active_character_id'], ['id'],
        use_alter=True,
    )

    op.create_table('character_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=True),
        sa.Column('xp', sa.Integer(), nullable=True),
        sa.Column('scrip', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_id'),
    )
    op.create_index(op.f('ix_character_stats_id'), 'character_stats', ['id'], unique=False)

    op.create_table('items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)
    op.create_index(op.f('ix_items_name'), 'items', ['name'], unique=False)
    op.create_index(op.f('ix_items_campaign_id'), 'items', ['campaign_id'], unique=False)

    op.create_table('inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_inventory_items_id'), 'inventory_items', ['id'], unique=False)

    op.create_table('store_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('quantity_available', sa.Integer(), nullable=False, server_default='-1'),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_id'),
    )
    op.create_index(op.f('ix_store_items_id'), 'store_items', ['id'], unique=False)

    op.create_table('generated_oneshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('generation_params', sa.JSON(), nullable=False),
        sa.Column('llm_model_used', sa.String(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('content', sa.JSON(), nullable=True),
        sa.Column('foundry_module_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_generated_oneshots_id'), 'generated_oneshots', ['id'], unique=False)

    op.create_table('missions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='Available'),
        sa.Column('tier', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('last_run_date', sa.DateTime(), nullable=True),
        sa.Column('cooldown_days', sa.Integer(), nullable=True, server_default='7'),
        sa.Column('is_retired', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('is_discoverable', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('prerequisite_id', sa.Integer(), nullable=True),
        sa.Column('oneshot_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.ForeignKeyConstraint(['oneshot_id'], ['generated_oneshots.id']),
        sa.ForeignKeyConstraint(['prerequisite_id'], ['missions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_missions_id'), 'missions', ['id'], unique=False)
    op.create_index(op.f('ix_missions_name'), 'missions', ['name'], unique=False)

    op.create_table('mission_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mission_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('xp', sa.Integer(), nullable=True),
        sa.Column('scrip', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_mission_rewards_id'), 'mission_rewards', ['id'], unique=False)

    op.create_table('mission_players',
        sa.Column('mission_id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id']),
        sa.PrimaryKeyConstraint('mission_id', 'character_id'),
    )

    op.create_table('game_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('session_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='Scheduled'),
        sa.Column('after_action_report', sa.String(), nullable=True),
        sa.Column('field_report', sa.String(), nullable=True),
        sa.Column('min_players', sa.Integer(), nullable=True, server_default='4'),
        sa.Column('max_players', sa.Integer(), nullable=True, server_default='6'),
        sa.Column('result', sa.String(), nullable=True),
        sa.Column('essence_earned', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('confirmed_mission_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.ForeignKeyConstraint(['confirmed_mission_id'], ['missions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_game_sessions_id'), 'game_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_game_sessions_name'), 'game_sessions', ['name'], unique=False)

    op.create_table('game_session_players',
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id']),
        sa.PrimaryKeyConstraint('session_id', 'character_id'),
    )

    op.create_table('session_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('mission_id', sa.Integer(), nullable=False),
        sa.Column('proposed_by_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, server_default='proposed'),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id']),
        sa.ForeignKeyConstraint(['proposed_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_session_proposals_id'), 'session_proposals', ['id'], unique=False)

    op.create_table('proposal_backers',
        sa.Column('proposal_id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.ForeignKeyConstraint(['proposal_id'], ['session_proposals.id']),
        sa.PrimaryKeyConstraint('proposal_id', 'character_id'),
    )

    op.create_table('hex_maps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True, server_default='20'),
        sa.Column('height', sa.Integer(), nullable=True, server_default='20'),
        sa.Column('hex_size', sa.Integer(), nullable=True, server_default='60'),
        sa.Column('default_terrain', sa.String(), nullable=True, server_default='plains'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_hex_maps_id'), 'hex_maps', ['id'], unique=False)

    op.create_table('hexes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('map_id', sa.Integer(), nullable=False),
        sa.Column('q', sa.Integer(), nullable=False),
        sa.Column('r', sa.Integer(), nullable=False),
        sa.Column('terrain', sa.String(), nullable=True, server_default='plains'),
        sa.Column('is_discovered', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('hex_state', sa.String(), nullable=True, server_default='wilderness'),
        sa.Column('controlling_faction', sa.String(), nullable=True),
        sa.Column('player_notes', sa.JSON(), nullable=True),
        sa.Column('linked_mission_id', sa.Integer(), nullable=True),
        sa.Column('linked_location_name', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['linked_mission_id'], ['missions.id']),
        sa.ForeignKeyConstraint(['map_id'], ['hex_maps.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('map_id', 'q', 'r', name='unique_hex_coord'),
    )
    op.create_index(op.f('ix_hexes_id'), 'hexes', ['id'], unique=False)

    op.create_table('faction_reputations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('faction_name', sa.String(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.CheckConstraint('level >= -5 AND level <= 5', name='reputation_level_range'),
        sa.UniqueConstraint('campaign_id', 'faction_name', name='uq_faction_per_campaign'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_faction_reputations_id'), 'faction_reputations', ['id'], unique=False)

    op.create_table('faction_reputation_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reputation_id', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reputation_id'], ['faction_reputations.id']),
        sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_faction_reputation_events_id'), 'faction_reputation_events', ['id'], unique=False)

    op.create_table('ships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('essence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('motd', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id'),
    )
    op.create_index(op.f('ix_ships_id'), 'ships', ['id'], unique=False)

    op.create_table('ledger_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('essence_delta', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ship_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ledger_entries_id'), 'ledger_entries', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('ledger_entries')
    op.drop_table('ships')
    op.drop_table('faction_reputation_events')
    op.drop_table('faction_reputations')
    op.drop_table('hexes')
    op.drop_table('hex_maps')
    op.drop_table('proposal_backers')
    op.drop_table('session_proposals')
    op.drop_table('game_session_players')
    op.drop_table('game_sessions')
    op.drop_table('mission_players')
    op.drop_table('mission_rewards')
    op.drop_table('missions')
    op.drop_table('generated_oneshots')
    op.drop_table('store_items')
    op.drop_table('inventory_items')
    op.drop_table('items')
    op.drop_table('character_stats')
    op.drop_constraint('fk_users_active_character_id', 'users', type_='foreignkey')
    op.drop_table('characters')
    op.drop_table('users')
    op.drop_table('campaigns')
