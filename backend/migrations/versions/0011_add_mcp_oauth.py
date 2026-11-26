"""Add MCP OAuth tables and missions.foundry_module

Revision ID: 0011_add_mcp_oauth
Revises: 0010_add_ship_starting_gold
Create Date: 2026-11-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0011_add_mcp_oauth'
down_revision: Union[str, None] = '0010_add_ship_starting_gold'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'oauth_clients',
        sa.Column('client_id', sa.String(), primary_key=True),
        sa.Column('client_name', sa.String(), nullable=True),
        sa.Column('redirect_uris', sa.JSON(), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'oauth_pending_authorizations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('redirect_uri', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('code_challenge', sa.String(), nullable=False),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('scopes', sa.String(), nullable=False),
        sa.Column('csrf', sa.String(), nullable=False),
        sa.Column('client_consented', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('discord_id', sa.String(), nullable=True),
        sa.Column('discord_username', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'oauth_grants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('scopes', sa.String(), nullable=False),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_oauth_grants_id', 'oauth_grants', ['id'])
    op.create_index('ix_oauth_grants_user_id', 'oauth_grants', ['user_id'])
    op.create_index('ix_oauth_grants_campaign_id', 'oauth_grants', ['campaign_id'])
    op.create_table(
        'oauth_codes',
        sa.Column('code_hash', sa.String(), primary_key=True),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('redirect_uri', sa.String(), nullable=False),
        sa.Column('code_challenge', sa.String(), nullable=False),
        sa.Column('code_challenge_method', sa.String(), nullable=False, server_default='S256'),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('scopes', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('grant_id', sa.Integer(), sa.ForeignKey('oauth_grants.id'), nullable=True),
    )
    op.create_table(
        'oauth_refresh_tokens',
        sa.Column('token_hash', sa.String(), primary_key=True),
        sa.Column('grant_id', sa.Integer(), sa.ForeignKey('oauth_grants.id'), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('replaced_by', sa.String(), nullable=True),
    )
    op.create_index('ix_oauth_refresh_tokens_grant_id', 'oauth_refresh_tokens', ['grant_id'])
    op.create_table(
        'oauth_consents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('discord_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('scopes', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('discord_id', 'client_id', 'campaign_id', name='uq_oauth_consent'),
    )
    op.create_index('ix_oauth_consents_id', 'oauth_consents', ['id'])
    op.create_index('ix_oauth_consents_discord_id', 'oauth_consents', ['discord_id'])

    with op.batch_alter_table('missions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('foundry_module', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('missions', schema=None) as batch_op:
        batch_op.drop_column('foundry_module')

    op.drop_table('oauth_consents')
    op.drop_table('oauth_refresh_tokens')
    op.drop_table('oauth_codes')
    op.drop_table('oauth_grants')
    op.drop_table('oauth_pending_authorizations')
    op.drop_table('oauth_clients')
