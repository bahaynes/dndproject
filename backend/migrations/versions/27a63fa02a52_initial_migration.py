"""Initial migration

Revision ID: 27a63fa02a52
Revises:
Create Date: 2025-08-23 15:56:25.304616

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27a63fa02a52'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dev reset: drop legacy tables if present to align with current models
    conn = op.get_bind()
    for table in [
        "game_session_players",
        "game_sessions",
        "mission_players",
        "mission_rewards",
        "missions",
        "store_items",
        "inventory_items",
        "character_stats",
        "items",
        "characters",
        "users",
        "hex_defs",
        "terrain_defs",
    ]:
        conn.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String, nullable=False, unique=True, index=True),
        sa.Column("email", sa.String, nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("role", sa.String, nullable=False, server_default="player"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("1")),
    )

    # Characters
    op.create_table(
        "characters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, index=True),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("image_url", sa.String, nullable=True),
        sa.Column("status", sa.Enum("ready", "deployed", "fatigued", "medical_leave", name="characterstatus"), nullable=False, server_default="ready"),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    )

    op.create_table(
        "character_stats",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("character_id", sa.Integer, sa.ForeignKey("characters.id"), nullable=False, unique=True),
        sa.Column("xp", sa.Integer, nullable=False, server_default="0"),
        sa.Column("commendations", sa.Integer, nullable=False, server_default="0"),
        sa.Column("current_hp", sa.Integer, nullable=False, server_default="0"),
        sa.Column("short_rest_available", sa.Boolean, nullable=False, server_default=sa.text("1")),
    )

    # Items and inventory
    op.create_table(
        "items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True, index=True),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("rarity", sa.String, nullable=False, server_default="common"),
        sa.Column("attunement_required", sa.Boolean, nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_attuned", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("character_id", sa.Integer, sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("items.id"), nullable=False),
    )

    op.create_table(
        "store_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("quantity_available", sa.Integer, nullable=False, server_default="-1"),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("items.id"), nullable=False, unique=True),
    )

    # Map tables
    op.create_table(
        "terrain_defs",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("travel_cost_mult", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("color_hex", sa.String, nullable=False),
        sa.Column("icon_ref", sa.String, nullable=True),
    )

    op.create_table(
        "hex_defs",
        sa.Column("coordinate", sa.String, primary_key=True),
        sa.Column("terrain_id", sa.String, sa.ForeignKey("terrain_defs.id"), nullable=False),
        sa.Column("owner", sa.Enum("alliance", "hegemony", "neutral", name="hexownership"), nullable=False, server_default="neutral"),
        sa.Column("fog_level", sa.Enum("black", "grey", "blue", name="foglevel"), nullable=False, server_default="black"),
        sa.Column("dossier_data", sa.JSON, server_default=sa.text("'{}'")),
    )

    # Missions
    op.create_table(
        "missions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("title", sa.String, nullable=False, index=True),
        sa.Column("summary", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="available"),
        sa.Column("target_hex", sa.String, sa.ForeignKey("hex_defs.coordinate"), nullable=True),
        sa.Column("dossier_data", sa.JSON, server_default=sa.text("'{}'")),
    )

    op.create_table(
        "mission_players",
        sa.Column("mission_id", sa.String, sa.ForeignKey("missions.id"), primary_key=True),
        sa.Column("character_id", sa.Integer, sa.ForeignKey("characters.id"), primary_key=True),
    )

    # Sessions
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("mission_id", sa.String, sa.ForeignKey("missions.id"), nullable=False),
        sa.Column("title", sa.String, nullable=False, index=True),
        sa.Column("session_date", sa.DateTime, nullable=False),
        sa.Column("status", sa.Enum("open", "confirmed", "completed", "cancelled", name="sessionstatus"), nullable=False, server_default="open"),
        sa.Column("route_data", sa.JSON, server_default=sa.text("'[]'")),
        sa.Column("gm_notes", sa.Text, nullable=True),
        sa.Column("aar_summary", sa.Text, nullable=True),
    )

    op.create_table(
        "game_session_players",
        sa.Column("session_id", sa.String, sa.ForeignKey("game_sessions.id"), primary_key=True),
        sa.Column("character_id", sa.Integer, sa.ForeignKey("characters.id"), primary_key=True),
    )


def downgrade() -> None:
    for table in [
        "game_session_players",
        "game_sessions",
        "mission_players",
        "missions",
        "store_items",
        "inventory_items",
        "items",
        "character_stats",
        "characters",
        "users",
        "hex_defs",
        "terrain_defs",
    ]:
        op.drop_table(table)

    for enum_name in ["sessionstatus", "foglevel", "hexownership", "characterstatus"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
